# WhatsApp & Zoom AI Automation Architecture

## 1. Overview
The automation subsystem handles instant dispatch of appointment confirmations, personalized instructions, and Zoom video consultation links via WhatsApp.

---

## 2. Configuration & Credentials

The automation engine operates in two complementary modes:
1. **Live API Webhook Mode:** Connects to WhatsApp Cloud API (Meta Graph API) or Twilio WhatsApp API when credentials are provided in `.env`.
2. **Direct Browser Deep-Link Mode (Zero Friction / Fallback):** Formulates an instant, pre-filled WhatsApp API URL (`https://wa.me/...`) that automatically opens WhatsApp Web / WhatsApp Desktop / WhatsApp Mobile with the exact personalized message.

### Environment Variables
```env
# WhatsApp Automation
WHATSAPP_API_ENABLED=true
WHATSAPP_API_URL=https://graph.facebook.com/v19.0
WHATSAPP_PHONE_NUMBER_ID=your_meta_phone_id
WHATSAPP_ACCESS_TOKEN=your_meta_permanent_token
CLINIC_PRIMARY_WHATSAPP=+918465058469

# Zoom Video Automation
ZOOM_API_KEY=your_zoom_key
ZOOM_API_SECRET=your_zoom_secret
ZOOM_BASE_MEETING_URL=https://us05web.zoom.us/j/
```

---

## 3. Automation Logic by Consultation Mode

### 3.1 Mode A: Voice Call (వాయిస్ కాల్ సంప్రదింపు)
* **Trigger:** Patient books an appointment and selects `Voice Call`.
* **Patient Phone Notice:**
  ```text
  🌿 *AYESHA AYURVEDIC CLINIC* 🌿
  _Dr. Shaik Ayesha, B.A.M.S. (Ayurvedic Physician)_
  Regn No: 2545/A/2025 | Thollabazar, Tiruvuru

  Namaste {PatientName},
  Your online voice consultation is *CONFIRMED*!

  📅 *Date:* {DateFormatted} (Wednesday/Friday)
  ⏰ *Time Window:* 5:00 PM – 8:30 PM IST
  📞 *Consultation Mode:* Voice Call
  🔖 *Booking Reference:* {ReferenceCode}

  *Next Steps:*
  Dr. Ayesha Shaik will call you directly on your phone number ({PatientPhone}) during the consultation window (5:00 PM – 8:30 PM IST). Please ensure your phone is reachable.

  📍 Clinic Address: Thollabazar, Near Congress Office, Tiruvuru
  📞 Helpline & WhatsApp: +91 8465058469
  ```

---

### 3.2 Mode B: Video Call (వీడియో కాల్ సంప్రదింపు)
* **Trigger:** Patient books an appointment and selects `Video Call`.
* **Backend Zoom Automation:**
  1. Generates unique Zoom Room ID: `846-505-8469-{Random4Digits}`
  2. Generates Passcode: `AYESHA{Random3Digits}`
  3. Joins URL: `https://us05web.zoom.us/j/8465058469?pwd={Passcode}`
* **Patient WhatsApp Notice:**
  ```text
  🌿 *AYESHA AYURVEDIC CLINIC* 🌿
  _Dr. Shaik Ayesha, B.A.M.S. (Ayurvedic Physician)_
  Regn No: 2545/A/2025 | Thollabazar, Tiruvuru

  Namaste {PatientName},
  Your online video consultation is *CONFIRMED*!

  📅 *Date:* {DateFormatted} (Wednesday/Friday)
  ⏰ *Scheduled Time:* {TimeFormatted} IST
  🎥 *Consultation Mode:* Video Call (Zoom)
  🔖 *Booking Reference:* {ReferenceCode}

  *Your Secure Video Consultation Link:*
  🔗 Zoom Link: {ZoomJoinUrl}
  🔑 Meeting Passcode: {ZoomPasscode}

  *Instructions:*
  Please click the link 5 minutes before your scheduled slot. The doctor will join the session on time. If you face any issues, reply directly on this WhatsApp chat.

  📍 Clinic Address: Thollabazar, Near Congress Office, Tiruvuru
  📞 Helpline & WhatsApp: +91 8465058469
  ```

---

### 3.3 Doctor / Clinic Internal WhatsApp Alert
Simultaneously, a notification is dispatched to Dr. Ayesha Shaik's primary WhatsApp number (`+91 8465058469`):
```text
🔔 *NEW APPOINTMENT BOOKED*
Patient: {PatientName} ({Age} yrs)
Phone: {PatientPhone}
Mode: {Mode} ({Voice/Video})
Date & Time: {DateFormatted} at {TimeFormatted}
Ref: {ReferenceCode}
Concern: {HealthConcern}
Current Week Total: {WeekBookedCount}/6
```
