# 🚀 دليل النشر - منصة SAIF.AI

هذا الدليل يشرح كيفية نشر منصة SAIF.AI على منصات الاستضافة المختلفة.

## 📋 المتطلبات الأساسية

قبل البدء، تأكد من أن لديك:
- حساب على منصة الاستضافة (Render, Heroku, DigitalOcean, إلخ)
- مستودع GitHub للمشروع
- مفاتيح API من OpenRouter و/أو Gemini
- قاعدة بيانات PostgreSQL
- خادم Redis (اختياري لكن موصى به)

---

## 🎯 النشر على Render.com (الأسهل والأفضل)

Render توفر تجربة نشر سهلة وموثوقة مع دعم Docker والمتغيرات البيئية.

### الخطوة 1: إنشاء حساب على Render
1. اذهب إلى [render.com](https://render.com)
2. سجل حساب جديد أو سجل الدخول
3. ربط حساب GitHub الخاص بك

### الخطوة 2: إنشاء قاعدة بيانات PostgreSQL

1. من لوحة التحكم، اختر **New +** → **PostgreSQL**
2. أدخل المعلومات:
   - **Name**: `saif-ai-db`
   - **Database**: `saif_ai`
   - **User**: `postgres`
   - **Region**: اختر المنطقة الأقرب
   - **PostgreSQL Version**: 15
3. اختر الخطة المجانية أو المدفوعة
4. انقر **Create Database**
5. **انسخ رابط الاتصال** (ستحتاجه لاحقاً)

### الخطوة 3: إنشاء خادم Redis

1. من لوحة التحكم، اختر **New +** → **Redis**
2. أدخل المعلومات:
   - **Name**: `saif-ai-redis`
   - **Region**: نفس منطقة قاعدة البيانات
3. اختر الخطة المجانية
4. انقر **Create Redis**
5. **انسخ رابط الاتصال**

### الخطوة 4: إنشاء Web Service

1. من لوحة التحكم، اختر **New +** → **Web Service**
2. اختر مستودع GitHub الخاص بك (`sa885if.ai`)
3. أدخل المعلومات:
   - **Name**: `saif-ai-api`
   - **Region**: نفس المنطقة
   - **Branch**: `main`
   - **Runtime**: `Docker`
   - **Build Command**: سيتم اكتشافه تلقائياً
   - **Start Command**: سيتم اكتشافه تلقائياً

### الخطوة 5: إضافة متغيرات البيئة

في صفحة الخدمة، اذهب إلى **Environment** وأضف:

```
APP_NAME=SAIF.AI
APP_VERSION=2.0.0
DEBUG=False

DATABASE_URL=postgresql+asyncpg://[user]:[password]@[host]:[port]/[database]
REDIS_URL=redis://[user]:[password]@[host]:[port]

OPENROUTER_API_KEY=sk-or-...
OPENROUTER_DEFAULT_MODEL=google/gemini-2.0-flash-lite-001

GEMINI_API_KEY=AIzaSy...
GEMINI_DEFAULT_MODEL=gemini-2.0-flash

ACTIVE_PROVIDER=openrouter

SHORT_MEMORY_SIZE=20
SUMMARY_TRIGGER=15
CACHE_TTL=3600
RATE_LIMIT_PER_MINUTE=30

THINKING_MODE_ENABLED=True
IMAGE_GEN_ENABLED=True
VOICE_ENABLED=True
FILE_UPLOAD_ENABLED=True
CAMERA_ENABLED=True
DARK_MODE_DEFAULT=True
```

### الخطوة 6: النشر

1. انقر **Create Web Service**
2. سيبدأ البناء والنشر تلقائياً
3. انتظر حتى يكتمل (عادة 5-10 دقائق)
4. **انسخ رابط الخدمة** - هذا هو رابط API الخاص بك!

---

## 🐳 النشر باستخدام Docker

إذا كنت تريد نشر المشروع على أي خادم يدعم Docker:

### الخطوة 1: بناء الصورة

```bash
docker build -t saif-ai:latest .
```

### الخطوة 2: تشغيل الحاوية

```bash
docker run -d \
  --name saif-ai \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e REDIS_URL="redis://..." \
  -e OPENROUTER_API_KEY="sk-or-..." \
  -e ACTIVE_PROVIDER="openrouter" \
  saif-ai:latest
```

### الخطوة 3: التحقق

```bash
# فحص حالة الحاوية
docker ps

# عرض السجلات
docker logs saif-ai

# فحص صحة الخدمة
curl http://localhost:8000/api/v1/health/
```

---

## 🌐 النشر على DigitalOcean App Platform

### الخطوة 1: إنشاء تطبيق جديد

1. اذهب إلى [DigitalOcean](https://www.digitalocean.com)
2. اختر **Apps** → **Create App**
3. اختر مستودع GitHub

### الخطوة 2: إعدادات التطبيق

1. اختر **Docker** كنوع التطبيق
2. أضف متغيرات البيئة المطلوبة
3. اختر خطة الموارد

### الخطوة 3: النشر

انقر **Deploy** وانتظر حتى يكتمل.

---

## 🔧 النشر على Heroku (قديم)

**ملاحظة**: Heroku أوقفت الخطة المجانية. استخدم Render بدلاً منها.

---

## ✅ اختبار الخدمة بعد النشر

### 1. فحص الصحة

```bash
curl https://your-app-url.onrender.com/api/v1/health/
```

### 2. إنشاء جلسة جديدة

```bash
curl -X POST https://your-app-url.onrender.com/api/v1/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'
```

### 3. إرسال رسالة

```bash
curl -X POST https://your-app-url.onrender.com/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "مرحبا، كيف حالك؟"
  }'
```

---

## 🔍 استكشاف الأخطاء

### خطأ: "Cannot connect to database"

**الحل**: تحقق من:
- صحة رابط `DATABASE_URL`
- أن قاعدة البيانات قيد التشغيل
- أن المتغيرات البيئية صحيحة

### خطأ: "Redis connection failed"

**الحل**: تحقق من:
- صحة رابط `REDIS_URL`
- أن Redis قيد التشغيل
- أنك تستخدم الرابط الصحيح

### خطأ: "Invalid API key"

**الحل**: تحقق من:
- صحة `OPENROUTER_API_KEY` أو `GEMINI_API_KEY`
- أن المفتاح لم ينته صلاحيته
- أنك استخدمت المفتاح الصحيح

### خطأ: "Build failed"

**الحل**: تحقق من:
- أن ملف `requirements.txt` موجود وصحيح
- أن ملف `Dockerfile` موجود
- أن جميع الملفات مرفوعة على GitHub

---

## 📊 المراقبة والصيانة

### عرض السجلات

على Render:
1. اذهب إلى خدمتك
2. اختر **Logs**
3. شاهد السجلات الحية

### إعادة تشغيل الخدمة

```bash
# على Render
# من لوحة التحكم → Manual Deploy → Deploy latest commit
```

### تحديث الكود

```bash
# ادفع التغييرات إلى GitHub
git add .
git commit -m "Update features"
git push origin main

# سيتم النشر تلقائياً على Render
```

---

## 🔐 الأمان

### نصائح أمان مهمة

1. **استخدم HTTPS فقط**: تأكد من أن جميع الاتصالات مشفرة
2. **أخف مفاتيح API**: لا تضعها في الكود، استخدم متغيرات البيئة
3. **حدّث الحزم**: حدّث `requirements.txt` بانتظام
4. **استخدم قاعدة بيانات آمنة**: استخدم كلمات مرور قوية
5. **فعّل Rate Limiting**: تم تفعيله افتراضياً (30 طلب/دقيقة)

---

## 📞 الدعم

إذا واجهت مشاكل:
1. تحقق من السجلات
2. اقرأ [README.md](README.md)
3. افتح issue على GitHub
4. تواصل معنا على support@saif.ai

---

**صُنع بـ ❤️ من قبل فريق SAIF.AI**
