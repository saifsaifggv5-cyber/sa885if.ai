# services/memory_manager.py
from typing import List, Dict, Optional
from repositories.chat_repo import ChatRepository
from config.settings import settings


class MemoryManager:
    """
    مدير الذاكرة الهجينة للمنصة.
    
    يتكون من:
    1. Short Memory: آخر N رسالة من قاعدة البيانات
    2. Summary Memory: ملخص المحادثة (يُحدث كل فترة)
    
    يتم دمجهم لبناء سياق متكامل يُرسل للنموذج.
    """
    
    def __init__(self, chat_repo: ChatRepository, llm_service=None):
        self.repo = chat_repo
        self.llm = llm_service  # يُحقن لاحقاً لتوليد الملخصات
        self.SHORT_MEMORY_SIZE = settings.SHORT_MEMORY_SIZE  # 20
        self.SUMMARY_TRIGGER = settings.SUMMARY_TRIGGER      # 15
    
    # ═══════════════════════════════════════════
    # بناء السياق
    # ═══════════════════════════════════════════
    
    async def build_context(
        self,
        session_id: str,
        new_message: str,
        persona: str = None
    ) -> List[Dict[str, str]]:
        """
        بناء السياق الكامل لإرساله للنموذج.
        
        الترتيب:
        1. رسالة النظام (System Prompt) = الشخصية + ملخص المحادثة
        2. آخر N رسالة (Short Memory)
        3. الرسالة الجديدة من المستخدم
        
        Args:
            session_id: معرف الجلسة
            new_message: الرسالة الجديدة
            persona: نص الشخصية (اختياري)
            
        Returns:
            قائمة رسائل جاهزة للإرسال للمزود
        """
        context = []
        
        # 1. بناء System Prompt
        system_content = self._build_system_prompt(session_id, persona)
        if system_content:
            context.append({"role": "system", "content": system_content})
        
        # 2. إضافة الذاكرة القصيرة (آخر الرسائل)
        short_memory = await self.repo.get_recent_messages(
            session_id,
            limit=self.SHORT_MEMORY_SIZE
        )
        for msg in short_memory:
            context.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 3. إضافة الرسالة الجديدة
        context.append({"role": "user", "content": new_message})
        
        return context
    
    async def _build_system_prompt(
        self,
        session_id: str,
        persona: str = None
    ) -> str:
        """
        بناء رسالة النظام من الشخصية + ملخص المحادثة.
        """
        parts = []
        
        # إضافة الشخصية
        persona = persona or settings.DEFAULT_PERSONA
        parts.append(persona)
        
        # إضافة ملخص المحادثة (إن وجد)
        summary = await self.repo.get_session_summary(session_id)
        if summary:
            parts.append(f"\n\n📋 ملخص المحادثة السابقة:\n{summary}")
            parts.append("\nاستخدم هذا الملخص لتتذكر سياق المحادثة ولا تكرر ما قيل سابقاً.")
        
        return "\n".join(parts)
    
    # ═══════════════════════════════════════════
    # إدارة الملخصات
    # ═══════════════════════════════════════════
    
    async def maybe_update_summary(self, session_id: str):
        """
        التحقق إذا كان الوقت قد حان لتحديث ملخص المحادثة.
        يتم استدعاؤها كـ Background Task بعد كل رد.
        """
        message_count = await self.repo.count_messages(session_id)
        
        # نحدث الملخص كل SUMMARY_TRIGGER رسالة
        if message_count > 0 and message_count % self.SUMMARY_TRIGGER == 0:
            await self._generate_and_save_summary(session_id)
    
    async def _generate_and_save_summary(self, session_id: str):
        """
        توليد ملخص جديد للمحادثة وحفظه.
        """
        if not self.llm:
            return  # لا يمكن التوليد بدون LLM Service
        
        try:
            # جلب آخر 30 رسالة للسياق
            recent_messages = await self.repo.get_recent_messages(
                session_id,
                limit=30
            )
            
            if not recent_messages:
                return
            
            # تحويل الرسائل للصيغة المناسبة
            conversation = []
            for msg in recent_messages:
                role_label = "المستخدم" if msg.role == "user" else "المساعد"
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # الجلب الملخص القديم (إن وجد) لدمجه
            old_summary = await self.repo.get_session_summary(session_id)
            
            # بناء طلب التلخيص
            summary_prompt = self._build_summary_prompt(old_summary, conversation)
            
            # توليد الملخص
            new_summary = await self.llm.generate_summary(summary_prompt)
            
            if new_summary:
                await self.repo.save_session_summary(session_id, new_summary)
                
        except Exception as e:
            # لا نوقف المحادثة إذا فشل التلخيص
            print(f"⚠️ فشل تحديث الملخص للجلسة {session_id}: {e}")
    
    def _build_summary_prompt(
        self,
        old_summary: Optional[str],
        conversation: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        بناء الـ Prompt الخاص بتوليد الملخص.
        يدمج الملخص القديم مع الرسائل الجديدة.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "أنت مساعد خبير في تلخيص المحادثات بالعربية. "
                    "لخص المحادثة التالية بتركيز على:\n"
                    "- النقاط الرئيسية والمعلومات المهمة\n"
                    "- الأسئلة التي طرحها المستخدم\n"
                    "- الإجابات المهمة التي قُدمت\n"
                    "- أي حقائق أو تفضيلات ذكرها المستخدم\n"
                    "استخدم جملًا مختصرة وواضحة بالعربية الفصحى."
                )
            }
        ]
        
        # إضافة الملخص القديم للسياق
        if old_summary:
            messages.append({
                "role": "user",
                "content": f"الملخص السابق للمحادثة:\n{old_summary}\n\nاستمر في المحادثة التالية:"
            })
        
        # إضافة المحادثة الحالية
        messages.extend(conversation)
        
        # طلب الملخص
        messages.append({
            "role": "user",
            "content": "من فضلك لخص هذه المحادثة."
        })
        
        return messages
    
    # ═══════════════════════════════════════════
    # معلومات الذاكرة
    # ═══════════════════════════════════════════
    
    async def get_memory_stats(self, session_id: str) -> dict:
        """
        إحصائيات عن حالة الذاكرة للجلسة.
        """
        message_count = await self.repo.count_messages(session_id)
        summary = await self.repo.get_session_summary(session_id)
        
        return {
            "total_messages": message_count,
            "short_memory_size": min(message_count, self.SHORT_MEMORY_SIZE),
            "summary_exists": summary is not None,
            "summary_trigger_every": self.SUMMARY_TRIGGER,
            "next_summary_at": (
                self.SUMMARY_TRIGGER - (message_count % self.SUMMARY_TRIGGER)
                if message_count > 0 else self.SUMMARY_TRIGGER
            )
        }
    
    async def clear_memory(self, session_id: str) -> bool:
        """
        مسح ملخص الجلسة (للحذف أو إعادة الضبط).
        """
        await self.repo.save_session_summary(session_id, "")
        return True
    
    async def force_update_summary(self, session_id: str):
        """
        تحديث إجباري للملخص (بغض النظر عن العداد).
        """
        await self._generate_and_save_summary(session_id)