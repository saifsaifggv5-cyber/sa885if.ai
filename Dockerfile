# استخدام صورة Python الرسمية
FROM python:3.11-slim

# تعيين مجلد العمل
WORKDIR /app

# تثبيت المكتبات النظامية المطلوبة
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف requirements.txt
COPY requirements.txt .

# تثبيت المكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إنشاء مجلد التخزين
RUN mkdir -p storage/uploads

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# تشغيل التطبيق
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
