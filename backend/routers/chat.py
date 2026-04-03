"""
Chat Router
POST /api/chat         - Non-streaming chat
POST /api/chat/stream  - Server-Sent Events streaming chat
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import logging

from services.rag_chain import run_rag_chain, stream_rag_chain

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str
    chat_history: list[dict] = []
    doc_ids: Optional[list[str]] = None


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
        try:
            async for chunk in stream_rag_chain(
                question=req.question,
                chat_history=req.chat_history,
                doc_ids=req.doc_ids,
            ):
                if chunk.startswith("__SOURCES__"):
                    sources_json = chunk.replace("__SOURCES__", "").strip()
                    yield f"event: sources\ndata: {sources_json}\n\n"
                else:
                    # Each token as a data event
                    token_json = json.dumps({"token": chunk})
                    yield f"data: {token_json}\n\n"

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
