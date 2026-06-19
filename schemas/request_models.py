# schemas/request_models.py
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """
    نموذج طلب إرسال رسالة جديدة.
    """
    session_id: Optional[str] = Field(
        default=None,
        description="معرف المحادثة. إذا لم يُرسل، سيتم إنشاء محادثة جديدة تلقائياً."
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="نص الرسالة المراد إرسالها."
    )
    persona: Optional[str] = Field(
        default=None,
        description="نص الشخصية المخصص. إذا لم يُرسل، تُستخدم الشخصية الافتراضية."
    )
    model: Optional[str] = Field(
        default=None,
        description="اسم النموذج المطلوب. إذا لم يُرسل، يُستخدم النموذج الافتراضي."
    )
    thinking_mode: Optional[bool] = Field(
        default=False,
        description="تفعيل وضع التفكير لإظهار خطوات استدلال الـ AI."
    )
    attachments: Optional[List[str]] = Field(
        default=None,
        description="قائمة روابط الملفات المرفقة (صور، PDF، إلخ)."
    )
    system_command: Optional[bool] = Field(
        default=False,
        description="هل هذه الرسالة أمر نظام للتحكم بالمنصة؟"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def",
                "message": "ما هي عاصمة فرنسا؟",
                "persona": "أنت معلم جغرافيا خبير",
                "thinking_mode": True,
                "attachments": [],
                "system_command": False
            }
        }


class RegenerateRequest(BaseModel):
    """
    نموذج طلب إعادة توليد آخر رد.
    """
    session_id: str = Field(
        ...,
        description="معرف المحادثة المطلوب إعادة توليد آخر رد فيها."
    )
    persona: Optional[str] = Field(
        default=None,
        description="تغيير الشخصية للرد الجديد (اختياري)."
    )
    model: Optional[str] = Field(
        default=None,
        description="تغيير النموذج للرد الجديد (اختياري)."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def",
                "persona": None,
                "model": "google/gemini-2.0-flash-lite-001"
            }
        }


class SessionCreate(BaseModel):
    """
    نموذج طلب إنشاء محادثة جديدة.
    """
    user_id: str = Field(
        default="default_user",
        min_length=1,
        max_length=100,
        description="معرف المستخدم المالك للمحادثة."
    )
    title: Optional[str] = Field(
        default="محادثة جديدة",
        min_length=1,
        max_length=200,
        description="عنوان المحادثة. إذا لم يُرسل، يُستخدم العنوان الافتراضي."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-456",
                "title": "تعلم بايثون"
            }
        }


class SessionUpdate(BaseModel):
    """
    نموذج طلب تحديث بيانات محادثة.
    جميع الحقول اختيارية، ولن يُحدّث إلا ما تم إرساله.
    """
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="العنوان الجديد للمحادثة."
    )
    is_pinned: Optional[bool] = Field(
        default=None,
        description="تثبيت أو إلغاء تثبيت المحادثة."
    )
    is_archived: Optional[bool] = Field(
        default=None,
        description="أرشفة أو إلغاء أرشفة المحادثة."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "خطة تعلم بايثون متقدمة",
                "is_pinned": True,
                "is_archived": False
            }
        }


class ImageGenRequest(BaseModel):
    """
    نموذج طلب إنشاء صورة بالذكاء الاصطناعي.
    """
    prompt: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="وصف الصورة المطلوب إنشاؤها."
    )
    style: Optional[str] = Field(
        default="realistic",
        description="نمط الرسم (realistic, anime, digital, oil, 3d, sketch)."
    )
    size: Optional[str] = Field(
        default="1024x1024",
        description="أبعاد الصورة المطلوبة."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "قطة ترتدي قبعة في الفضاء الخارجي",
                "style": "realistic",
                "size": "1024x1024"
            }
        }


class VoiceTranscribeRequest(BaseModel):
    """
    نموذج طلب تحويل الصوت لنص.
    يُستخدم مع رفع ملف صوتي عبر multipart/form-data.
    """
    language: Optional[str] = Field(
        default="ar",
        description="لغة المقطع الصوتي (ar, en, fr, إلخ)."
    )
    model: Optional[str] = Field(
        default="whisper-1",
        description="نموذج تحويل الصوت لنص."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "language": "ar",
                "model": "whisper-1"
            }
        }


class SystemCommandRequest(BaseModel):
    """
    نموذج أمر النظام - الـ AI يتحكم في المنصة بأمر من المستخدم.
    """
    command: str = Field(
        ...,
        description="نص الأمر (مثال: غير الثيم إلى أزرق، امسح الكاش)."
    )
    session_id: Optional[str] = Field(
        default=None,
        description="معرف المحادثة المرتبطة (اختياري)."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "command": "فعل الوضع الليلي",
                "session_id": "abc-123-def"
            }
        }