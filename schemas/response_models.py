# schemas/response_models.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════
# المحادثة
# ═══════════════════════════════════════════

class SessionResponse(BaseModel):
    """
    رد مختصر لبيانات محادثة.
    """
    id: str = Field(..., description="معرف المحادثة الفريد")
    title: str = Field(..., description="عنوان المحادثة")
    created_at: datetime = Field(..., description="وقت الإنشاء")
    updated_at: datetime = Field(..., description="وقت آخر تحديث")
    is_pinned: bool = Field(default=False, description="هل المحادثة مثبتة")
    messages_count: int = Field(default=0, description="عدد الرسائل في المحادثة")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc-123-def",
                "title": "تعلم بايثون",
                "created_at": "2026-06-19T18:00:00Z",
                "updated_at": "2026-06-19T18:30:00Z",
                "is_pinned": False,
                "messages_count": 15
            }
        }


class MessageResponse(BaseModel):
    """
    رد لرسالة واحدة.
    """
    id: str = Field(..., description="معرف الرسالة الفريد")
    role: str = Field(..., description="الدور: user, assistant, system")
    content: str = Field(..., description="محتوى الرسالة")
    created_at: datetime = Field(..., description="وقت الإرسال")
    is_completed: bool = Field(default=True, description="هل اكتملت الرسالة")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-456",
                "role": "assistant",
                "content": "عاصمة فرنسا هي باريس",
                "created_at": "2026-06-19T18:30:05Z",
                "is_completed": True
            }
        }


class SessionDetailResponse(BaseModel):
    """
    رد تفصيلي لمحادثة مع رسائلها.
    """
    id: str = Field(..., description="معرف المحادثة")
    title: str = Field(..., description="عنوان المحادثة")
    created_at: datetime = Field(..., description="وقت الإنشاء")
    updated_at: datetime = Field(..., description="وقت آخر تحديث")
    is_pinned: bool = Field(default=False, description="هل مثبتة")
    messages_count: int = Field(default=0, description="عدد الرسائل")
    messages: List[MessageResponse] = Field(default=[], description="قائمة الرسائل")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc-123-def",
                "title": "تعلم بايثون",
                "created_at": "2026-06-19T18:00:00Z",
                "updated_at": "2026-06-19T18:30:00Z",
                "is_pinned": False,
                "messages_count": 2,
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "content": "ما هي عاصمة فرنسا؟",
                        "created_at": "2026-06-19T18:30:00Z",
                        "is_completed": True
                    },
                    {
                        "id": "msg-2",
                        "role": "assistant",
                        "content": "عاصمة فرنسا هي باريس",
                        "created_at": "2026-06-19T18:30:05Z",
                        "is_completed": True
                    }
                ]
            }
        }


# ═══════════════════════════════════════════
# الدردشة
# ═══════════════════════════════════════════

class ChatResponse(BaseModel):
    """
    رد على طلب إرسال رسالة (للاستخدام في غير الـ Streaming).
    """
    session_id: str = Field(..., description="معرف المحادثة")
    message_id: str = Field(..., description="معرف الرسالة الجديدة")
    content: str = Field(..., description="محتوى الرد الكامل")
    thinking: Optional[str] = Field(default=None, description="خطوات التفكير إن وُجدت")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def",
                "message_id": "msg-789",
                "content": "عاصمة فرنسا هي باريس",
                "thinking": None
            }
        }


class StreamChunk(BaseModel):
    """
    قطعة من الرد في وضع الـ Streaming.
    """
    token: str = Field(..., description="كلمة أو جزء من الرد")
    type: str = Field(default="content", description="النوع: content, thinking, done, error")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "عاصمة ",
                "type": "content"
            }
        }


class RegenerateResponse(BaseModel):
    """
    رد على طلب إعادة توليد الرد.
    """
    session_id: str = Field(..., description="معرف المحادثة")
    new_message_id: str = Field(..., description="معرف الرد الجديد")
    content: str = Field(..., description="محتوى الرد الجديد")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def",
                "new_message_id": "msg-999",
                "content": "عاصمة فرنسا هي باريس، وتلقب بمدينة النور"
            }
        }


# ═══════════════════════════════════════════
# الأخطاء
# ═══════════════════════════════════════════

class ErrorResponse(BaseModel):
    """
    رد موحد لأخطاء API.
    """
    detail: str = Field(..., description="وصف الخطأ")
    code: Optional[str] = Field(default=None, description="كود الخطأ التقني")
    type: Optional[str] = Field(default=None, description="نوع الخطأ")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "المحادثة غير موجودة",
                "code": "SESSION_NOT_FOUND",
                "type": "not_found"
            }
        }


class ErrorReason(BaseModel):
    """أسباب الأخطاء المحتملة."""
    reason: str = Field(..., description="سبب الخطأ")


# ═══════════════════════════════════════════
# الذاكرة
# ═══════════════════════════════════════════

class SummaryResponse(BaseModel):
    """
    رد ملخص المحادثة.
    """
    session_id: str = Field(..., description="معرف المحادثة")
    summary: str = Field(..., description="نص الملخص")
    version: int = Field(..., description="رقم إصدار الملخص")
    updated_at: Optional[datetime] = Field(default=None, description="وقت آخر تحديث")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def",
                "summary": "المستخدم يسأل عن عواصم دول أوروبية، تمت الإجابة عن فرنسا وألمانيا",
                "version": 2,
                "updated_at": "2026-06-19T19:00:00Z"
            }
        }


# ═══════════════════════════════════════════
# إنشاء الصور
# ═══════════════════════════════════════════

class ImageGenResponse(BaseModel):
    """
    رد على طلب إنشاء صورة.
    """
    image_url: str = Field(..., description="رابط الصورة المولدة")
    prompt: str = Field(..., description="الوصف المستخدم")
    style: str = Field(..., description="نمط الرسم المستخدم")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="وقت الإنشاء")

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://storage.saif.ai/images/gen_abc123.png",
                "prompt": "قطة في الفضاء",
                "style": "realistic",
                "created_at": "2026-06-19T18:45:00Z"
            }
        }


# ═══════════════════════════════════════════
# تحويل الصوت
# ═══════════════════════════════════════════

class VoiceTranscribeResponse(BaseModel):
    """
    رد على طلب تحويل الصوت لنص.
    """
    text: str = Field(..., description="النص المستخرج من الصوت")
    language: str = Field(default="ar", description="اللغة المكتشفة")
    duration: Optional[float] = Field(default=None, description="مدة المقطع بالثواني")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "مرحباً كيف حالك",
                "language": "ar",
                "duration": 3.5
            }
        }


# ═══════════════════════════════════════════
# أوامر النظام
# ═══════════════════════════════════════════

class SystemCommandResponse(BaseModel):
    """
    رد على أمر نظام.
    """
    success: bool = Field(..., description="هل تم تنفيذ الأمر بنجاح")
    message: str = Field(..., description="رسالة تأكيد أو خطأ")
    action: Optional[str] = Field(default=None, description="الإجراء المنفذ")
    data: Optional[dict] = Field(default=None, description="بيانات إضافية")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "تم تفعيل الوضع الليلي",
                "action": "toggleDarkMode",
                "data": {"enabled": True}
            }
        }


# ═══════════════════════════════════════════
# الإحصائيات
# ═══════════════════════════════════════════

class StatsResponse(BaseModel):
    """
    رد إحصائيات المنصة.
    """
    total_sessions: int = Field(default=0, description="إجمالي المحادثات")
    total_messages: int = Field(default=0, description="إجمالي الرسائل")
    today_messages: int = Field(default=0, description="رسائل اليوم")
    active_users: int = Field(default=0, description="المستخدمين النشطين")
    avg_response_time: Optional[float] = Field(default=None, description="متوسط زمن الرد")

    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 42,
                "total_messages": 520,
                "today_messages": 35,
                "active_users": 5,
                "avg_response_time": 1.2
            }
        }


# ═══════════════════════════════════════════
# الصحة
# ═══════════════════════════════════════════

class HealthResponse(BaseModel):
    """
    رد فحص صحة المنصة.
    """
    status: str = Field(default="healthy", description="حالة المنصة")
    version: str = Field(..., description="إصدار المنصة")
    uptime: Optional[float] = Field(default=None, description="مدة التشغيل بالثواني")
    database: bool = Field(default=True, description="حالة اتصال قاعدة البيانات")
    redis: bool = Field(default=True, description="حالة اتصال Redis")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.5,
                "database": True,
                "redis": True
            }
        }


# ═══════════════════════════════════════════
# قوائم وتصفح
# ═══════════════════════════════════════════

class PaginationMeta(BaseModel):
    """
    بيانات التصفح (Pagination Metadata).
    """
    total: int = Field(..., description="إجمالي عدد العناصر")
    limit: int = Field(..., description="عدد العناصر في الصفحة")
    offset: int = Field(..., description="عدد العناصر المتخطاة")
    has_more: bool = Field(default=False, description="هل توجد صفحات تالية")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "limit": 20,
                "offset": 0,
                "has_more": True
            }
        }


class PaginatedSessions(BaseModel):
    """
    رد قائمة المحادثات مع بيانات التصفح.
    """
    data: List[SessionResponse] = Field(..., description="قائمة المحادثات")
    meta: PaginationMeta = Field(..., description="بيانات التصفح")


class PaginatedMessages(BaseModel):
    """
    رد قائمة الرسائل مع بيانات التصفح.
    """
    data: List[MessageResponse] = Field(..., description="قائمة الرسائل")
    meta: PaginationMeta = Field(..., description="بيانات التصفح")


# ═══════════════════════════════════════════
# أحداث البث (Streaming Events)
# ═══════════════════════════════════════════

class StreamEvent(BaseModel):
    """
    حدث في بث الـ Streaming.
    """
    event: str = Field(..., description="نوع الحدث: token, thinking, done, error, metadata")
    data: str = Field(..., description="بيانات الحدث")
    session_id: Optional[str] = Field(default=None, description="معرف المحادثة")

    class Config:
        json_schema_extra = {
            "example": {
                "event": "token",
                "data": "عاصمة ",
                "session_id": "abc-123-def"
            }
        }