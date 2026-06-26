# services/providers/gemini.py
"""
مزود Google Gemini - نموذج ذكي قوي من Google.
يدعم البث والتوليد العادي.
"""

import logging
from typing import AsyncGenerator, List, Dict, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from config.settings import settings
from services.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """
    مزود Google Gemini - نموذج ذكي متقدم.
    يدعم البث والتوليد العادي والرؤية.
    """
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.default_model = settings.GEMINI_DEFAULT_MODEL
        
        if not GEMINI_AVAILABLE:
            logger.warning("⚠️ google-generativeai not installed. Install with: pip install google-generativeai")
        
        if not self.api_key:
            logger.warning("⚠️ Gemini API Key not configured. Chat will not work.")
        else:
            try:
                genai.configure(api_key=self.api_key)
                logger.info("✅ Gemini API configured successfully")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini: {e}")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        بث الرد من Gemini كلمة كلمة.
        """
        if not GEMINI_AVAILABLE:
            yield "❌ مكتبة Gemini غير مثبتة"
            return
        
        if not self.api_key:
            yield "❌ خطأ: لم يتم تكوين مفتاح Gemini API"
            return
        
        model = model or self.default_model
        
        try:
            # تحويل الرسائل إلى صيغة Gemini
            gemini_messages = self._convert_messages(messages)
            
            # إنشاء النموذج
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    **kwargs
                )
            )
            
            # بث الرد
            response = gemini_model.generate_content(
                gemini_messages,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield f"❌ خطأ في البث من Gemini: {str(e)}"
    
    async def generate_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        توليد رد كامل من Gemini بدون بث.
        """
        if not GEMINI_AVAILABLE:
            return "❌ مكتبة Gemini غير مثبتة"
        
        if not self.api_key:
            return "❌ خطأ: لم يتم تكوين مفتاح Gemini API"
        
        model = model or self.default_model
        
        try:
            # تحويل الرسائل إلى صيغة Gemini
            gemini_messages = self._convert_messages(messages)
            
            # إنشاء النموذج
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    **kwargs
                )
            )
            
            # توليد الرد
            response = gemini_model.generate_content(gemini_messages)
            
            return response.text if response.text else "❌ لم يتم الحصول على رد من Gemini"
        
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return f"❌ خطأ في التوليد من Gemini: {str(e)}"
    
    async def validate_connection(self) -> bool:
        """
        التحقق من اتصال Gemini بنجاح.
        """
        if not GEMINI_AVAILABLE:
            logger.warning("google-generativeai not installed")
            return False
        
        if not self.api_key:
            logger.warning("Gemini API Key not configured")
            return False
        
        try:
            genai.configure(api_key=self.api_key)
            
            # محاولة توليد رد بسيط
            model = genai.GenerativeModel(self.default_model)
            response = model.generate_content("مرحبا")
            
            if response.text:
                logger.info("✅ Gemini connection validated")
                return True
            else:
                logger.warning("Gemini validation failed: no response")
                return False
        
        except Exception as e:
            logger.error(f"Gemini validation error: {e}")
            return False
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """
        تحويل صيغة الرسائل من OpenAI إلى صيغة Gemini.
        """
        gemini_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Gemini يستخدم "user" و "model" بدلاً من "user" و "assistant"
            if role == "assistant":
                role = "model"
            elif role == "system":
                # دمج system messages مع أول رسالة user
                if gemini_messages:
                    gemini_messages[-1]["parts"][0] = content + "\n\n" + gemini_messages[-1]["parts"][0]
                    continue
                else:
                    role = "user"
            
            gemini_messages.append({
                "role": role,
                "parts": [content]
            })
        
        return gemini_messages
