# services/llm_service.py
import hashlib
from typing import AsyncGenerator, List, Dict, Optional, Any
from config.settings import settings
from cache.redis_client import redis_cache
from services.providers.base import BaseProvider
from services.providers.openrouter import OpenRouterProvider
from services.providers.gemini import GeminiProvider


class LLMService:
    """
    طبقة التنسيق المركزية للذكاء الاصطناعي.
    تتعامل مع اختيار المزود، الكاش، البث، وإدارة السياق.
    """
    
    def __init__(self):
        self.provider = self._init_provider()
    
    def _init_provider(self) -> BaseProvider:
        """
        تهيئة المزود النشط بناءً على ACTIVE_PROVIDER في الإعدادات.
        """
        if settings.ACTIVE_PROVIDER == "gemini":
            return GeminiProvider()
        else:
            # الافتراضي OpenRouter (يدعم موديلات متعددة ومجانية)
            return OpenRouterProvider()
    
    def switch_provider(self, provider_name: str):
        """
        تبديل المزود في وقت التشغيل.
        """
        if provider_name == "gemini":
            self.provider = GeminiProvider()
        else:
            self.provider = OpenRouterProvider()
    
    # ═══════════════════════════════════════════
    # البث المباشر (Streaming)
    # ═══════════════════════════════════════════
    
    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        use_cache: bool = True,
        cache_context: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        بث الرد كلمة كلمة من النموذج.
        
        Args:
            messages: قائمة الرسائل الكاملة (مع system prompt)
            model: اسم النموذج (اختياري، يُستخدم الافتراضي إن لم يُحدد)
            use_cache: هل نبحث في الكاش أولاً؟
            cache_context: بيانات إضافية لتوليد مفتاح الكاش
        Yields:
            قطع نصية من الرد
        """
        # 1. محاولة استرجاع رد مخزن
        if use_cache and cache_context:
            cached = await self._get_cached_response(messages, cache_context)
            if cached:
                # بث الرد المخزن كقطعة واحدة (أو محاكاة بث سريع)
                yield cached
                return
        
        # 2. اختيار النموذج المناسب
        model = model or settings.OPENROUTER_DEFAULT_MODEL
        
        # 3. بث الرد من المزود
        full_response = ""
        async for token in self.provider.stream_chat(messages, model=model):
            full_response += token
            yield token
        
        # 4. تخزين الرد في الكاش للمستقبل
        if use_cache and cache_context and full_response:
            await self._cache_response(messages, cache_context, full_response)
    
    # ═══════════════════════════════════════════
    # التوليد العادي (بدون بث)
    # ═══════════════════════════════════════════
    
    async def generate_async(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        توليد رد كامل بدون بث (للملخصات والعناوين وغيرها).
        
        Args:
            messages: قائمة الرسائل
            model: اسم النموذج
            temperature: حرارة الإبداع
            max_tokens: أقصى عدد رموز للرد
        Returns:
            الرد الكامل كنص واحد
        """
        model = model or settings.OPENROUTER_DEFAULT_MODEL
        return await self.provider.generate_sync(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def generate_json(self, prompt: str) -> str:
        """
        توليد رد بصيغة JSON (لاستخراج الحقائق وغيرها).
        """
        messages = [
            {"role": "system", "content": "أنت مساعد يخرج البيانات بصيغة JSON صالحة فقط، بدون أي نص آخر."},
            {"role": "user", "content": prompt}
        ]
        response = await self.generate_async(messages, temperature=0.2)
        # محاولة تنظيف الرد إذا كان محاطاً بـ ```json
        return response.strip().removeprefix("```json").removesuffix("```").strip()
    
    # ═══════════════════════════════════════════
    # الكاش الذكي
    # ═══════════════════════════════════════════
    
    def _generate_cache_key(
        self,
        messages: List[Dict[str, str]],
        context: Dict[str, str]
    ) -> str:
        """
        توليد مفتاح كاش فريد يعتمد على:
        - الرسائل الأخيرة (آخر رسالة user + assistant)
        - الشخصية
        - النموذج
        - ملخص الجلسة
        """
        # نبني نصاً يمثل السياق
        last_user_msg = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break
        
        raw = (
            f"session:{context.get('session_id', '')}"
            f"|model:{context.get('model', '')}"
            f"|persona:{context.get('persona', '')}"
            f"|summary:{context.get('summary_version', '')}"
            f"|msg:{last_user_msg}"
        )
        return f"llm_cache:{hashlib.sha256(raw.encode()).hexdigest()}"
    
    async def _get_cached_response(
        self,
        messages: List[Dict[str, str]],
        context: Dict[str, str]
    ) -> Optional[str]:
        """
        محاولة جلب رد مخزن من Redis.
        """
        key = self._generate_cache_key(messages, context)
        try:
            return await redis_cache.get(key)
        except Exception:
            return None
    
    async def _cache_response(
        self,
        messages: List[Dict[str, str]],
        context: Dict[str, str],
        response: str
    ) -> bool:
        """
        تخزين الرد في Redis مع مدة صلاحية.
        """
        key = self._generate_cache_key(messages, context)
        try:
            return await redis_cache.set(key, response, ttl=settings.CACHE_TTL)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════
    # دوال مساعدة
    # ═══════════════════════════════════════════
    
    async def generate_title(self, first_message: str, response: str) -> str:
        """
        توليد عنوان ذكي للمحادثة بناءً على أول رسالة وردها.
        """
        messages = [
            {"role": "system", "content": "أنت مساعد يولد عناوين قصيرة وجذابة للمحادثات بالعربية. أعط العنوان فقط بدون أي نص آخر."},
            {"role": "user", "content": f"اقترح عنواناً قصيراً (أقل من 7 كلمات) لمحادثة تبدأ بهذه الرسالة:\nالمستخدم: {first_message}\nالمساعد: {response[:200]}"}
        ]
        title = await self.generate_async(messages, max_tokens=50)
        return title.strip().strip('"').strip("'") or "محادثة جديدة"
    
    async def generate_summary(self, conversation: List[Dict[str, str]]) -> str:
        """
        توليد ملخص لمحادثة كاملة (يُستخدم في MemoryManager).
        """
        messages = [
            {"role": "system", "content": "لخص المحادثة التالية بتركيز على النقاط المهمة والحقائق المذكورة. استخدم العربية الفصحى المختصرة."},
            *conversation,
            {"role": "user", "content": "من فضلك لخص هذه المحادثة."}
        ]
        return await self.generate_async(messages, max_tokens=500)


# نسخة واحدة من الخدمة تُستورد في أي مكان
llm_service = LLMService()