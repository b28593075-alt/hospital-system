# 🏥 HEMRS - نظام إدارة السجلات الطبية الإلكترونية
## تعليمات الإعداد والنشر

---

## ✅ الملفات المتضمنة:

```
hospital_system_final/
├── app.py                    ✅ التطبيق الرئيسي
├── app_postgresql.py         ✅ نسخة PostgreSQL
├── requirements.txt          ✅ المكتبات المطلوبة
├── Procfile                  ✅ تكوين Render
├── .gitignore               ✅ ملفات التجاهل
├── templates/
│   ├── login.html           ✅ صفحة الدخول (معدلة)
│   ├── base.html            ✅ القالب الأساسي
│   ├── dashboard.html       ✅ لوحة التحكم
│   ├── patients_list.html   ✅ قائمة المرضى
│   ├── add_patient.html     ✅ إضافة مريض
│   ├── patient_profile.html ✅ ملف المريض
│   ├── edit_patient.html    ✅ تعديل المريض
│   ├── settings.html        ✅ الإعدادات
│   └── audit_log.html       ✅ سجل العمليات
└── uploads/                 📁 مجلد الملفات
```

---

## 🚀 الخطوات الكاملة:

### الخطوة 1: استبدال الملفات في مشروعك

```bash
# انسخ جميع الملفات من hospital_system_final إلى مجلد المشروع
# Desktop\hospital_system\

# ملفات Python:
copy app.py
copy app_postgresql.py
copy requirements.txt
copy Procfile
copy .gitignore

# مجلد templates:
xcopy templates templates /E /I
```

### الخطوة 2: رفع على GitHub

```bash
cd Desktop\hospital_system

# أضف جميع الملفات
git add .

# أنشئ commit
git commit -m "Complete HEMRS system with PostgreSQL integration and corrected credentials"

# رفع
git push
```

### الخطوة 3: تفعيل على Render

```
1. اذهب: https://dashboard.render.com
2. اختر مشروعك: hospital-system
3. اضغط: Manual Deploy
4. اختر: Clear Cache and Deploy
5. انتظر: 2-3 دقايق
```

---

## 🔐 بيانات الدخول:

```
📧 البريد: admin@hospital.iq
🔐 الرمز: 0987654321
```

---

## 🛠️ التكوينات المطلوبة في Render:

### Environment Variables:

```
DATABASE_URL = postgresql://...  (من PostgreSQL اللي أضفته)
FLASK_ENV = production
```

---

## ✨ المميزات:

✅ نظام طبي كامل
✅ قاعدة بيانات PostgreSQL آمنة
✅ تشفير كلمات المرور (bcrypt)
✅ سجلات العمليات والأمان
✅ واجهة عربية احترافية
✅ رفع الملفات الطبية
✅ إدارة المرضى والزيارات

---

## 📞 المساعدة:

إذا واجهت أي مشكلة:
1. تحقق من Logs في Render
2. تأكد من DATABASE_URL
3. تأكد من requirements.txt
4. جرب Manual Deploy مع Clear Cache

---

**تم بنجاح! 🎉**
