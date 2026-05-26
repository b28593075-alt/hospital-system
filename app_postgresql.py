from flask import Flask, render_template, request, redirect, url_for, session, flash

import psycopg2

from psycopg2.extras import RealDictCursor

import bcrypt

from datetime import datetime

from functools import wraps

import os

from werkzeug.utils import secure_filename



app = Flask(__name__)

app.secret_key = "hospital_secure_key_2024"



UPLOAD_FOLDER = 'uploads'

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx'}



os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024



# PostgreSQL Connection

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/hospital_db')

if DATABASE_URL.startswith('postgres://'):

    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)



def get_db():

    conn = psycopg2.connect(DATABASE_URL)

    conn.row_factory = RealDictCursor

    return conn



def query_db(query, args=(), one=False):

    conn = psycopg2.connect(DATABASE_URL)

    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(query, args)

    rv = cur.fetchall()

    conn.commit()

    cur.close()

    conn.close()

    return (rv[0] if rv else None) if one else rv



def exec_db(query, args=()):

    conn = psycopg2.connect(DATABASE_URL)

    cur = conn.cursor()

    cur.execute(query, args)

    conn.commit()

    cur.close()

    conn.close()



def init_db():

    try:

        exec_db('''

        CREATE TABLE IF NOT EXISTS hospitals(

            id SERIAL PRIMARY KEY,

            hospital_id VARCHAR(50) UNIQUE,

            name VARCHAR(255),

            city VARCHAR(100),

            phone VARCHAR(20),

            email VARCHAR(255) UNIQUE,

            password VARCHAR(255),

            director_name VARCHAR(255),

            address TEXT,

            website VARCHAR(255),

            is_active INTEGER DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        ''')



        exec_db('''

        CREATE TABLE IF NOT EXISTS patients(

            id SERIAL PRIMARY KEY,

            patient_id VARCHAR(50) UNIQUE,

            full_name VARCHAR(255),

            birth_date DATE,

            gender VARCHAR(10),

            blood_type VARCHAR(5),

            phone VARCHAR(20),

            address TEXT,

            emergency_contact VARCHAR(255),

            emergency_phone VARCHAR(20),

            national_id VARCHAR(50) UNIQUE,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        ''')



        exec_db('''

        CREATE TABLE IF NOT EXISTS chronic_diseases(

            id SERIAL PRIMARY KEY,

            patient_id VARCHAR(50),

            disease VARCHAR(255),

            diagnosed DATE,

            doctor_name VARCHAR(255),

            notes TEXT,

            status VARCHAR(50) DEFAULT 'active',

            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)

        )

        ''')



        exec_db('''

        CREATE TABLE IF NOT EXISTS allergies(

            id SERIAL PRIMARY KEY,

            patient_id VARCHAR(50),

            allergen VARCHAR(255),

            reaction VARCHAR(255),

            severity VARCHAR(50) DEFAULT 'medium',

            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)

        )

        ''')



        exec_db('''

        CREATE TABLE IF NOT EXISTS surgeries(

            id SERIAL PRIMARY KEY,

            patient_id VARCHAR(50),

            hospital_id VARCHAR(50),

            surgery_name VARCHAR(255),

            surgery_date DATE,

            doctor_name VARCHAR(255),

            surgeon_name VARCHAR(255),

            anesthesia_type VARCHAR(255),

            result VARCHAR(50) DEFAULT 'successful',

            notes TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),

            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)

        )

        ''')



        exec_db('''

        CREATE TABLE IF NOT EXISTS visits(

            id SERIAL PRIMARY KEY,

            patient_id VARCHAR(50),

            hospital_id VARCHAR(50),

            visit_date TIMESTAMP,

            reason VARCHAR(255),

            diagnosis TEXT,

            doctor_name VARCHAR(255),

            chief_complaint TEXT,

            prescription TEXT,

            notes TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),

            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)

        )

        ''')



        exec_db('''

        CREATE TABLE IF NOT EXISTS medications(

            id SERIAL PRIMARY KEY,

            patient_id VARCHAR(50),

            hospital_id VARCHAR(50),

            drug_name VARCHAR(255),

            dosage VARCHAR(100),

            frequency VARCHAR(100),

            start_date DATE,

            end_date DATE,

            prescribed_by VARCHAR(255),

            indication TEXT,

            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),

            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)

        )

        ''')



        exec_db('''

        CREATE TABLE IF NOT EXISTS medical_files(

            id SERIAL PRIMARY KEY,

            patient_id VARCHAR(50),

            hospital_id VARCHAR(50),

            file_type VARCHAR(100),

            file_name VARCHAR(255),

            file_path VARCHAR(500),

            test_date DATE,

            doctor_name VARCHAR(255),

            diagnosis TEXT,

            description TEXT,

            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(patient_id) REFERENCES patients(patient_id),

            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)

        )

        ''')



        exec_db('''

        CREATE TABLE IF NOT EXISTS audit_log(

            id SERIAL PRIMARY KEY,

            hospital_id VARCHAR(50),

            action VARCHAR(100),

            patient_id VARCHAR(50),

            details TEXT,

            ip_address VARCHAR(50),

            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        ''')



        # تحقق من وجود بيانات تجريبية

        result = query_db("SELECT COUNT(*) as cnt FROM hospitals")

        if result and result[0]['cnt'] == 0:

            pwd = bcrypt.hashpw(b'0987654321', bcrypt.gensalt()).decode()

            exec_db(

                "INSERT INTO hospitals(hospital_id,name,city,phone,email,password,director_name,address) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",

                ('HSP001', 'مستشفى الرشيد التعليمي', 'بغداد', '07701234567', 'admin@hospital.iq', pwd, 'أ.د محمد علي', 'بغداد - الكرادة')

            )

        

        print("✅ Database initialized successfully!")

    except Exception as e:

        print(f"❌ Database error: {e}")



def allowed_file(filename):

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



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

        exec_db(

            'INSERT INTO audit_log(hospital_id,action,patient_id,details,ip_address) VALUES(%s,%s,%s,%s,%s)',

            (session.get('hospital_id','SYSTEM'), action, patient_id, details, request.remote_addr)

        )

    except:pass



def gen_patient_id():

    result = query_db("SELECT COUNT(*) as cnt FROM patients")

    cnt = result[0]['cnt'] if result else 0

    return f"PAT{str(cnt + 1).zfill(6)}"



@app.route('/')

def index():

    return redirect(url_for('dashboard')) if 'hospital_id' in session else redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        email = request.form['email'].strip()

        password = request.form['password'].strip()

        result = query_db("SELECT * FROM hospitals WHERE email = %s AND is_active = 1", (email,), one=True)

        

        if result and bcrypt.checkpw(password.encode(), result['password'].encode()):

            session['hospital_id'] = result['hospital_id']

            session['hospital_name'] = result['name']

            session['hospital_city'] = result['city']

            session['director_name'] = result['director_name']

            log_action("LOGIN")

            flash(f"مرحباً {result['name']}", 'success')

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

    total = query_db("SELECT COUNT(*) as cnt FROM patients")[0]['cnt']

    visits = query_db("SELECT COUNT(*) as cnt FROM visits WHERE hospital_id = %s", (session['hospital_id'],))[0]['cnt']

    surgeries = query_db("SELECT COUNT(*) as cnt FROM surgeries WHERE hospital_id = %s", (session['hospital_id'],))[0]['cnt']

    files = query_db("SELECT COUNT(*) as cnt FROM medical_files WHERE hospital_id = %s", (session['hospital_id'],))[0]['cnt']

    recent = query_db('SELECT v.*,p.full_name FROM visits v JOIN patients p ON v.patient_id = p.patient_id WHERE v.hospital_id = %s ORDER BY v.visit_date DESC LIMIT 5', (session['hospital_id'],))

    return render_template('dashboard.html', total_patients=total, my_visits=visits, my_surgeries=surgeries, total_files=files, recent_visits=recent)



@app.route('/settings', methods=['GET', 'POST'])

@login_required

def settings():

    if request.method == 'POST':

        h = query_db("SELECT * FROM hospitals WHERE hospital_id = %s", (session['hospital_id'],), one=True)

        if not bcrypt.checkpw(request.form.get('current_password').encode(), h['password'].encode()):

            flash('كلمة المرور غير صحيحة', 'danger')

            return redirect(url_for('settings'))

        np = request.form.get('new_password')

        pwd = bcrypt.hashpw(np.encode(), bcrypt.gensalt()).decode() if np else h['password']

        exec_db('UPDATE hospitals SET name=%s,director_name=%s,phone=%s,address=%s,website=%s,password=%s WHERE hospital_id=%s', 

            (request.form.get('name'),request.form.get('director_name'),request.form.get('phone'),request.form.get('address'),request.form.get('website'),pwd,session['hospital_id']))

        session['hospital_name'] = request.form.get('name')

        log_action("UPDATE_SETTINGS")

        flash('تم التحديث', 'success')

        return redirect(url_for('settings'))

    h = query_db("SELECT * FROM hospitals WHERE hospital_id = %s", (session['hospital_id'],), one=True)

    return render_template('settings.html', hospital=h)



@app.route('/patients')

@login_required

def patients_list():

    s = request.args.get('search', '').strip()

    if s:

        ps = query_db('SELECT * FROM patients WHERE full_name ILIKE %s OR patient_id ILIKE %s ORDER BY created_at DESC', (f'%{s}%', f'%{s}%'))

        log_action("SEARCH_PATIENT", details=f"بحث: {s}")

    else:

        ps = query_db("SELECT * FROM patients ORDER BY created_at DESC")

    return render_template('patients_list.html', patients=ps, search=s)



@app.route('/patients/add', methods=['GET', 'POST'])

@login_required

def add_patient():

    if request.method == 'POST':

        pid = gen_patient_id()

        try:

            exec_db('INSERT INTO patients(patient_id,full_name,birth_date,gender,blood_type,phone,address,emergency_contact,emergency_phone,national_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',

                (pid,request.form['full_name'],request.form['birth_date'],request.form['gender'],request.form['blood_type'],request.form.get('phone',''),request.form.get('address',''),request.form.get('emergency_contact',''),request.form.get('emergency_phone',''),request.form.get('national_id','')))

            log_action("ADD_PATIENT", patient_id=pid, details=f"إضافة: {request.form['full_name']}")

            flash(f'تم الإضافة! رقم: {pid}', 'success')

            return redirect(url_for('patient_profile', patient_id=pid))

        except Exception as e:

            flash(f'خطأ: {str(e)}', 'danger')

    return render_template('add_patient.html')



@app.route('/patients/<patient_id>')

@login_required

def patient_profile(patient_id):

    p = query_db("SELECT * FROM patients WHERE patient_id = %s", (patient_id,), one=True)

    if not p:

        flash('المريض غير موجود', 'danger')

        return redirect(url_for('patients_list'))

    d = query_db("SELECT * FROM chronic_diseases WHERE patient_id = %s", (patient_id,))

    a = query_db("SELECT * FROM allergies WHERE patient_id = %s", (patient_id,))

    su = query_db('SELECT s.*,h.name as hospital_name FROM surgeries s JOIN hospitals h ON s.hospital_id = h.hospital_id WHERE s.patient_id = %s ORDER BY s.surgery_date DESC', (patient_id,))

    v = query_db('SELECT v.*,h.name as hospital_name FROM visits v JOIN hospitals h ON v.hospital_id = h.hospital_id WHERE v.patient_id = %s ORDER BY v.visit_date DESC', (patient_id,))

    m = query_db('SELECT m.*,h.name as hospital_name FROM medications m JOIN hospitals h ON m.hospital_id = h.hospital_id WHERE m.patient_id = %s ORDER BY m.start_date DESC', (patient_id,))

    mf = query_db('SELECT * FROM medical_files WHERE patient_id = %s ORDER BY uploaded_at DESC', (patient_id,))

    log_action("VIEW_PATIENT", patient_id=patient_id)

    return render_template('patient_profile.html', patient=p, diseases=d, allergies=a, surgeries=su, visits=v, medications=m, medical_files=mf)



@app.route('/patients/<patient_id>/edit', methods=['GET', 'POST'])

@login_required

def edit_patient(patient_id):

    if request.method == 'POST':

        try:

            exec_db('UPDATE patients SET full_name=%s,birth_date=%s,gender=%s,blood_type=%s,phone=%s,address=%s,emergency_contact=%s,emergency_phone=%s,national_id=%s WHERE patient_id=%s',

                (request.form['full_name'],request.form['birth_date'],request.form['gender'],request.form['blood_type'],request.form.get('phone',''),request.form.get('address',''),request.form.get('emergency_contact',''),request.form.get('emergency_phone',''),request.form.get('national_id',''),patient_id))

            log_action("EDIT_PATIENT", patient_id=patient_id)

            flash('تم التحديث', 'success')

            return redirect(url_for('patient_profile', patient_id=patient_id))

        except Exception as e:

            flash(f'خطأ: {str(e)}', 'danger')

    p = query_db("SELECT * FROM patients WHERE patient_id = %s", (patient_id,), one=True)

    return render_template('edit_patient.html', patient=p) if p else redirect(url_for('patients_list'))



@app.route('/patients/<patient_id>/add_disease', methods=['POST'])

@login_required

def add_disease(patient_id):

    try:

        exec_db('INSERT INTO chronic_diseases(patient_id,disease,diagnosed,doctor_name,status) VALUES(%s,%s,%s,%s,%s)',

            (patient_id,request.form['disease'],request.form.get('diagnosed'),request.form.get('doctor_name',''),request.form.get('status','active')))

        log_action("ADD_DISEASE", patient_id=patient_id)

        flash('تم الإضافة', 'success')

    except Exception as e:

        flash(f'خطأ: {str(e)}', 'danger')

    return redirect(url_for('patient_profile', patient_id=patient_id))



@app.route('/patients/<patient_id>/add_visit', methods=['POST'])

@login_required

def add_visit(patient_id):

    try:

        exec_db('INSERT INTO visits(patient_id,hospital_id,visit_date,reason,diagnosis,doctor_name,chief_complaint,prescription,notes) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',

            (patient_id,session['hospital_id'],request.form['visit_date'],request.form['reason'],request.form.get('diagnosis',''),request.form.get('doctor_name',''),request.form.get('chief_complaint',''),request.form.get('prescription',''),request.form.get('notes','')))

        log_action("ADD_VISIT", patient_id=patient_id)

        flash('تم الإضافة', 'success')

    except Exception as e:

        flash(f'خطأ: {str(e)}', 'danger')

    return redirect(url_for('patient_profile', patient_id=patient_id))



@app.route('/patients/<patient_id>/add_surgery', methods=['POST'])

@login_required

def add_surgery(patient_id):

    try:

        exec_db('INSERT INTO surgeries(patient_id,hospital_id,surgery_name,surgery_date,doctor_name,surgeon_name,anesthesia_type,result,notes) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',

            (patient_id,session['hospital_id'],request.form['surgery_name'],request.form['surgery_date'],request.form.get('doctor_name',''),request.form.get('surgeon_name',''),request.form.get('anesthesia_type',''),request.form.get('result','successful'),request.form.get('notes','')))

        log_action("ADD_SURGERY", patient_id=patient_id)

        flash('تم الإضافة', 'success')

    except Exception as e:

        flash(f'خطأ: {str(e)}', 'danger')

    return redirect(url_for('patient_profile', patient_id=patient_id))



@app.route('/patients/<patient_id>/add_medication', methods=['POST'])

@login_required

def add_medication(patient_id):

    try:

        exec_db('INSERT INTO medications(patient_id,hospital_id,drug_name,dosage,frequency,start_date,end_date,prescribed_by,indication) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',

            (patient_id,session['hospital_id'],request.form['drug_name'],request.form.get('dosage',''),request.form.get('frequency',''),request.form.get('start_date'),request.form.get('end_date'),request.form.get('prescribed_by',''),request.form.get('indication','')))

        log_action("ADD_MEDICATION", patient_id=patient_id)

        flash('تم الإضافة', 'success')

    except Exception as e:

        flash(f'خطأ: {str(e)}', 'danger')

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

        fn = secure_filename(f"{patient_id}_{datetime.now().timestamp()}_{f.filename}")

        fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)

        f.save(fp)

        exec_db('INSERT INTO medical_files(patient_id,hospital_id,file_type,file_name,file_path,test_date,doctor_name,diagnosis,description) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',

            (patient_id,session['hospital_id'],request.form.get('file_type','document'),f.filename,fp,request.form.get('test_date'),request.form.get('doctor_name',''),request.form.get('diagnosis',''),request.form.get('description','')))

        log_action("UPLOAD_FILE", patient_id=patient_id)

        flash('تم الرفع', 'success')

    except Exception as e:

        flash(f'خطأ: {str(e)}', 'danger')

    return redirect(url_for('patient_profile', patient_id=patient_id))



@app.route('/audit')

@login_required

def audit_log():

    logs = query_db('SELECT a.*,h.name as hospital_name FROM audit_log a LEFT JOIN hospitals h ON a.hospital_id = h.hospital_id WHERE a.hospital_id = %s ORDER BY a.timestamp DESC LIMIT 200', (session['hospital_id'],))

    return render_template('audit_log.html', logs=logs)



if __name__ == '__main__':

    init_db()

    app.run(debug=True, host='0.0.0.0', port=5000) 

