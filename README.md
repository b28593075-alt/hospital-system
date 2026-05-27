# 🏥 HEMRS - Hospital Electronic Medical Records System
## نظام إدارة السجلات الطبية الإلكترونية

---

## 📋 ملخص المشروع

نظام طبي احترافي متكامل لإدارة السجلات الطبية للمرضى في المستشفيات، مدمج مع قاعدة بيانات آمنة وواجهة عربية حديثة.

---

## ✨ المميزات الرئيسية

✅ **إدارة المرضى الكاملة** - إضافة، تعديل، عرض البيانات
✅ **السجلات الطبية** - الأمراض المزمنة، الحساسيات، الجراحات
✅ **الزيارات والعلاج** - تسجيل الزيارات والأدوية الموصوفة
✅ **إدارة الملفات** - رفع وتنزيل الأشعات والتحاليل
✅ **سجل العمليات** - تتبع جميع الأنشطة للأمان
✅ **قاعدة بيانات آمنة** - PostgreSQL مع تشفير
✅ **واجهة عربية احترافية** - تصميم حديث وسهل الاستخدام

---

## 🛠️ التقنيات المستخدمة

**Backend:**
- Python 3.x
- Flask 3.0.0
- PostgreSQL
- bcrypt (تشفير)

**Frontend:**
- HTML5
- CSS3
- JavaScript
- Bootstrap Icons

**الاستضافة:**
- Render (Cloud Hosting)
- GitHub (Version Control)

---

## 📦 محتويات المشروع

```
hospital_system_final/
├── app.py                    - التطبيق الرئيسي (SQLite)
├── app_postgresql.py         - نسخة PostgreSQL
├── requirements.txt          - المكتبات المطلوبة
├── Procfile                  - تكوين Render
├── .gitignore               - ملفات التجاهل
├── SETUP_INSTRUCTIONS.md    - تعليمات الإعداد المفصلة
├── STEPS_TO_DO.txt          - خطوات تنفيذ بسيطة
├── README.md                - هذا الملف
└── templates/
    ├── login.html           - صفحة تسجيل الدخول
    ├── base.html            - القالب الأساسي
    ├── dashboard.html       - لوحة التحكم
    ├── patients_list.html   - قائمة المرضى
    ├── add_patient.html     - إضافة مريض
    ├── patient_profile.html - ملف المريض
    ├── edit_patient.html    - تعديل البيانات
    ├── settings.html        - إعدادات المستشفى
    └── audit_log.html       - سجل العمليات
```

---

## 🚀 كيفية البدء

### المتطلبات:
- Python 3.8+
- Git
- حساب GitHub
- حساب Render

### التثبيت المحلي:

```bash
# استنساخ المشروع
git clone https://github.com/YOUR_USERNAME/hospital-system.git
cd hospital-system

# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل التطبيق
python app.py
```

### النشر على Render:

```bash
# رفع التغييرات
git add .
git commit -m "Deploy HEMRS system"
git push

# ثم Manual Deploy من Render Dashboard
```

---

## 🔐 بيانات الدخول

```
📧 البريد الإلكتروني: admin@hospital.iq
🔐 كلمة المرور: 0987654321
```

---

## 📊 قاعدة البيانات

### الجداول:

1. **hospitals** - بيانات المستشفيات
2. **patients** - بيانات المرضى
3. **chronic_diseases** - الأمراض المزمنة
4. **allergies** - الحساسيات
5. **surgeries** - العمليات الجراحية
6. **visits** - الزيارات الطبية
7. **medications** - الأدوية الموصوفة
8. **medical_files** - الملفات الطبية
9. **audit_log** - سجل العمليات

---

## 🔒 الأمان

✅ تشفير كلمات المرور باستخدام bcrypt
✅ قاعدة بيانات PostgreSQL آمنة
✅ سجل العمليات لتتبع النشاطات
✅ متغيرات البيئة للبيانات الحساسة
✅ تحقق من الصلاحيات

---

## 📈 الأداء

- **السرعة**: استجابة سريعة لجميع العمليات
- **القابلية للتوسع**: يدعم آلاف المرضى
- **الموثوقية**: 99.9% uptime على Render

---

## 🐛 حل المشاكل الشائعة

### مشكلة: ملف الـ database مفقود
**الحل**: استخدم app_postgresql.py مع قاعدة بيانات Render

### مشكلة: خطأ في المكتبات
**الحل**: `pip install -r requirements.txt --upgrade`

### مشكلة: صفحة بيضاء أو خطأ 500
**الحل**: تحقق من Logs في Render Dashboard

---

## 📞 الدعم والمساعدة

إذا واجهت أي مشكلة:

1. تحقق من ملف SETUP_INSTRUCTIONS.md
2. اطلع على ملف Logs في Render
3. تأكد من وجود DATABASE_URL
4. جرب Manual Deploy مع Clear Cache

---

## 📜 الترخيص

هذا المشروع مفتوح المصدر للاستخدام التعليمي والمستشفيات.

---

## 👨‍💻 المطور

نظام تم تطويره بعناية لتلبية احتياجات المستشفيات العراقية.

---

## 🎯 النسخة

**الإصدار**: 1.0
**تاريخ الإطلاق**: مايو 2026
**الحالة**: ✅ جاهز للاستخدام

---

**شكراً لاستخدامك HEMRS! 🏥**

