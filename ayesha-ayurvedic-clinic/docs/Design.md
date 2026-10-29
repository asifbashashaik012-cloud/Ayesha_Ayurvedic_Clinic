# UI/UX Design Specification — Ayesha Ayurvedic Clinic

## 1. Brand Identity & Design Direction
The brand reflects authentic, classical Ayurveda combined with clinical professionalism and warmth:
* **Brand Name:** Ayesha Ayurvedic Clinic (ఆయేషా ఆయుర్వేదిక్ క్లినిక్)
* **Physician:** Dr. Shaik Ayesha, B.A.M.S., Ayurvedic Physician
* **Registration:** Andhra Board for Ayurveda Regn. No. 2545/A/2025
* **Atmosphere:** Calming, botanical, grounded, trustworthy, and modern. Strictly avoids tacky gradients, loud popups, and fabricated testimonials.

---

## 2. Design Tokens & Color System

```css
:root {
  /* Brand Palette */
  --color-forest: #1b4332;       /* Primary Deep Botanical */
  --color-leaf: #2d6a4f;         /* Herbal Leaf Green */
  --color-leaf-light: #40916c;   /* Accent Leaf */
  --color-sage: #d8f3dc;         /* Soft Herbal Mint */
  --color-cream-bg: #fdfbf7;     /* Warm Ivory Canvas */
  --color-card-bg: #f4f0ea;      /* Organic Textured Paper Surface */
  --color-gold: #b78a3e;         /* Traditional Ayurvedic Gold Accent */
  --color-gold-hover: #9c722e;   /* Gold Interaction State */
  --color-terracotta: #b25838;   /* Sunday In-Clinic Warm Accent */
  
  /* Text & Contrast */
  --text-main: #1d2a23;          /* Dark Forest Charcoal (High Contrast) */
  --text-muted: #4a5d52;         /* Earth Muted Text */
  --text-faint: #758a7e;         /* Secondary Notes */
  --border-subtle: #e3ded5;      /* Subtle Separator */
  
  /* Status Colors */
  --status-available: #2d6a4f;
  --status-limited: #b78a3e;
  --status-full: #8b3a3a;
  
  /* Shadows & Radius */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --shadow-subtle: 0 4px 20px rgba(27, 67, 50, 0.06);
  --shadow-elevated: 0 10px 30px rgba(27, 67, 50, 0.12);
}
```

---

## 3. Typography Hierarchy
* **Headings:** `Playfair Display`, `Cormorant Garamond`, Georgia, serif
  * Expresses herbal wisdom, physician authority, and heritage.
* **Body & UI Elements:** `Plus Jakarta Sans`, `Inter`, -apple-system, sans-serif
  * High legibility across mobile viewports, clear input fields, accessible contrast ratios (WCAG AAA compliant).

---

## 4. Component Inventory & Layout Blueprint

### 4.1 Header & Official Bar
* Official registration banner: `Andhra Board for Ayurveda Regn. No. 2545/A/2025` | `Direct Helpline: +91 8465058469`
* Main Navigation:
  * Brand mark with botanical leaf icon
  * Links: About Doctor, Treatments, Online Booking, Sunday In-Clinic, Location, Lookup, Admin Portal
  * CTA: **Book Consultation**

### 4.2 Hero Section
* Two-column desktop / stacked mobile layout:
  * Left: Dignified physician title, credential highlights (B.A.M.S. Dr. NTR UHS), quick-action buttons.
  * Right: Verified Ayurvedic Physician Badge & interactive certificate viewer with official seal.

### 4.3 Distinct Consultation Banners
* **Online Consultations Card:** Forest Green theme, highlighting Wednesday & Friday (5:00 PM – 8:30 PM), max 3 appointments/day, Voice Call & Video Call options.
* **Sunday Offline Clinic Card:** Terracotta/Warm Ochre theme, highlighting physical in-clinic visits (9 AM – 12 PM & 4 PM – 8 PM), walk-in guidance, and clinic address.

### 4.4 Verified Treatments Grid (Bilingual)
* Filterable cards:
  * Panchakarma Detoxification
  * Suvarnaprashana Child Immunity
  * Root-Cause Guidance
  * 19 specialized conditions (Skin, Hair, Acidity, PCOD, Joints, Diabetes, etc.) in Telugu and English.

### 4.5 Multistep Online Booking Interface
1. **Date Picker:** Only Wednesdays and Fridays are clickable. Real-time availability badges (`Available`, `1 Left`, `Full`).
2. **Time Slot Selector:** Valid slots between 5:00 PM and 8:30 PM IST.
3. **Consultation Mode Selector:**
   * **Voice Call:** Physician calls patient phone.
   * **Video Call:** Secure Zoom meeting link sent via WhatsApp.
4. **Patient Information Form:** Name, WhatsApp Phone (`+91`), Age, Health concern.
5. **Confirmation Modal / Card:**
   * Booking Reference (`AAC-XXXXXX`)
   * Automated WhatsApp notification trigger
   * One-click "Open WhatsApp Confirmation"
   * Calendar invite button (.ics)

### 4.6 Google Maps & Contact Card
* Embedded responsive iframe for `https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac`
* Address: 10-188, Tholla Bazar, Near Congress Office, Tiruvuru, AP - 521235
* Direct contact numbers: `+91 8465058469` (Primary & WhatsApp), `+91 9848339262`

### 4.7 Doctor Administrative Dashboard
* Password-protected physician interface
* Daily/Weekly quota monitoring (`X/3 daily`, `Y/6 weekly`)
* Table of upcoming appointments with Voice/Video badge, patient notes, phone dial button, and WhatsApp Zoom link dispatcher.
