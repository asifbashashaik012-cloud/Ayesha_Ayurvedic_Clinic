/**
 * Ayesha Ayurvedic Clinic — Interactive Client Application
 * Dr. Shaik Ayesha, B.A.M.S. | Andhra Board Regn. No. 2545/A/2025
 * Includes:
 * - Interactive Monthly Calendar with Green (Online Wed/Fri) and Red (Sunday Offline) circles
 * - Full-width vertical booking form
 * - Automated WhatsApp & Email Dispatch (Patient & Doctor ayeshashaik0211@gmail.com, Phone 8465058469)
 * - Dynamic Gallery Manager in Admin Panel
 */

// const API_BASE = window.location.origin.includes(":8080") || window.location.origin.includes(":5173") 
//   ? "/api" 
//   : "http://localhost:8080/api";
const API_BASE = "/api";

let clinicData = null;
let treatmentsData = [];
let galleryData = [];
let availabilityDays = [];

// Calendar state (defaults to current month: Oct 2026)
let calYear = 2026;
let calMonth = 9; // 0-indexed: 9 = October

let selectedDate = null;
let selectedSlot = "17:30";
let selectedMode = "VOICE_CALL";
let adminSettings = {};

document.addEventListener("DOMContentLoaded", () => {
  const now = new Date();
  calYear = now.getFullYear();
  calMonth = now.getMonth();

  initApp();
  setupEventListeners();
});

async function initApp() {
  await loadClinicInfo();
  await loadTreatments();
  await loadGallery();
  await loadAvailability();
}

function setupEventListeners() {
  const mobileToggle = document.getElementById("mobileToggle");
  const navLinks = document.getElementById("navLinks");
  if (mobileToggle) {
    mobileToggle.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });
  }

  const modeVoice = document.getElementById("modeVoice");
  const modeVideo = document.getElementById("modeVideo");
  if (modeVoice && modeVideo) {
    modeVoice.addEventListener("click", () => selectMode("VOICE_CALL"));
    modeVideo.addEventListener("click", () => selectMode("VIDEO_CALL"));
  }

  const bookingForm = document.getElementById("bookingForm");
  if (bookingForm) {
    bookingForm.addEventListener("submit", handleBookingSubmit);
  }

  const lookupForm = document.getElementById("lookupForm");
  if (lookupForm) {
    lookupForm.addEventListener("submit", handleLookupSubmit);
  }

  const adminLoginForm = document.getElementById("adminLoginForm");
  if (adminLoginForm) {
    adminLoginForm.addEventListener("submit", handleAdminLogin);
  }

  const adminSettingsForm = document.getElementById("adminSettingsForm");
  if (adminSettingsForm) {
    adminSettingsForm.addEventListener("submit", handleSaveSettings);
  }

  const newTreatmentForm = document.getElementById("newTreatmentForm");
  if (newTreatmentForm) {
    newTreatmentForm.addEventListener("submit", handleCreateTreatment);
  }

  const newGalleryForm = document.getElementById("newGalleryForm");
  if (newGalleryForm) {
    newGalleryForm.addEventListener("submit", handleCreateGalleryItem);
  }
}

function selectMode(mode) {
  selectedMode = mode;
  const modeVoice = document.getElementById("modeVoice");
  const modeVideo = document.getElementById("modeVideo");
  const modeHint = document.getElementById("modeHint");

  if (mode === "VOICE_CALL") {
    modeVoice.classList.add("selected");
    modeVideo.classList.remove("selected");
    if (modeHint) {
      modeHint.innerHTML = "📞 <b>Voice Call:</b> Dr. Ayesha Shaik will call your phone number directly during <b>5:00 PM – 8:30 PM IST</b> on the appointment day.";
    }
  } else {
    modeVideo.classList.add("selected");
    modeVoice.classList.remove("selected");
    if (modeHint) {
      modeHint.innerHTML = "🎥 <b>Video Call:</b> Dr. Ayesha Shaik will send you the secure Zoom video consultation meeting link on your WhatsApp in automation prior to your slot.";
    }
  }
}

// ==========================================================================
// 1. DATA LOADERS
// ==========================================================================

async function loadClinicInfo() {
  try {
    const res = await fetch(`${API_BASE}/clinic`);
    if (!res.ok) throw new Error("Could not load clinic data");
    clinicData = await res.json();

    if (clinicData.heroTitle) {
      const heroTitleEl = document.getElementById("heroTitleText");
      if (heroTitleEl) heroTitleEl.innerHTML = clinicData.heroTitle.replace(/\n/g, "<br>");
    }
    if (clinicData.heroSubtitle) {
      const heroSubEl = document.getElementById("heroSubtitleText");
      if (heroSubEl) heroSubEl.textContent = clinicData.heroSubtitle;
    }
    if (clinicData.doctorEmail) {
      document.querySelectorAll(".clinic-email-text").forEach(el => el.textContent = clinicData.doctorEmail);
      document.querySelectorAll(".clinic-email-link").forEach(el => el.setAttribute("href", `mailto:${clinicData.doctorEmail}`));
    }
    if (clinicData.registrationNumber) {
      document.querySelectorAll(".clinic-reg-badge").forEach(el => el.textContent = clinicData.registrationNumber);
    }
    if (clinicData.primaryPhone) {
      document.querySelectorAll(".clinic-phone-primary").forEach(el => el.textContent = clinicData.primaryPhone);
      document.querySelectorAll(".clinic-phone-link").forEach(el => el.setAttribute("href", `tel:${clinicData.primaryPhone.replace(/\s+/g, '')}`));
    }
    if (clinicData.primaryWhatsApp) {
      const cleanWa = clinicData.primaryWhatsApp.replace(/[^0-9]/g, '');
      document.querySelectorAll(".clinic-wa-link").forEach(el => el.setAttribute("href", `https://wa.me/${cleanWa}`));
    }
    if (clinicData.secondaryPhone) {
      document.querySelectorAll(".clinic-phone-secondary").forEach(el => el.textContent = clinicData.secondaryPhone);
    }
    if (clinicData.address) {
      document.querySelectorAll(".clinic-address-text").forEach(el => el.textContent = clinicData.address);
    }
    if (clinicData.sundayOfflineTimings) {
      document.querySelectorAll(".clinic-sunday-timings").forEach(el => el.textContent = clinicData.sundayOfflineTimings);
    }
    if (clinicData.onlineTimings) {
      document.querySelectorAll(".clinic-online-timings").forEach(el => el.textContent = clinicData.onlineTimings);
    }
  } catch (e) {
    console.warn("Using fallback clinic details:", e);
  }
}

async function loadTreatments() {
  const container = document.getElementById("treatmentsGrid");
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/treatments`);
    if (!res.ok) throw new Error("Could not load treatments");
    treatmentsData = await res.json();
    renderTreatments(treatmentsData);
  } catch (e) {
    console.warn("Treatments fetch fallback", e);
  }
}

function renderTreatments(list) {
  const container = document.getElementById("treatmentsGrid");
  if (!container) return;

  container.innerHTML = list.map(t => `
    <article class="treatment-card ${t.is_special_service ? 'special' : ''}">
      <div class="treatment-top">
        ${t.is_special_service ? '<span class="special-badge">★ ప్రత్యేక సేవ (Special Service)</span>' : ''}
        <h4 class="treatment-name-telugu">${t.name_telugu}</h4>
        <h5 class="treatment-name-eng">${t.name_english}</h5>
        <p class="treatment-desc">${t.description || 'Classical Ayurvedic clinical treatment.'}</p>
      </div>
      <div class="treatment-cat">${t.category}</div>
    </article>
  `).join("");
}

function filterTreatments(category, btn) {
  document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");

  if (category === "ALL") {
    renderTreatments(treatmentsData);
  } else if (category === "SPECIAL") {
    renderTreatments(treatmentsData.filter(t => t.is_special_service));
  } else {
    renderTreatments(treatmentsData.filter(t => t.category.toLowerCase().includes(category.toLowerCase())));
  }
}

async function loadGallery() {
  const grid = document.getElementById("galleryGrid");
  if (!grid) return;

  try {
    const res = await fetch(`${API_BASE}/gallery`);
    if (!res.ok) throw new Error("Could not load gallery");
    galleryData = await res.json();
    renderGallery(galleryData);
  } catch (e) {
    console.warn("Gallery fallback", e);
  }
}

function renderGallery(items) {
  const grid = document.getElementById("galleryGrid");
  if (!grid) return;

  grid.innerHTML = items.map(item => `
    <div class="gallery-item" onclick="openLightbox('${item.image_url}', '${encodeURIComponent(item.title)}', '${encodeURIComponent(item.description || '')}')">
      <div class="gallery-img-box">
        <img src="${item.image_url}" alt="${item.title}" loading="lazy" style="${item.image_url.includes('certificate') || item.image_url.includes('poster') ? 'object-fit: contain; background: #fff;' : ''}">
        <span class="gallery-zoom-badge">🔍 Click to Zoom</span>
      </div>
      <div class="gallery-desc">
        <h4>${item.title}</h4>
        <p>${item.description || ''}</p>
      </div>
    </div>
  `).join("");
}

// ==========================================================================
// 2. INTERACTIVE MONTHLY CALENDAR (GREEN & RED CIRCLES)
// ==========================================================================

async function loadAvailability() {
  try {
    const res = await fetch(`${API_BASE}/availability?weeks=12`);
    if (!res.ok) throw new Error("Could not load availability");
    const data = await res.json();
    availabilityDays = data.days || [];
    renderMonthlyCalendar();
    renderTimeSlots();
  } catch (e) {
    console.warn("Availability load error", e);
    renderMonthlyCalendar();
    renderTimeSlots();
  }
}

function renderMonthlyCalendar() {
  const titleEl = document.getElementById("calendarMonthTitle");
  const daysGrid = document.getElementById("calendarDaysGrid");
  if (!daysGrid || !titleEl) return;

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  titleEl.textContent = `${monthNames[calMonth]} ${calYear}`;

  const firstDay = new Date(calYear, calMonth, 1).getDay(); // 0 = Sun
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();

  const today = new Date();
  const tY = today.getFullYear();
  const tM = String(today.getMonth() + 1).padStart(2, "0");
  const tD = String(today.getDate()).padStart(2, "0");
  const todayKey = `${tY}-${tM}-${tD}`;

  let html = "";

  // 1. Blank padding cells for days before the 1st
  for (let i = 0; i < firstDay; i++) {
    html += `<div class="cal-day-cell cal-empty"></div>`;
  }

  // 2. Days of the current month
  for (let d = 1; d <= daysInMonth; d++) {
    const dStr = String(d).padStart(2, "0");
    const mStr = String(calMonth + 1).padStart(2, "0");
    const dateKey = `${calYear}-${mStr}-${dStr}`;
    const dayOfWeek = new Date(calYear, calMonth, d).getDay(); // 0=Sun, 3=Wed, 5=Fri

    // Case A: Sunday (0) -> RED CIRCLE (Offline Clinic Visit)
    if (dayOfWeek === 0) {
      html += `
        <div class="cal-day-cell cal-sunday" title="Sunday In-Clinic Visit: 9 AM–12 PM & 4 PM–8 PM at Tiruvuru" 
             onclick="handleSundayClick('${dateKey}')">
          <span>${d}</span>
          <span class="cal-slots-hint">Offline</span>
        </div>
      `;
    }
    // Case B: Wednesday (3) or Friday (5) -> GREEN CIRCLE (Online Booking)
    else if (dayOfWeek === 3 || dayOfWeek === 5) {
      const avail = availabilityDays.find(a => a.date === dateKey);
      const isSelected = (selectedDate === dateKey);
      const isPast = (dateKey < todayKey);
      const isFull = (avail && avail.booked >= avail.dayLimit);

      // Requirement: Completed past Wednesdays/Fridays -> THICK DARK GREEN + NOT AVAILABLE
      if (isPast) {
        html += `
          <div class="cal-day-cell cal-online thick-green past" 
               title="Completed Consultation Day (${d}) — Not Available" 
               onclick="handleDateSelect('${dateKey}', true, this, 'PAST')">
            <span>${d}</span>
            <span class="cal-slots-hint">Not Available</span>
          </div>
        `;
      }
      // Requirement: 3 appointments booked completely -> THICK DARK GREEN + NOT AVAILABLE
      else if (isFull || (avail && !avail.available)) {
        html += `
          <div class="cal-day-cell cal-online thick-green full" 
               title="Online Capacity Full (3/3 Booked) — Not Available" 
               onclick="handleDateSelect('${dateKey}', true, this, 'FULL')">
            <span>${d}</span>
            <span class="cal-slots-hint">Not Available</span>
          </div>
        `;
      }
      // Upcoming available Wednesday/Friday -> LIGHT GREEN WITH GREEN BORDER
      else {
        const slotsLeft = avail ? (avail.dayLimit - avail.booked) : 3;
        html += `
          <div class="cal-day-cell cal-online ${isSelected ? 'selected' : ''}" 
               title="Online Consultation Available (${slotsLeft} slots left)" 
               onclick="handleDateSelect('${dateKey}', false, this, 'AVAILABLE')">
            <span>${d}</span>
            <span class="cal-slots-hint">${slotsLeft} left</span>
          </div>
        `;
      }
    }
    // Case C: Non-consultation days (Mon, Tue, Thu, Sat) -> Disabled / Gray
    else {
      html += `
        <div class="cal-day-cell cal-disabled">
          <span>${d}</span>
        </div>
      `;
    }
  }

  daysGrid.innerHTML = html;
  updateSelectedDateBanner();
}

function prevMonth() {
  calMonth--;
  if (calMonth < 0) {
    calMonth = 11;
    calYear--;
  }
  renderMonthlyCalendar();
}

function nextMonth() {
  calMonth++;
  if (calMonth > 11) {
    calMonth = 0;
    calYear++;
  }
  renderMonthlyCalendar();
}

function handleSundayClick(dateKey) {
  const parts = dateKey.split("-");
  const formatted = `${parts[2]}/${parts[1]}/${parts[0]}`;
  alert(
    `🏥 SUNDAY IN-CLINIC VISIT (${formatted})\n\n` +
    `Every Sunday, Dr. Shaik Ayesha conducts in-person physical clinical consultations at:\n` +
    `10-188, Tholla Bazar, Near Congress Office / Jaibhavi Centre, Tiruvuru, AP - 521235.\n\n` +
    `Timings:\n` +
    `• Morning: 9:00 AM – 12:00 PM\n` +
    `• Evening: 4:00 PM – 8:00 PM\n\n` +
    `Walk-in consultations are welcome! No online reservation is required for Sunday visits.`
  );
}

function handleDateSelect(dateKey, isUnavailable, element, reason) {
  if (isUnavailable) {
    if (reason === 'PAST') {
      alert("⚠️ This Wednesday/Friday consultation date has already completed and is Not Available.\n\nPlease choose an upcoming available green-circled date.");
    } else {
      alert("⚠️ All 3 online consultation appointments for this date are completely booked (Not Available).\n\nPlease choose another available Wednesday or Friday.");
    }
    return;
  }
  selectedDate = dateKey;
  renderMonthlyCalendar();
  updateSelectedDateBanner();
}

function updateSelectedDateBanner() {
  const banner = document.getElementById("selectedDateBanner");
  if (!banner) return;

  if (!selectedDate) {
    banner.innerHTML = `<span style="color: var(--color-terracotta);">👉 Please click a <b>Green-Circled Date</b> on the calendar above to choose your consultation day.</span>`;
  } else {
    const dt = new Date(selectedDate + "T00:00:00");
    const weekday = dt.getDay() === 3 ? "Wednesday" : "Friday";
    const dateFormatted = dt.toLocaleDateString("en-US", { day: "numeric", month: "long", year: "numeric" });
    banner.innerHTML = `
      <div style="background: var(--color-online-green-bg); border: 1.5px solid var(--color-online-green); border-radius: var(--radius-sm); padding: 0.75rem 1rem; color: var(--color-forest); font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
        <span>✓ Selected Online Consultation Date:</span>
        <span style="color: var(--color-online-green);">${weekday}, ${dateFormatted} (5:00 PM – 8:30 PM IST)</span>
      </div>
    `;
  }
}

function renderTimeSlots() {
  const container = document.getElementById("timeSlotsGridVertical");
  if (!container) return;

  const slots = [
    { time: "17:00", label: "5:00 PM IST" },
    { time: "17:45", label: "5:45 PM IST" },
    { time: "18:30", label: "6:30 PM IST" },
    { time: "19:15", label: "7:15 PM IST" },
    { time: "20:00", label: "8:00 PM IST" }
  ];

  container.innerHTML = slots.map((s) => `
    <button type="button" class="time-slot-btn ${s.time === selectedSlot ? 'selected' : ''}" 
            onclick="handleSlotSelect('${s.time}', this)">
      ${s.label}
    </button>
  `).join("");
}

function handleSlotSelect(timeVal, element) {
  selectedSlot = timeVal;
  document.querySelectorAll(".time-slot-btn").forEach(b => b.classList.remove("selected"));
  element.classList.add("selected");
}

// ==========================================================================
// 3. BOOKING SUBMISSION WITH PYTHON WHATSAPP & EMAIL AUTOMATION
// ==========================================================================

async function handleBookingSubmit(e) {
  e.preventDefault();

  if (!selectedDate) {
    alert("Please click an eligible Green-Circled Wednesday or Friday on the calendar first.");
    const calEl = document.getElementById("calendarWrapper");
    if (calEl) calEl.scrollIntoView({ behavior: "smooth" });
    return;
  }

  const patientName = document.getElementById("patientName").value.trim();
  const phone = document.getElementById("patientPhone").value.trim();
  const email = document.getElementById("patientEmail") ? document.getElementById("patientEmail").value.trim() : "";
  const age = document.getElementById("patientAge").value.trim();
  const healthConcern = document.getElementById("healthConcern").value.trim();
  const submitBtn = document.getElementById("submitBookingBtn");
  const formStatus = document.getElementById("formStatus");

  if (!patientName) {
    alert("Please enter the patient's full name.");
    return;
  }
  if (!phone) {
    alert("Please enter a valid WhatsApp / Mobile number.");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = "Processing Reservation & Triggering Automations…";
  formStatus.innerHTML = "";

  const startsAt = `${selectedDate}T${selectedSlot}:00+05:30`;

  try {
    const res = await fetch(`${API_BASE}/appointments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patientName,
        phone,
        email,
        startsAt,
        consultationType: selectedMode,
        age: age ? parseInt(age, 10) : null,
        healthConcern
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.message || "Booking could not be confirmed.");
    }

    renderWaitingForDoctor(data, patientName, phone, email);
    await loadAvailability();
  } catch (err) {
    formStatus.innerHTML = `<div style="background: #fee2e2; border: 1.5px solid #ef4444; color: #991b1b; padding: 0.85rem 1rem; border-radius: var(--radius-sm); font-weight: 600;">⚠ ${err.message}</div>`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = "Confirm Online Appointment &amp; Send Notifications →";
  }
}

// ==========================================================================
// REAL-TIME STATUS POLLING & WAITING SCREEN
// ==========================================================================
window._doctorPollTimer = null;

function renderWaitingForDoctor(data, patientName, phone, email) {
  const container = document.getElementById("bookingCardVertical");
  if (!container) return;

  if (window._doctorPollTimer) {
    clearInterval(window._doctorPollTimer);
    window._doctorPollTimer = null;
  }

  const doctorWaUrl = (data.notification || {}).doctorWhatsAppUrl || "";

  container.innerHTML = `
    <div class="wait-screen-card" id="patientWaitScreen">
      <div class="wait-pulse-loader">
        <div class="pulse-ring"></div>
        <div class="wait-icon">⏳</div>
      </div>
      <div class="wait-live-tag">
        <span class="live-dot-pulse"></span> Request Sent — Waiting for Doctor Response
      </div>
      <h3 style="font-family: var(--font-serif); font-size: 2rem; color: #b45309; margin: 0.75rem 0 0.5rem;">
        Your Request is Being Processed by the Doctor
      </h3>
      <div class="confirm-ref-badge" style="font-size: 1.05rem; padding: 0.45rem 1.35rem; background: #fef3c7; border: 1.5px solid #f59e0b; color: #92400e; margin-bottom: 1rem;">
        Booking Reference: <b>${data.reference}</b>
      </div>

      <div class="wait-status-message-box">
        <p style="font-size: 1rem; font-weight: 700; color: #143826; margin: 0 0 0.5rem;">
          ✅ Email sent to Dr. Shaik Ayesha automatically.
        </p>
        <p style="font-size: 0.95rem; color: #4b5563; margin: 0 0 1rem; line-height: 1.6;">
          WhatsApp has opened with the message ready to send to doctor — tap <b>Send</b> if it's open, or use the button below.
        </p>
        ${doctorWaUrl ? `
        <a href="${doctorWaUrl}" target="_blank"
           style="display:inline-flex;align-items:center;gap:0.5rem;background:#25d366;color:#fff;text-decoration:none;font-weight:800;padding:0.8rem 1.5rem;border-radius:10px;font-size:0.95rem;margin-bottom:0.75rem;box-shadow:0 4px 12px rgba(37,211,102,.3);">
          💬 Send WhatsApp to Doctor (+91 8465058469)
        </a>` : ""}
        <div class="patient-quick-summary" style="margin-top:0.75rem;">
          <div><b>Patient:</b> ${patientName}</div>
          <div><b>Mobile:</b> ${phone}</div>
          <div><b>Slot:</b> ${data.formattedDate || selectedDate} · ${data.formattedTime || "5:00 PM – 8:30 PM"} IST</div>
        </div>
      </div>

      <div class="wait-pulse-bar">
        <div class="wait-pulse-bar-fill"></div>
      </div>
      <p style="font-size: 0.82rem; color: #6b7280; margin-top: 0.85rem;">
        🔄 This page checks for doctor's response every 2 seconds automatically
      </p>
    </div>
  `;

  container.scrollIntoView({ behavior: "smooth", block: "start" });

  // Auto-open WhatsApp to doctor immediately
  if (doctorWaUrl) {
    setTimeout(() => { window.open(doctorWaUrl, "_blank"); }, 600);
  }

  // Poll every 2 seconds
  window._doctorPollTimer = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/appointments/status?ref=${encodeURIComponent(data.reference)}`);
      if (!res.ok) return;
      const sData = await res.json();
      if (sData.status === "CONFIRMED") {
        clearInterval(window._doctorPollTimer);
        window._doctorPollTimer = null;
        handleDoctorResponseAccepted(sData, patientName, phone, email);
      } else if (sData.status === "DECLINED") {
        clearInterval(window._doctorPollTimer);
        window._doctorPollTimer = null;
        handleDoctorResponseDeclined(sData, patientName, phone, email);
      }
    } catch (e) {
      console.warn("Status check poll:", e);
    }
  }, 2000);
}

// POPUP MODAL ON DOCTOR RESPONSE
function showDoctorResponsePopup(opts) {
  const existing = document.getElementById("doctorResponseModal");
  if (existing) existing.remove();

  const isAccepted = (opts.type === "ACCEPTED");
  const modal = document.createElement("div");
  modal.id = "doctorResponseModal";
  modal.className = "status-popup-backdrop";
  modal.innerHTML = `
    <div class="status-popup-card ${isAccepted ? 'accepted' : 'declined'}">
      <div class="popup-icon-circle ${isAccepted ? 'accepted' : 'declined'}">
        ${isAccepted ? '✓' : '✕'}
      </div>
      <h3 style="font-family: var(--font-serif); font-size: 1.85rem; color: ${isAccepted ? '#15803d' : '#b91c1c'}; margin-bottom: 0.5rem;">
        ${opts.title}
      </h3>
      <p style="font-size: 1.05rem; color: #374151; margin-bottom: 1.25rem; line-height: 1.6;">
        ${opts.message}
      </p>
      <div style="background: ${isAccepted ? '#f0fdf4' : '#fef2f2'}; border: 1px dashed ${isAccepted ? '#16a34a' : '#dc2626'}; padding: 0.75rem; border-radius: 8px; margin-bottom: 1.75rem; font-size: 0.95rem; font-weight: 700; color: ${isAccepted ? '#166534' : '#991b1b'};">
        Booking Reference: ${opts.ref}
      </div>
      <div style="display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap;">
        ${isAccepted ? `
          <button type="button" class="btn btn-primary" onclick="closeDoctorResponsePopup(); printAppointmentSlip();" style="background: #16a34a; border-color: #16a34a; font-weight: 700; padding: 0.85rem 1.6rem;">
            🖨️ Print Appointment Slip
          </button>
          <button type="button" class="btn btn-outline" onclick="closeDoctorResponsePopup()" style="padding: 0.85rem 1.4rem;">
            View Details
          </button>
        ` : `
          <button type="button" class="btn btn-gold" onclick="closeDoctorResponsePopup(); location.reload();" style="font-weight: 700; padding: 0.85rem 2rem; width: 100%;">
            🔄 Book Another Appointment
          </button>
        `}
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function closeDoctorResponsePopup() {
  const modal = document.getElementById("doctorResponseModal");
  if (modal) modal.remove();
}

// CASE A: DOCTOR ACCEPTS -> Show popup + Print Slip & Book Another
function handleDoctorResponseAccepted(sData, patientName, phone, email) {
  showDoctorResponsePopup({
    type: "ACCEPTED",
    title: "Doctor Has Accepted Your Appointment!",
    message: `Dr. Shaik Ayesha has accepted and confirmed your consultation for <b>${sData.formattedDate}</b> at <b>${sData.formattedTime} IST</b>.`,
    ref: sData.reference
  });

  const container = document.getElementById("bookingCardVertical");
  if (!container) return;

  const isVideo = (sData.consultationType === "VIDEO_CALL");
  const pName = sData.patientName || patientName;
  const pPhone = sData.patientPhone || phone;
  const pEmail = sData.patientEmail || email;

  const printSlip = `
    <div id="appointmentPrintSlip" style="display:none;">
      <div style="border:2px solid #143826;border-radius:8px;padding:24px;max-width:500px;margin:0 auto;font-family:serif;">
        <div style="text-align:center;border-bottom:2px solid #143826;padding-bottom:12px;margin-bottom:16px;">
          <div style="font-size:1.5rem;font-weight:900;letter-spacing:1px;color:#143826;">AYESHA AYURVEDIC CLINIC</div>
          <div style="font-size:0.85rem;color:#666;">Dr. Shaik Ayesha, B.A.M.S. &bull; Regn No: 2545/A/2025</div>
          <div style="font-size:0.8rem;color:#888;">Thollabazar, Near Congress Office, Tiruvuru, AP - 521235</div>
          <div style="font-size:0.8rem;color:#888;">+91 8465058469 | ayeshashaik0211@gmail.com</div>
        </div>
        <div style="text-align:center;margin-bottom:16px;">
          <div style="font-size:1rem;font-weight:700;color:#143826;">APPOINTMENT SLIP (CONFIRMED)</div>
          <div style="font-size:0.85rem;font-family:monospace;background:#f0f9f0;padding:6px 16px;border:1px dashed #143826;display:inline-block;margin-top:4px;">${sData.reference}</div>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
          <tr><td style="padding:6px 4px;color:#555;width:45%;">Patient Name:</td><td style="padding:6px 4px;font-weight:700;">${pName}</td></tr>
          <tr><td style="padding:6px 4px;color:#555;">Mobile / WhatsApp:</td><td style="padding:6px 4px;font-weight:700;">${pPhone}</td></tr>
          ${pEmail ? `<tr><td style="padding:6px 4px;color:#555;">Email:</td><td style="padding:6px 4px;">${pEmail}</td></tr>` : ""}
          <tr><td style="padding:6px 4px;color:#555;">Date:</td><td style="padding:6px 4px;font-weight:700;">${sData.formattedDate}</td></tr>
          <tr><td style="padding:6px 4px;color:#555;">Time Window:</td><td style="padding:6px 4px;font-weight:700;">${sData.formattedTime || "5:00 PM - 8:30 PM"} IST</td></tr>
          <tr><td style="padding:6px 4px;color:#555;">Consultation Mode:</td><td style="padding:6px 4px;font-weight:700;">${isVideo ? "Video Call (Zoom)" : "Voice Call (Phone)"}</td></tr>
          ${isVideo && sData.zoomMeetingLink ? `<tr><td style="padding:6px 4px;color:#555;">Zoom Link:</td><td style="padding:6px 4px;font-size:.78rem;">${sData.zoomMeetingLink}</td></tr>` : ""}
          ${isVideo && sData.zoomPasscode ? `<tr><td style="padding:6px 4px;color:#555;">Passcode:</td><td style="padding:6px 4px;font-family:monospace;">${sData.zoomPasscode}</td></tr>` : ""}
        </table>
        <div style="border-top:1px dashed #143826;margin-top:16px;padding-top:10px;text-align:center;font-size:0.78rem;color:#888;">
          Keep this slip for your records. Helpline: +91 8465058469
        </div>
      </div>
    </div>
  `;

  container.innerHTML = `
    ${printSlip}
    <div class="confirm-box-full" id="confirmBoxFull" style="border-color: #16a34a;">
      <div class="confirm-icon-big" style="background: #dcfce7; color: #16a34a;">✓</div>
      <h3 style="font-family: var(--font-serif); font-size: 2.2rem; color: #15803d; margin-bottom: 0.5rem;">
        Doctor Has Accepted Your Appointment!
      </h3>
      <div class="confirm-ref-badge" style="background: #f0fdf4; border: 1.5px solid #16a34a; color: #166534;">${sData.reference}</div>

      <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; padding: 1rem 1.25rem; margin: 1.5rem 0; text-align: center;">
        <p style="font-size: 1.05rem; color: #166534; font-weight: 700; margin: 0;">
          ✓ Dr. Shaik Ayesha has confirmed your consultation for ${sData.formattedDate} at ${sData.formattedTime} IST.
        </p>
      </div>

      <div class="confirm-details-table">
        <div class="confirm-row">
          <span style="color: var(--text-muted);">Patient Name:</span>
          <b>${pName}</b>
        </div>
        <div class="confirm-row">
          <span style="color: var(--text-muted);">WhatsApp Mobile:</span>
          <b>${pPhone}</b>
        </div>
        ${pEmail ? `
        <div class="confirm-row">
          <span style="color: var(--text-muted);">Patient Email:</span>
          <b>${pEmail} <span style="color: green; font-size: 0.8rem;">(Email Sent ✓)</span></b>
        </div>` : ""}
        <div class="confirm-row">
          <span style="color: var(--text-muted);">Consultation Date &amp; Time:</span>
          <b>${sData.formattedDate} at ${sData.formattedTime} IST</b>
        </div>
        <div class="confirm-row">
          <span style="color: var(--text-muted);">Consultation Mode:</span>
          <b style="color: var(--color-forest);">${isVideo ? "📹 Video Call (Zoom)" : "📞 Voice Call (Phone Call)"}</b>
        </div>
        ${isVideo && sData.zoomMeetingLink ? `
        <div class="confirm-row">
          <span style="color: var(--text-muted);">Zoom Join Link:</span>
          <b><a href="${sData.zoomMeetingLink}" target="_blank" style="color: #2563eb; text-decoration: underline;">Open Zoom Room</a></b>
        </div>
        <div class="confirm-row">
          <span style="color: var(--text-muted);">Meeting Passcode:</span>
          <b><code>${sData.zoomPasscode}</code></b>
        </div>` : (!isVideo ? `
        <div class="confirm-row">
          <span style="color: var(--text-muted);">Doctor Action:</span>
          <b>Dr. Shaik Ayesha will call your phone directly during 5:00 PM – 8:30 PM IST.</b>
        </div>` : "")}
      </div>

      <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-top: 1.5rem;">
        <button type="button" class="btn btn-outline" onclick="printAppointmentSlip()" style="border-color: #143826; font-weight: 700;">
          🖨️ Print Appointment Slip
        </button>
        <button type="button" class="btn btn-gold" onclick="location.reload()" style="font-weight: 700;">
          🔄 Book Another Appointment
        </button>
      </div>
    </div>
  `;

  container.scrollIntoView({ behavior: "smooth", block: "start" });
}

// CASE B: DOCTOR DECLINES -> Show popup + ONLY Book Another Appointment
function handleDoctorResponseDeclined(sData, patientName, phone, email) {
  showDoctorResponsePopup({
    type: "DECLINED",
    title: "Doctor Has Declined Your Appointment",
    message: `Dr. Shaik Ayesha is unavailable for this specific time slot (${sData.formattedDate || selectedDate}). Your slot has been released back into availability.`,
    ref: sData.reference
  });

  const container = document.getElementById("bookingCardVertical");
  if (!container) return;

  const pName = sData.patientName || patientName;

  container.innerHTML = `
    <div class="declined-box-full" id="declinedBoxFull">
      <div class="popup-icon-circle declined">✕</div>
      <h3 style="font-family: var(--font-serif); font-size: 2.2rem; color: #b91c1c; margin-bottom: 0.5rem;">
        Doctor Has Declined Your Appointment
      </h3>
      <div class="confirm-ref-badge" style="background: #fef2f2; border: 1.5px solid #ef4444; color: #991b1b; margin-bottom: 1.5rem;">
        ${sData.reference}
      </div>

      <div style="background: #fef2f2; border: 1.5px solid #f87171; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 1.75rem; text-align: left; max-width: 600px; margin-left: auto; margin-right: auto;">
        <p style="font-weight: 700; color: #991b1b; margin: 0 0 0.5rem; font-size: 1.05rem;">
          Appointment Status: Declined by Doctor
        </p>
        <p style="color: #7f1d1d; margin: 0 0 0.75rem; line-height: 1.6; font-size: 0.95rem;">
          Dear <b>${pName}</b>, Dr. Shaik Ayesha is unavailable for the requested slot on <b>${sData.formattedDate || selectedDate}</b>. The slot has been released back to the clinic calendar.
        </p>
        <p style="color: #7f1d1d; margin: 0; font-size: 0.9rem;">
          📞 Helpline: <b>+91 8465058469</b> | ✉️ <b>ayeshashaik0211@gmail.com</b>
        </p>
      </div>

      <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
        <button type="button" class="btn btn-gold" onclick="location.reload()" style="font-weight: 700; padding: 0.9rem 2.5rem; font-size: 1.05rem;">
          🔄 Book Another Appointment
        </button>
      </div>
    </div>
  `;

  container.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ==========================================================================
// PRINT APPOINTMENT SLIP — only the slip, not the whole website
// ==========================================================================
function printAppointmentSlip() {
  const slip = document.getElementById("appointmentPrintSlip");
  if (!slip) { window.print(); return; }
  const slipHtml = slip.innerHTML;
  const printWin = window.open("", "_blank", "width=600,height=700");
  printWin.document.write(`<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Appointment Slip — Ayesha Ayurvedic Clinic</title>
<style>
  body { margin: 20px; font-family: serif; }
  @media print { body { margin: 0; } }
</style>
</head><body>${slipHtml}</body></html>`);
  printWin.document.close();
  printWin.focus();
  setTimeout(() => { printWin.print(); printWin.close(); }, 400);
}

// ==========================================================================
// 4. LIGHTBOX GALLERY VIEWER
// ==========================================================================
function openLightbox(imgSrc, title, desc) {
  const modal = document.getElementById("lightboxModal");
  const imgEl = document.getElementById("lightboxImg");
  const titleEl = document.getElementById("lightboxTitle");
  const descEl = document.getElementById("lightboxDesc");

  if (modal && imgEl) {
    imgEl.src = imgSrc;
    if (titleEl) titleEl.textContent = decodeURIComponent(title || "");
    if (descEl) descEl.textContent = decodeURIComponent(desc || "");
    modal.classList.add("open");
  }
}

function closeLightbox() {
  const modal = document.getElementById("lightboxModal");
  if (modal) modal.classList.remove("open");
}

// ==========================================================================
// 5. TRACK BOOKING MODAL
// ==========================================================================
function openTrackModal() {
  const modal = document.getElementById("trackModal");
  if (modal) modal.classList.add("open");
}

function closeTrackModal() {
  const modal = document.getElementById("trackModal");
  if (modal) modal.classList.remove("open");
}

async function handleLookupSubmit(e) {
  e.preventDefault();
  const refCode = document.getElementById("lookupRef").value.trim();
  const phone = document.getElementById("lookupPhone").value.trim();
  const resultDiv = document.getElementById("lookupResult");

  resultDiv.innerHTML = `<div style="color: var(--text-muted);">Looking up appointment records…</div>`;

  try {
    const res = await fetch(`${API_BASE}/appointments/lookup?referenceCode=${encodeURIComponent(refCode)}&phone=${encodeURIComponent(phone)}`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.message || "Appointment not found.");

    const isVideo = (data.consultation_type === "VIDEO_CALL");
    resultDiv.innerHTML = `
      <div style="background: var(--color-surface-alt); padding: 1.25rem; border-radius: var(--radius-md); margin-top: 1rem;">
        <h4 style="color: var(--color-forest); margin-bottom: 0.5rem;">Booking Reference: ${data.reference_code}</h4>
        <p><b>Status:</b> <span style="color: ${data.status === 'CONFIRMED' ? 'green' : 'red'}; font-weight: 700;">${data.status}</span></p>
        <p><b>Patient:</b> ${data.patient_name} (${data.patient_phone})</p>
        <p><b>Date & Time:</b> ${data.starts_at}</p>
        <p><b>Consultation Mode:</b> ${isVideo ? '🎥 Video Call (Zoom)' : '📞 Voice Call'}</p>
        ${isVideo && data.zoom_meeting_link ? `<p><b>Zoom Link:</b> <a href="${data.zoom_meeting_link}" target="_blank" style="color: blue; text-decoration: underline;">Join Room</a> (Passcode: ${data.zoom_passcode})</p>` : ''}
        
        ${data.status === 'CONFIRMED' ? `
          <button type="button" class="btn btn-outline" style="color: #b91c1c; border-color: #b91c1c; margin-top: 1rem;" 
                  onclick="handleCancelAppointment('${data.reference_code}', '${data.patient_phone}')">
            Cancel Appointment
          </button>
        ` : ''}
      </div>
    `;
  } catch (err) {
    resultDiv.innerHTML = `<div style="color: #b91c1c; font-weight: 600; margin-top: 1rem;">⚠ ${err.message}</div>`;
  }
}

async function handleCancelAppointment(refCode, phone) {
  if (!confirm("Are you sure you want to cancel this online appointment? This will release the slot for other patients.")) {
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/appointments/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ referenceCode: refCode, phone })
    });
    const data = await res.json();
    alert(data.message || "Appointment cancelled.");
    closeTrackModal();
    await loadAvailability();
  } catch (e) {
    alert("Cancellation error: " + e.message);
  }
}

// ==========================================================================
// 6. DOCTOR ADMIN DASHBOARD WITH DYNAMIC GALLERY & EMAIL SETTINGS
// ==========================================================================

function openAdminModal() {
  const modal = document.getElementById("adminModal");
  if (modal) modal.classList.add("open");
}

function closeAdminModal() {
  const modal = document.getElementById("adminModal");
  if (modal) modal.classList.remove("open");
}

async function handleAdminLogin(e) {
  e.preventDefault();
  const u = document.getElementById("adminUser").value.trim();
  const p = document.getElementById("adminPass").value.trim();
  const statusDiv = document.getElementById("adminLoginStatus");

  try {
    const res = await fetch(`${API_BASE}/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p })
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.message || "Login failed");

    document.getElementById("adminLoginView").style.display = "none";
    document.getElementById("adminDashboardView").style.display = "block";
    switchAdminTab("settings");
    loadAdminSettings();
    loadAdminAppointments();
    loadAdminTreatments();
    loadAdminGallery();
  } catch (err) {
    statusDiv.textContent = err.message;
  }
}

function switchAdminTab(tabName) {
  document.querySelectorAll(".admin-tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".admin-tab-pane").forEach(p => p.style.display = "none");

  const activeBtn = document.getElementById(`tabBtn_${tabName}`);
  const activePane = document.getElementById(`tabPane_${tabName}`);
  if (activeBtn) activeBtn.classList.add("active");
  if (activePane) activePane.style.display = "block";
}

async function loadAdminSettings() {
  try {
    const res = await fetch(`${API_BASE}/admin/settings`);
    if (!res.ok) return;
    adminSettings = await res.json();

    const setVal = (id, key) => {
      const el = document.getElementById(id);
      if (el && adminSettings[key] !== undefined) el.value = adminSettings[key];
    };

    setVal("editClinicName", "clinic_name");
    setVal("editClinicTelugu", "clinic_name_telugu");
    setVal("editDoctorName", "doctor_name");
    setVal("editDoctorQual", "doctor_qualification");
    setVal("editDoctorEmail", "doctor_email");
    setVal("editRegNo", "registration_number");
    setVal("editPhonePrimary", "primary_phone");
    setVal("editWhatsApp", "primary_whatsapp");
    setVal("editPhoneSecondary", "secondary_phone");
    setVal("editAddress", "address");
    setVal("editMapsUrl", "google_maps_url");
    setVal("editHeroTitle", "hero_title");
    setVal("editHeroSubtitle", "hero_subtitle");
    setVal("editSundayTimings", "sunday_timings");
    setVal("editOnlineTimings", "online_timings");
    setVal("editDailyLimit", "daily_limit");
    setVal("editWeeklyLimit", "weekly_limit");
    setVal("editSmtpHost", "smtp_host");
    setVal("editSmtpPort", "smtp_port");
    setVal("editSmtpUser", "smtp_user");
    setVal("editSmtpPass", "smtp_pass");
    setVal("editTelegramToken", "telegram_bot_token");
    setVal("editTelegramChatId", "telegram_doctor_chat_id");
    setVal("editSmsApiKey", "sms_api_key");
    setVal("editCallMeBotKey", "callmebot_apikey");
    setVal("editBaseUrl", "server_base_url");

    const bookingOnEl = document.getElementById("editBookingEnabled");
    if (bookingOnEl) bookingOnEl.checked = (adminSettings["booking_enabled"] !== "false");
  } catch (e) {
    console.error("Error loading settings:", e);
  }
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const statusDiv = document.getElementById("settingsSaveStatus");
  statusDiv.innerHTML = `<span style="color: var(--text-muted);">Saving clinic settings…</span>`;

  const getVal = id => {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
  };

  const payload = {
    clinic_name: getVal("editClinicName"),
    clinic_name_telugu: getVal("editClinicTelugu"),
    doctor_name: getVal("editDoctorName"),
    doctor_qualification: getVal("editDoctorQual"),
    doctor_email: getVal("editDoctorEmail"),
    registration_number: getVal("editRegNo"),
    primary_phone: getVal("editPhonePrimary"),
    primary_whatsapp: getVal("editWhatsApp"),
    secondary_phone: getVal("editPhoneSecondary"),
    address: getVal("editAddress"),
    google_maps_url: getVal("editMapsUrl"),
    hero_title: getVal("editHeroTitle"),
    hero_subtitle: getVal("editHeroSubtitle"),
    sunday_timings: getVal("editSundayTimings"),
    online_timings: getVal("editOnlineTimings"),
    daily_limit: getVal("editDailyLimit"),
    weekly_limit: getVal("editWeeklyLimit"),
    smtp_host: getVal("editSmtpHost") || "smtp.gmail.com",
    smtp_port: getVal("editSmtpPort") || "587",
    smtp_user: getVal("editSmtpUser") || "ayeshashaik0211@gmail.com",
    smtp_pass: getVal("editSmtpPass"),
    telegram_bot_token: getVal("editTelegramToken"),
    telegram_doctor_chat_id: getVal("editTelegramChatId"),
    sms_api_key: getVal("editSmsApiKey"),
    callmebot_apikey: getVal("editCallMeBotKey"),
    server_base_url: getVal("editBaseUrl") || "http://localhost:8080",
    booking_enabled: document.getElementById("editBookingEnabled").checked ? "true" : "false"
  };

  try {
    const res = await fetch(`${API_BASE}/admin/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Could not save settings.");
    statusDiv.innerHTML = `<span style="color: #15803d; font-weight: 700;">✓ Settings updated and live on website!</span>`;
    await loadClinicInfo();
    await loadAvailability();
  } catch (err) {
    statusDiv.innerHTML = `<span style="color: #b91c1c;">⚠ ${err.message}</span>`;
  }
}

// Admin Tab 2: Treatments Manager
async function loadAdminTreatments() {
  const tbody = document.getElementById("adminTreatmentsTbody");
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/admin/treatments`);
    const list = await res.json();

    tbody.innerHTML = list.map(t => `
      <tr style="border-bottom: 1px solid var(--color-border-subtle);">
        <td style="padding: 0.65rem 0.5rem;"><b>${t.name_english}</b></td>
        <td style="padding: 0.65rem 0.5rem;">${t.name_telugu}</td>
        <td style="padding: 0.65rem 0.5rem;">${t.category}</td>
        <td style="padding: 0.65rem 0.5rem;">${t.is_special_service ? '★ Special' : 'Standard'}</td>
        <td style="padding: 0.65rem 0.5rem;">
          <button type="button" class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; color: #b91c1c; border-color: #b91c1c;" 
                  onclick="handleDeleteTreatment(${t.id})">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color: red; padding: 1rem;">Failed to load treatments: ${e.message}</td></tr>`;
  }
}

async function handleCreateTreatment(e) {
  e.preventDefault();
  const name_eng = document.getElementById("newTreatEng").value.trim();
  const name_tel = document.getElementById("newTreatTel").value.trim();
  const cat = document.getElementById("newTreatCat").value.trim();
  const desc = document.getElementById("newTreatDesc").value.trim();
  const is_special = document.getElementById("newTreatSpecial").checked;

  try {
    const res = await fetch(`${API_BASE}/admin/treatments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name_english: name_eng,
        name_telugu: name_tel,
        category: cat,
        description: desc,
        is_special_service: is_special
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Could not add treatment.");
    alert("New treatment added!");
    document.getElementById("newTreatmentForm").reset();
    await loadAdminTreatments();
    await loadTreatments();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function handleDeleteTreatment(id) {
  if (!confirm("Are you sure you want to delete this treatment?")) return;
  try {
    const res = await fetch(`${API_BASE}/admin/treatments/${id}`, { method: "DELETE" });
    const data = await res.json();
    alert(data.message || "Treatment removed.");
    await loadAdminTreatments();
    await loadTreatments();
  } catch (e) {
    alert("Delete error: " + e.message);
  }
}

// Admin Tab 3: Appointments List
async function loadAdminAppointments() {
  const tableBody = document.getElementById("adminTableBody");
  const statsDiv = document.getElementById("adminStats");
  if (!tableBody) return;

  try {
    const res = await fetch(`${API_BASE}/admin/appointments`);
    const data = await res.json();

    if (statsDiv) {
      statsDiv.innerHTML = `
        <div style="display: flex; gap: 1.5rem; margin-bottom: 1.5rem; background: var(--color-surface-alt); padding: 1rem; border-radius: var(--radius-md);">
          <div><b>Current Week Booked:</b> ${data.weekBooked} / ${data.weeklyLimit}</div>
          <div><b>Daily Cap:</b> ${data.dailyLimit} per day</div>
          <div><b>Total Records:</b> ${data.appointments.length}</div>
        </div>
      `;
    }

    tableBody.innerHTML = data.appointments.map(a => `
      <tr style="border-bottom: 1px solid var(--color-border-subtle);">
        <td style="padding: 0.65rem 0.5rem; font-family: monospace; font-weight: 700;">${a.reference_code}</td>
        <td style="padding: 0.65rem 0.5rem;">
          <b>${a.patient_name}</b><br>
          <small>${a.patient_phone} ${a.patient_email ? `· ${a.patient_email}` : ''}</small><br>
          <span style="font-size: 0.75rem; color: var(--text-muted);">${a.health_concern || ''}</span>
        </td>
        <td style="padding: 0.65rem 0.5rem;">${a.starts_at.slice(0, 16)}</td>
        <td style="padding: 0.65rem 0.5rem;">
          <span style="display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.78rem; font-weight: 700; background: ${a.consultation_type === 'VIDEO_CALL' ? '#dbeafe' : '#e0e7ff'}; color: #1e40af;">
            ${a.consultation_type}
          </span>
        </td>
        <td style="padding: 0.65rem 0.5rem;">
          <select onchange="handleAdminStatusChange(${a.id}, this.value)" style="padding: 0.25rem; font-size: 0.8rem; border-radius: 4px; font-weight: 700; color: ${a.status === 'CONFIRMED' ? '#15803d' : (a.status === 'DECLINED' ? '#b91c1c' : '#b45309')};">
            <option value="PENDING" ${a.status === 'PENDING' ? 'selected' : ''}>PENDING</option>
            <option value="CONFIRMED" ${a.status === 'CONFIRMED' ? 'selected' : ''}>CONFIRMED</option>
            <option value="DECLINED" ${a.status === 'DECLINED' ? 'selected' : ''}>DECLINED</option>
            <option value="COMPLETED" ${a.status === 'COMPLETED' ? 'selected' : ''}>COMPLETED</option>
            <option value="CANCELLED" ${a.status === 'CANCELLED' ? 'selected' : ''}>CANCELLED</option>
          </select>
        </td>
        <td style="padding: 0.65rem 0.5rem;">
          <a href="tel:${a.patient_phone}" class="btn btn-outline" style="padding: 0.3rem 0.55rem; font-size: 0.75rem;">Call</a>
          <a href="https://wa.me/${a.patient_phone.replace(/[^0-9]/g, '')}" target="_blank" class="btn btn-whatsapp" style="padding: 0.3rem 0.55rem; font-size: 0.75rem;">WhatsApp</a>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tableBody.innerHTML = `<tr><td colspan="6" style="padding: 1rem; color: red;">Failed to load appointments: ${e.message}</td></tr>`;
  }
}

async function handleAdminStatusChange(apptId, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/admin/appointments/${apptId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    alert(data.message || "Status updated.");
    await loadAdminAppointments();
    await loadAvailability();
  } catch (e) {
    alert("Error: " + e.message);
  }
}

// Admin Tab 4: Gallery Manager
async function loadAdminGallery() {
  const tbody = document.getElementById("adminGalleryTbody");
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/admin/gallery`);
    const list = await res.json();

    tbody.innerHTML = list.map(item => `
      <tr style="border-bottom: 1px solid var(--color-border-subtle);">
        <td style="padding: 0.65rem 0.5rem;">
          <img src="${item.image_url}" alt="${item.title}" class="admin-thumb-img">
        </td>
        <td style="padding: 0.65rem 0.5rem;"><b>${item.title}</b></td>
        <td style="padding: 0.65rem 0.5rem;"><small>${item.image_url}</small></td>
        <td style="padding: 0.65rem 0.5rem;">
          <button type="button" class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; color: #b91c1c; border-color: #b91c1c;" 
                  onclick="handleDeleteGalleryItem(${item.id})">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="4" style="color: red; padding: 1rem;">Failed to load gallery items: ${e.message}</td></tr>`;
  }
}

async function handleCreateGalleryItem(e) {
  e.preventDefault();
  const title = document.getElementById("newGalleryTitle").value.trim();
  const imgUrl = document.getElementById("newGalleryUrl").value.trim();
  const desc = document.getElementById("newGalleryDesc").value.trim();

  try {
    const res = await fetch(`${API_BASE}/admin/gallery`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        image_url: imgUrl,
        description: desc
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Could not add gallery photo.");
    alert("New gallery photo added to website!");
    document.getElementById("newGalleryForm").reset();
    await loadAdminGallery();
    await loadGallery();
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function handleDeleteGalleryItem(id) {
  if (!confirm("Are you sure you want to delete this photo from the clinic gallery?")) return;
  try {
    const res = await fetch(`${API_BASE}/admin/gallery/${id}`, { method: "DELETE" });
    const data = await res.json();
    alert(data.message || "Photo removed from gallery.");
    await loadAdminGallery();
    await loadGallery();
  } catch (e) {
    alert("Delete error: " + e.message);
  }
}
