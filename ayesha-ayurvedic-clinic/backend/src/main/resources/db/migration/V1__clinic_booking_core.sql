-- V1: Core Clinic Database Schema for Ayesha Ayurvedic Clinic
-- PostgreSQL 16 compatible schema

CREATE TABLE IF NOT EXISTS patient (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    age INTEGER,
    health_concern TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doctor (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    qualification VARCHAR(120) NOT NULL,
    registration_number VARCHAR(60) NOT NULL,
    state_board VARCHAR(120) NOT NULL,
    phone_primary VARCHAR(20) NOT NULL,
    phone_secondary VARCHAR(20),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS treatment (
    id BIGSERIAL PRIMARY KEY,
    name_english VARCHAR(160) NOT NULL UNIQUE,
    name_telugu VARCHAR(160) NOT NULL,
    category VARCHAR(80) NOT NULL,
    description TEXT,
    is_special_service BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS medicine (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    category VARCHAR(80),
    indications TEXT
);

CREATE TABLE IF NOT EXISTS booking_week_lock (
    week_start DATE PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS appointment (
    id BIGSERIAL PRIMARY KEY,
    reference_code VARCHAR(32) NOT NULL UNIQUE,
    patient_id BIGINT NOT NULL REFERENCES patient(id),
    doctor_id BIGINT NOT NULL REFERENCES doctor(id),
    mode VARCHAR(16) NOT NULL CHECK (mode IN ('ONLINE', 'OFFLINE')),
    consultation_type VARCHAR(20) NOT NULL DEFAULT 'VOICE_CALL' CHECK (consultation_type IN ('VOICE_CALL', 'VIDEO_CALL')),
    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED' CHECK (status IN ('CONFIRMED', 'CANCELLED', 'COMPLETED', 'RESCHEDULED')),
    starts_at TIMESTAMPTZ NOT NULL,
    clinic_week_start DATE NOT NULL,
    zoom_meeting_link TEXT,
    zoom_passcode VARCHAR(40),
    whatsapp_status VARCHAR(40) DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Partial index to prevent simultaneous double booking of the exact same slot time when confirmed
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_exact_slot ON appointment(starts_at, mode) WHERE status = 'CONFIRMED';

-- High-performance query index for capacity checking by week, mode, and status
CREATE INDEX IF NOT EXISTS idx_appointment_week_mode_status ON appointment(clinic_week_start, mode, status);
CREATE INDEX IF NOT EXISTS idx_appointment_starts_at ON appointment(starts_at);
CREATE INDEX IF NOT EXISTS idx_patient_phone ON patient(phone);

CREATE TABLE IF NOT EXISTS prescription (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patient(id),
    doctor_id BIGINT NOT NULL REFERENCES doctor(id),
    appointment_id BIGINT REFERENCES appointment(id),
    clinical_notes TEXT,
    dietary_advice TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prescription_medicine (
    prescription_id BIGINT NOT NULL REFERENCES prescription(id) ON DELETE CASCADE,
    medicine_id BIGINT NOT NULL REFERENCES medicine(id),
    dosage_instructions VARCHAR(240),
    duration_days INTEGER,
    PRIMARY KEY (prescription_id, medicine_id)
);

-- Seed authoritative physician record
INSERT INTO doctor (full_name, qualification, registration_number, state_board, phone_primary, phone_secondary, active)
VALUES (
    'Dr. Shaik Ayesha',
    'B.A.M.S., Ayurvedic Physician (Dr. N.T.R.U.H.S.)',
    '2545/A/2025',
    'Andhra Board for Ayurveda',
    '+918465058469',
    '+919848339262',
    TRUE
)
ON CONFLICT DO NOTHING;

-- Seed verified clinic treatments (Extracted from official poster)
INSERT INTO treatment (name_english, name_telugu, category, description, is_special_service, active) VALUES
('Panchakarma Detox Therapy', 'పంచకర్మ', 'Specialized Therapy', 'Classical five-fold detoxification and bio-cleansing therapy for chronic systemic disorders.', TRUE, TRUE),
('Suvarnaprashana Immunization', 'సువర్ణప్రాశన', 'Specialized Therapy', 'Ancient Ayurvedic formulation administered to children to enhance immunity, intelligence, and vitality.', TRUE, TRUE),
('Root-Cause Diagnosis & Guidance', 'వ్యాధుల కారణాలపై ప్రత్యేక మార్గదర్శకత్వం', 'Specialized Therapy', 'Individualized Prakriti analysis and holistic dietary/lifestyle counseling.', TRUE, TRUE),
('Skin Diseases & Allergies', 'చర్మ వ్యాధులు', 'Dermatology', 'Therapies for Eczema, Psoriasis, allergic dermatitis, and chronic rashes.', FALSE, TRUE),
('Hair Loss & Scalp Problems', 'జుట్టు సమస్యలు', 'Trichology', 'Treatment for premature hair fall, dandruff, and scalp nourishment.', FALSE, TRUE),
('Acidity & Acid Reflux', 'ఆమ్లత్వం', 'Gastroenterology', 'Herbal treatments to balance Pitta dosha, relieve hyperacidity and heartburn.', FALSE, TRUE),
('Digestive Disorders & IBS', 'జీర్ణ సమస్యలు', 'Gastroenterology', 'Deepana-Pachana treatments for chronic indigestion, bloating, and constipation.', FALSE, TRUE),
('Women Health & Wellness', 'మహిళల వ్యాధులు', 'Gynecology', 'Holistic care for menstrual irregularity, uterine health, and postnatal wellbeing.', FALSE, TRUE),
('PCOD & PCOS Management', 'పి.సి.ఓ.డి', 'Gynecology', 'Hormonal balancing, metabolic correction, and ovarian health restoration.', FALSE, TRUE),
('Mental Stress & Sleep Disorders', 'మానసిక సమస్యలు', 'Psychiatry & Wellness', 'Medhya Rasayanas and therapies for anxiety, stress relief, and restorative sleep.', FALSE, TRUE),
('Obesity & Metabolic Correction', 'ఊబకాయం', 'Metabolic Health', 'Weight reduction through Agni regulation and natural lipid-balancing formulations.', FALSE, TRUE),
('Asthma & Respiratory Illness', 'ఉబ్బసం', 'Pulmonology', 'Bronchial relief, Kapha clearing, and immune strengthening for asthma and wheezing.', FALSE, TRUE),
('Liver Diseases & Fatty Liver', 'కాలేయ వ్యాధులు', 'Hepatology', 'Hepato-protective Ayurvedic herbs to cleanse and rejuvenate liver function.', FALSE, TRUE),
('Arthritis & Joint Pains', 'ఆర్థరైటిస్', 'Rheumatology', 'Vata-pacifying therapies for joint inflammation, sciatica, and cervical spondylitis.', FALSE, TRUE),
('Pediatric Care', 'పిల్లల వ్యాధులు', 'Pediatrics', 'Gentle, safe Ayurvedic care for recurrent colds, digestion, and child growth.', FALSE, TRUE),
('Allergic Cold & Cough', 'అలర్జీ జలుబు, దగ్గు', 'Respiratory Care', 'Natural remedies for seasonal allergies, chronic rhinitis, and dry/wet cough.', FALSE, TRUE),
('Headache & Migraine', 'తలనొప్పి / మైగ్రేన్', 'Neurology', 'Therapies targeting vascular tension and Shiroroga alleviation.', FALSE, TRUE),
('Kidney Stones & Renal Health', 'కిడ్నీ స్టోన్', 'Nephrology', 'Diuretic and lithotriptic herbs to safely dissolve and expel renal calculi.', FALSE, TRUE),
('Thyroid Disorders', 'థైరాయిడ్ డిజార్డర్', 'Endocrinology', 'Glandular balance and metabolic correction for hypo- and hyper-thyroidism.', FALSE, TRUE),
('Piles & Fissure Care', 'పైల్స్, ఫిషర్', 'Anorectal Care', 'Non-surgical dietary and herbal healing for hemorrhoids and anal fissures.', FALSE, TRUE),
('Diabetes Management', 'మధుమేహం', 'Metabolic Health', 'Madhumeha management through glucose regulation, dietetics, and Rasayana support.', FALSE, TRUE),
('Weight & Height Management', 'బరువు & ఎత్తు నిర్వహణ', 'Development & Nutrition', 'Nutritional balance for developmental growth in youth and balanced BMI.', FALSE, TRUE)
ON CONFLICT (name_english) DO NOTHING;
