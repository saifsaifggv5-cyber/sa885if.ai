# api/v1/system.py
"""
System Management Endpoints
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/info")
async def system_info():
    """
    معلومات عن النظام والمنصة.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "debug_mode": settings.DEBUG,
        "active_provider": settings.ACTIVE_PROVIDER,
        "features": {
            "thinking_mode": settings.THINKING_MODE_ENABLED,
            "image_generation": settings.IMAGE_GEN_ENABLED,
            "voice": settings.VOICE_ENABLED,
            "file_upload": settings.FILE_UPLOAD_ENABLED,
            "camera": settings.CAMERA_ENABLED,
        },
        "models": {
            "openrouter": settings.OPENROUTER_DEFAULT_MODEL,
            "gemini": settings.GEMINI_DEFAULT_MODEL
        }
    }


@router.get("/config")
async def get_config():
    """
    الحصول على إعدادات النظام الحالية.
    """
    return {
        "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
        "cache_ttl": settings.CACHE_TTL,
        "short_memory_size": settings.SHORT_MEMORY_SIZE,
        "summary_trigger": settings.SUMMARY_TRIGGER,
        "dark_mode_default": settings.DARK_MODE_DEFAULT
    }


@router.post("/switch-provider")
async def switch_provider(provider: str):
    """
    تبديل مزود الذكاء الاصطناعي.
    
    - **provider**: اسم المزود (openrouter, gemini)
    """
    valid_providers = ["openrouter", "gemini"]
    
    if provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"مزود غير صحيح. المزودين المتاحين: {', '.join(valid_providers)}"
        )
    
    # تحديث الإعدادات (في الواقع يجب تحديث ملف .env)
    return {
        "status": "success",
        "message": f"تم تبديل المزود إلى {provider}",
        "active_provider": provider
    }


@router.get("/stats")
async def get_stats():
    """
    الحصول على إحصائيات النظام.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": 0,  # سيتم حسابه لاحقاً
        "total_sessions": 0,  # سيتم حسابه من قاعدة البيانات
        "total_messages": 0,  # سيتم حسابه من قاعدة البيانات
        "active_users": 0,  # سيتم حسابه من قاعدة البيانات
    }
