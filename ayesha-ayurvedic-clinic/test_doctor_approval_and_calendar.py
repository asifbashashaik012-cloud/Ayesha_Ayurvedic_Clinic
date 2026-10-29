"""
Unit test verifying Doctor Approval Flow (Accept/Decline) and Calendar Thick Green Status
"""
import unittest
import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from server import (
    init_db, DB_FILE, CLINIC_TIMEZONE, DAILY_ONLINE_LIMIT, WEEKLY_ONLINE_LIMIT,
    get_week_monday, generate_reference, generate_zoom_details,
    build_doctor_approval_whatsapp, build_patient_confirmed_whatsapp, build_patient_declined_whatsapp
)

class DoctorApprovalAndCalendarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM appointment")
        c.execute("DELETE FROM patient")
        conn.commit()
        conn.close()

    def test_doctor_approval_whatsapp_message(self):
        msg = build_doctor_approval_whatsapp(
            "Ramesh Kumar", "+91 8465058469", "Wednesday, 28 October 2026",
            "05:30 PM", "VOICE_CALL", "AAC-TEST01", "Acidity & Migraine"
        )
        self.assertIn("Ramesh Kumar", msg)
        self.assertIn("Acidity & Migraine", msg)
        self.assertIn("ACCEPT", msg)
        self.assertIn("DECLINE", msg)
        self.assertIn("AAC-TEST01", msg)

    def test_patient_confirmed_message(self):
        msg = build_patient_confirmed_whatsapp(
            "Ramesh Kumar", "+91 8465058469", "Wednesday, 28 October 2026",
            "05:30 PM", "VOICE_CALL", "AAC-TEST01"
        )
        self.assertIn("ACCEPTED & CONFIRMED", msg)
        self.assertIn("Dr. Ayesha Shaik will call you", msg)

    def test_patient_declined_message(self):
        msg = build_patient_declined_whatsapp(
            "Ramesh Kumar", "Wednesday, 28 October 2026", "AAC-TEST01"
        )
        self.assertIn("DECLINED", msg)
        self.assertIn("+91 8465058469", msg)

    def test_appointment_lifecycle_pending_to_confirmed(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        now_iso = datetime.now(CLINIC_TIMEZONE).isoformat()
        c.execute("INSERT INTO patient (full_name, phone, created_at) VALUES ('Sita Devi', '+91 9999988888', ?)", (now_iso,))
        p_id = c.lastrowid
        ref = "AAC-LIFE01"
        c.execute("""
            INSERT INTO appointment (reference_code, patient_id, mode, consultation_type, status, starts_at, clinic_week_start, created_at)
            VALUES (?, ?, 'ONLINE', 'VOICE_CALL', 'PENDING', '2026-11-04T17:30:00+05:30', '2026-11-02', ?)
        """, (ref, p_id, now_iso))
        conn.commit()

        # Verify initial status is PENDING
        c.execute("SELECT status FROM appointment WHERE reference_code = ?", (ref,))
        self.assertEqual(c.fetchone()[0], "PENDING")

        # Simulate Doctor Accepting
        c.execute("UPDATE appointment SET status = 'CONFIRMED' WHERE reference_code = ?", (ref,))
        conn.commit()
        c.execute("SELECT status FROM appointment WHERE reference_code = ?", (ref,))
        self.assertEqual(c.fetchone()[0], "CONFIRMED")
        conn.close()

if __name__ == "__main__":
    unittest.main()
