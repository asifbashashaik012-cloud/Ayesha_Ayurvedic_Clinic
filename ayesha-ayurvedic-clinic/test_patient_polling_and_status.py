import unittest
import sqlite3
import threading
import urllib.request
import urllib.parse
import json
import time
from http.server import HTTPServer
import server

TEST_PORT = 9876

class PatientStatusPollingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server.DB_FILE = "test_status_clinic.db"
        server.init_db()
        cls.httpd = HTTPServer(("127.0.0.1", TEST_PORT), server.ClinicHandler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        import os
        if os.path.exists("test_status_clinic.db"):
            try:
                os.remove("test_status_clinic.db")
            except Exception:
                pass

    def setUp(self):
        conn = sqlite3.connect("test_status_clinic.db")
        c = conn.cursor()
        c.execute("DELETE FROM appointment")
        c.execute("DELETE FROM patient")
        conn.commit()
        conn.close()

    def _insert_appointment(self, ref, status="PENDING"):
        conn = sqlite3.connect("test_status_clinic.db")
        c = conn.cursor()
        c.execute("INSERT INTO patient (full_name, phone, email, created_at) VALUES (?, ?, ?, ?)",
                  ("Test Patient", "9876543210", "test@example.com", "2026-10-27T00:00:00+05:30"))
        pid = c.lastrowid
        c.execute("""
            INSERT INTO appointment (reference_code, patient_id, mode, consultation_type, status, starts_at, clinic_week_start, created_at)
            VALUES (?, ?, 'ONLINE', 'VIDEO_CALL', ?, '2026-10-28T17:00:00+05:30', '2026-10-26', '2026-10-27T00:00:00+05:30')
        """, (ref, pid, status))
        conn.commit()
        conn.close()

    def test_status_pending(self):
        self._insert_appointment("AAC-TEST99", "PENDING")
        url = f"http://127.0.0.1:{TEST_PORT}/api/appointments/status?ref=AAC-TEST99"
        with urllib.request.urlopen(url) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode())
            self.assertEqual(data["reference"], "AAC-TEST99")
            self.assertEqual(data["status"], "PENDING")
            self.assertIn("Waiting", data["message"])
            self.assertEqual(data["patientName"], "Test Patient")

    def test_status_confirmed_when_doctor_accepts(self):
        self._insert_appointment("AAC-ACCPT1", "CONFIRMED")
        url = f"http://127.0.0.1:{TEST_PORT}/api/appointments/status?ref=AAC-ACCPT1"
        with urllib.request.urlopen(url) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode())
            self.assertEqual(data["reference"], "AAC-ACCPT1")
            self.assertEqual(data["status"], "CONFIRMED")
            self.assertIn("accepted", data["message"].lower())

    def test_status_declined_when_doctor_declines(self):
        self._insert_appointment("AAC-DECLN1", "DECLINED")
        url = f"http://127.0.0.1:{TEST_PORT}/api/appointments/status?ref=AAC-DECLN1"
        with urllib.request.urlopen(url) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode())
            self.assertEqual(data["reference"], "AAC-DECLN1")
            self.assertEqual(data["status"], "DECLINED")
            self.assertIn("declined", data["message"].lower())

    def test_status_not_found(self):
        url = f"http://127.0.0.1:{TEST_PORT}/api/appointments/status?ref=AAC-NONEXIST"
        try:
            urllib.request.urlopen(url)
            self.fail("Should return 404")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

if __name__ == "__main__":
    unittest.main()
