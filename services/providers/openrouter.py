# services/providers/openrouter.py
"""
مزود OpenRouter - يوفر وصول لمئات النماذج الذكية من مختلف الشركات.
يدعم البث والتوليد العادي.
"""

import httpx
import logging
from typing import AsyncGenerator, List, Dict, Optional
from config.settings import settings
from services.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseProvider):
    """
    مزود OpenRouter - يدعم نماذج متعددة مثل:
    - Claude (Anthropic)
    - GPT-4 (OpenAI)
    - Gemini (Google)
    - Llama (Meta)
    - وغيرها...
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.default_model = settings.OPENROUTER_DEFAULT_MODEL
        
        if not self.api_key:
            logger.warning("⚠️ OpenRouter API Key not configured. Chat will not work.")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        بث الرد من OpenRouter كلمة كلمة.
        """
        model = model or self.default_model
        
        if not self.api_key:
            yield "❌ خطأ: لم يتم تكوين مفتاح OpenRouter API"
            return
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://saif.ai",
            "X-Title": "SAIF.AI",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.atext()
                        logger.error(f"OpenRouter Error {response.status_code}: {error_text}")
                        yield f"❌ خطأ من OpenRouter: {response.status_code}"
                        return
                    
                    async for line in response.aiter_lines():
                        if not line or line.startswith(":"):
                            continue
                        
                        if line.startswith("data: "):
                            data = line[6:]
                            
                            if data == "[DONE]":
                                break
                            
                            try:
                                import json
                                chunk = json.loads(data)
                                
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    
                                    if content:
                                        yield content
                            
                            except json.JSONDecodeError:
                                continue
        
        except httpx.TimeoutException:
            logger.error("OpenRouter request timeout")
            yield "❌ انتهت مهلة الانتظار. يرجى المحاولة مرة أخرى."
        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            yield f"❌ خطأ في البث: {str(e)}"
    
    async def generate_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        توليد رد كامل من OpenRouter بدون بث.
        """
        model = model or self.default_model
        
        if not self.api_key:
            return "❌ خطأ: لم يتم تكوين مفتاح OpenRouter API"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://saif.ai",
            "X-Title": "SAIF.AI",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"OpenRouter Error {response.status_code}: {error_text}")
                    return f"❌ خطأ من OpenRouter: {response.status_code}"
                
                import json
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                
                return "❌ لم يتم الحصول على رد من OpenRouter"
        
        except httpx.TimeoutException:
            logger.error("OpenRouter request timeout")
            return "❌ انتهت مهلة الانتظار. يرجى المحاولة مرة أخرى."
        except Exception as e:
            logger.error(f"OpenRouter generation error: {e}")
            return f"❌ خطأ في التوليد: {str(e)}"
    
    async def validate_connection(self) -> bool:
        """
        التحقق من اتصال OpenRouter بنجاح.
        """
        if not self.api_key:
            logger.warning("OpenRouter API Key not configured")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://saif.ai",
                "X-Title": "SAIF.AI"
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.BASE_URL}/models",
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info("✅ OpenRouter connection validated")
                    return True
                else:
                    logger.warning(f"OpenRouter validation failed: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"OpenRouter validation error: {e}")
            return False
