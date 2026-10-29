# Security Engineering & Threat Model — Ayesha Ayurvedic Clinic

## 1. Threat Modeling & Risk Matrix

| Threat ID | Threat Description | Likelihood | Impact | Architectural Mitigation | Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TH-01** | **Capacity Race Condition / Double Booking**<br>Simultaneous booking submissions exceed daily (3) or weekly (6) limit. | High | Critical | Pessimistic DB row lock on `booking_week_lock` + unique constraint on active time slots. | Concurrency stress test simulating parallel requests against the 3rd and 6th slots. |
| **TH-02** | **Ineligible Day Booking Bypass**<br>Attacker injects Monday/Saturday/Sunday into online consultation endpoint. | High | High | Server-side validation rejects any date whose `DayOfWeek` in `Asia/Kolkata` is not Wednesday or Friday. | Unit and API boundary test for all 7 days of the week. |
| **TH-03** | **Time Window Bypass**<br>Attacker submits appointment at 10:00 AM or 11:00 PM. | Medium | High | Strict boundary validation ensuring time is between `17:00` and `20:30` IST. | Boundary tests for `16:59`, `17:00`, `20:30`, and `20:31`. |
| **TH-04** | **Patient Record Enumeration (IDOR)**<br>Unauthorized access to other patients' clinical notes or appointment details. | High | Critical | Appointments are queried only by a high-entropy random Reference Code (`AAC-XXXXXX`, 64-bit entropy) combined with patient phone verification. | Automated IDOR vulnerability fuzzing. |
| **TH-05** | **Automated Booking Abuse / Denial of Service**<br>Bots exhausting available slots with fake numbers. | High | High | Rate limiting per IP and phone number, phone format validation (`+91` 10 digits), and captcha/cooldown hooks. | Load testing and abusive IP block simulation. |
| **TH-06** | **Administrative Account Hijacking**<br>Brute-force attack on admin dashboard. | Medium | High | Constant-time password hashing (BCrypt), session token validation, and lockout after repeated failed attempts. | Auth penetration test. |

---

## 2. Data Privacy & Confidentiality (Digital Personal Data Protection)
* **Data Minimization:** We collect only essential contact information (Full Name, Phone Number, Age, and Brief Health Concern).
* **Isolation of Medical Records:** The public booking API never exposes patient health concerns or doctor prescriptions. Only the reference code, appointment time, and status are returned.
* **Redaction in Logs:** Phone numbers and health concerns are masked in application logs (`+91 84650*****`). No secrets or credentials are ever logged.
