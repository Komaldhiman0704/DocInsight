"""
DocInsight - FastAPI Backend
Free stack: HuggingFace Embeddings + ChromaDB + Groq LLM (free tier)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from routers import chat, upload, documents, sessions
from services.vector_store import shutdown_vectorstore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocInsight API",
    description="RAG-powered document chatbot using LangChain + ChromaDB",
    version="1.0.0"
)

# CORS - allow frontend on port 5173 (Vite default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded PDFs for preview
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(chat.router,   prefix="/api", tags=["Chat"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])

@app.on_event("startup")
async def startup_event():
    """Log system status on startup"""
    logger.info("=" * 80)
    logger.info("DocInsight Backend Starting")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on app shutdown"""
    shutdown_vectorstore()

@app.get("/")
def root():
    return {"status": "DocInsight API running", "version": "1.0.0"}

@app.get("/health")
def health():
    """Enhanced health check with component status"""
    from config import get_settings
    settings = get_settings()
    return {
        "status": "ok",
        "backend": "running",
        "llm_provider": settings.LLM_PROVIDER,
        "embeddings_model": "HuggingFace (local)",
        "vector_store": "ChromaDB (local)",
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB
    }
