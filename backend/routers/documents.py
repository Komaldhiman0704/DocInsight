"""
Documents Router
GET    /api/documents       - List all documents
DELETE /api/documents/{id}  - Delete a document
GET    /api/documents/{id}/pdf - Get PDF file with CORS headers
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from services.document_store import get_all_documents, get_document, delete_document as store_delete
from services.vector_store import delete_document as vector_delete

router = APIRouter()

@router.get("/documents")
def list_documents():
    """Return all uploaded documents with metadata"""
    docs = get_all_documents()
    return {"documents": docs, "count": len(docs)}

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Delete a document from vector store + file system"""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, f"Document {doc_id} not found")

    # Delete from ChromaDB
    vector_delete(doc_id)

    # Delete metadata
    store_delete(doc_id)

    # Delete physical file
    if os.path.exists(doc["file_path"]):
        os.remove(doc["file_path"])

    return {"success": True, "message": f"Document '{doc['filename']}' deleted"}


@router.get("/documents/{doc_id}/summary")
def get_document_summary(doc_id: str):
    """Get the AI-generated summary for a document"""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, f"Document {doc_id} not found")
    
    return {
        "doc_id": doc_id,
        "filename": doc["filename"],
        "summary": doc.get("summary"),
        "generating": doc.get("summary") is None,
    }


@router.get("/documents/{doc_id}/pdf")
def get_pdf(doc_id: str):
    """Serve PDF file with proper CORS headers for inline preview"""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, f"Document {doc_id} not found")
    
    file_path = doc["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(404, f"PDF file not found: {file_path}")
    
    # FileResponse automatically handles Range requests and streaming
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{doc['filename']}\"",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Range",
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
        }
    )
