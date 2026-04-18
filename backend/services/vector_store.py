"""
Vector Store Service
Uses ChromaDB (local, free) + HuggingFace sentence-transformers (free, runs locally)
No API keys needed for embeddings!
"""
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton instances (loads once, reuses)
_embeddings = None
_chroma_client = None
_vectorstore = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    return _embeddings

def get_chroma_client():
    """Get or create singleton ChromaDB client"""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        logger.info(f"Initializing ChromaDB client at {settings.CHROMA_PERSIST_DIR}")
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _chroma_client

def get_vectorstore():
    """Get or create singleton ChromaDB vector store"""
    global _vectorstore
    if _vectorstore is None:
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        logger.info(f"Initializing Chroma vectorstore from {settings.CHROMA_PERSIST_DIR}")
        _vectorstore = Chroma(
            collection_name=settings.CHROMA_COLLECTION,
            embedding_function=get_embeddings(),
            persist_directory=settings.CHROMA_PERSIST_DIR,
            client=get_chroma_client(),
        )
    return _vectorstore


def load_docx_file(file_path: str, filename: str) -> list[Document]:
    """
    Load a DOCX file and return list of Document objects.
    Each paragraph becomes a document with metadata.
    """
    try:
        from docx import Document as DocxDocument
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")
    
    logger.info(f"Loading DOCX file: {filename}")
    doc = DocxDocument(file_path)
    
    # Extract all paragraphs
    documents = []
    for para_idx, para in enumerate(doc.paragraphs):
        if para.text.strip():  # Skip empty paragraphs
            doc_obj = Document(
                page_content=para.text,
                metadata={"page": para_idx + 1, "filename": filename}
            )
            documents.append(doc_obj)
    
    logger.info(f"Extracted {len(documents)} paragraphs from {filename}")
    return documents


def load_txt_file(file_path: str, filename: str) -> list[Document]:
    """
    Load a TXT file and return list of Document objects.
    """
    logger.info(f"Loading TXT file: {filename}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by double newlines (paragraphs) first
    paragraphs = content.split('\n\n')
    documents = []
    
    for para_idx, para in enumerate(paragraphs):
        if para.strip():  # Skip empty sections
            doc_obj = Document(
                page_content=para.strip(),
                metadata={"page": para_idx + 1, "filename": filename}
            )
            documents.append(doc_obj)
    
    logger.info(f"Extracted {len(documents)} sections from {filename}")
    return documents


def ingest_document(file_path: str, doc_id: str, filename: str) -> int:
    """
    Generic document ingestion function that detects file type and processes accordingly.
    Supports: PDF, DOCX, TXT
    Returns number of chunks stored.
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    try:
        if file_ext == '.pdf':
            # Load PDF
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            
            # Add metadata
            for i, page in enumerate(pages):
                page.metadata["doc_id"] = doc_id
                page.metadata["filename"] = filename
                page.metadata["page"] = i + 1
        
        elif file_ext == '.docx':
            # Load DOCX
            pages = load_docx_file(file_path, filename)
            for doc in pages:
                doc.metadata["doc_id"] = doc_id
        
        elif file_ext == '.txt':
            # Load TXT
            pages = load_txt_file(file_path, filename)
            for doc in pages:
                doc.metadata["doc_id"] = doc_id
        
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )
        chunks = splitter.split_documents(pages)
        
        logger.info(f"Split {filename} into {len(chunks)} chunks")
        
        # Add doc_id to each chunk for filtering
        for chunk in chunks:
            chunk.metadata["doc_id"] = doc_id
            chunk.metadata["filename"] = filename
        
        # Store in ChromaDB
        vectorstore = get_vectorstore()
        vectorstore.add_documents(chunks)
        
        logger.info(f"Stored {len(chunks)} chunks for {filename}")
        return len(chunks)
        
    except Exception as e:
        logger.error(f"Failed to ingest document {filename}: {e}", exc_info=True)
        raise


# Keep ingest_pdf for backward compatibility
def ingest_pdf(file_path: str, doc_id: str, filename: str) -> int:
    """
    Backward compatibility wrapper for ingest_document.
    """
    return ingest_document(file_path, doc_id, filename)

def delete_document(doc_id: str):
    """Delete all chunks belonging to a document"""
    client = get_chroma_client()
    collection = client.get_or_create_collection(settings.CHROMA_COLLECTION)
    # Delete by metadata filter
    collection.delete(where={"doc_id": doc_id})
    logger.info(f"Deleted document {doc_id} from vector store")

def get_retriever(doc_ids: list[str] | None = None):
    """
    Get a retriever, optionally filtered to specific documents.
    """
    vectorstore = get_vectorstore()

    search_kwargs = {"k": settings.TOP_K_RESULTS}
    if doc_ids:
        search_kwargs["filter"] = {"doc_id": {"$in": doc_ids}}

    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )

def get_docs_with_scores(query: str, doc_ids: list[str] | None = None) -> list[tuple]:
    """
    Get documents with similarity scores for a query.
    Returns: list of (doc, score) tuples where score is 0.0-1.0
    """
    vectorstore = get_vectorstore()
    
    # Get all results first
    results = vectorstore.similarity_search_with_score(
        query=query,
        k=settings.TOP_K_RESULTS * 2,  # Get more to account for filtering
    )
    
    # Filter by doc_ids if specified
    if doc_ids:
        results = [
            (doc, score) for doc, score in results 
            if doc.metadata.get("doc_id") in doc_ids
        ]
        # Trim to TOP_K_RESULTS after filtering
        results = results[:settings.TOP_K_RESULTS]
    else:
        results = results[:settings.TOP_K_RESULTS]
    
    return results

def get_document_count(doc_id: str) -> int:
    """Return number of chunks stored for a document"""
    client = get_chroma_client()
    collection = client.get_or_create_collection(settings.CHROMA_COLLECTION)
    results = collection.get(where={"doc_id": doc_id})
    return len(results["ids"])

def shutdown_vectorstore():
    """
    Cleanup singleton instances on app shutdown.
    Call this during FastAPI shutdown events.
    """
    global _vectorstore, _chroma_client, _embeddings
    try:
        if _vectorstore is not None:
            logger.info("Shutting down vectorstore...")
            _vectorstore = None
        if _chroma_client is not None:
            logger.info("Shutting down Chroma client...")
            _chroma_client = None
        logger.info("Vector store shutdown complete")
    except Exception as e:
        logger.error(f"Error during vectorstore shutdown: {e}")
