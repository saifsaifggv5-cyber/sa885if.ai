# repositories/chat_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, desc
from typing import List, Optional
import uuid

from models.chat import ChatSession, ChatMessage, SessionSummary


class ChatRepository:
    """
    كل استعلامات قاعدة البيانات في مكان واحد.
    لا يوجد SQL في أي مكان آخر غير هذا الملف.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════
    # ChatSession
    # ═══════════════════════════════════════════

    async def create_session(self, user_id: str, title: str = "محادثة جديدة") -> ChatSession:
        """إنشاء جلسة محادثة جديدة."""
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session_by_id(self, session_id: str) -> Optional[ChatSession]:
        """جلب جلسة بمعرفها."""
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        archived: bool = False
    ) -> List[ChatSession]:
        """جلب قائمة جلسات المستخدم."""
        query = (
            select(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.is_archived == archived
            )
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_session(self, session_id: str, **kwargs) -> Optional[ChatSession]:
        """تحديث بيانات جلسة (عنوان، تثبيت، أرشفة)."""
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(**kwargs)
        )
        await self.db.commit()
        return await self.get_session_by_id(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """حذف جلسة وكل رسائلها وملخصاتها (Cascade)."""
        await self.db.execute(
            delete(ChatSession).where(ChatSession.id == session_id)
        )
        await self.db.commit()
        return True

    # ═══════════════════════════════════════════
    # ChatMessage
    # ═══════════════════════════════════════════

    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata_info: dict = None,
        is_completed: bool = True
    ) -> ChatMessage:
        """حفظ رسالة جديدة."""
        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            metadata_info=metadata_info or {},
            is_completed=is_completed
        )
        self.db.add(message)
        
        # تحديث وقت آخر تعديل للجلسة
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=func.now())
        )
        
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[ChatMessage]:
        """جلب آخر N رسالة من الجلسة (للذاكرة القصيرة)."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.is_completed == True
            )
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        messages = list(result.scalars().all())
        # عكس الترتيب ليكون من الأقدم للأحدث
        messages.reverse()
        return messages

    async def get_all_messages(self, session_id: str) -> List[ChatMessage]:
        """جلب كل رسائل الجلسة."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def get_messages_paginated(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChatMessage]:
        """جلب رسائل الجلسة مع التقسيم لصفحات."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_last_user_message(self, session_id: str) -> Optional[ChatMessage]:
        """جلب آخر رسالة من المستخدم (لإعادة التوليد)."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "user"
            )
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_last_assistant_message(self, session_id: str) -> Optional[ChatMessage]:
        """جلب آخر رسالة من المساعد."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "assistant"
            )
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_last_assistant_message(self, session_id: str) -> bool:
        """حذف آخر رسالة من المساعد (لإعادة التوليد)."""
        last_msg = await self.get_last_assistant_message(session_id)
        if last_msg:
            await self.db.delete(last_msg)
            await self.db.commit()
            return True
        return False

    async def count_messages(self, session_id: str) -> int:
        """عدد رسائل الجلسة."""
        result = await self.db.execute(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.session_id == session_id)
        )
        return result.scalar() or 0

    async def is_first_message(self, session_id: str) -> bool:
        """هل هذه أول رسالة في الجلسة؟ (لتوليد عنوان تلقائي)."""
        count = await self.count_messages(session_id)
        return count <= 2  # رسالة المستخدم + رد المساعد = 2

    # ═══════════════════════════════════════════
    # SessionSummary (ذاكرة الملخصات)
    # ═══════════════════════════════════════════

    async def get_session_summary(self, session_id: str) -> Optional[str]:
        """جلب نص ملخص الجلسة (إن وجد)."""
        result = await self.db.execute(
            select(SessionSummary)
            .where(SessionSummary.session_id == session_id)
        )
        summary_obj = result.scalar_one_or_none()
        return summary_obj.summary if summary_obj else None

    async def save_session_summary(
        self,
        session_id: str,
        summary_text: str
    ) -> SessionSummary:
        """حفظ أو تحديث ملخص الجلسة."""
        # البحث عن ملخص موجود
        result = await self.db.execute(
            select(SessionSummary)
            .where(SessionSummary.session_id == session_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # تحديث الملخص الموجود
            existing.summary = summary_text
            existing.version += 1
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # إنشاء ملخص جديد
            summary = SessionSummary(
                id=str(uuid.uuid4()),
                session_id=session_id,
                summary=summary_text,
                version=1
            )
            self.db.add(summary)
            await self.db.commit()
            await self.db.refresh(summary)
            return summary