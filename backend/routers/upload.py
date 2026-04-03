"""
Upload Router
POST /api/upload  - Upload and ingest a PDF
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uuid
import os
import shutil
import logging

from config import get_settings
from services.vector_store import ingest_pdf
from services.document_store import add_document

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"application/pdf", "application/x-pdf"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file, process it into chunks, and store embeddings.
    Returns document metadata.
    
    Raises:
      400: Invalid file type or empty file
      413: File exceeds max size
      500: Processing error
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported. Please upload a .pdf file.")

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
        logger.info(f"Processing PDF: {file.filename} ({len(content) / (1024*1024):.1f}MB)")
        # Ingest into vector store
        chunk_count = ingest_pdf(file_path, doc_id, file.filename)

        # Save metadata
        add_document(
            doc_id=doc_id,
            filename=file.filename,
            file_path=file_path,
            chunk_count=chunk_count,
            file_size=len(content),
        )
        
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
        logger.error(f"PDF processing failed: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to process PDF: {str(e)}")
