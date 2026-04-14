"""
Sessions Router - API endpoints for chat session management
GET  /api/sessions           → list all sessions
POST /api/sessions           → create new session
GET  /api/sessions/{id}      → get session with messages
DELETE /api/sessions/{id}    → delete session
PATCH /api/sessions/{id}     → rename session
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from services.chat_store import (
    create_session,
    get_session,
    list_sessions,
    delete_session,
    rename_session,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateSessionRequest(BaseModel):
    """Create a new session with document IDs"""
    doc_ids: list[str] = []


class RenameSessionRequest(BaseModel):
    """Rename a session"""
    title: str


class SessionResponse(BaseModel):
    """Session summary (for list endpoint)"""
    id: str
    title: str
    created_at: str
    doc_ids: list[str]
    message_count: int


class SessionDetailResponse(BaseModel):
    """Full session with all messages"""
    id: str
    title: str
    created_at: str
    doc_ids: list[str]
    messages: list[dict]


@router.get("/sessions", response_model=list[SessionResponse])
async def list_all_sessions():
    """Get all chat sessions, newest first"""
    try:
        sessions = list_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@router.post("/sessions", response_model=dict)
async def create_new_session(req: CreateSessionRequest):
    """Create a new chat session"""
    try:
        session = create_session(doc_ids=req.doc_ids)
        return {
            "id": session["id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "doc_ids": session["doc_ids"],
            "message_count": 0
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(session_id: str):
    """Get a session with all its messages"""
    try:
        session = get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Delete a chat session"""
    try:
        success = delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"id": session_id, "deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@router.patch("/sessions/{session_id}")
async def rename_session_endpoint(session_id: str, req: RenameSessionRequest):
    """Rename a chat session"""
    try:
        success = rename_session(session_id, req.title)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        session = get_session(session_id)
        return {
            "id": session["id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "doc_ids": session["doc_ids"],
            "message_count": len(session["messages"])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error renaming session: {str(e)}")
