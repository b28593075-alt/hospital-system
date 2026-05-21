-- ================================================
--   نظام إدارة السجلات الطبية الإلكترونية
--   Hospital Management System - Database Schema
-- ================================================

CREATE DATABASE IF NOT EXISTS hospital_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hospital_db;

-- ── جدول المستشفيات ──────────────────────────────
CREATE TABLE hospitals (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id VARCHAR(10)  UNIQUE NOT NULL,   -- مثال: HSP001
    name        VARCHAR(100) NOT NULL,
    city        VARCHAR(50)  NOT NULL,
    phone       VARCHAR(20),
    email       VARCHAR(100) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,           -- bcrypt
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── جدول المرضى ──────────────────────────────────
CREATE TABLE patients (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      VARCHAR(10) UNIQUE NOT NULL,  -- مثال: PAT00001
    full_name       VARCHAR(100) NOT NULL,
    birth_date      DATE NOT NULL,
    gender          ENUM('male','female') NOT NULL,
    blood_type      ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    phone           VARCHAR(20),
    address         TEXT,
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(20),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── جدول الأمراض المزمنة ─────────────────────────
CREATE TABLE chronic_diseases (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    patient_id  VARCHAR(10) NOT NULL,
    disease     VARCHAR(100) NOT NULL,
    diagnosed   DATE,
    notes       TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

-- ── جدول الحساسية ────────────────────────────────
CREATE TABLE allergies (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    patient_id  VARCHAR(10) NOT NULL,
    allergen    VARCHAR(100) NOT NULL,
    reaction    VARCHAR(200),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

-- ── جدول العمليات الجراحية ───────────────────────
CREATE TABLE surgeries (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    patient_id    VARCHAR(10) NOT NULL,
    hospital_id   VARCHAR(10) NOT NULL,
    surgery_name  VARCHAR(200) NOT NULL,
    surgery_date  DATE NOT NULL,
    doctor_name   VARCHAR(100),
    result        ENUM('successful','complications','failed') DEFAULT 'successful',
    notes         TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)  REFERENCES patients(patient_id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
);

-- ── جدول الزيارات الطبية ─────────────────────────
CREATE TABLE visits (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    patient_id   VARCHAR(10) NOT NULL,
    hospital_id  VARCHAR(10) NOT NULL,
    visit_date   DATETIME NOT NULL,
    reason       VARCHAR(200) NOT NULL,
    diagnosis    TEXT,
    doctor_name  VARCHAR(100),
    prescription TEXT,
    notes        TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id)  REFERENCES patients(patient_id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
);

-- ── جدول الأدوية الحالية ─────────────────────────
CREATE TABLE medications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    patient_id  VARCHAR(10) NOT NULL,
    hospital_id VARCHAR(10) NOT NULL,
    drug_name   VARCHAR(100) NOT NULL,
    dosage      VARCHAR(50),
    frequency   VARCHAR(50),
    start_date  DATE,
    end_date    DATE,
    prescribed_by VARCHAR(100),
    FOREIGN KEY (patient_id)  REFERENCES patients(patient_id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
);

-- ── جدول سجل الدخول (Audit Log) ──────────────────
CREATE TABLE audit_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id VARCHAR(10) NOT NULL,
    action      VARCHAR(100) NOT NULL,
    patient_id  VARCHAR(10),
    details     TEXT,
    ip_address  VARCHAR(50),
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── بيانات تجريبية - مستشفيات ────────────────────
-- كلمة المرور: Hospital@123 (مشفرة bcrypt)
INSERT INTO hospitals (hospital_id, name, city, phone, email, password) VALUES
('HSP001', 'مستشفى الرشيد التعليمي',   'بغداد',  '07701234567', 'rasheed@hospital.iq',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiBtNXS5L3JJe6kLkHJcH.7gxFG6'),
('HSP002', 'مستشفى ابن سينا',           'البصرة', '07709876543', 'ibnsina@hospital.iq',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiBtNXS5L3JJe6kLkHJcH.7gxFG6'),
('HSP003', 'مستشفى الكندي التخصصي',    'الموصل', '07701112233', 'alkindi@hospital.iq',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiBtNXS5L3JJe6kLkHJcH.7gxFG6');

-- ── بيانات تجريبية - مرضى ────────────────────────
INSERT INTO patients (patient_id, full_name, birth_date, gender, blood_type, phone, address, emergency_contact, emergency_phone) VALUES
('PAT00001', 'أحمد محمد علي',    '1985-03-15', 'male',   'A+', '07751234567', 'بغداد - الكرادة',    'محمد علي',   '07751234568'),
('PAT00002', 'فاطمة حسين كاظم', '1990-07-22', 'female', 'O+', '07759876543', 'البصرة - العشار',   'حسين كاظم',  '07759876544'),
('PAT00003', 'عمر خالد إبراهيم', '1978-11-30', 'male',   'B-', '07701112233', 'الموصل - الدواسة', 'خالد إبراهيم','07701112234');

-- ── بيانات تجريبية - أمراض مزمنة ────────────────
INSERT INTO chronic_diseases (patient_id, disease, diagnosed, notes) VALUES
('PAT00001', 'السكري النوع الثاني', '2015-06-10', 'يحتاج متابعة شهرية'),
('PAT00001', 'ضغط الدم المرتفع',   '2018-02-20', 'تحت السيطرة بالدواء'),
('PAT00002', 'الربو',               '2005-09-14', 'حالة معتدلة');

-- ── بيانات تجريبية - حساسية ──────────────────────
INSERT INTO allergies (patient_id, allergen, reaction) VALUES
('PAT00001', 'البنسلين',   'طفح جلدي وصعوبة تنفس'),
('PAT00002', 'الأسبرين',   'التهاب معدة'),
('PAT00003', 'الغلوتين',   'اضطرابات هضمية');

-- ── بيانات تجريبية - عمليات ──────────────────────
INSERT INTO surgeries (patient_id, hospital_id, surgery_name, surgery_date, doctor_name, result, notes) VALUES
('PAT00001', 'HSP001', 'استئصال الزائدة الدودية', '2020-04-10', 'د. سامي العبيدي',  'successful', 'تعافى بشكل كامل'),
('PAT00002', 'HSP002', 'عملية قيصرية',            '2022-08-15', 'د. نوال الموسوي',  'successful', 'ولادة طبيعية سليمة'),
('PAT00003', 'HSP003', 'تثبيت كسر الساق',         '2019-12-01', 'د. حيدر الجبوري', 'successful', 'شفاء تام بعد 3 أشهر');
