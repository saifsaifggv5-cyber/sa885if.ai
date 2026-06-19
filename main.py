"""
main.py
الملف الرئيسي لتشغيل منصة SAIF.AI
يحتوي على تهيئة التطبيق، الـ Middleware، والـ Routes
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# استيرادات المشروع
from config.settings import settings
from config.database import init_db, engine
from cache.redis_client import redis_cache

# استيرادات الـ Routers
from api.v1 import chat, sessions, system, images, voice, health

# استيرادات الـ Helpers
from utils.helpers import log_safe, get_client_ip, safe_execute

# ── إعدادات التسجيل (Logging) ──────────────
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('saif_ai.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# 1. دورة حياة التطبيق (Lifespan)
# ═══════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    إدارة دورة حياة التطبيق:
    - تُنفذ عند بدء التشغيل (Startup)
    - تُنفذ عند الإغلاق (Shutdown)
    """
    logger.info("🚀 Starting SAIF.AI Platform...")
    
    # ── بدء التشغيل ──────────────────────────
    try:
        # 1. تهيئة قاعدة البيانات
        logger.info("📊 Initializing database...")
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # 2. الاتصال بـ Redis
        logger.info("🔴 Connecting to Redis...")
        redis_connected = await redis_cache.connect()
        if redis_connected:
            logger.info("✅ Redis connected successfully")
        else:
            logger.warning("⚠️ Redis connection failed - running without cache")
        
        # 3. تسجيل الإعدادات
        logger.info(f"⚙️ Active Provider: {settings.ACTIVE_PROVIDER}")
        logger.info(f"📦 Default Model: {settings.OPENROUTER_DEFAULT_MODEL}")
        logger.info(f"🎯 Version: {settings.APP_VERSION}")
        
        logger.info("✅ SAIF.AI Platform started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    # ── تشغيل التطبيق ────────────────────────
    yield
    
    # ── الإغلاق ──────────────────────────────
    logger.info("🛑 Shutting down SAIF.AI Platform...")
    
    try:
        # 1. إغلاق اتصال Redis
        await redis_cache.close()
        logger.info("✅ Redis connection closed")
        
        # 2. إغلاق اتصال قاعدة البيانات
        await engine.dispose()
        logger.info("✅ Database connection closed")
        
        logger.info("👋 SAIF.AI Platform stopped successfully")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# ═══════════════════════════════════════════════════════════════════
# 2. إنشاء تطبيق FastAPI
# ═══════════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="منصة SAIF.AI - الذكاء الاصطناعي المتقدم للمحادثات",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ═══════════════════════════════════════════════════════════════════
# 3. الـ Middleware
# ═══════════════════════════════════════════════════════════════════

# ── CORS ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*" if settings.DEBUG else None,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware مخصص لتسجيل الطلبات ──────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    تسجيل كل الطلبات الواردة مع معلومات IP والوقت.
    """
    import time
    
    start_time = time.perf_counter()
    client_ip = get_client_ip(request)
    
    # تسجيل الطلب
    logger.info(f"📥 Request: {request.method} {request.url.path} from {client_ip}")
    
    try:
        response = await call_next(request)
        
        # حساب وقت الاستجابة
        process_time = time.perf_counter() - start_time
        
        # تسجيل الرد
        logger.info(
            f"📤 Response: {request.method} {request.url.path} "
            f"→ {response.status_code} ({process_time:.3f}s)"
        )
        
        # إضافة هيدر وقت الاستجابة
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in {request.method} {request.url.path}: {e}")
        raise


# ── Middleware للـ Rate Limiting ─────────────
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    تطبيق نظام الحد من الطلبات (Rate Limiting).
    """
    from utils.security import security
    
    # استثناء بعض المسارات من التقييد
    excluded_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
    if request.url.path in excluded_paths:
        return await call_next(request)
    
    # الحصول على معرف المستخدم أو IP
    user_id = request.headers.get("X-User-Id") or get_client_ip(request)
    
    # فحص التقييد
    allowed, current, remaining = security.check_rate_limit(user_id)
    
    if not allowed:
        logger.warning(f"🚫 Rate limit exceeded for {user_id}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "تم تجاوز الحد الأقصى للطلبات. يرجى الانتظار دقيقة ثم المحاولة مرة أخرى.",
                "code": "RATE_LIMIT_EXCEEDED",
                "type": "rate_limit"
            }
        )
    
    response = await call_next(request)
    
    # إضافة هيدرات التقييد
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = "60"
    
    return response


# ── معالج الأخطاء العالمي ────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    معالج الأخطاء HTTP الموحد.
    """
    logger.error(f"HTTP Error {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "type": "http_error",
            "path": request.url.path
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    معالج أخطاء التحقق من البيانات.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.error(f"Validation Error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "خطأ في البيانات المرسلة",
            "code": "VALIDATION_ERROR",
            "type": "validation_error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    معالج الأخطاء العام (لأي استثناء غير متوقع).
    """
    logger.error(f"❌ Unhandled Exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "حدث خطأ داخلي في الخادم. يرجى المحاولة مرة أخرى لاحقاً.",
            "code": "INTERNAL_SERVER_ERROR",
            "type": "server_error",
            "path": request.url.path
        }
    )


# ═══════════════════════════════════════════════════════════════════
# 4. Static Files (الملفات الثابتة)
# ═══════════════════════════════════════════════════════════════════

try:
    app.mount("/uploads", StaticFiles(directory="storage/uploads"), name="uploads")
    logger.info("📁 Uploads directory mounted at /uploads")
except Exception as e:
    logger.warning(f"⚠️ Could not mount uploads directory: {e}")


# ═══════════════════════════════════════════════════════════════════
# 5. تسجيل الـ Routers
# ═══════════════════════════════════════════════════════════════════

# ── Routers API ──────────────────────────────
app.include_router(chat.router)          # /api/v1/chat
app.include_router(sessions.router)      # /api/v1/sessions
app.include_router(system.router)        # /api/v1/system
app.include_router(images.router)        # /api/v1/images
app.include_router(voice.router)         # /api/v1/voice
app.include_router(health.router)        # /api/v1/health

logger.info("✅ All routers registered successfully")


# ═══════════════════════════════════════════════════════════════════
# 6. نقاط النهاية الأساسية (Root Endpoints)
# ═══════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """
    الصفحة الرئيسية - معلومات عن المنصة.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else None,
        "providers": {
            "active": settings.ACTIVE_PROVIDER,
            "available": ["openrouter", "gemini"]
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


@app.get("/health")
async def health_check():
    """
    فحص صحة المنصة.
    """
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "uptime": None,  # يمكن إضافة وقت التشغيل
        "database": True,
        "redis": False,
    }
    
    # فحص Redis
    try:
        health_status["redis"] = await redis_cache.connect()
    except:
        health_status["redis"] = False
    
    return health_status


# ═══════════════════════════════════════════════════════════════════
# 7. تشغيل التطبيق
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Running {settings.APP_NAME} v{settings.APP_VERSION}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )