# cache/redis_client.py
import hashlib
import json
from typing import Optional, Any
import redis.asyncio as redis
from config.settings import settings


class RedisCache:
    """
    مدير التخزين المؤقت Redis.
    يوفر دوال للتخزين والاسترجاع والحذف مع دعم TTL.
    """
    
    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def connect(self):
        """اختبار الاتصال بـ Redis"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def close(self):
        """إغلاق الاتصال"""
        await self.redis.close()
    
    # ═══════════════════════════════════════════
    # دوال التخزين والاسترجاع الأساسية
    # ═══════════════════════════════════════════
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        تخزين قيمة مع مفتاح.
        
        Args:
            key: المفتاح
            value: القيمة (يتم تحويلها لـ JSON تلقائياً)
            ttl: وقت الصلاحية بالثواني (اختياري، الافتراضي من الإعدادات)
        
        Returns:
            True إذا تم التخزين بنجاح
        """
        try:
            ttl = ttl or settings.CACHE_TTL
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception:
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        استرجاع قيمة بمفتاح.
        
        Args:
            key: المفتاح
        
        Returns:
            القيمة المخزنة أو None
        """
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None
    
    async def delete(self, key: str) -> bool:
        """
        حذف مفتاح من الكاش.
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """
        التحقق من وجود مفتاح.
        """
        try:
            return await self.redis.exists(key) > 0
        except Exception:
            return False
    
    # ═══════════════════════════════════════════
    # دوال متخصصة للمنصة
    # ═══════════════════════════════════════════
    
    def generate_chat_cache_key(
        self,
        session_id: str,
        message: str,
        persona: str,
        model: str
    ) -> str:
        """
        توليد مفتاح كاش فريد للمحادثة.
        
        Args:
            session_id: معرف الجلسة
            message: نص الرسالة
            persona: الشخصية المستخدمة
            model: اسم النموذج
        
        Returns:
            مفتاح SHA256 فريد
        """
        raw = f"{session_id}:{model}:{persona}:{message}"
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        return f"chat:{hashed}"
    
    async def get_cached_response(self, session_id: str, message: str, persona: str, model: str) -> Optional[str]:
        """
        محاولة جلب رد مخزن مسبقاً لنفس السؤال.
        """
        key = self.generate_chat_cache_key(session_id, message, persona, model)
        return await self.get(key)
    
    async def cache_response(self, session_id: str, message: str, persona: str, model: str, response: str) -> bool:
        """
        تخزين رد في الكاش للاستخدام المستقبلي.
        """
        key = self.generate_chat_cache_key(session_id, message, persona, model)
        return await self.set(key, response)
    
    async def cache_session_data(self, session_id: str, data: dict, ttl: int = 300) -> bool:
        """
        تخزين بيانات جلسة مؤقتة (5 دقائق افتراضياً).
        """
        key = f"session:{session_id}"
        return await self.set(key, data, ttl)
    
    async def get_session_data(self, session_id: str) -> Optional[dict]:
        """
        استرجاع بيانات جلسة مخزنة.
        """
        key = f"session:{session_id}"
        return await self.get(key)
    
    # ═══════════════════════════════════════════
    # دوال Rate Limiting
    # ═══════════════════════════════════════════
    
    async def check_rate_limit(self, user_id: str, limit: int = None) -> tuple[bool, int]:
        """
        فحص عدد الطلبات المتبقية للمستخدم.
        
        Args:
            user_id: معرف المستخدم
            limit: الحد الأقصى للطلبات في الدقيقة (افتراضي من الإعدادات)
        
        Returns:
            (مسموح, الطلبات المتبقية)
        """
        limit = limit or settings.RATE_LIMIT_PER_MINUTE
        key = f"rate:{user_id}"
        
        try:
            current = await self.redis.get(key)
            if current is None:
                # أول طلب في الدقيقة
                await self.redis.setex(key, 60, 1)
                return True, limit - 1
            
            current = int(current)
            if current >= limit:
                return False, 0
            
            remaining = limit - current - 1
            await self.redis.incr(key)
            return True, remaining
            
        except Exception:
            # لو Redis واقع، نسمح بالطلب عشان المنصة تفضل شغالة
            return True, limit
    
    # ═══════════════════════════════════════════
    # دوال إحصائية
    # ═══════════════════════════════════════════
    
    async def increment_counter(self, counter_name: str) -> int:
        """
        زيادة عداد معين (مثلاً: عدد الرسائل اليومية).
        """
        try:
            return await self.redis.incr(f"stats:{counter_name}")
        except Exception:
            return 0
    
    async def get_counter(self, counter_name: str) -> int:
        """
        قراءة قيمة عداد.
        """
        try:
            value = await self.redis.get(f"stats:{counter_name}")
            return int(value) if value else 0
        except Exception:
            return 0


# نسخة واحدة من الكاش يتم استيرادها في أي مكان
redis_cache = RedisCache()