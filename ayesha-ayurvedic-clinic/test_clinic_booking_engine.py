"""
Automated Comprehensive Test Suite for Ayesha Ayurvedic Clinic Booking Engine
Tests all mandatory invariants, capacity limits, WhatsApp/Zoom automation, and boundary conditions.
"""

import unittest
import sqlite3
import os
import json
import threading
from datetime import datetime, date, time, timedelta, timezone
import urllib.request
import urllib.parse
from server import run_server, DB_FILE, CLINIC_TIMEZONE, DAILY_ONLINE_LIMIT, WEEKLY_ONLINE_LIMIT

TEST_PORT = 8999
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

class ClinicBookingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reset test DB
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
            except Exception:
                pass

        # Start server in background thread
        cls.server_thread = threading.Thread(target=run_server, args=(TEST_PORT,), daemon=True)
        cls.server_thread.start()

        # Wait briefly for server to bind
        import time as tm
        tm.sleep(1.0)

    def api_get(self, path):
        req = urllib.request.Request(f"{BASE_URL}{path}")
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def api_post(self, path, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def test_01_clinic_info_verified_data(self):
        status, data = self.api_get("/api/clinic")
        self.assertEqual(status, 200)
        self.assertEqual(data["name"], "Ayesha Ayurvedic Clinic")
        self.assertEqual(data["registrationNumber"], "2545/A/2025")
        self.assertEqual(data["primaryPhone"], "+91 8465058469")
        self.assertEqual(data["primaryWhatsApp"], "+91 8465058469")
        self.assertIn("https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac", data["googleMapsUrl"])

    def test_02_treatments_directory_from_poster(self):
        status, data = self.api_get("/api/treatments")
        self.assertEqual(status, 200)
        self.assertTrue(len(data) >= 20)
        # Check special therapies
        names = [t["name_english"] for t in data]
        self.assertIn("Panchakarma Detox Therapy", names)
        self.assertIn("Suvarnaprashana Immunization", names)
        self.assertIn("PCOD & PCOS Management", names)
        self.assertIn("Skin Diseases & Allergies", names)

    def test_03_availability_matrix_only_wednesdays_and_fridays(self):
        status, data = self.api_get("/api/availability?weeks=4")
        self.assertEqual(status, 200)
        days = data["days"]
        self.assertTrue(len(days) >= 8)
        for d in days:
            self.assertIn(d["weekday"], ["WEDNESDAY", "FRIDAY"])
            self.assertEqual(d["dayLimit"], 3)
            self.assertEqual(d["weekLimit"], 6)

    def test_04_reject_booking_on_ineligible_day(self):
        # 2026-10-27 is a Tuesday
        payload = {
            "patientName": "Ramesh Kumar",
            "phone": "+91 9876543210",
            "startsAt": "2026-10-27T17:30:00+05:30",
            "consultationType": "VOICE_CALL"
        }
        status, data = self.api_post("/api/appointments", payload)
        self.assertEqual(status, 400)
        self.assertIn("Wednesday and Friday", data["message"])

    def test_05_reject_booking_outside_time_window(self):
        # 2026-10-28 is a Wednesday, but 10:00 AM is outside 5:00 PM - 8:30 PM
        payload = {
            "patientName": "Ramesh Kumar",
            "phone": "+91 9876543210",
            "startsAt": "2026-10-28T10:00:00+05:30",
            "consultationType": "VOICE_CALL"
        }
        status, data = self.api_post("/api/appointments", payload)
        self.assertEqual(status, 400)
        self.assertIn("5:00 PM and 8:30 PM", data["message"])

    def test_06_successful_voice_call_booking_and_message(self):
        # 2026-10-28 is a Wednesday at 17:30 IST
        payload = {
            "patientName": "Sita Lakshmi",
            "phone": "+91 9440112233",
            "startsAt": "2026-10-28T17:30:00+05:30",
            "consultationType": "VOICE_CALL",
            "age": 34,
            "healthConcern": "Acidity and indigestion"
        }
        status, data = self.api_post("/api/appointments", payload)
        self.assertEqual(status, 201)
        self.assertEqual(data["consultationType"], "VOICE_CALL")
        self.assertTrue(data["reference"].startswith("AAC-"))
        self.assertIn("doctor will call you during 5:00-8:30 PM", data["message"].lower())
        self.assertIsNone(data["zoomMeetingLink"])
        
        # WhatsApp notification check
        notif = data["notification"]
        self.assertIn("Voice Call", notif["patientMessage"])
        self.assertIn("+91 8465058469", notif["patientMessage"])

    def test_07_successful_video_call_booking_and_zoom_automation(self):
        # 2026-10-28 Wednesday at 18:15 IST
        payload = {
            "patientName": "Venkatesh Rao",
            "phone": "+91 9848123456",
            "startsAt": "2026-10-28T18:15:00+05:30",
            "consultationType": "VIDEO_CALL",
            "age": 42,
            "healthConcern": "Joint pain and arthritis"
        }
        status, data = self.api_post("/api/appointments", payload)
        self.assertEqual(status, 201)
        self.assertEqual(data["consultationType"], "VIDEO_CALL")
        self.assertIn("zoom meeting on whatsapp", data["message"].lower())
        self.assertIsNotNone(data["zoomMeetingLink"])
        self.assertIn("zoom.us/j/846", data["zoomMeetingLink"])
        self.assertIsNotNone(data["zoomPasscode"])

        # Check Zoom link in WhatsApp message
        notif = data["notification"]
        self.assertIn("Video Call (Zoom)", notif["patientMessage"])
        self.assertIn(data["zoomMeetingLink"], notif["patientMessage"])

    def test_08_daily_capacity_limit_enforcement(self):
        # 3rd booking on Wednesday 2026-10-28
        payload3 = {
            "patientName": "Ananya Sharma",
            "phone": "+91 9123456780",
            "startsAt": "2026-10-28T19:00:00+05:30",
            "consultationType": "VOICE_CALL"
        }
        status3, data3 = self.api_post("/api/appointments", payload3)
        self.assertEqual(status3, 201)

        # 4th booking attempt on the SAME Wednesday must be rejected (max 3/day)
        payload4 = {
            "patientName": "Surya Prakash",
            "phone": "+91 9123456789",
            "startsAt": "2026-10-28T20:00:00+05:30",
            "consultationType": "VOICE_CALL"
        }
        status4, data4 = self.api_post("/api/appointments", payload4)
        self.assertEqual(status4, 409)
        self.assertIn("maximum capacity of 3 online appointments", data4["message"])

    def test_09_weekly_capacity_limit_enforcement(self):
        # Now fill Friday (2026-10-30) of the SAME week with 3 bookings
        for i, slot_time in enumerate(["17:00", "18:00", "19:00"]):
            payload = {
                "patientName": f"Friday Patient {i+1}",
                "phone": f"+91 900000000{i}",
                "startsAt": f"2026-10-30T{slot_time}:00+05:30",
                "consultationType": "VIDEO_CALL"
            }
            status, data = self.api_post("/api/appointments", payload)
            self.assertEqual(status, 201)

        # Total for week of Oct 26-Nov 1 is now 3 (Wed) + 3 (Fri) = 6.
        # Now any 7th booking attempt for this week must be rejected!
        payload_seventh = {
            "patientName": "Seventh Patient",
            "phone": "+91 9999999999",
            "startsAt": "2026-10-30T20:00:00+05:30",
            "consultationType": "VOICE_CALL"
        }
        status_seven, data_seven = self.api_post("/api/appointments", payload_seventh)
        self.assertEqual(status_seven, 409)
        self.assertIn("maximum quota of 6 online appointments", data_seven["message"])

    def test_10_cancellation_releases_capacity(self):
        # Look up one of the Friday appointments
        status_list, data_admin = self.api_get("/api/admin/appointments")
        self.assertEqual(status_list, 200)
        friday_appt = [a for a in data_admin["appointments"] if "2026-10-30" in a["starts_at"]][0]

        ref = friday_appt["reference_code"]
        phone = friday_appt["patient_phone"]

        # Cancel it
        status_cancel, data_cancel = self.api_post("/api/appointments/cancel", {"referenceCode": ref, "phone": phone})
        self.assertEqual(status_cancel, 200)

        # Now weekly total drops to 5, so a new booking on Friday 2026-10-30 must succeed!
        payload_retry = {
            "patientName": "New Slot Patient",
            "phone": "+91 9777788888",
            "startsAt": "2026-10-30T20:00:00+05:30",
            "consultationType": "VOICE_CALL"
        }
        status_retry, data_retry = self.api_post("/api/appointments", payload_retry)
        self.assertEqual(status_retry, 201)

    def test_11_patient_lookup(self):
        # Lookup an existing appointment
        status_admin, data_admin = self.api_get("/api/admin/appointments")
        appt = data_admin["appointments"][0]
        ref = appt["reference_code"]
        phone = appt["patient_phone"]

        status, data = self.api_get(f"/api/appointments/lookup?referenceCode={ref}&phone={urllib.parse.quote(phone)}")
        self.assertEqual(status, 200)
        self.assertEqual(data["reference_code"], ref)

if __name__ == "__main__":
    unittest.main()
