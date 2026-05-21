"""
╔══════════════════════════════════════════════════════╗
║   نظام إدارة السجلات الطبية الإلكترونية             ║
║   Hospital Electronic Medical Records System         ║
╚══════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import bcrypt
from datetime import datetime
from functools import wraps
import random
import string

app = Flask(__name__)
app.secret_key = "hospital_secret_key_2024_secure"

# ── إعدادات MySQL ─────────────────────────────────────
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = ''           # كلمة مرور MySQL (فارغة في XAMPP)
app.config['MYSQL_DB']       = 'hospital_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# ── دوال مساعدة ───────────────────────────────────────
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
    """تسجيل كل العمليات في Audit Log"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO audit_log (hospital_id, action, patient_id, details, ip_address)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session.get('hospital_id', 'SYSTEM'),
            action,
            patient_id,
            details,
            request.remote_addr
        ))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print(f"Log error: {e}")


def generate_patient_id():
    """توليد ID فريد للمريض"""
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM patients")
    count = cur.fetchone()['cnt']
    cur.close()
    return f"PAT{str(count + 1).zfill(5)}"


# ══════════════════════════════════════════════════════
#   المسارات (Routes)
# ══════════════════════════════════════════════════════

# ── الصفحة الرئيسية ───────────────────────────────────
@app.route('/')
def index():
    if 'hospital_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# ── تسجيل الدخول ──────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email'].strip()
        password = request.form['password'].strip()

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM hospitals WHERE email = %s AND is_active = 1", (email,))
        hospital = cur.fetchone()
        cur.close()

        if hospital and bcrypt.checkpw(password.encode(), hospital['password'].encode()):
            session['hospital_id']   = hospital['hospital_id']
            session['hospital_name'] = hospital['name']
            session['hospital_city'] = hospital['city']
            log_action("LOGIN", details=f"تسجيل دخول ناجح")
            flash(f"مرحباً بك، {hospital['name']} 👋", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')

    return render_template('login.html')


# ── تسجيل الخروج ──────────────────────────────────────
@app.route('/logout')
@login_required
def logout():
    log_action("LOGOUT", details="تسجيل خروج")
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))


# ── لوحة التحكم ───────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()

    # إحصائيات عامة
    cur.execute("SELECT COUNT(*) as cnt FROM patients")
    total_patients = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) as cnt FROM visits WHERE hospital_id = %s", (session['hospital_id'],))
    my_visits = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) as cnt FROM surgeries WHERE hospital_id = %s", (session['hospital_id'],))
    my_surgeries = cur.fetchone()['cnt']

    # آخر 5 زيارات
    cur.execute("""
        SELECT v.*, p.full_name FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE v.hospital_id = %s
        ORDER BY v.visit_date DESC LIMIT 5
    """, (session['hospital_id'],))
    recent_visits = cur.fetchall()

    cur.close()
    return render_template('dashboard.html',
        total_patients=total_patients,
        my_visits=my_visits,
        my_surgeries=my_surgeries,
        recent_visits=recent_visits
    )


# ── قائمة المرضى ──────────────────────────────────────
@app.route('/patients')
@login_required
def patients_list():
    search = request.args.get('search', '').strip()
    cur = mysql.connection.cursor()

    if search:
        cur.execute("""
            SELECT * FROM patients
            WHERE full_name LIKE %s OR patient_id LIKE %s
            ORDER BY created_at DESC
        """, (f'%{search}%', f'%{search}%'))
        log_action("SEARCH_PATIENT", details=f"بحث عن: {search}")
    else:
        cur.execute("SELECT * FROM patients ORDER BY created_at DESC")

    patients = cur.fetchall()
    cur.close()
    return render_template('patients_list.html', patients=patients, search=search)


# ── إضافة مريض جديد ───────────────────────────────────
@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        patient_id = generate_patient_id()
        cur = mysql.connection.cursor()
        try:
            # بيانات المريض الأساسية
            cur.execute("""
                INSERT INTO patients
                (patient_id, full_name, birth_date, gender, blood_type, phone, address, emergency_contact, emergency_phone)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
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

            # أمراض مزمنة
            diseases = request.form.getlist('disease[]')
            disease_dates = request.form.getlist('disease_date[]')
            for d, dd in zip(diseases, disease_dates):
                if d.strip():
                    cur.execute("""
                        INSERT INTO chronic_diseases (patient_id, disease, diagnosed)
                        VALUES (%s, %s, %s)
                    """, (patient_id, d, dd or None))

            # حساسية
            allergens = request.form.getlist('allergen[]')
            reactions = request.form.getlist('reaction[]')
            for a, r in zip(allergens, reactions):
                if a.strip():
                    cur.execute("""
                        INSERT INTO allergies (patient_id, allergen, reaction)
                        VALUES (%s, %s, %s)
                    """, (patient_id, a, r))

            mysql.connection.commit()
            log_action("ADD_PATIENT", patient_id=patient_id, details=f"إضافة مريض: {request.form['full_name']}")
            flash(f'تم إضافة المريض بنجاح! رقمه: {patient_id}', 'success')
            return redirect(url_for('patient_profile', patient_id=patient_id))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'خطأ في الحفظ: {str(e)}', 'danger')
        finally:
            cur.close()

    return render_template('add_patient.html')


# ── ملف المريض الكامل ─────────────────────────────────
@app.route('/patients/<patient_id>')
@login_required
def patient_profile(patient_id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
    patient = cur.fetchone()
    if not patient:
        flash('المريض غير موجود', 'danger')
        return redirect(url_for('patients_list'))

    cur.execute("SELECT * FROM chronic_diseases WHERE patient_id = %s", (patient_id,))
    diseases = cur.fetchall()

    cur.execute("SELECT * FROM allergies WHERE patient_id = %s", (patient_id,))
    allergies = cur.fetchall()

    cur.execute("""
        SELECT s.*, h.name as hospital_name FROM surgeries s
        JOIN hospitals h ON s.hospital_id = h.hospital_id
        WHERE s.patient_id = %s ORDER BY s.surgery_date DESC
    """, (patient_id,))
    surgeries = cur.fetchall()

    cur.execute("""
        SELECT v.*, h.name as hospital_name FROM visits v
        JOIN hospitals h ON v.hospital_id = h.hospital_id
        WHERE v.patient_id = %s ORDER BY v.visit_date DESC
    """, (patient_id,))
    visits = cur.fetchall()

    cur.execute("""
        SELECT m.*, h.name as hospital_name FROM medications m
        JOIN hospitals h ON m.hospital_id = h.hospital_id
        WHERE m.patient_id = %s ORDER BY m.start_date DESC
    """, (patient_id,))
    medications = cur.fetchall()

    cur.close()
    log_action("VIEW_PATIENT", patient_id=patient_id, details="عرض ملف المريض")

    return render_template('patient_profile.html',
        patient=patient, diseases=diseases, allergies=allergies,
        surgeries=surgeries, visits=visits, medications=medications
    )


# ── إضافة زيارة طبية ──────────────────────────────────
@app.route('/patients/<patient_id>/add_visit', methods=['POST'])
@login_required
def add_visit(patient_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO visits (patient_id, hospital_id, visit_date, reason, diagnosis, doctor_name, prescription, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            patient_id,
            session['hospital_id'],
            request.form['visit_date'],
            request.form['reason'],
            request.form.get('diagnosis', ''),
            request.form.get('doctor_name', ''),
            request.form.get('prescription', ''),
            request.form.get('notes', '')
        ))
        mysql.connection.commit()
        log_action("ADD_VISIT", patient_id=patient_id, details=f"إضافة زيارة: {request.form['reason']}")
        flash('تم إضافة الزيارة بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        cur.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))


# ── إضافة عملية جراحية ────────────────────────────────
@app.route('/patients/<patient_id>/add_surgery', methods=['POST'])
@login_required
def add_surgery(patient_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO surgeries (patient_id, hospital_id, surgery_name, surgery_date, doctor_name, result, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            patient_id,
            session['hospital_id'],
            request.form['surgery_name'],
            request.form['surgery_date'],
            request.form.get('doctor_name', ''),
            request.form.get('result', 'successful'),
            request.form.get('notes', '')
        ))
        mysql.connection.commit()
        log_action("ADD_SURGERY", patient_id=patient_id, details=f"إضافة عملية: {request.form['surgery_name']}")
        flash('تم إضافة العملية بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        cur.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))


# ── إضافة دواء ────────────────────────────────────────
@app.route('/patients/<patient_id>/add_medication', methods=['POST'])
@login_required
def add_medication(patient_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO medications (patient_id, hospital_id, drug_name, dosage, frequency, start_date, end_date, prescribed_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            patient_id,
            session['hospital_id'],
            request.form['drug_name'],
            request.form.get('dosage', ''),
            request.form.get('frequency', ''),
            request.form.get('start_date') or None,
            request.form.get('end_date') or None,
            request.form.get('prescribed_by', '')
        ))
        mysql.connection.commit()
        log_action("ADD_MEDICATION", patient_id=patient_id, details=f"إضافة دواء: {request.form['drug_name']}")
        flash('تم إضافة الدواء بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        cur.close()
    return redirect(url_for('patient_profile', patient_id=patient_id))


# ── سجل العمليات (Audit Log) ──────────────────────────
@app.route('/audit')
@login_required
def audit_log():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT a.*, h.name as hospital_name FROM audit_log a
        LEFT JOIN hospitals h ON a.hospital_id = h.hospital_id
        WHERE a.hospital_id = %s
        ORDER BY a.timestamp DESC LIMIT 100
    """, (session['hospital_id'],))
    logs = cur.fetchall()
    cur.close()
    return render_template('audit_log.html', logs=logs)


# ══════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
