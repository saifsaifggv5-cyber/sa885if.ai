# api/v1/health.py
"""
Health Check Endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from config.settings import settings
from cache.redis_client import redis_cache

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/")
async def health_check():
    """
    فحص صحة المنصة الشامل.
    """
    # فحص Redis
    redis_status = False
    try:
        redis_status = await redis_cache.connect()
    except:
        redis_status = False
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "services": {
            "database": True,
            "redis": redis_status,
            "ai_provider": settings.ACTIVE_PROVIDER
        },
        "features": {
            "streaming": True,
            "thinking_mode": settings.THINKING_MODE_ENABLED,
            "image_generation": settings.IMAGE_GEN_ENABLED,
            "voice": settings.VOICE_ENABLED,
            "file_upload": settings.FILE_UPLOAD_ENABLED,
            "camera": settings.CAMERA_ENABLED,
        }
    }


@router.get("/status")
async def status():
    """
    حالة سريعة للنظام.
    """
    return {
        "status": "running",
        "version": settings.APP_VERSION,
        "provider": settings.ACTIVE_PROVIDER
    }
