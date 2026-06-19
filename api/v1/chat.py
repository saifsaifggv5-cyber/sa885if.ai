# api/v1/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config.database import get_db
from config.settings import settings
from schemas.request_models import ChatRequest, RegenerateRequest
from schemas.response_models import ChatResponse, ErrorResponse
from services.llm_service import LLMService
from services.memory_manager import MemoryManager
from repositories.chat_repo import ChatRepository

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    إرسال رسالة واستقبال الرد مباشرة كلمة كلمة (Streaming).
    
    - **session_id**: معرف المحادثة (ينشأ تلقائياً لو مش موجود)
    - **message**: نص الرسالة
    - **persona**: الشخصية المستخدمة (اختياري)
    """
    try:
        # تهيئة الخدمات
        chat_repo = ChatRepository(db)
        llm_service = LLMService()
        memory_manager = MemoryManager(chat_repo, llm_service)
        
        # 1. إنشاء جلسة جديدة لو مفيش session_id
        if not request.session_id:
            session = await chat_repo.create_session(user_id="default_user")
            request.session_id = session.id
        
        # 2. حفظ رسالة المستخدم فوراً
        await chat_repo.create_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        
        # 3. بناء السياق (ذاكرة قصيرة + ملخص)
        persona = request.persona or settings.DEFAULT_PERSONA
        context_messages = await memory_manager.build_context(
            session_id=request.session_id,
            new_message=request.message,
            persona=persona
        )
        
        # 4. بث الرد
        async def event_generator():
            full_reply = ""
            try:
                async for token in llm_service.stream_response(
                    messages=context_messages,
                    provider=settings.ACTIVE_PROVIDER
                ):
                    full_reply += token
                    yield f"data: {token}\n\n"
                
                # إشارة انتهاء البث
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: [ERROR] حدث خطأ: {str(e)}\n\n"
                return
            
            # 5. مهام الخلفية بعد انتهاء الرد
            background_tasks.add_task(
                chat_repo.create_message,
                session_id=request.session_id,
                role="assistant",
                content=full_reply
            )
            background_tasks.add_task(
                memory_manager.maybe_update_summary,
                session_id=request.session_id
            )
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-Id": request.session_id
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate")
async def regenerate_response(
    request: RegenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    إعادة توليد آخر رد في المحادثة.
    
    - **session_id**: معرف المحادثة
    """
    try:
        chat_repo = ChatRepository(db)
        
        # 1. جلب آخر رسالة من المستخدم
        last_user_message = await chat_repo.get_last_user_message(request.session_id)
        if not last_user_message:
            raise HTTPException(status_code=404, detail="لا توجد رسائل سابقة")
        
        # 2. حذف آخر رد من المساعد
        await chat_repo.delete_last_assistant_message(request.session_id)
        
        # 3. إعادة إرسال نفس الطلب مع البث
        llm_service = LLMService()
        memory_manager = MemoryManager(chat_repo, llm_service)
        persona = request.persona or settings.DEFAULT_PERSONA
        
        context_messages = await memory_manager.build_context(
            session_id=request.session_id,
            new_message=last_user_message.content,
            persona=persona
        )
        
        async def event_generator():
            full_reply = ""
            try:
                async for token in llm_service.stream_response(
                    messages=context_messages,
                    provider=settings.ACTIVE_PROVIDER
                ):
                    full_reply += token
                    yield f"data: {token}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: [ERROR] حدث خطأ: {str(e)}\n\n"
                return
            
            background_tasks.add_task(
                chat_repo.create_message,
                session_id=request.session_id,
                role="assistant",
                content=full_reply
            )
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-Id": request.session_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))