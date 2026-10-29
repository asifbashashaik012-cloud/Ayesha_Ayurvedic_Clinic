# Ayesha Ayurvedic Clinic — Official Healthcare Website & Booking System

[![Physician: Dr. Shaik Ayesha](https://img.shields.io/badge/Physician-Dr.%20Shaik%20Ayesha%20B.A.M.S.-163828.svg)](#)
[![Registration: Andhra Board 2545/A/2025](https://img.shields.io/badge/Andhra%20Board%20Regn-2545%2FA%2F2025-b78a3e.svg)](#)
[![Primary Contact](https://img.shields.io/badge/WhatsApp%20%26%20Phone-%2B91%208465058469-25d366.svg)](#)

Authoritative web application and patient booking platform for **Ayesha Ayurvedic Clinic** (ఆయేషా ఆయుర్వేదిక్ క్లినిక్), Tiruvuru, Krishna District, Andhra Pradesh.

---

## 1. Verified Clinical Information

* **Clinic Name:** Ayesha Ayurvedic Clinic
* **Ayurvedic Physician:** Dr. Shaik Ayesha, B.A.M.S. (Dr. N.T.R. University of Health Sciences, Vijayawada)
* **Registration Authority:** Andhra Board for Ayurveda (Constituted under Andhra Act 1956)
* **Registration Number:** `2545/A/2025` (Valid through 11-12-2030)
* **Primary Phone & WhatsApp:** `+91 8465058469` *(Official contact for bookings & WhatsApp automation)*
* **Secondary Contact:** `+91 9848339262`
* **Clinic Location:** 10-188, Tholla Bazar (తోళ్లబజార్), Near Congress Office / Jaibhavi Centre, Tiruvuru, Krishna District, Andhra Pradesh - 521235
* **Google Maps Link:** [https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac](https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac)
* **Zero Demo Values Guarantee:** No fake 5-star ratings or stock physician images. 100% verified credentials and authentic clinic posters.

---

## 2. Consultation Policies & Invariants

### Online Doctor Appointments (Wednesday & Friday Only)
* **Days:** Strictly **Wednesdays** and **Fridays**.
* **Consultation Window:** **5:00 PM – 8:30 PM IST (Asia/Kolkata)**.
* **Daily Limit:** Exactly **3 confirmed appointments** per day.
* **Weekly Limit:** Exactly **6 confirmed appointments** across the Monday–Sunday clinic week.
* **Consultation Modes:**
  1. **Voice Call:** The physician calls the patient's phone number during 5:00 PM – 8:30 PM IST on the appointment day.
  2. **Video Call:** Automated Zoom meeting room link is generated and sent via WhatsApp prior to the consultation.
* **WhatsApp Automation:** Instant booking confirmation with one-click WhatsApp sync to `+91 8465058469`.

### Sunday Offline In-Clinic Visits (Physical Clinic Only)
* **Schedule:** Every Sunday only (Morning: 9:00 AM – 12:00 PM | Evening: 4:00 PM – 8:00 PM).
* **Mode:** Walk-in consultations at the physical clinic in Tiruvuru. No online slots are offered for Sunday offline visits to prevent confusion.

---

## 3. Quick Start & Execution

### Option A: Zero-Dependency Local Runner (Immediate Preview)
Requires only standard Python 3 (already installed on this Windows environment):
```powershell
python server.py
```
Open **`http://localhost:8080`** in any web browser.
* Serves the complete responsive clinic website.
* Embedded Google Map with direct navigation button.
* Working online booking engine with live slot calendar (Wed/Fri 5-8:30 PM).
* Voice Call & Video Call options with automated WhatsApp message formulation and Zoom link generator.
* Self-service booking lookup and cancellation.
* Doctor administration dashboard (`ayesha_clinic` / `Ayurveda@2026`).

### Option B: Docker Compose (Production Stack)
Runs PostgreSQL 16, Java 21 Spring Boot 3 backend, and Vite React frontend:
```bash
docker compose up --build
```
* Frontend: `http://localhost:5173`
* Backend API: `http://localhost:8080/api`
* PostgreSQL: `localhost:5432`

---

## 4. Automated Verification & Testing

Run the automated test suite verifying booking invariants, day/time boundaries, capacity limits (3 daily / 6 weekly), WhatsApp payloads, and Zoom link automation:
```powershell
python test_clinic_engine_direct.py
```
**Test Results:**
```text
Ran 7 tests in 0.207s
OK
```

---

## 5. Documentation Pack

* [`docs/PRD.md`](docs/PRD.md) — Product Requirements Document
* [`docs/Design.md`](docs/Design.md) — UI/UX Design System Specification & Color Tokens
* [`docs/Architecture.md`](docs/Architecture.md) — System Architecture, Concurrency Locks & PostgreSQL Schema
* [`docs/BookingFlows.md`](docs/BookingFlows.md) — End-to-End User Journeys & State Transitions
* [`docs/Security.md`](docs/Security.md) — Threat Model, Data Privacy & Concurrency Verification
* [`docs/WHATSAPP_AND_ZOOM_AUTOMATION.md`](docs/WHATSAPP_AND_ZOOM_AUTOMATION.md) — WhatsApp Cloud API & Zoom Automation Guide
* [`docs/openapi.yaml`](docs/openapi.yaml) — OpenAPI 3.0 REST API Specification
