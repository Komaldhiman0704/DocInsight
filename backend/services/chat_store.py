"""
Chat Session Store - Persists chat sessions as JSON files.
Sessions are stored in ./chat_sessions/ folder, one file per session.
"""
import json
import os
from datetime import datetime
from typing import Optional
import uuid
from pathlib import Path

SESSIONS_DIR = "./chat_sessions"


def _ensure_dir():
    """Create chat_sessions directory if it doesn't exist"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)


def _get_session_path(session_id: str) -> str:
    """Get the file path for a session"""
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def create_session(doc_ids: list[str]) -> dict:
    """
    Create a new chat session.
    
    Args:
        doc_ids: List of document IDs associated with this session
        
    Returns:
        Session dict with id, doc_ids, title, created_at, messages
    """
    _ensure_dir()
    
    session_id = str(uuid.uuid4())
    session = {
        "id": session_id,
        "doc_ids": doc_ids,
        "title": "New Chat",  # Will be updated with first message
        "created_at": datetime.now().isoformat(),
        "messages": []
    }
    
    # Save to file
    path = _get_session_path(session_id)
    with open(path, "w") as f:
        json.dump(session, f, indent=2)
    
    return session


def get_session(session_id: str) -> Optional[dict]:
    """Get a session by ID"""
    _ensure_dir()
    
    path = _get_session_path(session_id)
    if not os.path.exists(path):
        return None
    
    with open(path, "r") as f:
        return json.load(f)


def save_message(session_id: str, role: str, content: str, sources: list = None, confidence: str = None, relevance_score: float = None, suggestions: list = None) -> bool:
    """
    Save a message to a session.
    
    Args:
        session_id: Session to add message to
        role: "user" or "assistant"
        content: Message content
        sources: Optional list of source documents
        confidence: Optional confidence level ("high", "medium", "low")
        relevance_score: Optional relevance score (0.0-1.0)
        suggestions: Optional list of follow-up suggestions
        
    Returns:
        True if successful, False if session not found
    """
    _ensure_dir()
    
    session = get_session(session_id)
    if session is None:
        return False
    
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "sources": sources or [],
        "suggestions": suggestions or []
    }
    
    # Add confidence metrics if provided (AI responses)
    if confidence:
        message["confidence"] = confidence
        message["relevance_score"] = relevance_score
    
    session["messages"].append(message)
    
    # Auto-set title from first user message (if still "New Chat")
    if role == "user" and session["title"] == "New Chat":
        # Truncate to 50 chars
        title = content[:50]
        if len(content) > 50:
            title += "…"
        session["title"] = title
    
    # Save updated session
    path = _get_session_path(session_id)
    with open(path, "w") as f:
        json.dump(session, f, indent=2)
    
    return True


def list_sessions() -> list[dict]:
    """
    List all sessions, newest first.
    
    Returns:
        List of session dicts (id, title, created_at, doc_ids, message_count)
    """
    _ensure_dir()
    
    sessions = []
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json"):
            path = os.path.join(SESSIONS_DIR, filename)
            with open(path, "r") as f:
                session = json.load(f)
                # Count only user messages (queries), not assistant responses
                user_message_count = sum(1 for msg in session["messages"] if msg.get("role") == "user")
                sessions.append({
                    "id": session["id"],
                    "title": session["title"],
                    "created_at": session["created_at"],
                    "doc_ids": session["doc_ids"],
                    "message_count": user_message_count
                })
    
    # Sort by created_at descending (newest first)
    sessions.sort(key=lambda s: s["created_at"], reverse=True)
    return sessions


def delete_session(session_id: str) -> bool:
    """Delete a session"""
    _ensure_dir()
    
    path = _get_session_path(session_id)
    if not os.path.exists(path):
        return False
    
    os.remove(path)
    return True


def rename_session(session_id: str, new_title: str) -> bool:
    """Rename a session"""
    _ensure_dir()
    
    session = get_session(session_id)
    if session is None:
        return False
    
    session["title"] = new_title.strip()
    path = _get_session_path(session_id)
    with open(path, "w") as f:
        json.dump(session, f, indent=2)
    
    return True
