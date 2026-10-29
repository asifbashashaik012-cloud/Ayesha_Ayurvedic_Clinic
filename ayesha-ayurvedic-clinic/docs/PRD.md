# Product Requirements Document (PRD) — Ayesha Ayurvedic Clinic

**Document Version:** 2.0  
**Status:** Approved & Implemented  
**Date:** October 25, 2026  
**Author:** Principal Software Architect & Product Lead  

---

## 1. Executive Summary
Ayesha Ayurvedic Clinic is a premier traditional healthcare clinic led by **Dr. Shaik Ayesha, B.A.M.S.**, registered with the **Andhra Board for Ayurveda (Registration No. 2545/A/2025)**. The clinic operates physical walk-in clinical consultations in Tiruvuru, Andhra Pradesh, and provides structured, high-touch online consultations on scheduled days.

This web application serves as the authoritative digital presence of the clinic. It enables patients to discover verified Ayurvedic treatments, check live consultation availability, schedule online appointments (Voice Call or Video Call) with strict capacity enforcement, receive automated WhatsApp booking confirmations and Zoom links, and access physical clinic visit information and directions.

---

## 2. Authoritative Clinic Profile & Verified Facts
Every piece of clinic and physician data presented on the website is derived directly from the verified Andhra Board of Ayurveda registration certificate and official clinic posters:

| Attribute | Verified Official Record | Source Document |
| :--- | :--- | :--- |
| **Clinic Name** | Ayesha Ayurvedic Clinic (ఆయేషా ఆయుర్వేదిక్ క్లినిక్) | Official Clinic Banners & Poster |
| **Ayurvedic Physician** | Dr. Shaik Ayesha (Dr. Ayesha Shaik), B.A.M.S. | Registration Certificate 2545/A/2025 |
| **Father's Name** | Shaik Khasim | Registration Certificate 2545/A/2025 |
| **Date of Birth** | 11-02-2001 | Registration Certificate 2545/A/2025 |
| **Medical Degree** | B.A.M.S. (Bachelor of Ayurvedic Medicine & Surgery) | Dr. N.T.R.U.H.S. Vijayawada (Sept 2024, Regd No: 19A101101048) |
| **Registration Authority**| Andhra Board for Ayurveda (Andhra Act 1956) | Registered at Vijayawada on 12-12-2025 |
| **Registration Number** | **2545/A/2025** | Valid through 11-12-2030 |
| **Primary Phone / WhatsApp**| **+91 8465058469** | Primary Contact for Bookings & Automation |
| **Secondary Phone** | **+91 9848339262** | Clinic Poster Reference |
| **Physical Location** | 10-188, Tholla Bazar (తోళ్లబజార్), Near Congress Office / Jaibhavi Centre, Tiruvuru, Krishna Dist, AP - 521235 | Registered Address & Posters |
| **Google Maps Link** | `https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac` | Official Clinic Map Pin |
| **Content Integrity Rule**| Zero demo values, fake star ratings, or stock placeholder doctor images. All content is 100% verified. | Master Specification |

---

## 3. Mandatory Business Policies & Invariants

### 3.1 Online Doctor Consultations
* **Eligible Days:** Available strictly on **Wednesdays** and **Fridays**. No online consultations on Monday, Tuesday, Thursday, Saturday, or Sunday.
* **Consultation Hours:** **5:00 PM to 8:30 PM IST (Asia/Kolkata)**.
* **Daily Capacity Limit:** Exactly **3 confirmed online appointments per Wednesday**, and **3 confirmed online appointments per Friday**.
* **Weekly Capacity Limit:** Exactly **6 confirmed online appointments per clinic-local week (Monday 00:00 through Sunday 23:59:59 Asia/Kolkata)**.
* **Seventh Booking Invariant:** The system must reject any attempt to create a 7th online booking in the same week, regardless of day distribution.
* **Concurrency Enforcement:** Capacity must be verified and reserved inside an atomic database transaction using row-level locking (`SELECT ... FOR UPDATE` on `booking_week_lock`).
* **Consultation Modes:**
  1. **Voice Call:** The physician calls the patient's phone during 5:00 PM – 8:30 PM IST on the appointed date.
  2. **Video Call:** The physician conducts a secure one-on-one video consultation; an automated Zoom meeting link is generated and sent to the patient's WhatsApp before the consultation.

### 3.2 Sunday Offline Clinic Visits
* **Schedule:** Every Sunday only.
  * **Morning Hours:** 9:00 AM – 12:00 PM IST.
  * **Evening Hours:** 4:00 PM – 8:00 PM IST (poster confirms 4–8 PM; English banner notes 4–6 PM).
* **Location:** Physical clinic at Thollabazar, Near Congress Office, Tiruvuru.
* **Policy:** In-person consultations only. No online reservation is offered for Sunday offline visits to prevent confusion. Patients are provided address, interactive map, and direct call buttons.

---

## 4. WhatsApp Automation & Zoom AI Workflow

### 4.1 Automated Patient Messaging
When an appointment is confirmed:
1. **Instant On-Screen Visual Confirmation:** Displays booking reference (`AAC-XXXXXX`), confirmed date, time slot, selected mode (Voice Call vs Video Call), and instructions.
2. **Consultation Mode-Specific Messages:**
   * **Voice Call Message:**  
     > *"Namaste [Patient Name], your online consultation with Dr. Ayesha Shaik (B.A.M.S.) is confirmed for [Day], [Date] between [Time]. Dr. Ayesha will call you directly on your phone number (+91 XXXXXXXXXX) during 5:00 PM – 8:30 PM IST. Clinic Helpline: +91 8465058469."*
   * **Video Call Message:**  
     > *"Namaste [Patient Name], your online video consultation with Dr. Ayesha Shaik (B.A.M.S.) is confirmed for [Day], [Date] at [Time]. The doctor will send you the Zoom meeting link on WhatsApp prior to your scheduled consultation. Join Link: [Zoom URL]. Passcode: [Passcode]. Clinic Helpline: +91 8465058469."*
3. **Automated WhatsApp Webhook & Direct Action:**
   * Automated backend trigger via WhatsApp Business API / Webhook.
   * Fallback 1-click **"Open WhatsApp Confirmation"** button allowing the patient to synchronize their booking directly with clinic number `+91 8465058469`.

---

## 5. Verified Treatment Directory (Bilingual: Telugu & English)
Extracted verbatim from the official clinic poster:

### 5.1 Specialized Core Therapies (ప్రత్యేక సేవలు)
1. **Panchakarma (పంచకర్మ):** Classical 5-fold Ayurvedic detoxification and rejuvenation therapy.
2. **Suvarnaprashana (సువర్ణప్రాశన):** Ancient Ayurvedic pediatric immunization and cognitive development formulation.
3. **Root-Cause Guidance (వ్యాధుల కారణాలపై ప్రత్యేక మార్గదర్శకత్వం):** Comprehensive diagnosis of underlying Dosha imbalance (Vata, Pitta, Kapha) with personalized dietary and lifestyle guidance.

### 5.2 Illnesses & Conditions Treated (అన్ని వ్యాధులకు చికిత్స అందుబాటులో ఉంది)
1. చర్మ వ్యాధులు (Skin Disorders: Eczema, Psoriasis, Allergies)
2. జుట్టు సమస్యలు (Hair Problems: Hair fall, Dandruff, Alopecia)
3. ఆమ్లత్వం (Acidity, Heartburn, Acid Reflux)
4. జీర్ణ సమస్యలు (Digestive Disorders, IBS, Indigestion, Constipation)
5. మహిళల వ్యాధులు (Women's Health, Gynecological Wellness)
6. పి.సి.ఓ.డి (PCOD / PCOS, Hormonal Irregularities)
7. మానసిక సమస్యలు (Mental Wellbeing, Stress, Anxiety, Insomnia)
8. ఊబకాయం (Obesity & Healthy Weight Loss)
9. ఉబ్బసం (Asthma, Wheezing, Respiratory Allergies)
10. కాలేయ వ్యాధులు (Liver Diseases & Fatty Liver)
11. ఆర్థరైటిస్ (Arthritis, Joint Pains, Sciatica, Rheumatism)
12. పిల్లల వ్యాధులు (Pediatric Conditions & Child Immunity)
13. అలర్జీ జలుబు, దగ్గు (Allergic Rhinitis, Chronic Cold, Persistent Cough)
14. తలనొప్పి / మైగ్రేన్ (Headache & Migraine Relief)
15. కిడ్నీ స్టోన్ (Kidney Stones & Renal Health)
16. థైరాయిడ్ డిజార్డర్ (Thyroid Disorders: Hypo / Hyperthyroidism)
17. పైల్స్, ఫిషర్ (Piles, Fissure & Anorectal Care)
18. మధుమేహం (Diabetes Mellitus / Madhumeha Management)
19. బరువు & ఎత్తు నిర్వహణ (Healthy Weight & Height Management for Children and Youths)

---

## 6. Functional Requirements
* **FR-01 [Availability Engine]:** Calculate remaining capacity for the next 8 weeks (Wednesdays and Fridays). Highlight dates that are available, nearly full (1 slot left), or sold out.
* **FR-02 [Slot Selection]:** Allow patient to select eligible Wednesday or Friday, choose available start time within 5:00 PM – 8:30 PM, and choose Voice Call or Video Call.
* **FR-03 [Atomic Reservation]:** Execute booking under weekly serial lock. Reject duplicate exact slots or capacity overages (>3/day, >6/week).
* **FR-04 [WhatsApp & Zoom Automation]:** Formulate mode-specific message templates, generate Zoom meeting links, and trigger WhatsApp delivery.
* **FR-05 [Patient Self-Service]:** Allow lookup of booking status and cancellation using Reference Code and Phone Number.
* **FR-06 [Google Maps Integration]:** Embed interactive map for `https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac` with direct navigation button.
* **FR-07 [Administrative Dashboard]:** Secure admin interface for Dr. Ayesha Shaik to view weekly appointments, track capacity usage, view patient notes, and update Zoom meeting links.
