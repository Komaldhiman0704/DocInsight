"""
Configuration - loads from .env file
All free services, no paid APIs required
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # LLM Provider - choose: "groq" (free) | "ollama" (local) | "openai"
    LLM_PROVIDER: str = "groq"

    # Groq API (FREE - https://console.groq.com)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Latest Groq production model

    # Ollama (fully local, no API key needed)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # OpenAI (paid fallback)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # HuggingFace Embeddings (FREE, runs locally)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ChromaDB (local vector DB, no setup needed)
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION: str = "pdf_documents"

    # File uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # RAG settings - OCR-optimized chunking
    # Reduced chunk_size for better granularity in scanned PDFs
    # Scanned PDFs avg 300 chars/page; native PDFs avg 2000 chars/page
    CHUNK_SIZE: int = 400          # ✓ Down from 1000 - handles short OCR pages
    CHUNK_OVERLAP: int = 60        # ✓ Down from 200 - maintains continuity
    TOP_K_RESULTS: int = 5         # ✓ Up from 4 - better retrieval coverage
    
    # OCR Detection thresholds (scaled by document size)
    OCR_MIN_CHAR_THRESHOLD: int = 100     # Minimum chars for successful extraction
    OCR_MIN_VALID_RATIO: float = 0.5      # Minimum valid char ratio (50%)
    OCR_QUALITY_MIN_RATIO: float = 0.6    # Threshold for "good" quality (60%)
    
    # Chunking fallback (force minimum chunks per page)
    MIN_CHUNKS_PER_PAGE: int = 3          # ✓ New: Force at least 3 chunks if possible
    MIN_CHUNK_SIZE: int = 200             # ✓ New: Minimum viable chunk (chars)
    
    # Query preprocessing
    QUERY_NORMALIZE: bool = True           # ✓ New: Enable query preprocessing
    QUERY_KEYWORDS_MAX: int = 5            # ✓ New: Extract top-5 keywords for hybrid search
    
    # Retrieval fallback
    ENABLE_FALLBACK_RETRIEVAL: bool = True # ✓ New: Show top-2 when no results
    HYBRID_RETRIEVAL_ENABLED: bool = True  # ✓ New: Combine vector + keyword search

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
