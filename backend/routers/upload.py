"""
Upload Router
POST /api/upload  - Upload and ingest a document (PDF, DOCX, or TXT)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
import os
import shutil
import logging

from config import get_settings
from services.vector_store import ingest_document
from services.document_store import add_document, update_document_summary
from services.summarizer import generate_summary

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf", 
    "application/x-pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "text/plain"  # TXT
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


async def generate_summary_and_save(doc_id: str, file_path: str, filename: str):
    """Background task to generate and save document summary"""
    try:
        summary = await generate_summary(file_path, filename)
        if summary:
            update_document_summary(doc_id, summary)
            logger.info(f"Summary saved for document {doc_id}")
    except Exception as e:
        logger.error(f"Background summary generation failed for {doc_id}: {e}", exc_info=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload a document (PDF, DOCX, or TXT), process it into chunks, and store embeddings.
    Returns document metadata.
    
    Raises:
      400: Invalid file type or empty file
      413: File exceeds max size
      500: Processing error
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400, 
            f"Unsupported file type: {file_ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()
    
    # Validate file not empty
    if not content:
        raise HTTPException(400, "Uploaded file is empty")

    # Check file size
    if len(content) > MAX_BYTES:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            413, 
            f"File too large ({size_mb:.1f}MB). Maximum allowed: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Generate unique ID and save file
    doc_id = str(uuid.uuid4())[:8]
    safe_name = f"{doc_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        file_type = file_ext[1:].upper()  # Remove the dot and uppercase
        logger.info(f"Processing {file_type}: {file.filename} ({len(content) / (1024*1024):.1f}MB)")
        
        # Ingest document (handles PDF, DOCX, TXT)
        chunk_count = ingest_document(file_path, doc_id, file.filename)

        # Save metadata
        add_document(
            doc_id=doc_id,
            filename=file.filename,
            file_path=file_path,
            chunk_count=chunk_count,
            file_size=len(content),
        )
        
        # Generate summary in background (non-blocking)
        if background_tasks:
            background_tasks.add_task(generate_summary_and_save, doc_id, file_path, file.filename)
        
        logger.info(f"Successfully processed {file.filename} into {chunk_count} chunks")

        return {
            "success": True,
            "document": {
                "id": doc_id,
                "filename": file.filename,
                "chunk_count": chunk_count,
                "file_size": len(content),
                "file_url": f"/uploads/{safe_name}",
            }
        }

    except Exception as e:
        # Cleanup on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Document processing failed: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to process document: {str(e)}")
