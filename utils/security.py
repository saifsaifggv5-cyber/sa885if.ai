# utils/security.py
import hashlib
import hmac
import secrets
import time
import re
from typing import Tuple, Optional, List
from datetime import datetime, timedelta
from config.settings import settings


class SecurityManager:
    """
    مدير الأمان - فحص الطلبات، تنظيف المدخلات، التشفير.
    """

    # ── إعدادات Rate Limiting ──────────────
    _rate_limit_store: dict = {}  # {key: [timestamps]}

    # ── أنماط خطيرة ────────────────────────
    DANGEROUS_PATTERNS = [
        r'(?:<script.*?>.*?</script>)',           # XSS
        r'(?:javascript\s*:)',                     # javascript: URLs
        r'(?:on\w+\s*=\s*["\'].*?["\'])',        # event handlers
        r'(?:DROP\s+TABLE|DELETE\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET)',  # SQL Injection
        r'(?:UNION\s+SELECT|SELECT\s+.*?\s+FROM)',  # SQL Injection
        r'(?:\.\./|\.\.\\)',                       # Path Traversal
        r'(?:/etc/passwd|/bin/bash|cmd\.exe)',     # System files
        r'(?:\$\{.*?\}|\{\{.*?\}\})',              # Template Injection
    ]

    # ═══════════════════════════════════════════
    # Rate Limiting
    # ═══════════════════════════════════════════

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = None,
        window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        فحص إذا كان الطلب مسموحاً به.
        
        Args:
            identifier: معرف المستخدم أو IP
            max_requests: أقصى عدد طلبات في النافذة الزمنية
            window_seconds: مدة النافذة الزمنية بالثواني
            
        Returns:
            (مسموح, عدد الطلبات الحالي, الطلبات المتبقية)
        """
        max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        now = time.time()
        window_start = now - window_seconds

        # تنظيف السجلات القديمة
        if identifier not in self._rate_limit_store:
            self._rate_limit_store[identifier] = []

        # إزالة الطوابع القديمة
        self._rate_limit_store[identifier] = [
            ts for ts in self._rate_limit_store[identifier]
            if ts > window_start
        ]

        current_count = len(self._rate_limit_store[identifier])

        if current_count >= max_requests:
            return False, current_count, 0

        # إضافة الطلب الحالي
        self._rate_limit_store[identifier].append(now)
        remaining = max_requests - current_count - 1
        return True, current_count + 1, remaining

    def get_rate_limit_info(self, identifier: str) -> dict:
        """
        معلومات عن حالة Rate Limit لمستخدم.
        """
        if identifier not in self._rate_limit_store:
            return {
                "current": 0,
                "limit": settings.RATE_LIMIT_PER_MINUTE,
                "remaining": settings.RATE_LIMIT_PER_MINUTE,
                "reset_in": 0
            }

        now = time.time()
        recent = [ts for ts in self._rate_limit_store[identifier] if ts > now - 60]
        remaining = max(0, settings.RATE_LIMIT_PER_MINUTE - len(recent))

        return {
            "current": len(recent),
            "limit": settings.RATE_LIMIT_PER_MINUTE,
            "remaining": remaining,
            "reset_in": 60 - (now - recent[0]) if recent else 0
        }

    def clear_rate_limit(self, identifier: str):
        """مسح سجلات Rate Limit لمستخدم."""
        if identifier in self._rate_limit_store:
            del self._rate_limit_store[identifier]

    # ═══════════════════════════════════════════
    # التحقق من المدخلات
    # ═══════════════════════════════════════════

    def sanitize_input(self, text: str, max_length: int = 8000) -> str:
        """
        تنظيف النص المدخل من محتوى خطير.
        
        Args:
            text: النص المدخل
            max_length: أقصى طول مسموح
            
        Returns:
            النص النظيف
        """
        if not text:
            return ""

        # قص النص للحد الأقصى
        text = text[:max_length]

        # إزالة أحرف التحكم (ما عدا الأسطر الجديدة)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        # إزالة أنماط HTML خطيرة
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript\s*:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', text, flags=re.IGNORECASE)

        return text.strip()

    def is_dangerous(self, text: str) -> bool:
        """
        فحص إذا كان النص يحتوي على أنماط خطيرة.
        """
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def validate_email(self, email: str) -> bool:
        """
        التحقق من صحة بريد إلكتروني.
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate_phone(self, phone: str) -> bool:
        """
        التحقق من صحة رقم هاتف (مصري/دولي).
        """
        pattern = r'^(\+?2?0?1[0125]\d{8}|\+?\d{10,15})$'
        return bool(re.match(pattern, phone.strip().replace(' ', '')))

    # ═══════════════════════════════════════════
    # التشفير والتجزئة
    # ═══════════════════════════════════════════

    def hash_text(self, text: str, algorithm: str = "sha256") -> str:
        """
        تجزئة نص (تشفير باتجاه واحد).
        """
        if algorithm == "sha256":
            return hashlib.sha256(text.encode()).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(text.encode()).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(text.encode()).hexdigest()
        else:
            return hashlib.sha256(text.encode()).hexdigest()

    def hash_ip(self, ip: str) -> str:
        """
        تشفير عنوان IP للحفاظ على الخصوصية.
        """
        return hashlib.sha256(f"saif_ai_salt_{ip}".encode()).hexdigest()[:16]

    def generate_token(self, length: int = 32) -> str:
        """
        توليد رمز عشوائي آمن.
        """
        return secrets.token_urlsafe(length)

    def generate_api_key(self, prefix: str = "saif") -> str:
        """
        توليد مفتاح API.
        مثال: saif_a1b2c3d4e5f6...
        """
        random_part = secrets.token_hex(24)
        return f"{prefix}_{random_part}"

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        التحقق من توقيع HMAC.
        """
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def create_signature(self, payload: str, secret: str) -> str:
        """
        إنشاء توقيع HMAC.
        """
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    # ═══════════════════════════════════════════
    # حماية API
    # ═══════════════════════════════════════════

    def validate_api_key(self, api_key: str) -> bool:
        """
        التحقق من صحة مفتاح API.
        """
        if not api_key:
            return False
        # التحقق من المفاتيح المخزنة (يمكن استخدام قاعدة بيانات)
        valid_keys = [
            settings.OPENROUTER_API_KEY,
            settings.GEMINI_API_KEY,
            settings.OPENAI_API_KEY,
        ]
        return api_key in [k for k in valid_keys if k]

    def mask_api_key(self, api_key: str, visible: int = 8) -> str:
        """
        إخفاء جزء من مفتاح API للأمان.
        مثال: sk-or-v1-abcd...xyz
        """
        if not api_key or len(api_key) <= visible:
            return "*" * len(api_key) if api_key else ""
        return api_key[:visible] + "..." + api_key[-4:]

    # ═══════════════════════════════════════════
    # كلمات مرور
    # ═══════════════════════════════════════════

    def check_password_strength(self, password: str) -> Tuple[bool, str, int]:
        """
        فحص قوة كلمة المرور.
        
        Returns:
            (قوية, رسالة, درجة 0-100)
        """
        score = 0
        messages = []

        if len(password) < 8:
            messages.append("كلمة المرور قصيرة (أقل من 8 أحرف)")
        else:
            score += 20

        if re.search(r'[A-Z]', password):
            score += 15
        else:
            messages.append("أضف حرفاً كبيراً (A-Z)")

        if re.search(r'[a-z]', password):
            score += 15
        else:
            messages.append("أضف حرفاً صغيراً (a-z)")

        if re.search(r'\d', password):
            score += 20
        else:
            messages.append("أضف رقماً (0-9)")

        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 30
        else:
            messages.append("أضف رمزاً خاصاً (!@#$...)")

        is_strong = score >= 70
        message = "كلمة المرور قوية ✓" if is_strong else "؛ ".join(messages)

        return is_strong, message, score

    # ═══════════════════════════════════════════
    # تنظيف البيانات الحساسة
    # ═══════════════════════════════════════════

    def redact_sensitive_data(self, text: str) -> str:
        """
        إخفاء البيانات الحساسة في النص.
        - أرقام بطاقات ائتمان
        - أرقام هواتف
        - إيميلات
        - مفاتيح API
        """
        # بطاقات ائتمان
        text = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CREDIT_CARD]', text)

        # أرقام هواتف مصرية
        text = re.sub(r'01[0125]\d{8}', '[PHONE]', text)

        # إيميلات
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)

        # مفاتيح API
        text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[API_KEY]', text)
        text = re.sub(r'AIza[0-9A-Za-z\-_]{35}', '[GOOGLE_KEY]', text)

        return text

    # ═══════════════════════════════════════════
    # سجلات الأمان
    # ═══════════════════════════════════════════

    def log_security_event(self, event_type: str, details: str, ip: str = None):
        """
        تسجيل حدث أمني.
        """
        timestamp = datetime.utcnow().isoformat()
        hashed_ip = self.hash_ip(ip) if ip else "unknown"

        log_entry = f"[{timestamp}] [{event_type}] IP:{hashed_ip} | {details}\n"

        # في الإنتاج: يُكتب في ملف أو يُرسل لنظام مراقبة
        print(f"🔒 {log_entry.strip()}")

    def detect_suspicious_activity(self, identifier: str, request_count: int) -> bool:
        """
        اكتشاف نشاط مشبوه بناءً على عدد الطلبات.
        """
        SUSPICIOUS_THRESHOLD = 100  # طلب في الدقيقة

        if request_count > SUSPICIOUS_THRESHOLD:
            self.log_security_event(
                "SUSPICIOUS_ACTIVITY",
                f"معدل طلبات مرتفع: {request_count} طلب/دقيقة",
                identifier
            )
            return True
        return False


# نسخة واحدة من مدير الأمان
security = SecurityManager()