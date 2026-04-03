"""
Documents Router
GET    /api/documents       - List all documents
DELETE /api/documents/{id}  - Delete a document
"""
from fastapi import APIRouter, HTTPException
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
