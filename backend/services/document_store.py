"""
Document Store - tracks uploaded PDFs in a simple JSON file.
No database required - perfect for students and local development.
"""
import json
import os
from datetime import datetime
from typing import Optional

STORE_PATH = "./uploads/documents.json"

def _load() -> dict:
    if os.path.exists(STORE_PATH):
        with open(STORE_PATH, "r") as f:
            return json.load(f)
    return {"documents": []}

def _save(data: dict):
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def add_document(doc_id: str, filename: str, file_path: str, chunk_count: int, file_size: int):
    data = _load()
    data["documents"].append({
        "id": doc_id,
        "filename": filename,
        "file_path": file_path,
        "chunk_count": chunk_count,
        "file_size": file_size,
        "uploaded_at": datetime.now().isoformat(),
    })
    _save(data)

def get_all_documents() -> list[dict]:
    return _load()["documents"]

def get_document(doc_id: str) -> Optional[dict]:
    for doc in _load()["documents"]:
        if doc["id"] == doc_id:
            return doc
    return None

def delete_document(doc_id: str) -> bool:
    data = _load()
    before = len(data["documents"])
    data["documents"] = [d for d in data["documents"] if d["id"] != doc_id]
    _save(data)
    return len(data["documents"]) < before
