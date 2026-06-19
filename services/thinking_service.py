# services/thinking_service.py
from typing import AsyncGenerator, Dict, List, Optional
from services.llm_service import LLMService
from config.settings import settings


class ThinkingService:
    """
    خدمة وضع التفكير العميق.
    تستخرج خطوات استدلال الـ AI بشكل منفصل عن الرد النهائي.
    
    طريقة العمل:
    1. يُرسل سؤال المستخدم لنموذج "مفكر" يولد خطوات الاستدلال
    2. تُرسل خطوات الاستدلال + السؤال الأصلي للنموذج الرئيسي
    3. يصل الرد النهائي مع خطوات التفكير للمستخدم
    """
    
    def __init__(self, llm_service: LLMService = None):
        self.llm = llm_service or LLMService()
        # نموذج التفكير - يفضل نموذج قوي في الاستدلال
        self.thinking_model = "google/gemini-2.0-flash-thinking-exp:free"  # OpenRouter
        
    async def think(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        persona: str = None
    ) -> str:
        """
        توليد خطوات التفكير فقط (بدون الرد النهائي).
        
        Args:
            user_message: سؤال المستخدم
            conversation_history: تاريخ المحادثة للسياق
            persona: الشخصية المستخدمة
            
        Returns:
            نص خطوات التفكير
        """
        persona = persona or settings.DEFAULT_PERSONA
        
        thinking_prompt = self._build_thinking_prompt(
            user_message,
            conversation_history,
            persona
        )
        
        try:
            # استخدام نموذج متخصص في التفكير
            thinking_steps = await self.llm.generate_async(
                messages=thinking_prompt,
                model=self.thinking_model,
                temperature=0.3,  # حرارة منخفضة للدقة
                max_tokens=1000
            )
            return thinking_steps
            
        except Exception as e:
            # إذا فشل نموذج التفكير، نستخدم نموذج عادي
            thinking_steps = await self.llm.generate_async(
                messages=thinking_prompt,
                temperature=0.3,
                max_tokens=800
            )
            return thinking_steps
    
    async def stream_with_thinking(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        persona: str = None
    ) -> AsyncGenerator[Dict[str, str], None]:
        """
        بث الرد مع خطوات التفكير أولاً.
        
        Yields:
            Dict يحتوي على:
            - type: "thinking" أو "content" أو "done"
            - data: النص
        """
        # 1. بث خطوات التفكير
        thinking_text = await self.think(user_message, conversation_history, persona)
        
        if thinking_text:
            yield {
                "type": "thinking_start",
                "data": "🧠 بدء عملية التفكير..."
            }
            
            # بث خطوات التفكير كلمة كلمة
            for word in thinking_text.split():
                yield {
                    "type": "thinking",
                    "data": word + " "
                }
            
            yield {
                "type": "thinking_end",
                "data": "\n✅ انتهى التفكير، جاري صياغة الرد..."
            }
        
        # 2. بناء الـ Prompt النهائي مع خطوات التفكير
        final_prompt = self._build_final_prompt(
            user_message,
            conversation_history,
            persona,
            thinking_text
        )
        
        # 3. بث الرد النهائي
        full_response = ""
        async for token in self.llm.stream_response(final_prompt):
            full_response += token
            yield {
                "type": "content",
                "data": token
            }
        
        yield {
            "type": "done",
            "data": "",
            "full_response": full_response,
            "thinking": thinking_text
        }
    
    def _build_thinking_prompt(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        persona: str = None
    ) -> List[Dict[str, str]]:
        """
        بناء الـ Prompt الخاص باستخراج خطوات التفكير.
        """
        persona = persona or settings.DEFAULT_PERSONA
        
        system_prompt = f"""{persona}

أنت الآن في "وضع التفكير العميق". مهمتك هي تحليل سؤال المستخدم وتوضيح خطوات استدلالك قبل الإجابة.

قم بما يلي:
1. 🎯 فهم السؤال: أعد صياغة سؤال المستخدم لتتأكد من فهمه
2. 🔍 تحليل المعطيات: حدد المعلومات المتاحة والمفقودة
3. 🧩 تقسيم المشكلة: قسم السؤال لأجزاء صغيرة
4. 💭 الاستدلال: فكر في كل جزء خطوة بخطوة
5. 📊 تقييم الخيارات: إذا تعددت الإجابات المحتملة، قارن بينها
6. ✅ الاستنتاج: استنتج الإجابة但不 تكتبها

⚠️ هام: لا تكتب الإجابة النهائية. فقط خطوات التفكير والتحليل.

استخدم تنسيقاً جميلاً مع إيموجي وتنسيق Markdown."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # إضافة تاريخ المحادثة للسياق
        if conversation_history:
            messages.extend(conversation_history[-6:])  # آخر 6 رسائل
        
        messages.append({"role": "user", "content": f"السؤال الذي يحتاج تفكيراً عميقاً:\n{user_message}"})
        
        return messages
    
    def _build_final_prompt(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        persona: str = None,
        thinking_steps: str = ""
    ) -> List[Dict[str, str]]:
        """
        بناء الـ Prompt النهائي مع تضمين خطوات التفكير.
        """
        persona = persona or settings.DEFAULT_PERSONA
        
        system_prompt = f"""{persona}

لقد قمت بعملية تفكير عميق للسؤال التالي. هذه هي خطوات التفكير التي توصلت إليها:

---
{thinking_steps}
---

الآن، استخدم خطوات التفكير أعلاه لتقديم إجابة شاملة ودقيقة ومنظمة.
قدم إجابة مفيدة ومباشرة، مع الاستفادة من التحليل الذي قمت به."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # إضافة تاريخ المحادثة
        if conversation_history:
            messages.extend(conversation_history[-6:])
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    # ═══════════════════════════════════════════
    # أوضاع تفكير مختلفة
    # ═══════════════════════════════════════════
    
    async def chain_of_thought(
        self,
        user_message: str,
        steps: int = 3
    ) -> List[str]:
        """
        تفكير متسلسل: كل خطوة تبني على السابقة.
        """
        chain = []
        current_prompt = user_message
        
        for i in range(steps):
            messages = [
                {"role": "system", "content": f"أنت في خطوة التفكير {i+1} من {steps}. حلل الجزء التالي من المشكلة:"},
                {"role": "user", "content": current_prompt}
            ]
            step_result = await self.llm.generate_async(messages, temperature=0.3)
            chain.append(step_result)
            current_prompt = f"{user_message}\n\nالتحليل السابق:\n{step_result}\n\nما هي الخطوة التالية؟"
        
        return chain
    
    async def self_reflection(
        self,
        user_message: str,
        initial_answer: str
    ) -> Dict[str, str]:
        """
        مراجعة ذاتية: يفحص الـ AI إجابته ويحسنها.
        """
        # فحص الإجابة
        reflection_prompt = [
            {"role": "system", "content": "راجع الإجابة التالية. هل هي دقيقة؟ كاملة؟ واضحة؟ ما الذي يمكن تحسينه؟"},
            {"role": "user", "content": f"السؤال: {user_message}\n\nالإجابة:\n{initial_answer}"}
        ]
        reflection = await self.llm.generate_async(reflection_prompt, temperature=0.2)
        
        # تحسين الإجابة بناءً على المراجعة
        improvement_prompt = [
            {"role": "system", "content": "حسن الإجابة التالية بناءً على ملاحظات المراجعة."},
            {"role": "user", "content": f"السؤال: {user_message}\n\nالإجابة الأصلية:\n{initial_answer}\n\nملاحظات المراجعة:\n{reflection}\n\nقدم الإجابة المحسنة:"}
        ]
        improved_answer = await self.llm.generate_async(improvement_prompt, temperature=0.5)
        
        return {
            "original": initial_answer,
            "reflection": reflection,
            "improved": improved_answer
        }


# نسخة واحدة من الخدمة
thinking_service = ThinkingService()