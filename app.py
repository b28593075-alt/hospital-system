"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🏥 نظام إدارة السجلات الطبية الإلكترونية                  ║
║   Hospital Electronic Medical Records System (HEMRS)          ║
║                                                               ║
║   Professional Version with Advanced Features                 ║
║   للاستخدام على مستوى المستشفيات الحديثة                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import bcrypt
from datetime import datetime
from functools import wraps
import os
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)
app.secret_key = "hospital_secure_key_2024_professional"

DATABASE = 'hospital.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
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
        director_name TEXT,
        address TEXT,
        website TEXT,
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
        national_id TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # جدول الأمراض المزمنة مع الدكتور المسؤول
    cursor.execute('''
    CREATE TABLE chronic_diseases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        disease TEXT NOT NULL,
        diagnosed DATE,
        doctor_name TEXT,
        notes TEXT,
        status TEXT DEFAULT 'active',
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
        severity TEXT DEFAULT 'medium',
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
        surgeon_name TEXT,
        anesthesia_type TEXT,
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
        chief_complaint TEXT,
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
        indication TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)
    )
    ''')
    
    # جدول التحاليل والأشعات
    cursor.execute('''
    CREATE TABLE medical_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        hospital_id TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        test_date DATE,
        doctor_name TEXT,
        diagnosis TEXT,
        description TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    hashed_password = bcrypt.hashpw(b'0987654321', bcrypt.gensalt()).decode()
    
    cursor.execute('''
    INSERT INTO hospitals (hospital_id, name, city, phone, email, password, director_name, address) VALUES
    (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('HSP001', 'مستشفى الرشيد التعليمي', 'بغداد', '07701234567', 'mnbvcxz', hashed_password, 'أ.د محمد علي', 'بغداد - الكرادة'))
    
    db.commit()
    db.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'hospital_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def log_action(action, patient_id=None, details=None):
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
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM patients")
    count = cursor.fetchone()['cnt']
    db.close()
    return f"PAT{str(count + 1).zfill(6)}"

# ══════════════════════════════════════════════════════════════
# المسارات (Routes)
# ══════════════════════════════════════════════════════════════

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
            session['director_name'] = hospital['director_name']
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
    
    cursor.execute("SELECT COUNT(*) as cnt FROM medical_files WHERE hospital_id = ?", (session['hospital_id'],))
    total_files = cursor.fetchone()['cnt']
    
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
        total_files=total_files,
        recent_visits=recent_visits
    )

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        cursor.execute("SELECT * FROM hospitals WHERE hospital_id = ?", (session['hospital_id'],))
        hospital = cursor.fetchone()
        
        if not bcrypt.checkpw(current_password.encode(), hospital['password'].encode()):
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
            db.close()
            return redirect(url_for('settings'))
        
        name = request.form.get('name')
        director_name = request.form.get('director_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        website = request.form.get('website')
        
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode() if new_password else hospital['password']
        
        cursor.execute('''
            UPDATE hospitals 
            SET name = ?, director_name = ?, phone = ?, address = ?, website = ?, password = ?
            WHERE hospital_id = ?
        ''', (name, director_name, phone, address, website, hashed_password, session['hospital_id']))
        
        db.commit()
        session['hospital_name'] = name
        session['director_name'] = director_name
        log_action("UPDATE_SETTINGS", details="تحديث بيانات المستشفى")
        flash('تم تحديث البيانات بنجاح', 'success')
        db.close()
        return redirect(url_for('settings'))
    
    cursor.execute("SELECT * FROM hospitals WHERE hospital_id = ?", (session['hospital_id'],))
    hospital = cursor.fetchone()
    db.close()
    
    return render_template('settings.html', hospital=hospital)

@app.route('/patients')
@login_required
def patients_list():
    search = request.args.get('search', '').strip()
    db = get_db()
    cursor = db.cursor()
    
    if search:
        cursor.execute('''
            SELECT * FROM patients
            WHERE full_name LIKE ? OR patient_id LIKE ? OR national_id LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{search}%', f'%{search}%', f'%{search}%'))
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
                (patient_id, full_name, birth_date, gender, blood_type, phone, address, emergency_contact, emergency_phone, national_id)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (
                patient_id,
                request.form['full_name'],
                request.form['birth_date'],
                request.form['gender'],
                request.form['blood_type'],
                request.form.get('phone', ''),
                request.form.get('address', ''),
                request.form.get('emergency_contact', ''),
                request.form.get('emergency_phone', ''),
                request.form.get('national_id', '')
            ))
            
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
    
    cursor.execute('''
        SELECT * FROM medical_files
        WHERE patient_id = ?
        ORDER BY uploaded_at DESC
    ''', (patient_id,))
    medical_files = cursor.fetchall()
    
    db.close()
    log_action("VIEW_PATIENT", patient_id=patient_id, details="عرض ملف المريض")
    
    return render_template('patient_profile.html',
        patient=patient, diseases=diseases, allergies=allergies,
        surgeries=surgeries, visits=visits, medications=medications,
        medical_files=medical_files
    )

@app.route('/patients/<patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        try:
            cursor.execute('''
                UPDATE patients
                SET full_name = ?, birth_date = ?, gender = ?, blood_type = ?, 
                    phone = ?, address = ?, emergency_contact = ?, emergency_phone = ?, national_id = ?
                WHERE patient_id = ?
            ''', (
                request.form['full_name'],
                request.form['birth_date'],
                request.form['gender'],
                request.form['blood_type'],
                request.form.get('phone', ''),
                request.form.get('address', ''),
                request.form.get('emergency_contact', ''),
                request.form.get('emergency_phone', ''),
                request.form.get('national_id', ''),
                patient_id
            ))
            db.commit()
            log_action("EDIT_PATIENT", patient_id=patient_id, details="تعديل بيانات المريض")
            flash('تم تحديث البيانات بنجاح', 'success')
            db.close()
            return redirect(url_for('patient_profile', patient_id=patient_id))
        except Exception as e:
            db.rollback()
            flash(f'خطأ: {str(e)}', 'danger')
    
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    patient = cursor.fetchone()
    db.close()
    
    if not patient:
        flash('المريض غير موجود', 'danger')
        return redirect(url_for('patients_list'))
    
    return render_template('edit_patient.html', patient=patient)

@app.route('/patients/<patient_id>/add_disease', methods=['POST'])
@login_required
def add_disease(patient_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO chronic_diseases (patient_id, disease, diagnosed, doctor_name, status)
            VALUES (?,?,?,?,?)
        ''', (
            patient_id,
            request.form['disease'],
            request.form.get('diagnosed') or None,
            request.form.get('doctor_name', ''),
            request.form.get('status', 'active')
        ))
        db.commit()
        log_action("ADD_DISEASE", patient_id=patient_id, details=f"إضافة مرض: {request.form['disease']}")
        flash('تم إضافة المرض بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/patients/<patient_id>/add_visit', methods=['POST'])
@login_required
def add_visit(patient_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO visits (patient_id, hospital_id, visit_date, reason, diagnosis, doctor_name, chief_complaint, prescription, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            patient_id,
            session['hospital_id'],
            request.form['visit_date'],
            request.form['reason'],
            request.form.get('diagnosis', ''),
            request.form.get('doctor_name', ''),
            request.form.get('chief_complaint', ''),
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
            INSERT INTO surgeries (patient_id, hospital_id, surgery_name, surgery_date, doctor_name, surgeon_name, anesthesia_type, result, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            patient_id,
            session['hospital_id'],
            request.form['surgery_name'],
            request.form['surgery_date'],
            request.form.get('doctor_name', ''),
            request.form.get('surgeon_name', ''),
            request.form.get('anesthesia_type', ''),
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
            INSERT INTO medications (patient_id, hospital_id, drug_name, dosage, frequency, start_date, end_date, prescribed_by, indication)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            patient_id,
            session['hospital_id'],
            request.form['drug_name'],
            request.form.get('dosage', ''),
            request.form.get('frequency', ''),
            request.form.get('start_date') or None,
            request.form.get('end_date') or None,
            request.form.get('prescribed_by', ''),
            request.form.get('indication', '')
        ))
        db.commit()
        log_action("ADD_MEDICATION", patient_id=patient_id, details=f"إضافة دواء: {request.form['drug_name']}")
        flash('تم إضافة الدواء بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/patients/<patient_id>/upload_file', methods=['POST'])
@login_required
def upload_file(patient_id):
    try:
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(url_for('patient_profile', patient_id=patient_id))
        
        file = request.files['file']
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(url_for('patient_profile', patient_id=patient_id))
        
        if not allowed_file(file.filename):
            flash('نوع الملف غير مدعوم', 'danger')
            return redirect(url_for('patient_profile', patient_id=patient_id))
        
        filename = secure_filename(f"{patient_id}_{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO medical_files (patient_id, hospital_id, file_type, file_name, file_path, test_date, doctor_name, diagnosis, description)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            patient_id,
            session['hospital_id'],
            request.form.get('file_type', 'document'),
            file.filename,
            filepath,
            request.form.get('test_date') or None,
            request.form.get('doctor_name', ''),
            request.form.get('diagnosis', ''),
            request.form.get('description', '')
        ))
        db.commit()
        db.close()
        
        log_action("UPLOAD_FILE", patient_id=patient_id, details=f"رفع ملف: {file.filename}")
        flash('تم رفع الملف بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ في الرفع: {str(e)}', 'danger')
    
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        if os.path.exists(filepath):
            return open(filepath, 'rb')
    except Exception as e:
        flash(f'خطأ في التحميل: {str(e)}', 'danger')
    
    return redirect(url_for('patients_list'))

@app.route('/audit')
@login_required
def audit_log():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT a.*, h.name as hospital_name FROM audit_log a
        LEFT JOIN hospitals h ON a.hospital_id = h.hospital_id
        WHERE a.hospital_id = ?
        ORDER BY a.timestamp DESC LIMIT 200
    ''', (session['hospital_id'],))
    logs = cursor.fetchall()
    db.close()
    return render_template('audit_log.html', logs=logs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
