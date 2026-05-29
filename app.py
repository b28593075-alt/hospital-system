from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import bcrypt
from datetime import datetime
from functools import wraps
import os
import io
import mimetypes
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "hospital_secure_key_2024"

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

DATABASE = 'hospital.db'
UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    c = db.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS hospitals(
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
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS patients(
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
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS chronic_diseases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        disease TEXT NOT NULL,
        diagnosed DATE,
        doctor_name TEXT,
        notes TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS allergies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        allergen TEXT NOT NULL,
        reaction TEXT,
        severity TEXT DEFAULT 'medium',
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS surgeries(
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
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS visits(
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
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS medications(
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
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS medical_files(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        hospital_id TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_data BLOB,
        test_date DATE,
        doctor_name TEXT,
        diagnosis TEXT,
        description TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id TEXT,
        action TEXT NOT NULL,
        patient_id TEXT,
        details TEXT,
        ip_address TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    pwd = bcrypt.hashpw(b'0987654321', bcrypt.gensalt()).decode()
    c.execute('INSERT INTO hospitals(hospital_id,name,city,phone,email,password,director_name,address) VALUES(?,?,?,?,?,?,?,?)',
        ('HSP001','مستشفى الرشيد التعليمي','بغداد','07701234567','admin@hospital.iq',pwd,'أ.د محمد علي','بغداد - الكرادة'))
    
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
        c = db.cursor()
        c.execute('INSERT INTO audit_log(hospital_id,action,patient_id,details,ip_address) VALUES(?,?,?,?,?)',
            (session.get('hospital_id','SYSTEM'),action,patient_id,details,request.remote_addr))
        db.commit()
        c.close()
        db.close()
    except:pass

def gen_patient_id():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM patients")
    cnt = c.fetchone()['cnt']
    db.close()
    return f"PAT{str(cnt + 1).zfill(6)}"

@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'hospital_id' in session else redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM hospitals WHERE email = ? AND is_active = 1", (email,))
        h = c.fetchone()
        db.close()
        
        if h and bcrypt.checkpw(password.encode(), h['password'].encode()):
            session['hospital_id'] = h['hospital_id']
            session['hospital_name'] = h['name']
            session['hospital_city'] = h['city']
            session['director_name'] = h['director_name']
            log_action("LOGIN")
            flash(f"مرحباً {h['name']}", 'success')
            return redirect(url_for('dashboard'))
        flash('بيانات غير صحيحة', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_action("LOGOUT")
    session.clear()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM patients")
    p_cnt = c.fetchone()['cnt']
    c.execute("SELECT COUNT(*) as cnt FROM visits WHERE hospital_id = ?", (session['hospital_id'],))
    v_cnt = c.fetchone()['cnt']
    c.execute("SELECT COUNT(*) as cnt FROM surgeries WHERE hospital_id = ?", (session['hospital_id'],))
    s_cnt = c.fetchone()['cnt']
    c.execute("SELECT COUNT(*) as cnt FROM medical_files WHERE hospital_id = ?", (session['hospital_id'],))
    f_cnt = c.fetchone()['cnt']
    c.execute('SELECT v.*,p.full_name FROM visits v JOIN patients p ON v.patient_id = p.patient_id WHERE v.hospital_id = ? ORDER BY v.visit_date DESC LIMIT 5', (session['hospital_id'],))
    recent = c.fetchall()
    db.close()
    return render_template('dashboard.html', total_patients=p_cnt, my_visits=v_cnt, my_surgeries=s_cnt, total_files=f_cnt, recent_visits=recent)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    db = get_db()
    c = db.cursor()
    if request.method == 'POST':
        c.execute("SELECT * FROM hospitals WHERE hospital_id = ?", (session['hospital_id'],))
        h = c.fetchone()
        if not bcrypt.checkpw(request.form.get('current_password').encode(), h['password'].encode()):
            flash('كلمة المرور غير صحيحة', 'danger')
            db.close()
            return redirect(url_for('settings'))
        np = request.form.get('new_password')
        pwd = bcrypt.hashpw(np.encode(), bcrypt.gensalt()).decode() if np else h['password']
        c.execute('UPDATE hospitals SET name=?,city=?,director_name=?,phone=?,address=?,website=?,password=? WHERE hospital_id=?',
            (request.form.get('name'),request.form.get('city'),request.form.get('director_name'),request.form.get('phone'),request.form.get('address'),request.form.get('website'),pwd,session['hospital_id']))
        db.commit()
        session['hospital_name'] = request.form.get('name')
        log_action("UPDATE_SETTINGS")
        flash('✅ تم التحديث بنجاح', 'success')
        db.close()
        return redirect(url_for('settings'))
    c.execute("SELECT * FROM hospitals WHERE hospital_id = ?", (session['hospital_id'],))
    h = c.fetchone()
    db.close()
    return render_template('settings.html', hospital=h)

@app.route('/patients')
@login_required
def patients_list():
    s = request.args.get('search', '').strip()
    db = get_db()
    c = db.cursor()
    if s:
        c.execute('SELECT * FROM patients WHERE full_name LIKE ? OR patient_id LIKE ? OR national_id LIKE ? ORDER BY created_at DESC', (f'%{s}%', f'%{s}%', f'%{s}%'))
        log_action("SEARCH_PATIENT", details=f"بحث: {s}")
    else:
        c.execute("SELECT * FROM patients ORDER BY created_at DESC")
    ps = c.fetchall()
    db.close()
    return render_template('patients_list.html', patients=ps, search=s)

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        pid = gen_patient_id()
        db = get_db()
        c = db.cursor()
        try:
            national_id = request.form.get('national_id', '').strip()
            if not national_id:
                national_id = None
                
            phone = request.form.get('phone', '').strip()
            if not phone:
                phone = None
            
            c.execute('INSERT INTO patients(patient_id,full_name,birth_date,gender,blood_type,phone,address,emergency_contact,emergency_phone,national_id) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (pid, request.form['full_name'], request.form['birth_date'], request.form['gender'], request.form['blood_type'], phone, request.form.get('address',''), request.form.get('emergency_contact',''), request.form.get('emergency_phone',''), national_id))
            db.commit()
            log_action("ADD_PATIENT", patient_id=pid, details=f"إضافة: {request.form['full_name']}")
            flash(f'تم الإضافة! رقم: {pid}', 'success')
            db.close()
            return redirect(url_for('patient_profile', patient_id=pid))
        except Exception as e:
            db.rollback()
            flash(f'خطأ: {str(e)}', 'danger')
            db.close()
    return render_template('add_patient.html')

@app.route('/patients/<patient_id>')
@login_required
def patient_profile(patient_id):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    p = c.fetchone()
    if not p:
        flash('المريض غير موجود', 'danger')
        db.close()
        return redirect(url_for('patients_list'))
    c.execute("SELECT * FROM chronic_diseases WHERE patient_id = ?", (patient_id,))
    d = c.fetchall()
    c.execute("SELECT * FROM allergies WHERE patient_id = ?", (patient_id,))
    a = c.fetchall()
    c.execute('SELECT s.*,h.name as hospital_name FROM surgeries s JOIN hospitals h ON s.hospital_id = h.hospital_id WHERE s.patient_id = ? ORDER BY s.surgery_date DESC', (patient_id,))
    su = c.fetchall()
    c.execute('SELECT v.*,h.name as hospital_name FROM visits v JOIN hospitals h ON v.hospital_id = h.hospital_id WHERE v.patient_id = ? ORDER BY v.visit_date DESC', (patient_id,))
    v = c.fetchall()
    c.execute('SELECT m.*,h.name as hospital_name FROM medications m JOIN hospitals h ON m.hospital_id = h.hospital_id WHERE m.patient_id = ? ORDER BY m.start_date DESC', (patient_id,))
    m = c.fetchall()
    c.execute('SELECT id, patient_id, hospital_id, file_type, file_name, test_date, doctor_name, diagnosis, description, uploaded_at FROM medical_files WHERE patient_id = ? ORDER BY uploaded_at DESC', (patient_id,))
    mf = c.fetchall()
    db.close()
    log_action("VIEW_PATIENT", patient_id=patient_id)
    return render_template('patient_profile.html', patient=p, diseases=d, allergies=a, surgeries=su, visits=v, medications=m, medical_files=mf)

@app.route('/patients/<patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    db = get_db()
    c = db.cursor()
    if request.method == 'POST':
        try:
            c.execute('UPDATE patients SET full_name=?,birth_date=?,gender=?,blood_type=?,phone=?,address=?,emergency_contact=?,emergency_phone=?,national_id=? WHERE patient_id=?',
                (request.form['full_name'],request.form['birth_date'],request.form['gender'],request.form['blood_type'],request.form.get('phone',''),request.form.get('address',''),request.form.get('emergency_contact',''),request.form.get('emergency_phone',''),request.form.get('national_id',''),patient_id))
            db.commit()
            log_action("EDIT_PATIENT", patient_id=patient_id)
            flash('تم التحديث', 'success')
            db.close()
            return redirect(url_for('patient_profile', patient_id=patient_id))
        except Exception as e:
            db.rollback()
            flash(f'خطأ: {str(e)}', 'danger')
    c.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    p = c.fetchone()
    db.close()
    return render_template('edit_patient.html', patient=p) if p else redirect(url_for('patients_list'))

@app.route('/patients/<patient_id>/add_disease', methods=['POST'])
@login_required
def add_disease(patient_id):
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO chronic_diseases(patient_id,disease,diagnosed,doctor_name,status) VALUES(?,?,?,?,?)',
            (patient_id,request.form['disease'],request.form.get('diagnosed'),request.form.get('doctor_name',''),request.form.get('status','active')))
        db.commit()
        log_action("ADD_DISEASE", patient_id=patient_id)
        flash('تم الإضافة', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/patients/<patient_id>/add_allergy', methods=['POST'])
@login_required
def add_allergy(patient_id):
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO allergies(patient_id,allergen,reaction,severity) VALUES(?,?,?,?)',
            (patient_id,request.form['allergen'],request.form.get('reaction',''),request.form.get('severity','medium')))
        db.commit()
        log_action("ADD_ALLERGY", patient_id=patient_id)
        flash('✅ تم إضافة الحساسية', 'success')
    except Exception as e:
        flash(f'❌ خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/patients/<patient_id>/add_visit', methods=['POST'])
@login_required
def add_visit(patient_id):
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO visits(patient_id,hospital_id,visit_date,reason,diagnosis,doctor_name,chief_complaint,prescription,notes) VALUES(?,?,?,?,?,?,?,?,?)',
            (patient_id,session['hospital_id'],request.form['visit_date'],request.form['reason'],request.form.get('diagnosis',''),request.form.get('doctor_name',''),request.form.get('chief_complaint',''),request.form.get('prescription',''),request.form.get('notes','')))
        db.commit()
        log_action("ADD_VISIT", patient_id=patient_id)
        flash('تم الإضافة', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/patients/<patient_id>/add_surgery', methods=['POST'])
@login_required
def add_surgery(patient_id):
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO surgeries(patient_id,hospital_id,surgery_name,surgery_date,doctor_name,surgeon_name,anesthesia_type,result,notes) VALUES(?,?,?,?,?,?,?,?,?)',
            (patient_id,session['hospital_id'],request.form['surgery_name'],request.form['surgery_date'],request.form.get('doctor_name',''),request.form.get('surgeon_name',''),request.form.get('anesthesia_type',''),request.form.get('result','successful'),request.form.get('notes','')))
        db.commit()
        log_action("ADD_SURGERY", patient_id=patient_id)
        flash('تم الإضافة', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/patients/<patient_id>/add_medication', methods=['POST'])
@login_required
def add_medication(patient_id):
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO medications(patient_id,hospital_id,drug_name,dosage,frequency,start_date,end_date,prescribed_by,indication) VALUES(?,?,?,?,?,?,?,?,?)',
            (patient_id,session['hospital_id'],request.form['drug_name'],request.form.get('dosage',''),request.form.get('frequency',''),request.form.get('start_date'),request.form.get('end_date'),request.form.get('prescribed_by',''),request.form.get('indication','')))
        db.commit()
        log_action("ADD_MEDICATION", patient_id=patient_id)
        flash('تم الإضافة', 'success')
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
        
        f = request.files['file']
        if f.filename == '' or not allowed_file(f.filename):
            flash('ملف غير صحيح', 'danger')
            return redirect(url_for('patient_profile', patient_id=patient_id))
        
        # قراءة محتوى الملف
        file_data = f.read()
        
        db = get_db()
        c = db.cursor()
        
        # حفظ في قاعدة البيانات
        c.execute('INSERT INTO medical_files(patient_id,hospital_id,file_type,file_name,file_data,test_date,doctor_name,diagnosis,description) VALUES(?,?,?,?,?,?,?,?,?)',
            (patient_id, session['hospital_id'], request.form.get('file_type','document'), 
             f.filename, file_data, request.form.get('test_date'), 
             request.form.get('doctor_name',''), request.form.get('diagnosis',''), 
             request.form.get('description','')))
        
        db.commit()
        db.close()
        
        log_action("UPLOAD_FILE", patient_id=patient_id)
        flash('✅ تم رفع الملف بنجاح وحفظه!', 'success')
    except Exception as e:
        flash(f'❌ خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/files/<int:file_id>')
@login_required
def view_file(file_id):
    try:
        db = get_db()
        c = db.cursor()
        c.execute("SELECT file_name, file_data FROM medical_files WHERE id = ?", (file_id,))
        f = c.fetchone()
        db.close()
        
        if not f or not f['file_data']:
            flash('الملف غير موجود', 'danger')
            return redirect(url_for('dashboard'))
        
        file_data = f['file_data']
        
        # التعامل مع memoryview
        if isinstance(file_data, memoryview):
            file_data = file_data.tobytes()
        
        mime_type, _ = mimetypes.guess_type(f['file_name'])
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        return send_file(
            io.BytesIO(file_data),
            mimetype=mime_type,
            download_name=f['file_name'],
            as_attachment=False
        )
    except Exception as e:
        flash(f'❌ خطأ: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/audit')
@login_required
def audit_log():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT a.*,h.name as hospital_name FROM audit_log a LEFT JOIN hospitals h ON a.hospital_id = h.hospital_id WHERE a.hospital_id = ? ORDER BY a.timestamp DESC LIMIT 200', (session['hospital_id'],))
    logs = c.fetchall()
    db.close()
    return render_template('audit_log.html', logs=logs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
