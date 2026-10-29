"""
Ayesha Ayurvedic Clinic — Zero-Dependency Unified API & Static Web Server
Dr. Shaik Ayesha, B.A.M.S. | Andhra Board Regn. No. 2545/A/2025
Features:
- Full-width vertical booking architecture
- Interactive Monthly Calendar with Green (Wed/Fri) and Red (Sunday Offline) circles
- Doctor Approval Flow: PENDING -> CONFIRMED/DECLINED with auto patient notification
- Automated WhatsApp & Email Dispatch in Python (Patient & Doctor ayeshashaik0211@gmail.com, Phone 8465058469)
- Dynamic Admin Panel with Gallery Manager, Content Editor, and Capacity Controls
"""

import sys
import os
import json
import sqlite3
import random
import string
import urllib.parse
import smtplib
import re
import hmac
import hashlib
import secrets
import threading
import html as _htmllib
import mimetypes
import time as _time
import urllib.request
import urllib.error
from email.message import EmailMessage
from datetime import datetime, date, time, timedelta, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import webbrowser

CLINIC_TIMEZONE = timezone(timedelta(hours=5, minutes=30)) # Asia/Kolkata (UTC+5:30)
DAILY_ONLINE_LIMIT = 3
WEEKLY_ONLINE_LIMIT = 6


SERVER_PORT = 8080

def load_dotenv():
    """Reads the .env file next to server.py (no extra packages needed)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(path):
        print("[ENV] No .env file found next to server.py -> keys will only come from the Admin panel.")
        return
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = re.split(r"\s+#", v, maxsplit=1)[0]          # ignore a trailing "  # comment"
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and k not in os.environ:
                os.environ[k] = v

load_dotenv()

# .env name  ->  setting name used by the rest of the code
SECRET_SETTINGS = ("smtp_pass", "telegram_bot_token", "callmebot_apikey", "sms_api_key")

ENV_TO_SETTING = {
    "SMTP_PASS": "smtp_pass",
    "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
    "TELEGRAM_CHAT_ID": "telegram_doctor_chat_id",
    "CALLMEBOT_APIKEY": "callmebot_apikey",
    "FAST2SMS_API_KEY": "sms_api_key",
    "PUBLIC_BASE_URL": "server_base_url",
}

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinic.db")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

DEFAULT_SETTINGS = {
    "clinic_name": "Ayesha Ayurvedic Clinic",
    "clinic_name_telugu": "ఆయేషా ఆయుర్వేదిక్ క్లినిక్",
    "doctor_name": "Dr. Shaik Ayesha",
    "doctor_qualification": "B.A.M.S., Ayurvedic Physician (Dr. N.T.R.U.H.S.)",
    "doctor_email": "ayeshashaik0211@gmail.com",
    "registration_number": "2545/A/2025",
    "state_board": "Andhra Board for Ayurveda (Vijayawada)",
    "primary_phone": "+91 8465058469",
    "primary_whatsapp": "+91 8465058469",
    "secondary_phone": "+91 9848339262",
    "address": "10-188, Tholla Bazar, Near Congress Office / Jaibhavi Centre, Tiruvuru, Krishna District, AP - 521235",
    "google_maps_url": "https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac",
    "hero_title": "Rooted in Ancient Ayurvedic Wisdom.\nCentered on Holistic Healing.",
    "hero_subtitle": "Personalized Ayurvedic medical care led by Dr. Shaik Ayesha, B.A.M.S. in Tiruvuru. Classical treatments for chronic disorders, panchakarma, and natural vitality according to Charaka and Sushruta ideals.",
    "sunday_timings": "Morning: 9:00 AM – 12:00 PM · Evening: 4:00 PM – 8:00 PM",
    "online_timings": "Wednesdays & Fridays, 5:00 PM – 8:30 PM IST",
    "daily_limit": "3",
    "weekly_limit": "6",
    "booking_enabled": "true",
    "server_base_url": "http://localhost:8080",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": "587",
    "smtp_user": "ayeshashaik0211@gmail.com",
    "smtp_pass": "", # Configurable in admin panel
    "telegram_bot_token": "", # Free Telegram Bot Token from @BotFather
    "telegram_doctor_chat_id": "", # Doctor's chat ID from @userinfobot
    "sms_provider": "FAST2SMS", # FAST2SMS or SIMULATION
    "sms_api_key": "", # Free Fast2SMS API key
    "callmebot_apikey": "" # Free CallMeBot WhatsApp API key (optional)
}

DEFAULT_GALLERY = [
    {
        "title": "Clinical Examination & Vital Check",
        "image_url": "images/dr_ayesha_patient_examination.jpg",
        "description": "Dr. Shaik Ayesha conducting an in-person clinical assessment and vital check using a sphygmomanometer at the clinic."
    },
    {
        "title": "Medical Registration Certificate",
        "image_url": "images/dr_ayesha_registration_certificate.jpg",
        "description": "Andhra Board for Ayurveda Official Registration No. 2545/A/2025 with official seals and Registrar endorsement."
    },
    {
        "title": "Official Clinic Tri-Fold Brochure",
        "image_url": "images/ayesha_clinic_brochure_full.jpg",
        "description": "Ancient Wisdom for a Healthier You — Comprehensive brochure detailing Panchakarma, treatments, benefits, and contact."
    },
    {
        "title": "Consultation Timings & Service Card",
        "image_url": "images/ayesha_clinic_brochure_banner.jpg",
        "description": "Official notice displaying Sunday clinic timings (9 AM–12 PM & 4 PM–8 PM) and services checklist."
    },
    {
        "title": "Telugu Clinical Services Poster",
        "image_url": "images/ayesha_clinic_poster_telugu.jpg",
        "description": "Comprehensive list of 19 chronic illnesses, Panchakarma, and Suvarnaprashana in Telugu."
    },
    {
        "title": "Ayesha Ayurvedic Clinic Main Banner",
        "image_url": "images/ayesha_clinic_banner.jpg",
        "description": "Official clinic signboard and contact numbers (+91 8465058469 and +91 9848339262)."
    }
]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS setting (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS patient (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        age INTEGER,
        health_concern TEXT,
        created_at TEXT NOT NULL
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS appointment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference_code TEXT UNIQUE NOT NULL,
        patient_id INTEGER NOT NULL,
        mode TEXT NOT NULL,
        consultation_type TEXT NOT NULL,
        status TEXT NOT NULL,
        starts_at TEXT NOT NULL,
        clinic_week_start TEXT NOT NULL,
        zoom_meeting_link TEXT,
        zoom_passcode TEXT,
        whatsapp_status TEXT,
        email_status TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patient(id)
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS treatment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_english TEXT UNIQUE NOT NULL,
        name_telugu TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        is_special_service INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS gallery_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        image_url TEXT NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Populate settings
    for k, v in DEFAULT_SETTINGS.items():
        c.execute("INSERT OR IGNORE INTO setting (key, value) VALUES (?, ?)", (k, v))

    # Populate gallery if empty
    c.execute("SELECT count(*) FROM gallery_item")
    if c.fetchone()[0] == 0:
        now_str = datetime.now(CLINIC_TIMEZONE).isoformat()
        for item in DEFAULT_GALLERY:
            c.execute("INSERT INTO gallery_item (title, image_url, description, created_at) VALUES (?, ?, ?, ?)",
                      (item["title"], item["image_url"], item["description"], now_str))

    # Seed verified clinic treatments if empty
    c.execute("SELECT count(*) FROM treatment")
    if c.fetchone()[0] == 0:
        treatments_data = [
            ("Panchakarma Detox Therapy", "పంచకర్మ", "Specialized Therapy", "Classical five-fold detoxification (Vamana, Virechana, Basti, Nasya, Raktamokshana) to eliminate accumulated metabolic toxins (Aama).", 1),
            ("Suvarnaprashana Immunization", "సువర్ణప్రాశన", "Specialized Therapy", "Ancient Ayurvedic formulation of pure gold bhasma with Medhya herbs for pediatric immunity, intellect (Medha), and vitality.", 1),
            ("Root-Cause Diagnosis & Guidance", "వ్యాధుల కారణాలపై ప్రత్యేక మార్గదర్శకత్వం", "Specialized Therapy", "In-depth Prakriti & Tridosha analysis, identifying causative factors (Hetu) with personalized Dincharya & Pathya Ahara.", 1),
            ("Skin Diseases & Allergies", "చర్మ వ్యాధులు", "Dermatology", "Classical therapies for Eczema (Vicharchika), Psoriasis (Kitibha), allergic dermatitis, and chronic rashes.", 0),
            ("Hair Loss & Scalp Problems", "జుట్టు సమస్యలు", "Trichology", "Herbal oils, Nasya, and Pitta-soothing formulations for premature hair fall (Khalitya) and dandruff.", 0),
            ("Acidity & Acid Reflux", "ఆమ్లత్వం", "Gastroenterology", "Herbal treatments balancing Pachaka Pitta, treating hyperacidity (Amlapitta), heartburn, and peptic ulcers.", 0),
            ("Digestive Disorders & IBS", "జీర్ణ సమస్యలు", "Gastroenterology", "Deepana-Pachana treatments restoring digestive fire (Jatharagni) for IBS (Grahani), chronic bloating, and constipation.", 0),
            ("Women Health & Wellness", "మహిళల వ్యాధులు", "Gynecology", "Ayurvedic care for menstrual irregularities (Artava Dushti), uterine health, and postnatal rejuvenation.", 0),
            ("PCOD & PCOS Management", "పి.సి.ఓ.డి", "Gynecology", "Holistic hormonal balancing, metabolic correction, and ovarian follicle rejuvenation without side effects.", 0),
            ("Mental Stress & Sleep Disorders", "మానసిక సమస్యలు", "Psychiatry & Wellness", "Medhya Rasayanas (Brahmi, Shankhapushpi) for anxiety, tension headaches, and restorative deep sleep.", 0),
            ("Obesity & Metabolic Correction", "ఊబకాయం", "Metabolic Health", "Lekhana herbs and Medo-Dhatu regulation to stimulate Agni and promote safe, natural weight management (Sthaulya).", 0),
            ("Asthma & Respiratory Illness", "ఉబ్బసం", "Pulmonology", "Pranavaha Srotas clearing and immune-toning herbs for chronic asthma (Tamak Shwasa), bronchitis, and wheezing.", 0),
            ("Liver Diseases & Fatty Liver", "కాలేయ వ్యాధులు", "Hepatology", "Yakrit-protective formulations (Katuki, Bhumyamalaki) restoring optimal enzyme secretion and bile flow.", 0),
            ("Arthritis & Joint Pains", "ఆర్థరైటిస్", "Rheumatology", "Vata-pacifying therapies for Osteoarthritis (Sandhigata Vata), Sciatica (Gridhrasi), and spinal stiffness.", 0),
            ("Pediatric Care", "పిల్లల వ్యాధులు", "Pediatrics", "Gentle, non-toxic classical Ayurvedic remedies (Kaumarbhritya) for recurrent cough, digestive colics, and child growth.", 0),
            ("Allergic Cold & Cough", "అలర్జీ జలుబు, దగ్గు", "Respiratory Care", "Classical remedies for seasonal allergic rhinitis (Pratishyaya) and chronic persistent cough (Kasa).", 0),
            ("Headache & Migraine", "తలనొప్పి / మైగ్రేన్", "Neurology", "Therapies for vascular and Vata-Pitta headaches (Ardhavabhedaka / Shiroroga) promoting tranquil nerve function.", 0),
            ("Kidney Stones & Renal Health", "కిడ్నీ స్టోన్", "Nephrology", "Ashmari-hara (lithotriptic) and Mutrala herbs to dissolve renal stones safely and soothe the urinary tract.", 0),
            ("Thyroid Disorders", "థైరాయిడ్ డిజార్డర్", "Endocrinology", "Glandular metabolic correction and Galaganda treatment for hypo- and hyper-thyroidism.", 0),
            ("Piles & Fissure Care", "పైల్స్, ఫిషర్", "Anorectal Care", "Gentle herbal healing, Apana Vata regulation, and dietary guidance for hemorrhoids (Arsha) and anal fissures.", 0),
            ("Diabetes Management", "మధుమేహం", "Metabolic Health", "Madhumeha management via glucose stabilization, insulin sensitivity support, and vital organ Rasayana protection.", 0),
            ("Weight & Height Management", "బరువు & ఎత్తు నిర్వహణ", "Development & Nutrition", "Dhatu-nourishing regimens optimizing healthy physical development and balanced BMI in growing youth.", 0)
        ]
        c.executemany("INSERT INTO treatment (name_english, name_telugu, category, description, is_special_service) VALUES (?, ?, ?, ?, ?)", treatments_data)

    conn.commit()
    conn.close()

def get_settings():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, value FROM setting")
    s = dict(c.fetchall())
    conn.close()
    merged = dict(DEFAULT_SETTINGS)
    merged.update(s)
    for env_key, set_key in ENV_TO_SETTING.items():   # .env values win over the Admin-panel ones
        v = os.environ.get(env_key, "").strip()
        if v:
            merged[set_key] = v
    # Keys never contain spaces/line breaks: a copy-paste that wrapped onto two lines is repaired here
    for k in SECRET_SETTINGS:
        if merged.get(k):
            merged[k] = re.sub(r"\s+", "", merged[k])
    return merged


def mask_secrets(text):
    """Hide keys/tokens from anything printed in the terminal."""
    text = str(text)
    try:
        for k in SECRET_SETTINGS:
            v = get_settings().get(k, "")
            if v and len(v) > 4:
                text = text.replace(v, "***")
    except Exception:
        pass
    return text

def _e(v):
    """HTML-escape anything a patient typed before it goes into an email / web page."""
    return _htmllib.escape(str(v if v is not None else ""), quote=True)

def clean_line(v, maxlen):
    """Single-line text: control characters (incl. line breaks) removed, trimmed, length-limited."""
    return re.sub(r"[\x00-\x1f\x7f]+", " ", str(v if v is not None else "")).strip()[:maxlen]

def clean_text(v, maxlen):
    """Multi-line text: only dangerous control characters removed."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(v if v is not None else "")).strip()[:maxlen]

_RATE = {}
_RATE_LOCK = threading.Lock()

def rl_count(bucket, ip, window):
    now = _time.time()
    with _RATE_LOCK:
        lst = [t for t in _RATE.get((bucket, ip), []) if now - t < window]
        _RATE[(bucket, ip)] = lst
        return len(lst)

def rl_blocked(bucket, ip, limit, window):
    return rl_count(bucket, ip, window) >= limit

def rl_note(bucket, ip):
    with _RATE_LOCK:
        _RATE.setdefault((bucket, ip), []).append(_time.time())
        if len(_RATE) > 20000:                       # keep memory small
            cutoff = _time.time() - 3600
            for k in [k for k, v in _RATE.items() if not v or v[-1] < cutoff]:
                _RATE.pop(k, None)

SECRET_MASK = "********"
HIDDEN_SETTINGS = ("decision_secret",)
SPA_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
           "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
           "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https:; "
           "media-src 'self' https:; connect-src 'self'; "
           "frame-src https://www.google.com https://maps.google.com https://www.google.co.in https://www.openstreetmap.org; "
           "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")

ADMIN_SESSIONS = {}              # token -> expiry (kept in memory; admin must log in again after a server restart)
ADMIN_SESSION_HOURS = 12

def admin_credentials():
    user = os.environ.get("ADMIN_USERNAME", "").strip()
    pw = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not user or not pw:
        return "ayesha_clinic", "Ayurveda@2026", False      # old default - only for local testing
    return user, pw, True

def get_week_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())

def generate_reference() -> str:
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=6))
    return f"AAC-{suffix}"

def generate_zoom_details(ref_code: str):
    room_id = f"846{random.randint(1000000, 9999999)}"
    passcode = "AAC" + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
    join_url = f"https://us05web.zoom.us/j/{room_id}?pwd={passcode}"
    return room_id, passcode, join_url

def send_automated_email(to_email, subject, html_content):
    s = get_settings()
    smtp_host = s.get("smtp_host", "smtp.gmail.com")
    smtp_port = int(s.get("smtp_port", 587))
    smtp_user = s.get("smtp_user", "ayeshashaik0211@gmail.com")
    smtp_pass = s.get("smtp_pass", "").strip()

    if not smtp_pass:
        print(f"[EMAIL SIMULATION] App password not set. Simulated sending to {to_email}: {subject}")
        return "SIMULATED_NO_PASSWORD"

    try:
        msg = EmailMessage()
        msg["From"] = f"Ayesha Ayurvedic Clinic <{smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(html_content, subtype="html")

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=25) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except (TimeoutError, OSError) as first_err:
            if isinstance(first_err, smtplib.SMTPException):
                raise
            print(f"[EMAIL] port {smtp_port} unreachable ({first_err}); trying SSL port 465 ...")
            with smtplib.SMTP_SSL(smtp_host, 465, timeout=25) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        print(f"[EMAIL DISPATCHED] Successfully sent email to {to_email}")
        return "DISPATCHED"
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        return f"FAILED: {e}"


def send_telegram_message(chat_id, message, buttons=None):
    """Send message via Telegram Bot API (free). Plain text, optional Accept/Decline buttons."""
    s = get_settings()
    bot_token = s.get("telegram_bot_token", "").strip()
    if not bot_token or not chat_id:
        print(f"[TELEGRAM SIMULATION] Token or chat_id not set. Message: {message[:60]}...")
        return "SIMULATED_NO_TOKEN"
    try:
        payload = {"chat_id": str(chat_id), "text": re.sub(r"[*`]", "", message), "disable_web_page_preview": True}
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        req = urllib.request.Request(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                                     data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print(f"[TELEGRAM DISPATCHED] Message sent to chat_id {chat_id}")
                return "DISPATCHED"
            print(f"[TELEGRAM ERROR] {result}")
            return f"FAILED: {result}"
    except urllib.error.HTTPError as e:
        print(f"[TELEGRAM ERROR] HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
        return f"FAILED: HTTP {e.code}"
    except Exception as e:
        print(f"[TELEGRAM ERROR] {mask_secrets(e)}")
        return f"FAILED: {mask_secrets(e)}"


def telegram_api(method, payload, timeout=15):
    token = get_settings().get("telegram_bot_token", "").strip()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def telegram_listener():
    """Long-polls Telegram so the doctor's Accept/Decline BUTTONS work (no public URL needed).
    A button tap simply calls this server's own /api/appointments/respond endpoint."""
    s = get_settings()
    if not s.get("telegram_bot_token", "").strip():
        print("[TELEGRAM] No bot token -> Accept/Decline buttons in Telegram are OFF.")
        return
    doctor_chat = s.get("telegram_doctor_chat_id", "").strip()
    print("[TELEGRAM] Listening for the doctor's Accept/Decline taps ...")
    offset = 0
    while True:
        try:
            body = telegram_api("getUpdates", {"offset": offset, "timeout": 25, "allowed_updates": ["callback_query"]}, timeout=40)
            for upd in body.get("result", []):
                offset = upd["update_id"] + 1
                cq = upd.get("callback_query")
                if not cq:
                    continue
                chat_id = str(cq["message"]["chat"]["id"])
                data = cq.get("data", "")
                if chat_id != doctor_chat or ":" not in data:
                    telegram_api("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "Not allowed."})
                    continue
                code, ref = data.split(":", 1)
                action = "ACCEPT" if code == "acc" else "DECLINE"
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{SERVER_PORT}/api/appointments/respond?ref={urllib.parse.quote(ref)}&action={action}&sig={decision_sig(ref, action)}&confirm=1", timeout=60) as r:
                        page = r.read().decode("utf-8", "replace")
                    note = "Already answered earlier." if "already" in page.lower() else ("Accepted ✅ - patient is being notified." if action == "ACCEPT" else "Declined ❌ - patient is being notified.")
                except Exception as e:
                    note = f"Error: {e}"
                telegram_api("answerCallbackQuery", {"callback_query_id": cq["id"], "text": note})
                wa_match = re.search(r'href="(https://wa\.me/[^"]+)"', page) if note.startswith(("Accepted", "Declined")) else None
                wa_url = wa_match.group(1).replace("&amp;", "&") if wa_match else None
                edit = {"chat_id": chat_id, "message_id": cq["message"]["message_id"],
                        "text": (cq["message"].get("text") or "") + f"\n\n➡ {note}",
                        "reply_markup": {"inline_keyboard": []}}
                if wa_url and len(wa_url) < 1900:
                    edit["reply_markup"] = {"inline_keyboard": [[{"text": "💬 Send WhatsApp to patient", "url": wa_url}]]}
                telegram_api("editMessageText", edit)
                if wa_url and len(wa_url) >= 1900:
                    telegram_api("sendMessage", {"chat_id": chat_id, "text": "💬 Send WhatsApp to patient: " + wa_url})
        except Exception as e:
            print(f"[TELEGRAM] listener error: {mask_secrets(e)} (retry in 5s)")
            _time.sleep(5)


def send_automated_sms(to_phone, message):
    """Send SMS via Fast2SMS (free tier for Indian phone numbers) or local gateway."""
    s = get_settings()
    api_key = s.get("sms_api_key", "").strip()
    clean_phone = "".join(filter(str.isdigit, to_phone))
    if len(clean_phone) > 10:
        clean_phone = clean_phone[-10:]

    if not api_key:
        print(f"[SMS SIMULATION] Fast2SMS key not set. Simulated SMS to {clean_phone}: {message[:60]}...")
        return "SIMULATED_NO_KEY"
    try:
        import urllib.request
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = json.dumps({
            "route": "q",
            "message": message,
            "language": "english",
            "flash": 0,
            "numbers": clean_phone
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "authorization": api_key,
            "Content-Type": "application/json"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            if res_data.get("return"):
                print(f"[SMS DISPATCHED] Fast2SMS sent successfully to {clean_phone}")
                return "DISPATCHED"
            else:
                print(f"[SMS ERROR] Fast2SMS response: {res_data}")
                return f"FAILED: {res_data}"
    except Exception as e:
        print(f"[SMS ERROR] Failed to send SMS to {clean_phone}: {e}")
        return f"FAILED: {e}"


def send_automated_callmebot_whatsapp(phone, message):
    """Send free WhatsApp message directly via CallMeBot API (no paid Meta business account needed)."""
    s = get_settings()
    apikey = s.get("callmebot_apikey", "").strip()
    if not apikey:
        return "SIMULATED_NO_KEY"
    try:
        import urllib.request
        clean_phone = "".join(filter(str.isdigit, phone))
        if len(clean_phone) == 10:
            clean_phone = "91" + clean_phone
        encoded = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded}&apikey={apikey}"
        req = urllib.request.Request(url, headers={"User-Agent": "AyeshaAyurvedicClinic/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            out = resp.read().decode('utf-8')
            print(f"[CALLMEBOT WHATSAPP] Response for {clean_phone}: {out[:60]}")
            return "DISPATCHED"
    except Exception as e:
        print(f"[CALLMEBOT ERROR] {mask_secrets(e)}")
        return f"FAILED: {mask_secrets(e)}"


def _background(fn):
    """Send in a background thread: the website answers instantly even when a channel is slow or down."""
    def wrapper(*a, **kw):
        threading.Thread(target=lambda: fn(*a, **kw), daemon=True).start()
        return "QUEUED"
    wrapper.__name__ = fn.__name__
    return wrapper

send_automated_email = _background(send_automated_email)
send_telegram_message = _background(send_telegram_message)
send_automated_sms = _background(send_automated_sms)
send_automated_callmebot_whatsapp = _background(send_automated_callmebot_whatsapp)


def get_server_base_url():
    """Get the base URL of this server for accept/decline links."""
    s = get_settings()
    url = s.get("server_base_url", "").strip().rstrip("/")
    if not url or url == "http://localhost:8080":
        url = f"http://localhost:{SERVER_PORT}"
    return url


def decision_secret():
    """Server-only secret that makes Accept/Decline links impossible to forge."""
    sec = os.environ.get("DECISION_SECRET", "").strip()
    if sec:
        return sec
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM setting WHERE key = 'decision_secret'")
    row = c.fetchone()
    if not row:
        val = "".join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=40))
        c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('decision_secret', ?)", (val,))
        conn.commit()
        row = (val,)
    conn.close()
    return row[0]


def decision_sig(ref, action):
    return hmac.new(decision_secret().encode(), f"{ref}|{action}".encode(), hashlib.sha256).hexdigest()[:24]


def decision_link(ref, action):
    return f"{get_server_base_url()}/api/appointments/respond?ref={ref}&action={action}&sig={decision_sig(ref, action)}"


def build_doctor_approval_whatsapp(patient_name, phone, date_str, time_str, mode, ref_code,
                                   health_concern, zoom_link=None, zoom_pass=None, with_links=True):
    """Build WhatsApp message for doctor with Accept / Decline links."""
    base_url = get_server_base_url()
    accept_url = decision_link(ref_code, "ACCEPT")
    decline_url = decision_link(ref_code, "DECLINE")

    mode_text = "Video Call (Zoom)" if mode == "VIDEO_CALL" else "Voice Call (Phone)"

    d_lines = [
        "🔔 *NEW APPOINTMENT REQUEST — AYESHA AYURVEDIC CLINIC*",
        f"Patient: *{patient_name}*",
        f"Phone: *{phone}*",
        f"Health Concern: *{health_concern or 'Not specified'}*",
        f"Date: *{date_str}*",
        f"Time Slot: *{time_str} IST*",
        f"Mode: *{mode_text}*",
        f"Booking Ref: `{ref_code}`",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "Please ACCEPT or DECLINE this appointment:",
        "",
        f"✅ *ACCEPT:* {accept_url}",
        "",
        f"❌ *DECLINE:* {decline_url}",
        "━━━━━━━━━━━━━━━━━━━━",
        "After you click Accept/Decline, you will get a button to notify the patient on WhatsApp.",
    ]
    if mode == "VIDEO_CALL":
        d_lines.insert(d_lines.index("━━━━━━━━━━━━━━━━━━━━"), "🎥 Video call: please send the Zoom link to the patient on WhatsApp.")
    if not with_links:
        # the patient's own phone sends this text -> NO accept/decline links in it
        cut = d_lines.index("━━━━━━━━━━━━━━━━━━━━")
        d_lines = d_lines[:cut] + ["The doctor will confirm or decline shortly."]
    return "\n".join(d_lines)


def build_patient_confirmed_whatsapp(patient_name, phone, date_str, time_str, mode, ref_code,
                                     zoom_link=None, zoom_pass=None):
    """Build WhatsApp message for patient when doctor ACCEPTS."""
    mode_text = "Video Call (Zoom)" if mode == "VIDEO_CALL" else "Voice Call (Phone)"
    p_lines = [
        "🌿 *AYESHA AYURVEDIC CLINIC* 🌿",
        "_Dr. Shaik Ayesha, B.A.M.S. (Andhra Board Regn: 2545/A/2025)_",
        "Thollabazar, Near Congress Office, Tiruvuru\n",
        f"Namaste *{patient_name}*,",
        "✅ Your appointment has been *ACCEPTED & CONFIRMED* by Dr. Shaik Ayesha!\n",
        f"📅 *Date:* {date_str}",
        f"⏰ *Time Window:* {time_str} IST (5:00 PM – 8:30 PM)",
        f"📞 *Consultation Mode:* {mode_text}",
        f"🔖 *Booking Reference:* `{ref_code}`\n",
    ]
    if mode == "VIDEO_CALL":
        p_lines.append("*Video Consultation Details:*")
        p_lines.append("🔗 The Zoom link will be sent to you on WhatsApp before your consultation.\n")
    else:
        p_lines.append("*Voice Call Instructions:*")
        p_lines.append(f"Dr. Ayesha Shaik will call you on *{phone}* during 5:00 PM – 8:30 PM IST on the appointment day. Please keep your phone reachable.\n")
    p_lines += [
        "📍 Clinic: Thollabazar, Near Congress Office, Tiruvuru, AP - 521235",
        "📞 Helpline: +91 8465058469",
        "📧 Email: ayeshashaik0211@gmail.com",
    ]
    return "\n".join(p_lines)


def build_patient_declined_whatsapp(patient_name, date_str, ref_code):
    """Build WhatsApp message for patient when doctor DECLINES."""
    lines = [
        "🌿 *AYESHA AYURVEDIC CLINIC* 🌿",
        "_Dr. Shaik Ayesha, B.A.M.S._\n",
        f"Namaste *{patient_name}*,",
        "We regret to inform you that your appointment request has been *DECLINED* by the doctor for this slot.\n",
        f"🔖 *Booking Reference:* `{ref_code}`",
        f"📅 *Requested Date:* {date_str}\n",
        "This may be because the doctor is unavailable for that specific slot.",
        "Please try booking a different date or contact us directly:\n",
        "📞 Helpline: +91 8465058469",
        "📧 Email: ayeshashaik0211@gmail.com",
        "💬 WhatsApp: https://wa.me/918465058469",
    ]
    return "\n".join(lines)

def build_whatsapp_messages(patient_name, phone, date_str, time_str, mode, ref_code, zoom_link=None, zoom_pass=None):
    is_video = (mode == "VIDEO_CALL")
    mode_text = "🎥 Video Call (Zoom)" if is_video else "📞 Voice Call (Phone Call)"

    # 1. Message for Patient
    p_lines = [
        "🌿 *AYESHA AYURVEDIC CLINIC* 🌿",
        "_Dr. Shaik Ayesha, B.A.M.S. (Andhra Board Regn: 2545/A/2025)_",
        "Thollabazar, Near Congress Office, Tiruvuru\n",
        f"Namaste *{patient_name}*,",
        "Your online Ayurvedic consultation has been *booked successfully*!\n",
        f"📅 *Date:* {date_str} (Wednesday/Friday)",
        f"⏰ *Time Slot:* {time_str} IST (Window: 5:00 PM – 8:30 PM)",
        f"📞 *Consultation Mode:* {mode_text}",
        f"🔖 *Booking Reference:* `{ref_code}`\n"
    ]

    if is_video:
        p_lines.append("*Video Consultation Instructions:*")
        p_lines.append("🔗 The Zoom link will be sent to you on WhatsApp before your consultation.\n")
    else:
        p_lines.append("*Voice Call Consultation Instructions:*")
        p_lines.append(f"Dr. Ayesha Shaik will call you directly on your phone number ({phone}) during 5:00 PM – 8:30 PM IST on that day. Please ensure your phone is reachable.\n")

    p_lines.append("📍 Clinic Location: Thollabazar, Near Congress Office, Tiruvuru, AP - 521235")
    p_lines.append("📞 Helpline & WhatsApp: +91 8465058469")
    p_lines.append("📧 Email: ayeshashaik0211@gmail.com")
    p_lines.append("🌐 Map Directions: https://maps.app.goo.gl/wo1SKmo2VKCcEe8G8?g_st=ac")
    patient_msg = "\n".join(p_lines)

    # 2. Message for Doctor (Dr. Shaik Ayesha at 8465058469)
    d_lines = [
        "🔔 *NEW ONLINE APPOINTMENT NOTIFICATION*",
        f"Patient: *{patient_name}*",
        f"Phone: *{phone}*",
        f"Mode: *{mode_text}*",
        f"Date: *{date_str}*",
        f"Slot: *{time_str} IST*",
        f"Booking Ref: `{ref_code}`",
    ]
    if is_video:
        d_lines.append("Video call: please send the Zoom link to the patient on WhatsApp.")
    d_lines.append("\nPlease review patient consultation details in the clinic portal.")
    doctor_msg = "\n".join(d_lines)

    clean_patient_phone = "".join(filter(str.isdigit, phone))
    if len(clean_patient_phone) == 10:
        clean_patient_phone = "91" + clean_patient_phone

    clean_doc_phone = "918465058469"

    patient_wa_url = f"https://wa.me/{clean_patient_phone}?text={urllib.parse.quote(patient_msg)}"
    doctor_wa_url = f"https://wa.me/{clean_doc_phone}?text={urllib.parse.quote(doctor_msg)}"

    return {
        "patientMessage": patient_msg,
        "doctorMessage": doctor_msg,
        "patientWhatsAppUrl": patient_wa_url,
        "doctorWhatsAppUrl": doctor_wa_url,
        "clinicWhatsAppUrl": doctor_wa_url,
        "deliveryStatus": "READY_AND_DISPATCHED"
    }

build_whatsapp_message = build_whatsapp_messages


WATCHER_JS = r'''/* Live booking status for the patient: waits for the doctor's decision, then shows the result.
   Print Slip is offered ONLY after the doctor accepted; "Book Another" only after any decision. */
(function () {
  var KEY = "aacActiveBooking";
  var POLL_MS = 4000;
  var PENDING_TTL = 12 * 3600 * 1000;   // a never-answered request stops being shown after 12 h
  var FINAL_TTL = 15 * 60 * 1000;          // a finished booking is never kept longer than 15 minutes
  var AUTO_RESET_MS = 10 * 60 * 1000;      // ...and the page returns to a fresh booking form after 10 idle minutes
  var printedByUs = false, resetTimer = null;
  var origFetch = window.fetch;
  var current = null, lastData = null, timer = null, rendering = false, observer = null;

  function esc(v) {
    return String(v == null ? "" : v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function save(b) { try { localStorage.setItem(KEY, JSON.stringify(b)); } catch (e) {} }
  function clearStore() { try { localStorage.removeItem(KEY); } catch (e) {} }
  function load() {
    try {
      var b = JSON.parse(localStorage.getItem(KEY) || "null");
      if (!b) return null;
      if (b.final && b.shown) { clearStore(); return null; }     // result was already shown once -> new visit = fresh form
      var age = Date.now() - b.ts;
      if (b.final ? age > FINAL_TTL : age > PENDING_TTL) { clearStore(); return null; }
      return b;
    } catch (e) { return null; }
  }
  function fmt(startsAt) {
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(startsAt || "");
    if (!m) return { date: startsAt || "", time: "" };
    var d = new Date(+m[1], +m[2] - 1, +m[3]);
    var date = d.toLocaleDateString("en-GB", { weekday: "long", day: "2-digit", month: "long", year: "numeric" });
    var h = +m[4], ap = h >= 12 ? "PM" : "AM"; h = h % 12 || 12;
    return { date: date, time: (h < 10 ? "0" : "") + h + ":" + m[5] + " " + ap };
  }

  function injectPrintCss() {
    if (document.getElementById("aacPrintCss")) return;
    var st = document.createElement("style"); st.id = "aacPrintCss";
    st.textContent =
      "@media screen { #printSlip { display: none !important; } }" +
      "@media print {" +
      " @page { size: A4; margin: 14mm; }" +
      " html, body { background: #fff !important; margin: 0 !important; padding: 0 !important; height: auto !important; overflow: visible !important; }" +
      " body > *:not(#printSlip) { display: none !important; }" +
      " #printSlip { display: block !important; position: static !important; width: auto !important; max-width: 720px; margin: 0 auto !important; padding: 22px; border: 2px solid #143826; font-family: Arial, Helvetica, sans-serif; color: #000; background: #fff; }" +
      " #printSlip .slip-header { text-align: center; border-bottom: 2px solid #143826; padding-bottom: 10px; margin-bottom: 14px; }" +
      " #printSlip .slip-header h1 { font-size: 22px; margin: 0 0 4px; color: #143826; }" +
      " #printSlip .slip-header p { margin: 2px 0; font-size: 12px; }" +
      " #printSlip .slip-title { text-align: center; letter-spacing: 2px; font-size: 18px; margin: 12px 0 8px; }" +
      " #printSlip .slip-ref { text-align: center; font-family: monospace; font-size: 20px; font-weight: 700; border: 1px dashed #000; display: table; margin: 0 auto 16px; padding: 4px 16px; }" +
      " #printSlip .slip-table { width: 100%; border-collapse: collapse; }" +
      " #printSlip .slip-table th, #printSlip .slip-table td { border: 1px solid #888; padding: 8px 10px; text-align: left; font-size: 14px; }" +
      " #printSlip .slip-table th { width: 30%; background: #f0f0f0; }" +
      " #printSlip .slip-note { font-size: 12px; margin: 14px 0; }" +
      " #printSlip .slip-footer { font-size: 11px; text-align: center; border-top: 1px solid #888; padding-top: 8px; }" +
      "}";
    (document.head || document.documentElement).appendChild(st);
  }

  function buildSlip(d) {
    injectPrintCss();
    var old = document.getElementById("printSlip"); if (old) old.remove();
    var f = fmt(d.starts_at), isVideo = d.consultation_type === "VIDEO_CALL";
    var slip = document.createElement("div"); slip.id = "printSlip";
    slip.innerHTML =
      '<div class="slip-header"><h1>AYESHA AYURVEDIC CLINIC</h1><p class="slip-te">ఆయేషా ఆయుర్వేదిక్ క్లినిక్</p>' +
      '<p>Dr. Shaik Ayesha, B.A.M.S. (Ayurvedic Physician) · Regn. No: 2545/A/2025</p></div>' +
      '<h2 class="slip-title">APPOINTMENT SLIP</h2><div class="slip-ref">' + esc(d.reference_code) + '</div>' +
      '<table class="slip-table">' +
      '<tr><th>Patient Name</th><td>' + esc(d.patient_name) + '</td></tr>' +
      '<tr><th>Mobile</th><td>' + esc(d.patient_phone) + '</td></tr>' +
      '<tr><th>Date</th><td>' + esc(f.date) + '</td></tr>' +
      '<tr><th>Time</th><td>' + esc(f.time) + ' IST (consultation window 5:00 PM – 8:30 PM)</td></tr>' +
      '<tr><th>Mode</th><td>' + (isVideo ? "Video Call (Zoom) - the Zoom link will be sent to you on WhatsApp" : "Voice Call (the doctor will call you)") + '</td></tr>' +
      '<tr><th>Status</th><td>CONFIRMED by the doctor</td></tr></table>' +
      '<p class="slip-note">Please keep this slip and quote the reference number above for any query or cancellation.</p>' +
      '<div class="slip-footer">Thollabazar (10-188), Near Congress Office / Jaibhavi Centre, Tiruvuru, Krishna District, Andhra Pradesh - 521235<br>' +
      'Phone / WhatsApp: +91 8465058469 · +91 9848339262</div>';
    document.body.appendChild(slip);
  }

  function panelHtml(d) {
    var f = fmt(d.starts_at), isVideo = d.consultation_type === "VIDEO_CALL";
    var mode = isVideo ? "🎥 Video Call (Zoom)" : "📞 Voice Call (Phone Call)";
    var st = d.status, icon, color, head, msg, label, buttons = "";
    var another = '<button type="button" class="btn btn-gold" id="aacAnother">📅 Book Another Consultation</button>';
    var print = '<button type="button" class="btn btn-outline" id="aacPrint">🖨 Print Appointment Slip</button>';
    if (st === "CONFIRMED") {
      icon = "✓"; color = "#15803d"; head = "Appointment Booked Successfully!"; label = "CONFIRMED BY THE DOCTOR";
      msg = isVideo ? "Dr. Shaik Ayesha accepted your request. The Zoom link will be sent to you on WhatsApp before your slot."
                    : "Dr. Shaik Ayesha accepted your request. She will call you on " + esc(d.patient_phone) + " between 5:00 PM and 8:30 PM IST.";
      buttons = print + another;
    } else if (st === "DECLINED") {
      icon = "✕"; color = "#b91c1c"; head = "Appointment Not Accepted"; label = "NOT ACCEPTED BY THE DOCTOR";
      msg = "Sorry, the doctor could not accept your request for " + esc(f.date) + " at " + esc(f.time) + " IST. Please book another date.";
      buttons = another;
    } else if (st === "CANCELLED") {
      icon = "✕"; color = "#6b7280"; head = "Appointment Cancelled"; label = "CANCELLED";
      msg = "This appointment was cancelled. You can book a new one any time.";
      buttons = another;
    } else {
      icon = "⏳"; color = "#b45309"; head = "Request Processing by Doctor"; label = "REQUEST PROCESSING BY DOCTOR";
      msg = "Your request has been emailed to Dr. Shaik Ayesha. This page updates by itself as soon as she accepts or declines, so please keep it open.";
      if (current && current.waUrl) {
        buttons = '<a class="btn btn-gold" id="aacWaDoctor" href="' + esc(current.waUrl) + '" target="_blank" rel="noopener" ' +
                  'style="background:#25d366;border-color:#25d366;color:#fff;text-decoration:none;">💬 Send WhatsApp to Doctor</a>';
        msg += "<br><span style='font-size:0.95rem;font-weight:600;'>If WhatsApp did not open, tap the green button and press Send so the doctor is alerted.</span>";
      }
    }
    return '<div id="aacStatusPanel" class="confirm-box-full" data-status="' + esc(st) + '">' +
      '<div class="confirm-icon-big" style="background:' + color + ';color:#fff;">' + icon + '</div>' +
      '<h3 style="font-family: var(--font-serif); font-size: 2.1rem; color: ' + color + '; margin-bottom: 0.5rem;">' + head + '</h3>' +
      '<div class="confirm-ref-badge">' + esc(d.reference_code) + '</div>' +
      '<p style="font-size:1.1rem;font-weight:700;margin-bottom:1.5rem;">' + msg + '</p>' +
      '<div class="confirm-details-table">' +
      '<div class="confirm-row"><span style="color:var(--text-muted);">Patient Name:</span><b>' + esc(d.patient_name) + '</b></div>' +
      '<div class="confirm-row"><span style="color:var(--text-muted);">Mobile:</span><b>' + esc(d.patient_phone) + '</b></div>' +
      '<div class="confirm-row"><span style="color:var(--text-muted);">Date &amp; Time:</span><b>' + esc(f.date) + ' at ' + esc(f.time) + ' IST</b></div>' +
      '<div class="confirm-row"><span style="color:var(--text-muted);">Consultation Mode:</span><b>' + mode + '</b></div>' +
      '<div class="confirm-row"><span style="color:var(--text-muted);">Status:</span><b style="color:' + color + ';">' + label + '</b></div></div>' +
      (st === "PENDING" ? '<p style="color:var(--text-muted);font-size:0.9rem;margin:1.25rem 0;">Checking for the doctor\'s answer every few seconds…</p>' : '') +
      (buttons ? '<div style="display:flex;justify-content:center;gap:1rem;flex-wrap:wrap;margin-top:1.5rem;">' + buttons + '</div>' : '') +
      '</div>';
  }

  function render(d) {
    var c = document.getElementById("bookingCardVertical");
    if (!c) return;
    rendering = true;
    c.innerHTML = panelHtml(d);
    var p = document.getElementById("aacPrint"), a = document.getElementById("aacAnother");
    if (p) p.onclick = function () { printedByUs = true; window.print(); };
    if (a) a.onclick = function () { freshBooking(); };
    if (d.status === "CONFIRMED") buildSlip(d);
    else { var s = document.getElementById("printSlip"); if (s) s.remove(); }
    setTimeout(function () { rendering = false; }, 0);
  }

  function watchContainer() {
    var c = document.getElementById("bookingCardVertical");
    if (!c || observer) return;
    observer = new MutationObserver(function () {
      // the website's own code just replaced the card -> put the live status back
      if (!rendering && current && lastData && !c.querySelector("#aacStatusPanel")) render(lastData);
    });
    observer.observe(c, { childList: true });
  }

  function poll() {
    if (!current) return;
    origFetch("/api/appointments/lookup?referenceCode=" + encodeURIComponent(current.ref) +
              "&phone=" + encodeURIComponent(current.phone), { cache: "no-store" })
      .then(function (r) { if (r.status === 404) { stop(); clearStore(); return null; } return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d) return;
        var changed = !lastData || lastData.status !== d.status;
        lastData = d;
        var c = document.getElementById("bookingCardVertical");
        if (changed || (c && !c.querySelector("#aacStatusPanel"))) render(d);
        if (d.status !== "PENDING") {
          current.final = true; current.shown = true; current.ts = Date.now(); save(current);
          stop(); scheduleAutoReset();
        }
      })
      .catch(function () {});
  }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  function freshBooking() { stop(); clearStore(); location.reload(); }
  function scheduleAutoReset() {
    if (resetTimer) clearTimeout(resetTimer);
    resetTimer = setTimeout(freshBooking, AUTO_RESET_MS);
  }
  function finishAndReset(message) {
    stop();
    try {
      var t = document.createElement("div");
      t.setAttribute("role", "status");
      t.style.cssText = "position:fixed;left:50%;top:16px;transform:translateX(-50%);z-index:99999;background:#143826;color:#fff;" +
        "padding:14px 22px;border-radius:10px;font:600 15px/1.4 sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.35);max-width:92vw;text-align:center;";
      t.textContent = message;
      document.body.appendChild(t);
    } catch (e) {}
    clearStore();                                   // personal details are removed right now
    setTimeout(function () { location.reload(); }, 1600);
  }
  // After the slip is printed (or saved as PDF) the page goes back to a clean booking form
  window.addEventListener("afterprint", function () {
    if (!printedByUs) return;
    printedByUs = false;
    finishAndReset("Appointment slip printed \u2713  Getting a fresh booking form ready\u2026");
  });

  function track(b, provisional) {
    current = b; lastData = provisional; save(b);
    watchContainer();
    setTimeout(function () { if (lastData) render(lastData); poll(); }, 50);
    stop(); timer = setInterval(poll, POLL_MS);
  }

  // Catch the patient's successful booking request
  window.fetch = function (input, init) {
    var p = origFetch.apply(this, arguments);
    try {
      var url = typeof input === "string" ? input : (input && input.url) || "";
      var isBooking = /\/appointments$/.test(url.split("?")[0]) && init && String(init.method).toUpperCase() === "POST";
      if (isBooking) {
        p.then(function (res) {
          if (res.status !== 201) return;
          res.clone().json().then(function (data) {
            var body = {}; try { body = JSON.parse(init.body || "{}"); } catch (e) {}
            if (!data.reference || !body.phone) return;
            var waUrl = data.notification && data.notification.doctorWhatsAppUrl;
            if (waUrl) {
              // WhatsApp opens with the message already typed - the patient only has to press Send
              try { window.open(waUrl, "aacWhatsApp", "width=520,height=720"); } catch (e) {}
            }
            track({ ref: data.reference, phone: body.phone, ts: Date.now(), final: false, waUrl: waUrl || "" },
                  { status: "PENDING", reference_code: data.reference, starts_at: data.startsAt,
                    consultation_type: data.consultationType, patient_name: body.patientName, patient_phone: body.phone });
          });
        });
      }
    } catch (e) {}
    return p;
  };

  // Page reloaded or reopened: show the same booking's status again
  document.addEventListener("DOMContentLoaded", function () {
    var b = load();
    if (!b) return;
    track(b, null);   // nothing is drawn until the server has answered
  });
})();
'''


def doctor_result_page(accepted, ref, patient_name, patient_phone, formatted_date, consultation_type, patient_wa_url):
    """Page shown to the doctor after Accept/Decline: a POPUP asks her to notify the patient on WhatsApp."""
    colour = "#16a34a" if accepted else "#dc2626"
    bg = "#f0fdf4" if accepted else "#fef2f2"
    icon = "✅" if accepted else "❌"
    word = "ACCEPTED" if accepted else "DECLINED"
    btn_text = "💬 Send ACCEPTED message to Patient" if accepted else "💬 Send DECLINED message to Patient"
    btn_bg = "#25d366" if accepted else "#dc2626"
    return f"""
    <div style="font-family:sans-serif;text-align:center;padding:60px 20px;background:{bg};min-height:100vh;">
      <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;border:2px solid {colour};">
        <div style="font-size:3rem;margin-bottom:16px;">{icon}</div>
        <h2 style="color:{colour};margin-bottom:8px;">Appointment {word}</h2>
        <p style="font-size:1.1rem;font-weight:600;color:#143826;">Ref: {ref}</p>
        <p>Patient <b>{_e(patient_name)}</b> ({_e(patient_phone)}) &middot; {formatted_date}</p>
        <p>The patient's website page has been updated and they were emailed (if an email was given).</p>
      </div>
    </div>
    <div id="waPopup" style="position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;z-index:9999;padding:20px;">
      <div style="background:#fff;border-radius:14px;padding:32px 28px;max-width:420px;width:100%;text-align:center;border-top:6px solid {colour};box-shadow:0 10px 40px rgba(0,0,0,.35);">
        <div style="font-size:2.6rem;">📲</div>
        <h3 style="margin:8px 0;color:#143826;">Notify the patient on WhatsApp</h3>
        <p style="color:#444;">Tap the button. WhatsApp opens with your <b>{word}</b> reply to <b>{_e(patient_name)}</b> already typed - just press <b>Send</b>.</p>
        <a href="{patient_wa_url}" target="_blank" rel="noopener"
           onclick="setTimeout(function(){{document.getElementById('waPopup').style.display='none';}},400);"
           style="display:block;margin-top:18px;background:{btn_bg};color:#fff;padding:15px 20px;border-radius:8px;text-decoration:none;font-weight:700;font-size:1.05rem;">
           {btn_text}
        </a>
        <button type="button" onclick="document.getElementById('waPopup').style.display='none';"
           style="margin-top:12px;background:none;border:0;color:#777;cursor:pointer;font-size:.9rem;">Close (I will message later)</button>
      </div>
    </div>
    """

RESPONSIVE_CSS = """
/* Fit every screen: phone, tablet, laptop, big desktop */
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
html, body { max-width: 100%; overflow-x: clip; }
img, video, svg, canvas, iframe { max-width: 100%; }
img, video { height: auto; }
@media (min-width: 1200px) { html { font-size: 17.5px; } }
@media (min-width: 1500px) { html { font-size: 19px; } }
@media (min-width: 1800px) { html { font-size: 21px; } }
@media (min-width: 2300px) { html { font-size: 24px; } }
@media (max-width: 768px) {
  html { font-size: 16px; }
  input, select, textarea { font-size: 16px !important; max-width: 100%; }
  button, .btn, a.btn, [role="button"] { min-height: 44px; }
  table { display: block; max-width: 100%; overflow-x: auto; }
  .confirm-box-full { padding-left: 1rem !important; padding-right: 1rem !important; }
  .confirm-row { flex-wrap: wrap; gap: .25rem; }
}
@media print { html { font-size: 16px !important; } }
"""

def inject_into_index(body_bytes):
    if b'name="viewport"' not in body_bytes and b"name='viewport'" not in body_bytes and b"<head>" in body_bytes:
        body_bytes = body_bytes.replace(b"<head>", b'<head><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">', 1)
    style = ('<style id="aac-responsive">' + RESPONSIVE_CSS + '</style>').encode("utf-8")
    if b"</head>" in body_bytes:
        body_bytes = body_bytes.replace(b"</head>", style + b"</head>", 1)
    else:
        body_bytes = style + body_bytes
    tag = b'<script src="/status-watcher.js"></script>'
    if b"</body>" in body_bytes:
        return body_bytes.replace(b"</body>", tag + b"</body>", 1)
    return body_bytes + tag

class ClinicHandler(SimpleHTTPRequestHandler):
    timeout = 30                      # drop slow / stalled connections
    server_version = "Clinic"
    sys_version = ""

    def end_headers(self):
        allowed = os.environ.get("ALLOWED_ORIGIN", "").strip()
        if allowed and self.headers.get("Origin", "") == allowed:      # CORS is OFF unless you set ALLOWED_ORIGIN
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")          # Accept/Decline links never leak through Referer
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()")
        if os.environ.get("CSP_OFF", "").strip() != "1":
            self.send_header("Content-Security-Policy", SPA_CSP)
        if get_server_base_url().startswith("https://"):
            self.send_header("Strict-Transport-Security", "max-age=31536000")
        super().end_headers()

    def log_message(self, fmt, *args):
        # never print query strings (they contain phone numbers and decision links)
        try:
            line = fmt % args
            line = re.sub(r"\?[^ ]*", "?...", line, count=1)
            sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), line))
        except Exception:
            pass

    def client_ip(self):
        peer = self.client_address[0]
        if peer in ("127.0.0.1", "::1"):        # we sit behind a tunnel/proxy on this same machine
            for h in ("CF-Connecting-IP", "X-Forwarded-For"):
                v = self.headers.get(h, "")
                if v:
                    return v.split(",")[0].strip()[:64]
        return peer

    def _is_local(self):
        return self.client_ip() in ("127.0.0.1", "::1")

    def _flood_blocked(self):
        """Overall request flood guard: 600 requests / minute / visitor."""
        if self._is_local():
            return False
        ip = self.client_ip()
        rl_note("flood", ip)
        return rl_count("flood", ip, 60) > 600

    def _same_origin_ok(self):
        o = self.headers.get("Origin", "")
        if not o:
            return True
        allowed = os.environ.get("ALLOWED_ORIGIN", "").strip()
        return urllib.parse.urlparse(o).netloc == self.headers.get("Host", "") or (allowed and o == allowed)

    def _admin_ok(self):
        """True only for a logged-in admin (token in the login cookie or in an Authorization: Bearer header)."""
        token = ""
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "aac_admin":
                token = v
        auth = self.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip() or token
        exp = ADMIN_SESSIONS.get(token)
        if exp and exp > _time.time():
            return True
        ADMIN_SESSIONS.pop(token, None)
        return False

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, status_code, data, extra_headers=None):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        for hk, hv in (extra_headers or []):
            self.send_header(hk, hv)
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_html_response(self, status_code, body_html):
        """Send a full HTML page (used for doctor Accept/Decline responses)."""
        full_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ayesha Ayurvedic Clinic — Appointment Response</title>
<style>body{{margin:0;font-family:sans-serif;background:#f8f6f0;}}</style>
</head><body>{body_html}</body></html>"""
        encoded = full_html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self._flood_blocked():
            self.send_json(429, {"message": "Too many requests. Please wait a minute."})
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/admin/") and not self._admin_ok():
            self.send_json(401, {"message": "Admin login required."})
            return

        if path == "/api/clinic":
            s = get_settings()
            self.send_json(200, {
                "name": s["clinic_name"],
                "nameTelugu": s["clinic_name_telugu"],
                "doctor": s["doctor_name"],
                "qualification": s["doctor_qualification"],
                "doctorEmail": s.get("doctor_email", "ayeshashaik0211@gmail.com"),
                "registrationNumber": s["registration_number"],
                "stateBoard": s["state_board"],
                "primaryPhone": s["primary_phone"],
                "primaryWhatsApp": s["primary_whatsapp"],
                "secondaryPhone": s["secondary_phone"],
                "address": s["address"],
                "googleMapsUrl": s["google_maps_url"],
                "heroTitle": s["hero_title"],
                "heroSubtitle": s["hero_subtitle"],
                "onlineTimings": s["online_timings"],
                "sundayOfflineTimings": s["sunday_timings"],
                "dailyLimit": int(s.get("daily_limit", "3")),
                "weeklyLimit": int(s.get("weekly_limit", "6")),
                "bookingEnabled": s.get("booking_enabled", "true") == "true"
            })
            return

        elif path == "/api/treatments":
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM treatment WHERE active = 1 ORDER BY is_special_service DESC, category ASC")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self.send_json(200, rows)
            return

        elif path == "/api/gallery":
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM gallery_item ORDER BY id ASC")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self.send_json(200, rows)
            return

        elif path == "/api/admin/settings":
            s = get_settings()
            out = {k: v for k, v in s.items() if k not in HIDDEN_SETTINGS}
            for k in SECRET_SETTINGS:
                if out.get(k):
                    out[k] = SECRET_MASK          # secrets are never sent back to the browser
            self.send_json(200, out)
            return

        elif path == "/api/admin/treatments":
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM treatment ORDER BY is_special_service DESC, category ASC")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self.send_json(200, rows)
            return

        elif path == "/api/admin/gallery":
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM gallery_item ORDER BY id DESC")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self.send_json(200, rows)
            return

        elif path == "/api/availability":
            s = get_settings()
            daily_lim = int(s.get("daily_limit", "3"))
            weekly_lim = int(s.get("weekly_limit", "6"))
            booking_on = s.get("booking_enabled", "true") == "true"

            weeks = int(query.get("weeks", [8])[0])
            from_str = query.get("from", [None])[0]
            if from_str:
                start_date = datetime.strptime(from_str, "%Y-%m-%d").date()
            else:
                start_date = datetime.now(CLINIC_TIMEZONE).date()

            start_monday = get_week_monday(start_date)
            today_date = datetime.now(CLINIC_TIMEZONE).date()
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            days_list = []
            standard_slots = ["17:00", "17:45", "18:30", "19:15", "20:00"]

            for w in range(weeks):
                week_mon = start_monday + timedelta(weeks=w)
                week_mon_str = week_mon.isoformat()

                c.execute("SELECT count(*) FROM appointment WHERE clinic_week_start = ? AND mode = 'ONLINE' AND status IN ('CONFIRMED', 'PENDING')", (week_mon_str,))
                week_booked = c.fetchone()[0]

                for weekday_idx, weekday_name in [(2, "WEDNESDAY"), (4, "FRIDAY")]:
                    day_date = week_mon + timedelta(days=weekday_idx)
                    day_date_str = day_date.isoformat()

                    c.execute("""
                        SELECT count(*) FROM appointment 
                        WHERE date(starts_at) = ? AND mode = 'ONLINE' AND status IN ('CONFIRMED', 'PENDING')
                    """, (day_date_str,))
                    day_booked = c.fetchone()[0]

                    is_past = (day_date < today_date)
                    is_full = (day_booked >= daily_lim)
                    available = (booking_on and not is_past and not is_full and week_booked < weekly_lim)

                    days_list.append({
                        "date": day_date_str,
                        "weekday": weekday_name,
                        "booked": day_booked,
                        "dayLimit": daily_lim,
                        "weekBooked": week_booked,
                        "weekLimit": weekly_lim,
                        "isPast": is_past,
                        "isFull": is_full,
                        "available": available,
                        "availableSlots": standard_slots if available else []
                    })

            conn.close()
            self.send_json(200, {
                "timezone": "Asia/Kolkata",
                "bookingWeekStarts": "MONDAY",
                "dailyLimit": daily_lim,
                "weeklyLimit": weekly_lim,
                "days": days_list,
                "bookingEnabled": booking_on,
                "clinicTimings": s["online_timings"],
                "primaryPhone": s["primary_phone"]
            })
            return

        elif path == "/api/appointments/lookup":
            ref = query.get("referenceCode", [""])[0].strip().upper()[:20]
            phone = query.get("phone", [""])[0].strip()[:30]
            ip = self.client_ip()
            if not self._is_local() and rl_blocked("lookup_fail", ip, 20, 600):
                self.send_json(429, {"message": "Too many wrong attempts. Please try again in 10 minutes."})
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
                SELECT a.*, p.full_name as patient_name, p.phone as patient_phone, p.email as patient_email, p.age, p.health_concern
                FROM appointment a
                JOIN patient p ON a.patient_id = p.id
                WHERE a.reference_code = ?
            """, (ref,))
            row = c.fetchone()
            conn.close()

            if not row or "".join(filter(str.isdigit, row["patient_phone"]))[-10:] != "".join(filter(str.isdigit, phone))[-10:]:
                rl_note("lookup_fail", ip)
                self.send_json(404, {"message": "No matching appointment found with this reference code and phone number."})
                return

            d = dict(row)
            # only what the patient page needs - no email, age, health details, internal ids
            keep = ("reference_code", "status", "starts_at", "consultation_type", "mode", "patient_name", "patient_phone")
            self.send_json(200, {k: d.get(k) for k in keep})
            return

        elif path == "/api/admin/appointments":
            s = get_settings()
            daily_lim = int(s.get("daily_limit", "3"))
            weekly_lim = int(s.get("weekly_limit", "6"))

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            today = datetime.now(CLINIC_TIMEZONE).date()
            curr_mon = get_week_monday(today).isoformat()
            c.execute("SELECT count(*) FROM appointment WHERE clinic_week_start = ? AND mode = 'ONLINE' AND status = 'CONFIRMED'", (curr_mon,))
            week_booked = c.fetchone()[0]

            c.execute("""
                SELECT a.*, p.full_name as patient_name, p.phone as patient_phone, p.email as patient_email, p.age, p.health_concern
                FROM appointment a
                JOIN patient p ON a.patient_id = p.id
                ORDER BY a.starts_at DESC
            """)
            appointments = [dict(r) for r in c.fetchall()]
            conn.close()

            self.send_json(200, {
                "weekBooked": week_booked,
                "weeklyLimit": weekly_lim,
                "dailyLimit": daily_lim,
                "appointments": appointments
            })
            return

        elif path == "/api/appointments/respond":
            # ── DOCTOR ACCEPT / DECLINE ENDPOINT ──
            ref = query.get("ref", [""])[0].strip().upper()
            action = query.get("action", [""])[0].strip().upper()  # ACCEPT or DECLINE

            if not ref or action not in ["ACCEPT", "DECLINE"]:
                self._send_html_response(400, "<h2>Invalid request. Missing ref or action.</h2>")
                return

            if not hmac.compare_digest(query.get("sig", [""])[0], decision_sig(ref, action)):
                if not self._is_local():
                    rl_note("sig_fail", self.client_ip())
                    if rl_blocked("sig_fail", self.client_ip(), 10, 600):
                        self._send_html_response(429, "<h2>Too many attempts.</h2>")
                        return
                self._send_html_response(403, "<h2>This link is invalid. Only the doctor's own links work.</h2>")
                return

            if query.get("confirm", [""])[0] != "1":
                colour = "#16a34a" if action == "ACCEPT" else "#dc2626"
                label = "✅ Yes, ACCEPT this appointment" if action == "ACCEPT" else "❌ Yes, DECLINE this appointment"
                self._send_html_response(200, f"""
                <div style="font-family:sans-serif;text-align:center;padding:50px 20px;">
                  <h2>Appointment {ref}</h2>
                  <p>Press the button to confirm your decision. The patient is notified right after.</p>
                  <a href="/api/appointments/respond?ref={urllib.parse.quote(ref)}&action={action}&sig={query.get("sig", [""])[0]}&confirm=1"
                     style="display:inline-block;background:{colour};color:#fff;padding:16px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:1.1rem;">{label}</a>
                </div>""")
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
                SELECT a.*, p.full_name as patient_name, p.phone as patient_phone,
                       p.email as patient_email, p.age, p.health_concern
                FROM appointment a
                JOIN patient p ON a.patient_id = p.id
                WHERE a.reference_code = ?
            """, (ref,))
            row = c.fetchone()

            if not row:
                conn.close()
                self._send_html_response(404, f"<h2>Appointment {ref} not found.</h2>")
                return

            appt = dict(row)
            current_status = appt["status"]

            if current_status in ("CONFIRMED", "DECLINED", "CANCELLED"):
                conn.close()
                status_emoji = "✅" if current_status == "CONFIRMED" else "❌"
                self._send_html_response(200, f"""
                <div style="font-family:sans-serif;text-align:center;padding:60px 20px;">
                  <h2>{status_emoji} Appointment {ref} is already <b>{current_status}</b>.</h2>
                  <p>Patient: <b>{appt['patient_name']}</b></p>
                  <p>This appointment has already been responded to. No further action needed.</p>
                </div>
                """)
                return

            patient_name = appt["patient_name"]
            patient_phone = appt["patient_phone"]
            patient_email = appt["patient_email"] or ""
            consultation_type = appt["consultation_type"]
            zoom_link = None      # never put a Zoom link in messages/emails
            zoom_pass = None
            starts_at_str = appt["starts_at"]
            health_concern = appt["health_concern"] or ""

            try:
                dt_kolkata = datetime.fromisoformat(starts_at_str).astimezone(CLINIC_TIMEZONE)
            except Exception:
                dt_kolkata = datetime.now(CLINIC_TIMEZONE)

            formatted_date = dt_kolkata.strftime("%A, %d %B %Y")
            formatted_time = dt_kolkata.strftime("%I:%M %p")

            if action == "ACCEPT":
                c.execute("UPDATE appointment SET status = 'CONFIRMED' WHERE reference_code = ?", (ref,))
                conn.commit()
                conn.close()

                # Build patient WhatsApp confirmation
                patient_confirm_msg = build_patient_confirmed_whatsapp(
                    patient_name, patient_phone, formatted_date, formatted_time,
                    consultation_type, ref, zoom_link, zoom_pass
                )
                clean_patient_phone = "".join(filter(str.isdigit, patient_phone))
                if len(clean_patient_phone) == 10:
                    clean_patient_phone = "91" + clean_patient_phone
                patient_wa_url = f"https://wa.me/{clean_patient_phone}?text={urllib.parse.quote(patient_confirm_msg)}"

                # Send patient confirmation email
                if patient_email:
                    mode_text = "Video Call (Zoom)" if consultation_type == "VIDEO_CALL" else "Voice Call (Phone)"
                    confirm_html = f"""
                    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;border:2px solid #16a34a;border-radius:8px;padding:24px;background:#f0fdf4;">
                      <h2 style="color:#16a34a;">✅ Appointment CONFIRMED — Ayesha Ayurvedic Clinic</h2>
                      <p>Namaste <b>{_e(patient_name)}</b>,</p>
                      <p>Great news! Dr. Shaik Ayesha has <b>accepted your appointment request</b>.</p>
                      <table style="width:100%;border-collapse:collapse;margin:20px 0;background:#fff;border:1px solid #d1fae5;">
                        <tr><td style="padding:10px;color:#666;border-bottom:1px solid #eee;">Booking Ref:</td><td style="padding:10px;font-weight:bold;color:#16a34a;border-bottom:1px solid #eee;">{ref}</td></tr>
                        <tr><td style="padding:10px;color:#666;border-bottom:1px solid #eee;">Date:</td><td style="padding:10px;font-weight:bold;border-bottom:1px solid #eee;">{formatted_date}</td></tr>
                        <tr><td style="padding:10px;color:#666;border-bottom:1px solid #eee;">Time:</td><td style="padding:10px;font-weight:bold;border-bottom:1px solid #eee;">{formatted_time} IST (5:00 PM – 8:30 PM)</td></tr>
                        <tr><td style="padding:10px;color:#666;border-bottom:1px solid #eee;">Mode:</td><td style="padding:10px;font-weight:bold;border-bottom:1px solid #eee;">{mode_text}</td></tr>
                        {'<tr><td style="padding:10px;color:#666;">Zoom Link:</td><td style="padding:10px;">Will be sent to you on WhatsApp before your consultation.</td></tr>' if consultation_type == "VIDEO_CALL" else '<tr><td style="padding:10px;color:#666;">Action:</td><td style="padding:10px;">Doctor will call your phone directly.</td></tr>'}
                      </table>
                      <p>📞 Helpline: <b>+91 8465058469</b> | 📧 <b>ayeshashaik0211@gmail.com</b></p>
                    </div>
                    """
                    send_automated_email(patient_email, f"Appointment CONFIRMED [{ref}] — Ayesha Ayurvedic Clinic", confirm_html)

                # Send Telegram to patient if configured
                s2 = get_settings()
                patient_telegram_ids = s2.get("telegram_patient_chat_ids", "").strip()
                if patient_telegram_ids:
                    send_telegram_message(patient_telegram_ids, patient_confirm_msg)

                # Send Automated SMS to patient
                sms_confirm_msg = f"Ayesha Clinic: Your appointment is CONFIRMED for {formatted_date} at {formatted_time} IST. Ref: {ref}. Helpline: 8465058469"
                send_automated_sms(patient_phone, sms_confirm_msg)

                # Send confirmation email to DOCTOR confirming they accepted
                doc_confirm_note = f"""
                <h3>Appointment Accepted by Doctor</h3>
                <p>You have ACCEPTED the appointment for patient <b>{_e(patient_name)}</b> ({_e(patient_phone)}).</p>
                <p><b>Date:</b> {formatted_date} at {formatted_time} IST</p>
                <p><b>Mode:</b> {consultation_type} | <b>Ref:</b> {ref}</p>
                <p>The patient has been automatically notified via Email and SMS.</p>
                """
                send_automated_email("ayeshashaik0211@gmail.com", f"Confirmed: Appointment Accepted for {patient_name} [{ref}]", doc_confirm_note)

                # Telegram alert to doctor
                doc_telegram_id = s2.get("telegram_doctor_chat_id", "").strip()
                if doc_telegram_id:
                    send_telegram_message(doc_telegram_id, f"✅ You ACCEPTED appointment for *{patient_name}* on {formatted_date} ({formatted_time}). Ref: `{ref}`")

                # Optional CallMeBot WhatsApp to patient
                send_automated_callmebot_whatsapp(patient_phone, patient_confirm_msg)

                self._send_html_response(200, doctor_result_page(
                    True, ref, patient_name, patient_phone, formatted_date, consultation_type, patient_wa_url))

            else:  # DECLINE
                c.execute("UPDATE appointment SET status = 'DECLINED' WHERE reference_code = ?", (ref,))
                conn.commit()
                conn.close()

                # Build patient declined WhatsApp
                patient_decline_msg = build_patient_declined_whatsapp(patient_name, formatted_date, ref)
                clean_patient_phone = "".join(filter(str.isdigit, patient_phone))
                if len(clean_patient_phone) == 10:
                    clean_patient_phone = "91" + clean_patient_phone
                patient_wa_url = f"https://wa.me/{clean_patient_phone}?text={urllib.parse.quote(patient_decline_msg)}"

                # Send patient declined email
                if patient_email:
                    decline_html = f"""
                    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;border:2px solid #dc2626;border-radius:8px;padding:24px;background:#fef2f2;">
                      <h2 style="color:#dc2626;">❌ Appointment Request Declined</h2>
                      <p>Namaste <b>{_e(patient_name)}</b>,</p>
                      <p>We regret to inform you that Dr. Shaik Ayesha has <b>declined your appointment request</b> for {formatted_date} (Ref: {ref}).</p>
                      <p>Please try a different date or contact us directly:</p>
                      <p>📞 <b>+91 8465058469</b> | 📧 <b>ayeshashaik0211@gmail.com</b></p>
                      <p>💬 <a href="https://wa.me/918465058469">WhatsApp Us</a></p>
                    </div>
                    """
                    send_automated_email(patient_email, f"Appointment Request Declined [{ref}]", decline_html)

                # Send Automated SMS to patient
                sms_decline_msg = f"Ayesha Clinic: Your appointment request for {formatted_date} could not be confirmed. Call +91 8465058469 to reschedule. Ref: {ref}"
                send_automated_sms(patient_phone, sms_decline_msg)

                # Send notification email to DOCTOR confirming decline
                doc_decline_note = f"""
                <h3>Appointment Declined</h3>
                <p>You have DECLINED the appointment for patient <b>{_e(patient_name)}</b> ({_e(patient_phone)}) for {formatted_date}.</p>
                <p>The slot has been released back into availability. The patient has been informed.</p>
                """
                send_automated_email("ayeshashaik0211@gmail.com", f"Declined: Appointment {ref} for {patient_name}", doc_decline_note)

                # Telegram alert to doctor
                s3 = get_settings()
                doc_telegram_id = s3.get("telegram_doctor_chat_id", "").strip()
                if doc_telegram_id:
                    send_telegram_message(doc_telegram_id, f"❌ You DECLINED appointment for *{patient_name}* on {formatted_date}. Ref: `{ref}` (Slot released)")

                # Optional CallMeBot WhatsApp to patient
                send_automated_callmebot_whatsapp(patient_phone, patient_decline_msg)

                self._send_html_response(200, doctor_result_page(
                    False, ref, patient_name, patient_phone, formatted_date, consultation_type, patient_wa_url))
            return

        if path == "/status-watcher.js":
            data = WATCHER_JS.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # Serve static assets (only from frontend/dist - nothing else on this computer can ever be reached)
        base = os.path.realpath(STATIC_DIR)
        try:
            rel = urllib.parse.unquote(path).replace("\\", "/").lstrip("/")
            if "\x00" in rel:
                raise ValueError("bad path")
            cand = os.path.realpath(os.path.join(base, rel))
        except Exception:
            self.send_error(404)
            return
        inside = (cand == base) or cand.startswith(base + os.sep)
        hidden = any(part.startswith(".") for part in rel.split("/") if part)
        secret_ext = cand.lower().endswith((".db", ".sqlite", ".env", ".py", ".log", ".bak", ".sql", ".pem", ".key"))
        if path.startswith("/api/"):
            self.send_json(404, {"message": "Not found."})
            return
        if rel and (not inside or hidden or secret_ext):
            self.send_error(404)
            return
        if inside and os.path.isfile(cand):
            file_path = cand
        elif "." in os.path.basename(rel):          # a missing file such as /x.js or /y.png
            self.send_error(404)
            return
        else:                                        # a normal website page -> the React app
            file_path = os.path.join(base, "index.html")

        if os.path.isfile(file_path):
            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            if file_path.endswith((".js", ".mjs")): content_type = "application/javascript"
            elif file_path.endswith(".css"): content_type = "text/css"
            elif file_path.endswith(".svg"): content_type = "image/svg+xml"
            if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
                content_type += "; charset=utf-8"

            with open(file_path, "rb") as f:
                body_bytes = f.read()
            if os.path.basename(file_path) == "index.html":
                body_bytes = inject_into_index(body_bytes)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body_bytes)))
            if os.path.basename(file_path) == "index.html":
                self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body_bytes)
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if self._flood_blocked():
            self.send_json(429, {"message": "Too many requests. Please wait a minute."})
            return
        if not self._same_origin_ok():
            self.send_json(403, {"message": "Request blocked (wrong origin)."})
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self.send_json(400, {"message": "Bad request."})
            return
        if content_length < 0 or content_length > 1_000_000:
            self.send_json(413, {"message": "Request too large."})
            return
        try:
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            req = json.loads(body)
            if not isinstance(req, dict):
                raise ValueError("not an object")
        except Exception:
            self.send_json(400, {"message": "Invalid JSON payload."})
            return

        if path.startswith("/api/admin/") and path != "/api/admin/login" and not self._admin_ok():
            self.send_json(401, {"message": "Admin login required."})
            return

        if path == "/api/appointments":
            s = get_settings()
            if s.get("booking_enabled", "true") != "true":
                self.send_json(403, {"message": "Online booking is temporarily paused by the clinic."})
                return

            daily_lim = int(s.get("daily_limit", "3"))
            weekly_lim = int(s.get("weekly_limit", "6"))

            ip = self.client_ip()
            if not self._is_local():
                if rl_blocked("book", ip, 8, 3600):
                    self.send_json(429, {"message": "Too many booking requests from this device. Please try again later or call the clinic."})
                    return
                rl_note("book", ip)

            patient_name = clean_line(req.get("patientName", ""), 100)
            phone = clean_line(req.get("phone", ""), 25)
            email = clean_line(req.get("email", ""), 120)
            starts_at_str = clean_line(req.get("startsAt", ""), 40)
            consultation_type = clean_line(req.get("consultationType", "VOICE_CALL"), 20).upper()
            age = req.get("age")
            health_concern = clean_text(req.get("healthConcern", ""), 1000)
            try:
                age = int(age) if age not in (None, "") else None
                if age is not None and not (0 <= age <= 120):
                    age = None
            except (TypeError, ValueError):
                age = None

            if not patient_name or not phone or not starts_at_str:
                self.send_json(400, {"message": "Patient name, phone, and appointment date/time are required."})
                return
            if not (10 <= len("".join(ch for ch in phone if ch.isdigit())) <= 15) or not re.fullmatch(r"[0-9+()\- ]+", phone):
                self.send_json(400, {"message": "Please enter a valid mobile number."})
                return
            if email and not re.fullmatch(r"[^@\s<>\"']+@[^@\s<>\"']+\.[^@\s<>\"']+", email):
                self.send_json(400, {"message": "Please enter a valid email address or leave it empty."})
                return

            if consultation_type not in ["VOICE_CALL", "VIDEO_CALL"]:
                consultation_type = "VOICE_CALL"

            try:
                if "+" in starts_at_str:
                    dt = datetime.fromisoformat(starts_at_str)
                else:
                    dt = datetime.fromisoformat(starts_at_str).replace(tzinfo=CLINIC_TIMEZONE)
                dt_kolkata = dt.astimezone(CLINIC_TIMEZONE)
            except Exception:
                self.send_json(400, {"message": "Invalid appointment date/time."})
                return

            if dt_kolkata.date() < datetime.now(CLINIC_TIMEZONE).date():
                self.send_json(400, {"message": "Please choose a present or future date."})
                return

            appt_date = dt_kolkata.date()
            appt_time = dt_kolkata.time()

            # Rule 1: Wednesday (2) or Friday (4) only
            if appt_date.weekday() not in [2, 4]:
                self.send_json(400, {"message": "Online doctor consultations are available only on Wednesdays and Fridays."})
                return

            # Rule 2: 5:00 PM to 8:30 PM IST
            if appt_time < time(17, 0) or appt_time > time(20, 30):
                self.send_json(400, {"message": "Consultation time must be between 5:00 PM and 8:30 PM IST."})
                return

            appt_date_str = appt_date.isoformat()
            week_start = get_week_monday(appt_date)
            week_start_str = week_start.isoformat()

            conn = sqlite3.connect(DB_FILE, timeout=10.0)
            c = conn.cursor()
            try:
                c.execute("BEGIN IMMEDIATE")

                # 1. Weekly count check (< weekly_limit)
                c.execute("SELECT count(*) FROM appointment WHERE clinic_week_start = ? AND mode = 'ONLINE' AND status IN ('CONFIRMED','PENDING')", (week_start_str,))
                week_count = c.fetchone()[0]
                if week_count >= weekly_lim:
                    conn.rollback()
                    self.send_json(409, {"message": f"This clinic week has reached its maximum quota of {weekly_lim} online appointments. Please select an eligible date in a future week."})
                    return

                # 2. Daily count check (< daily_limit)
                c.execute("SELECT count(*) FROM appointment WHERE date(starts_at) = ? AND mode = 'ONLINE' AND status IN ('CONFIRMED','PENDING')", (appt_date_str,))
                day_count = c.fetchone()[0]
                if day_count >= daily_lim:
                    conn.rollback()
                    self.send_json(409, {"message": f"This day has reached its maximum capacity of {daily_lim} online appointments. Please choose another date."})
                    return

                now_iso = datetime.now(CLINIC_TIMEZONE).isoformat()
                c.execute("INSERT INTO patient (full_name, phone, email, age, health_concern, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                          (patient_name, phone, email if email else None, age, health_concern, now_iso))
                patient_id = c.lastrowid

                ref_code = generate_reference()
                zoom_link = None      # the doctor sends the Zoom link herself on WhatsApp - never auto-generated
                zoom_pass = None

                c.execute("""
                    INSERT INTO appointment (reference_code, patient_id, mode, consultation_type, status, starts_at, clinic_week_start, zoom_meeting_link, zoom_passcode, whatsapp_status, email_status, created_at)
                    VALUES (?, ?, 'ONLINE', ?, 'PENDING', ?, ?, ?, ?, 'PENDING', 'PENDING', ?)
                """, (ref_code, patient_id, consultation_type, dt_kolkata.isoformat(), week_start_str, zoom_link, zoom_pass, now_iso))

                conn.commit()
            except Exception as ex:
                conn.rollback()
                print(f"[BOOKING ERROR] {ex}")
                self.send_json(500, {"message": "Could not reserve this slot. Please try again or call the clinic."})
                return
            finally:
                conn.close()

            formatted_date = dt_kolkata.strftime("%A, %d %B %Y")
            formatted_time = dt_kolkata.strftime("%I:%M %p")

            # ── STEP 1: Build doctor's WhatsApp message with Accept/Decline links ──
            base_url = get_server_base_url()
            accept_url = decision_link(ref_code, "ACCEPT")
            decline_url = decision_link(ref_code, "DECLINE")
            doctor_msg = build_doctor_approval_whatsapp(
                patient_name, phone, formatted_date, formatted_time,
                consultation_type, ref_code, health_concern, zoom_link, zoom_pass
            )
            clean_doc_phone = "918465058469"
            doctor_msg_public = build_doctor_approval_whatsapp(
                patient_name, phone, formatted_date, formatted_time,
                consultation_type, ref_code, health_concern, zoom_link, zoom_pass, with_links=False
            )
            doctor_wa_url = f"https://wa.me/{clean_doc_phone}?text={urllib.parse.quote(doctor_msg_public)}"

            clean_patient_phone = "".join(filter(str.isdigit, phone))
            if len(clean_patient_phone) == 10:
                clean_patient_phone = "91" + clean_patient_phone

            # ── STEP 2: Send notification email to DOCTOR ──
            doc_email_body = f"""
            <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; border: 2px solid #143826; border-radius: 8px; padding: 24px; background: #fcfaf6;">
              <h2 style="color: #143826; margin-top: 0;">🔔 New Appointment Request — Ayesha Ayurvedic Clinic</h2>
              <p><b>Patient:</b> {_e(patient_name)} | <b>Phone:</b> {_e(phone)}</p>
              <p><b>Health Concern:</b> {_e(health_concern or 'Not specified')}</p>
              <p><b>Date:</b> {formatted_date} | <b>Time:</b> {formatted_time} IST</p>
              <p><b>Mode:</b> {consultation_type} | <b>Ref:</b> {ref_code}</p>
              {'<p><b>Video call:</b> after accepting, please send the Zoom link to the patient on WhatsApp.</p>' if consultation_type == "VIDEO_CALL" else ''}
              <div style="margin: 24px 0;">
                <a href="{accept_url}" style="background: #16a34a; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-right: 12px;">✅ ACCEPT APPOINTMENT</a>
                <a href="{decline_url}" style="background: #dc2626; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold;">❌ DECLINE APPOINTMENT</a>
              </div>
              <p style="font-size: 0.85rem; color: #666;">After you click Accept/Decline, a popup will help you send the reply to the patient on WhatsApp.</p>
            </div>
            """
            send_automated_email("ayeshashaik0211@gmail.com",
                                 f"New Appointment Request: {patient_name} [{ref_code}]",
                                 doc_email_body)

            # ── STEP 3: Also send telegram, SMS, CallMeBot to doctor if configured ──
            s = get_settings()
            doc_telegram_id = s.get("telegram_doctor_chat_id", "").strip()
            if doc_telegram_id:
                send_telegram_message(doc_telegram_id, doctor_msg, [[
                    {"text": "✅ Accept", "callback_data": f"acc:{ref_code}"},
                    {"text": "❌ Decline", "callback_data": f"dec:{ref_code}"}]])

            # Send SMS alert to Doctor
            doc_sms_alert = f"Ayesha Clinic Alert: New request from {patient_name} ({phone}) for {formatted_date}. Accept: {accept_url} Decline: {decline_url}"
            send_automated_sms("8465058469", doc_sms_alert)

            # Optional direct CallMeBot WhatsApp to doctor
            send_automated_callmebot_whatsapp("8465058469", doctor_msg)

            # Send pending acknowledgment email to PATIENT if email provided
            if email:
                patient_ack_html = f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #143826; border-radius: 8px; padding: 24px; background: #fcfaf6;">
                  <h2 style="color: #143826; margin-top: 0;">🌿 Ayesha Ayurvedic Clinic</h2>
                  <p>Namaste <b>{_e(patient_name)}</b>,</p>
                  <p>Your online consultation request has been <b>submitted successfully</b> to Dr. Shaik Ayesha.</p>
                  <div style="background: #fff; border: 1px solid #e4ddd3; border-radius: 6px; padding: 16px; margin: 16px 0;">
                    <p style="margin: 4px 0;"><b>Booking Ref:</b> {ref_code}</p>
                    <p style="margin: 4px 0;"><b>Date:</b> {formatted_date}</p>
                    <p style="margin: 4px 0;"><b>Requested Time:</b> {formatted_time} IST (5:00 PM – 8:30 PM)</p>
                    <p style="margin: 4px 0;"><b>Status:</b> <span style="color: #b45309; font-weight: bold;">PENDING DOCTOR APPROVAL</span></p>
                  </div>
                  <p>The doctor will review your request. You will receive an automated notification as soon as it is confirmed.</p>
                  <p>📞 Helpline: <b>+91 8465058469</b> | 📧 <b>ayeshashaik0211@gmail.com</b></p>
                </div>
                """
                send_automated_email(email, f"Appointment Request Received [{ref_code}] — Ayesha Ayurvedic Clinic", patient_ack_html)

            # Update DB notification status
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE appointment SET whatsapp_status = ?, email_status = ? WHERE reference_code = ?",
                      ("PENDING_DOCTOR", "DOCTOR_ALERTED", ref_code))
            conn.commit()
            conn.close()

            # ── STEP 4: Send pending confirmation to patient ──
            patient_pending_msg = (
                f"Your appointment request has been sent to Dr. Shaik Ayesha "
                f"(Ref: {ref_code}) for {formatted_date}. "
                f"You will receive a WhatsApp message once the doctor confirms."
            )

            self.send_json(201, {
                "reference": ref_code,
                "status": "PENDING",
                "mode": "ONLINE",
                "consultationType": consultation_type,
                "startsAt": dt_kolkata.isoformat(),
                "formattedDate": formatted_date,
                "formattedTime": formatted_time,
                "message": patient_pending_msg,
                "zoomMeetingLink": zoom_link,
                "zoomPasscode": zoom_pass,
                "patientPhone": phone,
                "patientEmail": email,
                "notification": {
                    "doctorWhatsAppUrl": doctor_wa_url,
                    "doctorAlerted": True,
                    "deliveryStatus": "DOCTOR_NOTIFIED_PENDING_APPROVAL"
                }
            })
            return

        elif path == "/api/appointments/cancel":
            ref = req.get("referenceCode", "").strip().upper()
            phone = req.get("phone", "").strip()
            if not ref or not phone:
                self.send_json(400, {"message": "Reference code and phone number are required to cancel."})
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
                SELECT a.id, p.phone FROM appointment a
                JOIN patient p ON a.patient_id = p.id
                WHERE a.reference_code = ?
            """, (ref,))
            row = c.fetchone()
            if not row or "".join(filter(str.isdigit, row[1]))[-10:] != "".join(filter(str.isdigit, phone))[-10:]:
                conn.close()
                self.send_json(404, {"message": "Appointment could not be found or verified."})
                return

            c.execute("UPDATE appointment SET status = 'CANCELLED' WHERE id = ?", (row[0],))
            conn.commit()
            conn.close()
            self.send_json(200, {"message": "Appointment has been cancelled successfully. Capacity has been released."})
            return

        elif path == "/api/admin/login":
            u = str(req.get("username", ""))
            p = str(req.get("password", ""))
            ip = self.client_ip()
            if rl_blocked("login_fail", ip, 5, 900):
                self.send_json(429, {"message": "Too many wrong attempts. Try again after 15 minutes."})
                return
            want_u, want_p, _ = admin_credentials()
            ok = hmac.compare_digest(u.encode(), want_u.encode()) and hmac.compare_digest(p.encode(), want_p.encode())
            if ok:
                token = secrets.token_urlsafe(32)
                ADMIN_SESSIONS[token] = _time.time() + ADMIN_SESSION_HOURS * 3600
                secure = "; Secure" if get_server_base_url().startswith("https://") else ""
                self.send_json(200, {
                    "token": token,
                    "role": "DOCTOR_ADMIN",
                    "physician": "Dr. Shaik Ayesha, B.A.M.S."
                }, [("Set-Cookie", f"aac_admin={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={ADMIN_SESSION_HOURS*3600}{secure}")])
            else:
                rl_note("login_fail", ip)
                _time.sleep(1.5)     # slows down password guessing
                self.send_json(401, {"message": "Invalid clinic credentials."})
            return

        elif path == "/api/admin/logout":
            for part in self.headers.get("Cookie", "").split(";"):
                k, _, v = part.strip().partition("=")
                if k == "aac_admin":
                    ADMIN_SESSIONS.pop(v, None)
            self.send_json(200, {"message": "Logged out."}, [("Set-Cookie", "aac_admin=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")])
            return

        elif path == "/api/admin/settings":
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for k, v in req.items():
                k = str(k)[:64]
                if k in HIDDEN_SETTINGS or not re.fullmatch(r"[A-Za-z0-9_]+", k):
                    continue
                v = str(v)[:5000]
                if v == SECRET_MASK:               # the panel sent the hidden placeholder back -> keep the real secret
                    continue
                c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?, ?)", (k, v))
            conn.commit()
            conn.close()
            self.send_json(200, {"message": "Settings updated successfully."})
            return

        elif path == "/api/admin/gallery":
            title = req.get("title", "").strip()
            img_url = req.get("image_url", "").strip()
            desc = req.get("description", "").strip()

            if not title or not img_url:
                self.send_json(400, {"message": "Title and image URL/path are required."})
                return

            now_str = datetime.now(CLINIC_TIMEZONE).isoformat()
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO gallery_item (title, image_url, description, created_at) VALUES (?, ?, ?, ?)",
                      (title, img_url, desc, now_str))
            conn.commit()
            new_id = c.lastrowid
            conn.close()
            self.send_json(201, {"id": new_id, "message": "Gallery item added successfully."})
            return

        elif path == "/api/admin/treatments":
            name_eng = req.get("name_english", "").strip()
            name_tel = req.get("name_telugu", "").strip()
            category = req.get("category", "General").strip()
            desc = req.get("description", "").strip()
            is_special = 1 if req.get("is_special_service") else 0

            if not name_eng or not name_tel:
                self.send_json(400, {"message": "English and Telugu names are required."})
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO treatment (name_english, name_telugu, category, description, is_special_service) VALUES (?, ?, ?, ?, ?)",
                          (name_eng, name_tel, category, desc, is_special))
                conn.commit()
                new_id = c.lastrowid
                self.send_json(201, {"id": new_id, "message": "Treatment created."})
            except Exception as e:
                print(f"[TREATMENT ERROR] {e}")
                self.send_json(400, {"message": "Could not create this treatment. Please check the details."})
            finally:
                conn.close()
            return

        elif path.startswith("/api/admin/appointments/") and path.endswith("/status"):
            appt_id = path.split("/")[4]
            new_status = req.get("status", "CONFIRMED").upper()
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE appointment SET status = ? WHERE id = ?", (new_status, appt_id))
            conn.commit()
            conn.close()
            self.send_json(200, {"message": f"Status updated to {new_status}"})
            return

        elif path.startswith("/api/admin/appointments/") and path.endswith("/zoom"):
            appt_id = path.split("/")[4]
            zoom_link = req.get("zoomLink", "")
            passcode = req.get("passcode", "")
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE appointment SET zoom_meeting_link = ?, zoom_passcode = ? WHERE id = ?", (zoom_link, passcode, appt_id))
            conn.commit()
            conn.close()
            self.send_json(200, {"message": "Zoom meeting link updated."})
            return

        self.send_json(404, {"message": "Not Found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if not self._same_origin_ok():
            self.send_json(403, {"message": "Request blocked (wrong origin)."})
            return
        if path.startswith("/api/admin/") and not self._admin_ok():
            self.send_json(401, {"message": "Admin login required."})
            return
        if path.startswith("/api/admin/gallery/"):
            g_id = path.split("/")[-1]
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM gallery_item WHERE id = ?", (g_id,))
            conn.commit()
            conn.close()
            self.send_json(200, {"message": "Gallery item deleted."})
            return
        elif path.startswith("/api/admin/treatments/"):
            t_id = path.split("/")[-1]
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM treatment WHERE id = ?", (t_id,))
            conn.commit()
            conn.close()
            self.send_json(200, {"message": "Treatment deleted."})
            return
        self.send_json(404, {"message": "Not Found"})

def run_server(port=8080):
    global SERVER_PORT
    SERVER_PORT = port
    init_db()
    threading.Thread(target=telegram_listener, daemon=True).start()
    _s = get_settings()
    print("[CONFIG] email password :", "SET" if _s.get("smtp_pass", "").strip() else "MISSING")
    print("[CONFIG] telegram token :", "SET" if _s.get("telegram_bot_token", "").strip() else "MISSING")
    print("[CONFIG] telegram chat  :", "SET" if _s.get("telegram_doctor_chat_id", "").strip() else "MISSING")
    print("[CONFIG] callmebot key  :", "SET" if _s.get("callmebot_apikey", "").strip() else "MISSING")
    print("[CONFIG] accept/decline links use:", get_server_base_url())
    if not admin_credentials()[2]:
        print("[SECURITY WARNING] ADMIN_USERNAME / ADMIN_PASSWORD are not set in .env -> the old default admin password is active. Set them before going online!")
    for _p in (DB_FILE, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
        try:
            if os.path.exists(_p):
                os.chmod(_p, 0o600)          # only the owner account can read the database and .env
        except Exception:
            pass
    server_address = (os.environ.get("BIND_HOST", ""), port)
    httpd = ThreadingHTTPServer(server_address, ClinicHandler)
    httpd.daemon_threads = True
    print(f"[AYESHA AYURVEDIC CLINIC] Server is running on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
