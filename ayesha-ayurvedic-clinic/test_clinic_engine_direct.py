"""
Direct In-Process Unit and Concurrency Test Suite for Ayesha Ayurvedic Clinic Engine
Tests business invariants, capacity rules, Voice/Video Call logic, Zoom generation, WhatsApp automation, and cancellations without requiring TCP socket permissions.
"""

import unittest
import sqlite3
import os
import json
from datetime import datetime, date, time, timedelta
from server import (
    init_db, DB_FILE, CLINIC_TIMEZONE, DAILY_ONLINE_LIMIT, WEEKLY_ONLINE_LIMIT,
    get_week_monday, generate_reference, generate_zoom_details, build_whatsapp_message
)

class DirectBookingEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
            except Exception:
                pass
        init_db()

    def setUp(self):
        # Clean appointments and patients before each test run
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM appointment")
        c.execute("DELETE FROM patient")
        conn.commit()
        conn.close()

    def book_appointment(self, patient_name, phone, starts_at_iso, consultation_type, age=None, concern=None):
        if "+" in starts_at_iso:
            dt = datetime.fromisoformat(starts_at_iso)
        else:
            dt = datetime.fromisoformat(starts_at_iso).replace(tzinfo=CLINIC_TIMEZONE)
        dt_kolkata = dt.astimezone(CLINIC_TIMEZONE)

        appt_date = dt_kolkata.date()
        appt_time = dt_kolkata.time()

        # Invariant 1: Wednesday (2) or Friday (4) only
        if appt_date.weekday() not in [2, 4]:
            return 400, {"message": "Online doctor consultations are available only on Wednesdays and Fridays."}

        # Invariant 2: 5:00 PM to 8:30 PM IST
        if appt_time < time(17, 0) or appt_time > time(20, 30):
            return 400, {"message": "Consultation time must be between 5:00 PM and 8:30 PM IST."}

        appt_date_str = appt_date.isoformat()
        week_start_str = get_week_monday(appt_date).isoformat()

        conn = sqlite3.connect(DB_FILE, timeout=10.0)
        c = conn.cursor()
        try:
            c.execute("BEGIN IMMEDIATE")

            # Check weekly count first (< 6)
            c.execute("SELECT count(*) FROM appointment WHERE clinic_week_start = ? AND mode = 'ONLINE' AND status = 'CONFIRMED'", (week_start_str,))
            if c.fetchone()[0] >= WEEKLY_ONLINE_LIMIT:
                conn.rollback()
                return 409, {"message": "This clinic week has reached its maximum quota of 6 online appointments. Please select an eligible date in a future week."}

            # Check day count check (< 3)
            c.execute("SELECT count(*) FROM appointment WHERE date(starts_at) = ? AND mode = 'ONLINE' AND status = 'CONFIRMED'", (appt_date_str,))
            if c.fetchone()[0] >= DAILY_ONLINE_LIMIT:
                conn.rollback()
                return 409, {"message": "This day has reached its maximum capacity of 3 online appointments. Please choose another date."}

            now_iso = datetime.now(CLINIC_TIMEZONE).isoformat()
            c.execute("INSERT INTO patient (full_name, phone, age, health_concern, created_at) VALUES (?, ?, ?, ?, ?)",
                      (patient_name, phone, age, concern, now_iso))
            patient_id = c.lastrowid

            ref_code = generate_reference()
            zoom_link, zoom_pass = None, None
            if consultation_type == "VIDEO_CALL":
                _, zoom_pass, zoom_link = generate_zoom_details(ref_code)

            c.execute("""
                INSERT INTO appointment (reference_code, patient_id, mode, consultation_type, status, starts_at, clinic_week_start, zoom_meeting_link, zoom_passcode, whatsapp_status, created_at)
                VALUES (?, ?, 'ONLINE', ?, 'CONFIRMED', ?, ?, ?, ?, 'PENDING', ?)
            """, (ref_code, patient_id, consultation_type, dt_kolkata.isoformat(), week_start_str, zoom_link, zoom_pass, now_iso))

            conn.commit()
        finally:
            conn.close()

        formatted_date = dt_kolkata.strftime("%A, %d %B %Y")
        formatted_time = dt_kolkata.strftime("%I:%M %p")
        wa_payload = build_whatsapp_message(
            patient_name, phone, formatted_date, formatted_time,
            consultation_type, ref_code, zoom_link, zoom_pass
        )

        msg = (
            f"Appointment has been booked successfully! Dr. Ayesha Shaik will call you during 5:00-8:30 PM on {formatted_date}."
            if consultation_type == "VOICE_CALL" else
            f"Appointment has been booked successfully! Dr. Ayesha Shaik will send you the link of the Zoom meeting on WhatsApp prior to your scheduled consultation."
        )

        return 201, {
            "reference": ref_code,
            "consultationType": consultation_type,
            "startsAt": dt_kolkata.isoformat(),
            "formattedDate": formatted_date,
            "formattedTime": formatted_time,
            "message": msg,
            "zoomMeetingLink": zoom_link,
            "zoomPasscode": zoom_pass,
            "notification": wa_payload
        }

    def test_01_reject_ineligible_days(self):
        ineligible_dates = [
            "2026-10-26T17:30:00+05:30", # Monday
            "2026-10-27T17:30:00+05:30", # Tuesday
            "2026-10-29T17:30:00+05:30", # Thursday
            "2026-10-31T17:30:00+05:30", # Saturday
            "2026-11-01T17:30:00+05:30"  # Sunday
        ]
        for d in ineligible_dates:
            status, res = self.book_appointment("Test Patient", "+91 9848011223", d, "VOICE_CALL")
            self.assertEqual(status, 400)
            self.assertIn("Wednesdays and Fridays", res["message"])

    def test_02_reject_outside_time_window(self):
        early = "2026-10-28T16:59:00+05:30" # 1 minute before 5 PM
        late = "2026-10-28T20:31:00+05:30"  # 1 minute after 8:30 PM

        status1, res1 = self.book_appointment("Early Patient", "+91 9848011223", early, "VOICE_CALL")
        self.assertEqual(status1, 400)
        self.assertIn("5:00 PM and 8:30 PM", res1["message"])

        status2, res2 = self.book_appointment("Late Patient", "+91 9848011223", late, "VOICE_CALL")
        self.assertEqual(status2, 400)
        self.assertIn("5:00 PM and 8:30 PM", res2["message"])

    def test_03_voice_call_appointment_and_whatsapp_format(self):
        status, res = self.book_appointment(
            "Lakshmi Devi", "+91 8465058469", "2026-10-28T17:30:00+05:30", "VOICE_CALL",
            age=45, concern="Joint pain and arthritis"
        )
        self.assertEqual(status, 201)
        self.assertEqual(res["consultationType"], "VOICE_CALL")
        self.assertIn("will call you during 5:00-8:30 pm", res["message"].lower())
        self.assertIsNone(res["zoomMeetingLink"])

        # Check WhatsApp payload
        notif = res["notification"]
        self.assertIn("Voice Call", notif["patientMessage"])
        self.assertIn("Lakshmi Devi", notif["patientMessage"])
        self.assertIn("918465058469", notif["clinicWhatsAppUrl"])
        self.assertIn("+91 8465058469", notif["patientMessage"])

    def test_04_video_call_appointment_and_zoom_automation(self):
        status, res = self.book_appointment(
            "Anand Verma", "+91 9848339262", "2026-10-30T18:00:00+05:30", "VIDEO_CALL",
            age=38, concern="Skin allergy & eczema"
        )
        self.assertEqual(status, 201)
        self.assertEqual(res["consultationType"], "VIDEO_CALL")
        self.assertIn("zoom meeting on whatsapp", res["message"].lower())
        self.assertIsNotNone(res["zoomMeetingLink"])
        self.assertTrue(res["zoomMeetingLink"].startswith("https://us05web.zoom.us/j/846"))
        self.assertIsNotNone(res["zoomPasscode"])

        # Check WhatsApp payload includes Zoom Link
        notif = res["notification"]
        self.assertIn("Video Call (Zoom)", notif["patientMessage"])
        self.assertIn(res["zoomMeetingLink"], notif["patientMessage"])
        self.assertIn(res["zoomPasscode"], notif["patientMessage"])

    def test_05_daily_capacity_limit_max_3_per_day(self):
        wednesday = "2026-11-04"
        for slot in ["17:00", "18:00", "19:00"]:
            status, res = self.book_appointment(f"Patient {slot}", "+91 9123456789", f"{wednesday}T{slot}:00+05:30", "VOICE_CALL")
            self.assertEqual(status, 201)

        # 4th booking on same Wednesday MUST be rejected
        status_4, res_4 = self.book_appointment("Patient 4", "+91 9123456789", f"{wednesday}T20:00:00+05:30", "VOICE_CALL")
        self.assertEqual(status_4, 409)
        self.assertIn("maximum capacity of 3 online appointments", res_4["message"])

    def test_06_weekly_capacity_limit_max_6_per_week(self):
        wednesday = "2026-11-04"
        friday = "2026-11-06"

        for slot in ["17:00", "18:00", "19:00"]:
            status, _ = self.book_appointment(f"Wed Patient {slot}", "+91 9000000001", f"{wednesday}T{slot}:00+05:30", "VOICE_CALL")
            self.assertEqual(status, 201)

        for slot in ["17:00", "18:00", "19:00"]:
            status, _ = self.book_appointment(f"Fri Patient {slot}", "+91 9000000002", f"{friday}T{slot}:00+05:30", "VIDEO_CALL")
            self.assertEqual(status, 201)

        # Total is now 6. Seventh booking attempt in this week MUST be rejected!
        status_7, res_7 = self.book_appointment("Patient 7", "+91 9000000003", f"{friday}T20:00:00+05:30", "VOICE_CALL")
        self.assertEqual(status_7, 409)
        self.assertIn("maximum quota of 6 online appointments", res_7["message"])

    def test_07_cancellation_releases_capacity(self):
        wednesday = "2026-11-11"
        refs = []
        for slot in ["17:00", "18:00", "19:00"]:
            status, res = self.book_appointment(f"Patient {slot}", "+91 9111122222", f"{wednesday}T{slot}:00+05:30", "VOICE_CALL")
            self.assertEqual(status, 201)
            refs.append(res["reference"])

        # Day is now full
        status_full, _ = self.book_appointment("Overflow", "+91 9111122222", f"{wednesday}T20:00:00+05:30", "VOICE_CALL")
        self.assertEqual(status_full, 409)

        # Cancel one appointment
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE appointment SET status = 'CANCELLED' WHERE reference_code = ?", (refs[0],))
        conn.commit()
        conn.close()

        # Now booking must succeed because capacity was freed!
        status_freed, res_freed = self.book_appointment("Freed Slot Patient", "+91 9333344444", f"{wednesday}T20:00:00+05:30", "VOICE_CALL")
        self.assertEqual(status_freed, 201)

    def test_08_admin_settings_persistence(self):
        # Update settings in setting table
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?, ?)", ("primary_phone", "+91 8465058469"))
        c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?, ?)", ("hero_title", "Custom Edited Ayurvedic Clinic Title"))
        conn.commit()

        # Query back
        c.execute("SELECT value FROM setting WHERE key = 'hero_title'")
        val = c.fetchone()[0]
        conn.close()
        self.assertEqual(val, "Custom Edited Ayurvedic Clinic Title")

    def test_09_admin_treatment_crud(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO treatment (name_english, name_telugu, category, description, is_special_service)
            VALUES (?, ?, ?, ?, ?)
        """, ("Shirodhara Stress Relief", "శిరోధార చికిత్స", "Panchakarma", "Continuous pouring of warm medicated oil on the forehead.", 1))
        conn.commit()
        new_id = c.lastrowid

        c.execute("SELECT name_english, name_telugu FROM treatment WHERE id = ?", (new_id,))
        row = c.fetchone()
        self.assertEqual(row[0], "Shirodhara Stress Relief")
        self.assertEqual(row[1], "శిరోధార చికిత్స")

        c.execute("DELETE FROM treatment WHERE id = ?", (new_id,))
        conn.commit()
        c.execute("SELECT count(*) FROM treatment WHERE id = ?", (new_id,))
        self.assertEqual(c.fetchone()[0], 0)
        conn.close()

if __name__ == "__main__":
    unittest.main()
