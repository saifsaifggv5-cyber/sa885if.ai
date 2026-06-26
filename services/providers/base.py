# services/providers/base.py
"""
الفئة الأساسية لجميع مزودي الذكاء الاصطناعي.
تحدد الواجهة التي يجب أن يتبعها كل مزود.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Optional


class BaseProvider(ABC):
    """
    الفئة الأساسية المجردة لمزودي الذكاء الاصطناعي.
    كل مزود (OpenRouter, Gemini, إلخ) يرث من هذه الفئة.
    """
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        بث الرد كلمة كلمة من النموذج.
        
        Args:
            messages: قائمة الرسائل (مع system prompt)
            model: اسم النموذج
            temperature: حرارة الإبداع (0-1)
            max_tokens: أقصى عدد رموز للرد
            **kwargs: معاملات إضافية حسب المزود
        
        Yields:
            قطع نصية من الرد
        """
        pass
    
    @abstractmethod
    async def generate_sync(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        توليد رد كامل بدون بث.
        
        Args:
            messages: قائمة الرسائل
            model: اسم النموذج
            temperature: حرارة الإبداع
            max_tokens: أقصى عدد رموز للرد
            **kwargs: معاملات إضافية
        
        Returns:
            الرد الكامل كنص واحد
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        التحقق من اتصال المزود بنجاح.
        
        Returns:
            True إذا كان الاتصال سليماً
        """
        pass
