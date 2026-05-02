"""
Chat Router
POST /api/chat         - Non-streaming chat
POST /api/chat/stream  - Server-Sent Events streaming chat
POST /api/chat/export  - Export chat session as PDF
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import logging
from io import BytesIO

from services.rag_chain import run_rag_chain, stream_rag_chain
from services.chat_store import save_message, get_session
from services.pdf_exporter import create_chat_export_pdf

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str
    chat_history: list[dict] = []
    doc_ids: Optional[list[str]] = None
    session_id: Optional[str] = None


@router.post("/chat")
async def chat(req: ChatRequest):
    """Standard (non-streaming) chat endpoint"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        result = await run_rag_chain(
            question=req.question,
            chat_history=req.chat_history,
            doc_ids=req.doc_ids,
        )
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Streaming chat using Server-Sent Events (SSE).
    Frontend receives tokens as they stream from the LLM.
    
    Event types:
      event: sources  → JSON array of source documents
      data: {...}     → { token: "word" } for each answer token  
      event: done     → stream complete
      event: error    → { error: "message" }
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async def event_generator():
        sources_list = []
        answer_content = ""
        confidence = None
        relevance_score = None
        suggestions = []
        enhanced_sources = []  # ✅ PHASE 3-4: Store semantically enhanced sources
        
        try:
            async for chunk in stream_rag_chain(
                question=req.question,
                chat_history=req.chat_history,
                doc_ids=req.doc_ids,
            ):
                if chunk.startswith("__SOURCES__"):
                    sources_json = chunk.replace("__SOURCES__", "").strip()
                    try:
                        sources_data = json.loads(sources_json)
                        # Handle both object format (with confidence) and array format
                        if isinstance(sources_data, dict):
                            sources_list = sources_data.get("sources", [])
                            confidence = sources_data.get("confidence")
                            relevance_score = sources_data.get("relevance_score")
                        else:
                            sources_list = sources_data
                    except:
                        sources_list = []
                    yield f"event: sources\ndata: {sources_json}\n\n"
                
                # ✅ PHASE 3-4: Handle semantically enhanced sources
                elif chunk.startswith("__SOURCES_ENHANCED__"):
                    enhanced_sources_json = chunk.replace("__SOURCES_ENHANCED__", "").strip()
                    try:
                        enhanced_data = json.loads(enhanced_sources_json)
                        enhanced_sources = enhanced_data.get("sources", [])
                        # Update sources_list with enhanced version
                        sources_list = enhanced_sources
                        logger.info(f"Received {len(enhanced_sources)} semantically reranked sources")
                    except Exception as e:
                        logger.warning(f"Failed to parse enhanced sources: {e}")
                    # Yield enhanced sources to frontend
                    yield f"event: sources_enhanced\ndata: {enhanced_sources_json}\n\n"
                
                elif chunk.startswith("__SUGGESTIONS__"):
                    suggestions_json = chunk.replace("__SUGGESTIONS__", "").strip()
                    try:
                        suggestions = json.loads(suggestions_json)
                        yield f"event: suggestions\ndata: {suggestions_json}\n\n"
                    except:
                        pass
                else:
                    # Each token as a data event
                    answer_content += chunk
                    token_json = json.dumps({"token": chunk})
                    yield f"data: {token_json}\n\n"

            # Save to session if session_id provided
            if req.session_id:
                try:
                    # Save user question
                    save_message(req.session_id, "user", req.question)
                    # Use enhanced sources if available, otherwise original
                    final_sources = enhanced_sources if enhanced_sources else sources_list
                    # Save assistant answer with sources, confidence, relevance, and suggestions
                    save_message(
                        req.session_id, 
                        "assistant", 
                        answer_content, 
                        sources=final_sources,
                        confidence=confidence,
                        relevance_score=relevance_score,
                        suggestions=suggestions
                    )
                except Exception as e:
                    logger.warning(f"Could not save session: {e}")

            yield "event: done\ndata: {}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            error_json = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {error_json}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/chat/export")
async def export_chat(session_id: str):
    """
    Export a chat session as PDF.
    
    Query params:
        session_id: ID of the session to export
        
    Returns:
        PDF file as download
    """
    if not session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        session = get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_title = session.get("title", "Chat Export")
        messages = session.get("messages", [])
        
        # Generate PDF bytes
        pdf_bytes = create_chat_export_pdf(session_title, messages)
        
        # Stream the PDF bytes as response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="chat_export_{session_id}.pdf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
