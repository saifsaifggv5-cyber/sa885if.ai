# models/chat.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# هنستورد Base من config/database.py لما نكتبه
from config.database import Base


class ChatSession(Base):
    """
    جدول المحادثات.
    كل محادثة ليها ID فريد ومرتبطة بمستخدم معين.
    """
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    title = Column(String, default="محادثة جديدة")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_pinned = Column(Boolean, default=False)  # تثبيت المحادثة
    is_archived = Column(Boolean, default=False)  # أرشفة المحادثة

    # العلاقات
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    summary = relationship("SessionSummary", back_populates="session", uselist=False, cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    جدول الرسائل داخل المحادثة.
    كل رسالة ليها دور (user/assistant/system) ومحتوى وبيانات إضافية.
    """
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # بيانات إضافية للميزات المتقدمة (ملفات، صور، إلخ)
    metadata_info = Column(JSON, nullable=True)
    
    # حالة الرسالة للـ Streaming
    is_completed = Column(Boolean, default=True)

    # العلاقة
    session = relationship("ChatSession", back_populates="messages")


class SessionSummary(Base):
    """
    جدول ملخصات المحادثات.
    يتم تحديثه كل عدد معين من الرسائل (حسب SUMMARY_TRIGGER).
    """
    __tablename__ = "session_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    version = Column(Integer, default=1)  # رقم إصدار الملخص
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقة
    session = relationship("ChatSession", back_populates="summary")