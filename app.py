"""
╔══════════════════════════════════════════════════════╗
║   نظام إدارة السجلات الطبية الإلكترونية             ║
║   Hospital Electronic Medical Records System         ║
║   SQLite Version - للإنترنت                         ║
╚══════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import bcrypt
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = "hospital_secret_key_2024_secure"

# مسار قاعدة البيانات
DATABASE = 'hospital.db'

def get_db():
    """الاتصال بـ SQLite"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """إنشاء قاعدة البيانات وجداولها"""
    if os.path.exists(DATABASE):
        return
    
    db = get_db()
    cursor = db.cursor()
    
    # جدول المستشفيات
    cursor.execute('''
    CREATE TABLE hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        phone TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # جدول المرضى
    cursor.execute('''
    CREATE TABLE patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        birth_date DATE NOT NULL,
        gender TEXT NOT NULL,
        blood_type TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        emergency_contact TEXT,
        emergency_phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # جدول الأمراض المزمنة
    cursor.execute('''
    CREATE TABLE chronic_diseases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        disease TEXT NOT NULL,
        diagnosed DATE,
        notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    )
    ''')
    
    # جدول الحساسية
    cursor.execute('''
    CREATE TABLE allergies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        allergen TEXT NOT NULL,
        reaction TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    )
    ''')
    
    # جدول العمليات الجراحية
    cursor.execute('''
    CREATE TABLE surgeries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        hospital_id TEXT NOT NULL,
        surgery_name TEXT NOT NULL,
        surgery_date DATE NOT NULL,
        doctor_name TEXT,
        result TEXT DEFAULT 'successful',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)
    )
    ''')
    
    # جدول الزيارات الطبية
    cursor.execute('''
    CREATE TABLE visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        hospital_id TEXT NOT NULL,
        visit_date DATETIME NOT NULL,
        reason TEXT NOT NULL,
        diagnosis TEXT,
        doctor_name TEXT,
        prescription TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)
    )
    ''')
    
    # جدول الأدوية
    cursor.execute('''
    CREATE TABLE medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        hospital_id TEXT NOT NULL,
        drug_name TEXT NOT NULL,
        dosage TEXT,
        frequency TEXT,
        start_date DATE,
        end_date DATE,
        prescribed_by TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)
    )
    ''')
    
    # جدول سجل العمليات
    cursor.execute('''
    CREATE TABLE audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id TEXT,
        action TEXT NOT NULL,
        patient_id TEXT,
        details TEXT,
        ip_address TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # إضافة بيانات تجريبية
    hashed_password = bcrypt.hashpw(b'Hospital@123', bcrypt.gensalt()).decode()
    
    cursor.execute('''
    INSERT INTO hospitals (hospital_id, name, city, phone, email, password) VALUES
    (?, ?, ?, ?, ?, ?)
    ''', ('HSP001', 'مستشفى الرشيد التعليمي', 'بغداد', '07701234567', 'rasheed@hospital.iq', hashed_password))
    
    cursor.execute('''
    INSERT INTO hospitals (hospital_id, name, city, phone, email, password) VALUES
    (?, ?, ?, ?, ?, ?)
    ''', ('HSP002', 'مستشفى ابن سينا', 'البصرة', '07709876543', 'ibnsina@hospital.iq', hashed_password))
    
    cursor.execute('''
    INSERT INTO patients (patient_id, full_name, birth_date, gender, blood_type, phone, address, emergency_contact, emergency_phone) VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('PAT00001', 'أحمد محمد علي', '1985-03-15', 'male', 'A+', '07751234567', 'بغداد - الكرادة', 'محمد علي', '07751234568'))
    
    db.commit()
    db.close()

def login_required(f):
    """التحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'hospital_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def log_action(action, patient_id=None, details=None):
    """تسجيل العمليات"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO audit_log (hospital_id, action, patient_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (session.get('hospital_id', 'SYSTEM'), action, patient_id, details, request.remote_addr))
        db.commit()
        db.close()
    except Exception as e:
        print(f"Log error: {e}")

def generate_patient_id():
    """توليد ID للمريض"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM patients")
    count = cursor.fetchone()['cnt']
    db.close()
    return f"PAT{str(count + 1).zfill(5)}"

# ══════════════════════════════════════════════════════
# المسارات (Routes)
# ══════════════════════════════════════════════════════

@app.route('/')
def index():
    if 'hospital_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM hospitals WHERE email = ? AND is_active = 1", (email,))
        hospital = cursor.fetchone()
        db.close()
        
        if hospital and bcrypt.checkpw(password.encode(), hospital['password'].encode()):
            session['hospital_id'] = hospital['hospital_id']
            session['hospital_name'] = hospital['name']
            session['hospital_city'] = hospital['city']
            log_action("LOGIN", details="تسجيل دخول ناجح")
            flash(f"مرحباً بك، {hospital['name']} 👋", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_action("LOGOUT", details="تسجيل خروج")
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) as cnt FROM patients")
    total_patients = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM visits WHERE hospital_id = ?", (session['hospital_id'],))
    my_visits = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM surgeries WHERE hospital_id = ?", (session['hospital_id'],))
    my_surgeries = cursor.fetchone()['cnt']
    
    cursor.execute('''
        SELECT v.*, p.full_name FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE v.hospital_id = ?
        ORDER BY v.visit_date DESC LIMIT 5
    ''', (session['hospital_id'],))
    recent_visits = cursor.fetchall()
    db.close()
    
    return render_template('dashboard.html',
        total_patients=total_patients,
        my_visits=my_visits,
        my_surgeries=my_surgeries,
        recent_visits=recent_visits
    )

@app.route('/patients')
@login_required
def patients_list():
    search = request.args.get('search', '').strip()
    db = get_db()
    cursor = db.cursor()
    
    if search:
        cursor.execute('''
            SELECT * FROM patients
            WHERE full_name LIKE ? OR patient_id LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{search}%', f'%{search}%'))
        log_action("SEARCH_PATIENT", details=f"بحث عن: {search}")
    else:
        cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
    
    patients = cursor.fetchall()
    db.close()
    return render_template('patients_list.html', patients=patients, search=search)

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        patient_id = generate_patient_id()
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('''
                INSERT INTO patients
                (patient_id, full_name, birth_date, gender, blood_type, phone, address, emergency_contact, emergency_phone)
                VALUES (?,?,?,?,?,?,?,?,?)
            ''', (
                patient_id,
                request.form['full_name'],
                request.form['birth_date'],
                request.form['gender'],
                request.form['blood_type'],
                request.form.get('phone', ''),
                request.form.get('address', ''),
                request.form.get('emergency_contact', ''),
                request.form.get('emergency_phone', '')
            ))
            
            diseases = request.form.getlist('disease[]')
            disease_dates = request.form.getlist('disease_date[]')
            for d, dd in zip(diseases, disease_dates):
                if d.strip():
                    cursor.execute('''
                        INSERT INTO chronic_diseases (patient_id, disease, diagnosed)
                        VALUES (?, ?, ?)
                    ''', (patient_id, d, dd or None))
            
            allergens = request.form.getlist('allergen[]')
            reactions = request.form.getlist('reaction[]')
            for a, r in zip(allergens, reactions):
                if a.strip():
                    cursor.execute('''
                        INSERT INTO allergies (patient_id, allergen, reaction)
                        VALUES (?, ?, ?)
                    ''', (patient_id, a, r))
            
            db.commit()
            log_action("ADD_PATIENT", patient_id=patient_id, details=f"إضافة مريض: {request.form['full_name']}")
            flash(f'تم إضافة المريض بنجاح! رقمه: {patient_id}', 'success')
            db.close()
            return redirect(url_for('patient_profile', patient_id=patient_id))
        
        except Exception as e:
            db.rollback()
            flash(f'خطأ في الحفظ: {str(e)}', 'danger')
            db.close()
    
    return render_template('add_patient.html')

@app.route('/patients/<patient_id>')
@login_required
def patient_profile(patient_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        flash('المريض غير موجود', 'danger')
        db.close()
        return redirect(url_for('patients_list'))
    
    cursor.execute("SELECT * FROM chronic_diseases WHERE patient_id = ?", (patient_id,))
    diseases = cursor.fetchall()
    
    cursor.execute("SELECT * FROM allergies WHERE patient_id = ?", (patient_id,))
    allergies = cursor.fetchall()
    
    cursor.execute('''
        SELECT s.*, h.name as hospital_name FROM surgeries s
        JOIN hospitals h ON s.hospital_id = h.hospital_id
        WHERE s.patient_id = ? ORDER BY s.surgery_date DESC
    ''', (patient_id,))
    surgeries = cursor.fetchall()
    
    cursor.execute('''
        SELECT v.*, h.name as hospital_name FROM visits v
        JOIN hospitals h ON v.hospital_id = h.hospital_id
        WHERE v.patient_id = ? ORDER BY v.visit_date DESC
    ''', (patient_id,))
    visits = cursor.fetchall()
    
    cursor.execute('''
        SELECT m.*, h.name as hospital_name FROM medications m
        JOIN hospitals h ON m.hospital_id = h.hospital_id
        WHERE m.patient_id = ? ORDER BY m.start_date DESC
    ''', (patient_id,))
    medications = cursor.fetchall()
    
    db.close()
    log_action("VIEW_PATIENT", patient_id=patient_id, details="عرض ملف المريض")
    
    return render_template('patient_profile.html',
        patient=patient, diseases=diseases, allergies=allergies,
        surgeries=surgeries, visits=visits, medications=medications
    )

@app.route('/patients/<patient_id>/add_visit', methods=['POST'])
@login_required
def add_visit(patient_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO visits (patient_id, hospital_id, visit_date, reason, diagnosis, doctor_name, prescription, notes)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (
            patient_id,
            session['hospital_id'],
            request.form['visit_date'],
            request.form['reason'],
            request.form.get('diagnosis', ''),
            request.form.get('doctor_name', ''),
            request.form.get('prescription', ''),
            request.form.get('notes', '')
        ))
        db.commit()
        log_action("ADD_VISIT", patient_id=patient_id, details=f"إضافة زيارة: {request.form['reason']}")
        flash('تم إضافة الزيارة بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/patients/<patient_id>/add_surgery', methods=['POST'])
@login_required
def add_surgery(patient_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO surgeries (patient_id, hospital_id, surgery_name, surgery_date, doctor_name, result, notes)
            VALUES (?,?,?,?,?,?,?)
        ''', (
            patient_id,
            session['hospital_id'],
            request.form['surgery_name'],
            request.form['surgery_date'],
            request.form.get('doctor_name', ''),
            request.form.get('result', 'successful'),
            request.form.get('notes', '')
        ))
        db.commit()
        log_action("ADD_SURGERY", patient_id=patient_id, details=f"إضافة عملية: {request.form['surgery_name']}")
        flash('تم إضافة العملية بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/patients/<patient_id>/add_medication', methods=['POST'])
@login_required
def add_medication(patient_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO medications (patient_id, hospital_id, drug_name, dosage, frequency, start_date, end_date, prescribed_by)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (
            patient_id,
            session['hospital_id'],
            request.form['drug_name'],
            request.form.get('dosage', ''),
            request.form.get('frequency', ''),
            request.form.get('start_date') or None,
            request.form.get('end_date') or None,
            request.form.get('prescribed_by', '')
        ))
        db.commit()
        log_action("ADD_MEDICATION", patient_id=patient_id, details=f"إضافة دواء: {request.form['drug_name']}")
        flash('تم إضافة الدواء بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/audit')
@login_required
def audit_log():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT a.*, h.name as hospital_name FROM audit_log a
        LEFT JOIN hospitals h ON a.hospital_id = h.hospital_id
        WHERE a.hospital_id = ?
        ORDER BY a.timestamp DESC LIMIT 100
    ''', (session['hospital_id'],))
    logs = cursor.fetchall()
    db.close()
    return render_template('audit_log.html', logs=logs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
