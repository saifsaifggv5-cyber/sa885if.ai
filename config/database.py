# config/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from config.settings import settings

# ── إنشاء المحرك غير المتزامن ─────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # طباعة استعلامات SQL في وضع التطوير
    pool_size=10,              # حجم تجمع الاتصالات
    max_overflow=20,           # اتصالات إضافية عند الضغط
    pool_pre_ping=True,        # فحص الاتصال قبل الاستخدام
    pool_recycle=3600          # إعادة تدوير الاتصالات كل ساعة
)

# ── إنشاء مصنع الجلسات غير المتزامنة ──────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,    # عدم انتهاء الكائنات بعد الـ commit
    autoflush=False,           # تعطيل الفلاش التلقائي
    autocommit=False           # تعطيل الـ autocommit
)

# ── القاعدة الأساسية لكل النماذج ──────────────
class Base(DeclarativeBase):
    """
    كل جداول قاعدة البيانات ترث من هذه القاعدة.
    """
    pass


# ── دالة توفير الجلسة للـ Dependency Injection ──
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    توفر جلسة قاعدة بيانات لكل طلب وتغلقها تلقائياً.
    تُستخدم مع Depends() في نقاط النهاية.
    
    مثال:
        @app.get("/")
        async def root(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # حفظ التغييرات تلقائياً
        except Exception:
            await session.rollback()  # التراجع عن التغييرات في حالة الخطأ
            raise
        finally:
            await session.close()  # إغلاق الجلسة


# ── دالة تهيئة قاعدة البيانات ──────────────────
async def init_db():
    """
    إنشاء كل الجداول تلقائياً عند بدء التشغيل.
    تُستدعى في main.py عند بدء التطبيق.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)