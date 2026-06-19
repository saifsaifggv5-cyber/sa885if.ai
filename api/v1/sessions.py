# api/v1/sessions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from config.database import get_db
from schemas.request_models import SessionCreate, SessionUpdate
from schemas.response_models import SessionResponse, SessionDetailResponse, MessageResponse
from repositories.chat_repo import ChatRepository

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    user_id: str = Query(default="default_user", description="معرف المستخدم"),
    limit: int = Query(default=50, ge=1, le=100, description="عدد النتائج"),
    offset: int = Query(default=0, ge=0, description="تخطي النتائج"),
    archived: Optional[bool] = Query(default=False, description="عرض المؤرشفة فقط"),
    db: AsyncSession = Depends(get_db)
):
    """
    جلب قائمة المحادثات للمستخدم.
    
    - **user_id**: معرف المستخدم
    - **limit**: عدد المحادثات (1-100)
    - **offset**: تخطي عدد معين من النتائج
    - **archived**: عرض المؤرشفة بدل النشطة
    """
    chat_repo = ChatRepository(db)
    sessions = await chat_repo.get_user_sessions(
        user_id=user_id,
        limit=limit,
        offset=offset,
        archived=archived
    )
    
    return [
        SessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            is_pinned=s.is_pinned,
            messages_count=s.messages_count if hasattr(s, 'messages_count') else 0
        )
        for s in sessions
    ]


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    إنشاء محادثة جديدة.
    
    - **user_id**: معرف المستخدم
    - **title**: عنوان المحادثة (اختياري)
    """
    chat_repo = ChatRepository(db)
    session = await chat_repo.create_session(
        user_id=request.user_id,
        title=request.title
    )
    
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_pinned=session.is_pinned,
        messages_count=0
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    include_messages: bool = Query(default=True, description="تضمين الرسائل"),
    db: AsyncSession = Depends(get_db)
):
    """
    جلب تفاصيل محادثة معينة.
    
    - **session_id**: معرف المحادثة
    - **include_messages**: تضمين قائمة الرسائل
    """
    chat_repo = ChatRepository(db)
    session = await chat_repo.get_session_by_id(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="المحادثة غير موجودة")
    
    messages = []
    if include_messages:
        msgs = await chat_repo.get_all_messages(session_id)
        messages = [
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
                is_completed=m.is_completed
            )
            for m in msgs
        ]
    
    return SessionDetailResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_pinned=session.is_pinned,
        messages=messages,
        messages_count=len(messages)
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    تعديل محادثة (تغيير العنوان، تثبيت، أرشفة).
    
    - **title**: عنوان جديد (اختياري)
    - **is_pinned**: تثبيت/إلغاء تثبيت (اختياري)
    - **is_archived**: أرشفة/إلغاء أرشفة (اختياري)
    """
    chat_repo = ChatRepository(db)
    
    session = await chat_repo.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="المحادثة غير موجودة")
    
    update_data = request.dict(exclude_unset=True)
    updated_session = await chat_repo.update_session(session_id, **update_data)
    
    return SessionResponse(
        id=updated_session.id,
        title=updated_session.title,
        created_at=updated_session.created_at,
        updated_at=updated_session.updated_at,
        is_pinned=updated_session.is_pinned,
        messages_count=0
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    حذف محادثة وكل رسائلها.
    
    - **session_id**: معرف المحادثة
    """
    chat_repo = ChatRepository(db)
    
    session = await chat_repo.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="المحادثة غير موجودة")
    
    await chat_repo.delete_session(session_id)
    return None


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    جلب رسائل محادثة معينة مع pagination.
    
    - **session_id**: معرف المحادثة
    - **limit**: عدد الرسائل (1-500)
    - **offset**: تخطي عدد معين من النتائج
    """
    chat_repo = ChatRepository(db)
    
    session = await chat_repo.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="المحادثة غير موجودة")
    
    messages = await chat_repo.get_messages_paginated(session_id, limit=limit, offset=offset)
    
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            is_completed=m.is_completed
        )
        for m in messages
    ]