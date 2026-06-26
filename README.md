# 🤖 SAIF.AI - منصة الذكاء الاصطناعي المتقدمة

منصة ذكاء اصطناعي متقدمة وقوية مبنية بـ **FastAPI** و **React**، توفر تجربة محادثة احترافية مع دعم كامل للغة العربية.

## ✨ المميزات الرئيسية

### 🧠 الذكاء الاصطناعي
- **دعم مزودين متعددين**: OpenRouter و Google Gemini
- **نماذج قوية**: Claude, GPT-4, Gemini 2.0 Flash, Llama وغيرها
- **البث المباشر**: استقبال الرد كلمة كلمة للتجربة الأفضل
- **وضع التفكير**: تفكير عميق قبل الإجابة (Deep Thinking)

### 💾 إدارة البيانات
- **الذاكرة الذكية**: تذكر السياق من المحادثات السابقة
- **الملخصات التلقائية**: تلخيص المحادثات الطويلة
- **الكاش الذكي**: تخزين الإجابات المتكررة

### 🎨 الواجهة الأمامية
- **تصميم احترافي**: واجهة حديثة وسهلة الاستخدام
- **الوضع الليلي**: دعم كامل للوضع الليلي والنهاري
- **دعم العربية**: دعم كامل للغة العربية الفصحى
- **تجاوب كامل**: تصميم متجاوب على جميع الأجهزة

### 🔧 الميزات المتقدمة
- ✅ توليد الصور (قريباً)
- ✅ تحويل الصوت لنص
- ✅ تحويل النص لصوت
- ✅ رفع الملفات والصور
- ✅ فتح الكاميرا
- ✅ نظام الأوامر الذكية

## 🚀 البدء السريع

### المتطلبات
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Node.js 18+ (للواجهة الأمامية)

### التثبيت المحلي

#### 1. استنساخ المستودع
```bash
git clone https://github.com/sa885if/sa885if.ai.git
cd sa885if.ai
```

#### 2. إعداد البيئة
```bash
# نسخ ملف الإعدادات
cp .env.example .env

# تحرير .env وإضافة مفاتيح API الخاصة بك
nano .env
```

#### 3. تثبيت المكتبات
```bash
# تثبيت مكتبات Python
pip install -r requirements.txt

# تثبيت مكتبات Node.js (للواجهة الأمامية)
cd frontend
npm install
```

#### 4. تشغيل قاعدة البيانات والـ Redis
```bash
# استخدام Docker Compose
docker-compose up -d
```

#### 5. تشغيل التطبيق
```bash
# تشغيل الخادم
python main.py

# أو استخدام uvicorn مباشرة
uvicorn main:app --reload
```

الخادم سيكون متاحاً على: `http://localhost:8000`

### التشغيل باستخدام Docker

```bash
# بناء الصورة وتشغيل الحاويات
docker-compose up --build

# الوصول إلى الخادم
# http://localhost:8000
```

## 📚 الهيكل

```
sa885if.ai/
├── api/v1/                    # API Endpoints
│   ├── chat.py               # المحادثة
│   ├── sessions.py           # إدارة الجلسات
│   ├── images.py             # توليد الصور
│   ├── voice.py              # معالجة الصوت
│   ├── system.py             # إدارة النظام
│   └── health.py             # فحص الصحة
├── services/                  # Business Logic
│   ├── llm_service.py        # خدمة الذكاء الاصطناعي
│   ├── memory_manager.py     # إدارة الذاكرة
│   ├── image_gen_service.py  # توليد الصور
│   ├── voice_service.py      # معالجة الصوت
│   └── providers/            # مزودي الذكاء الاصطناعي
│       ├── base.py           # الفئة الأساسية
│       ├── openrouter.py     # OpenRouter
│       └── gemini.py         # Google Gemini
├── models/                    # نماذج قاعدة البيانات
│   └── chat.py               # نماذج المحادثة
├── repositories/             # طبقة الوصول للبيانات
│   └── chat_repo.py          # مستودع المحادثة
├── schemas/                  # Pydantic Schemas
├── config/                   # الإعدادات
├── cache/                    # إدارة الكاش
├── frontend/                 # الواجهة الأمامية (React)
└── main.py                   # نقطة البداية
```

## 🔑 مفاتيح API المطلوبة

### OpenRouter
1. اذهب إلى [openrouter.ai/keys](https://openrouter.ai/keys)
2. أنشئ مفتاح API جديد
3. أضفه إلى ملف `.env`

```env
OPENROUTER_API_KEY=sk-or-...
```

### Google Gemini
1. اذهب إلى [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. أنشئ مفتاح API جديد
3. أضفه إلى ملف `.env`

```env
GEMINI_API_KEY=AIzaSy...
```

## 📡 API Endpoints

### المحادثة
- `POST /api/v1/chat/stream` - بث المحادثة
- `POST /api/v1/chat/regenerate` - إعادة توليد الرد

### الجلسات
- `GET /api/v1/sessions/` - قائمة الجلسات
- `POST /api/v1/sessions/` - إنشاء جلسة جديدة
- `GET /api/v1/sessions/{session_id}` - الحصول على جلسة
- `PATCH /api/v1/sessions/{session_id}` - تحديث الجلسة
- `DELETE /api/v1/sessions/{session_id}` - حذف الجلسة

### الصور
- `POST /api/v1/images/generate` - توليد صورة
- `GET /api/v1/images/styles` - قائمة الأنماط

### الصوت
- `POST /api/v1/voice/transcribe` - تحويل الصوت لنص
- `POST /api/v1/voice/synthesize` - تحويل النص لصوت
- `GET /api/v1/voice/languages` - قائمة اللغات

### النظام
- `GET /api/v1/system/info` - معلومات النظام
- `GET /api/v1/system/config` - الإعدادات
- `POST /api/v1/system/switch-provider` - تبديل المزود
- `GET /api/v1/system/stats` - الإحصائيات

### الصحة
- `GET /api/v1/health/` - فحص صحة كامل
- `GET /api/v1/health/status` - حالة سريعة

## 🌐 النشر

### النشر على Render

1. **ربط المستودع**
   - اذهب إلى [render.com](https://render.com)
   - اختر "New Web Service"
   - ربط مستودع GitHub

2. **إعدادات البناء**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **متغيرات البيئة**
   - أضف جميع متغيرات `.env` في لوحة التحكم

4. **قاعدة البيانات**
   - أنشئ قاعدة بيانات PostgreSQL على Render
   - أضف رابط الاتصال إلى `DATABASE_URL`

5. **Redis**
   - أنشئ Redis على Render
   - أضف رابط الاتصال إلى `REDIS_URL`

## 📊 الإحصائيات والمراقبة

يمكنك الوصول إلى:
- `GET /docs` - Swagger UI (في وضع التطوير)
- `GET /redoc` - ReDoc (في وضع التطوير)
- `GET /api/v1/health/` - فحص صحة النظام

## 🔐 الأمان

- **Rate Limiting**: حد أقصى 30 طلب في الدقيقة
- **CORS**: معالجة آمنة للطلبات من نطاقات مختلفة
- **معالجة الأخطاء**: معالجة شاملة لجميع الأخطاء
- **التحقق من البيانات**: التحقق الصارم من جميع المدخلات

## 🐛 استكشاف الأخطاء

### خطأ الاتصال بـ PostgreSQL
```
ERROR: could not connect to server: Connection refused
```

**الحل**: تأكد من تشغيل PostgreSQL
```bash
docker-compose up -d postgres
```

### خطأ الاتصال بـ Redis
```
ERROR: Connection refused
```

**الحل**: تأكد من تشغيل Redis
```bash
docker-compose up -d redis
```

### خطأ مفتاح API
```
ERROR: Invalid API key
```

**الحل**: تحقق من صحة مفاتيح API في ملف `.env`

## 📝 الترخيص

هذا المشروع مرخص تحت [MIT License](LICENSE)

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:
1. Fork المستودع
2. أنشئ فرع جديد (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push إلى الفرع (`git push origin feature/amazing-feature`)
5. افتح Pull Request

## 📧 التواصل

- **البريد الإلكتروني**: support@saif.ai
- **Twitter**: [@saif_ai](https://twitter.com/saif_ai)
- **GitHub Issues**: [Report a bug](https://github.com/sa885if/sa885if.ai/issues)

---

**صُنع بـ ❤️ من قبل فريق SAIF.AI**
