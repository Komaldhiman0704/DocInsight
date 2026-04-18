"""
Vector Store Service
Uses ChromaDB (local, free) + HuggingFace sentence-transformers (free, runs locally)
No API keys needed for embeddings!
Includes OCR support for scanned PDFs.
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

# Import OCR-enabled loader
from services.document_loader import load_pdf_with_ocr

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
    Smart document ingestion with page-aware chunking.
    
    CRITICAL FOR SOURCE ATTRIBUTION:
    - Chunks per page (NOT full document)
    - Preserves page metadata through pipeline
    - Assigns unique chunk_id for tracking
    - Logs chunk creation for debugging
    
    Supports: PDF (with OCR support), DOCX, TXT
    
    For PDFs:
    - Attempts standard text extraction first
    - Falls back to OCR for scanned PDFs
    - Preserves page numbers through chunking
    - Detects and marks OCR-extracted pages
    
    Returns number of chunks stored.
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    try:
        if file_ext == '.pdf':
            # Load PDF with OCR support - returns page-wise documents
            logger.info(f"Loading PDF with OCR support: {filename}")
            pages = load_pdf_with_ocr(file_path, filename)
            
            # Add doc_id to each page
            for page in pages:
                page.metadata["doc_id"] = doc_id
                page.metadata["filename"] = filename
        
        elif file_ext == '.docx':
            # Load DOCX
            pages = load_docx_file(file_path, filename)
            for doc in pages:
                doc.metadata["doc_id"] = doc_id
                doc.metadata["filename"] = filename
        
        elif file_ext == '.txt':
            # Load TXT
            pages = load_txt_file(file_path, filename)
            for doc in pages:
                doc.metadata["doc_id"] = doc_id
                doc.metadata["filename"] = filename
        
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Validate extraction
        if not pages:
            raise ValueError(f"No content could be extracted from {filename}")
        
        logger.info(
            f"Extracted {len(pages)} pages from {filename} - "
            f"now chunking per-page for source attribution"
        )
        
        # ─── SMART CHUNKING: Per-page to preserve source attribution ───
        all_chunks = []
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )
        
        for page_num, page_doc in enumerate(pages, 1):
            page_number = page_doc.metadata.get("page", page_num)
            
            # Chunk this page individually
            page_chunks = splitter.split_documents([page_doc])
            
            # Add comprehensive metadata to each chunk
            for chunk_idx, chunk in enumerate(page_chunks, 1):
                # Preserve all original metadata
                chunk.metadata["doc_id"] = doc_id
                chunk.metadata["filename"] = filename
                chunk.metadata["page"] = page_number
                
                # Add new tracking metadata
                chunk.metadata["chunk_id"] = f"{doc_id}_p{page_number}_c{chunk_idx}"
                chunk.metadata["chunk_index"] = chunk_idx
                chunk.metadata["chunks_on_page"] = len(page_chunks)
                
                # Preserve quality metrics from loader if available
                if "quality_score" in page_doc.metadata:
                    chunk.metadata["quality_score"] = page_doc.metadata["quality_score"]
                if "ocr_used" in page_doc.metadata:
                    chunk.metadata["ocr_used"] = page_doc.metadata["ocr_used"]
                if "char_count" in page_doc.metadata:
                    chunk.metadata["page_char_count"] = page_doc.metadata["char_count"]
                
                all_chunks.append(chunk)
                
                # Debug logging
                logger.debug(
                    f"Created chunk: {chunk.metadata['chunk_id']} "
                    f"({len(chunk.page_content)} chars) "
                    f"on page {page_number}"
                )
        
        logger.info(
            f"Split {filename} into {len(all_chunks)} chunks "
            f"across {len(pages)} pages"
        )
        
        # Store all chunks in ChromaDB
        vectorstore = get_vectorstore()
        vectorstore.add_documents(all_chunks)
        
        logger.info(
            f"✓ Stored {len(all_chunks)} chunks for {filename} in vector store"
        )
        return len(all_chunks)
        
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
    
    CRITICAL FOR DEBUGGING SOURCE ATTRIBUTION:
    - Logs all retrieved chunks with page numbers
    - Logs similarity scores for quality assessment
    - Logs filtering operations
    - Preserves metadata through entire pipeline
    
    Returns: list of (doc, score) tuples where score is 0.0-1.0
    """
    vectorstore = get_vectorstore()
    
    # Get all results first
    results = vectorstore.similarity_search_with_score(
        query=query,
        k=settings.TOP_K_RESULTS * 2,  # Get more to account for filtering
    )
    
    # Log retrieval for debugging
    logger.debug(f"Query: '{query}' → Retrieved {len(results)} candidates")
    
    # Filter by doc_ids if specified
    if doc_ids:
        logger.debug(f"Filtering by doc_ids: {doc_ids}")
        results = [
            (doc, score) for doc, score in results 
            if doc.metadata.get("doc_id") in doc_ids
        ]
        logger.debug(f"After filtering: {len(results)} results match selected documents")
        # Trim to TOP_K_RESULTS after filtering
        results = results[:settings.TOP_K_RESULTS]
    else:
        logger.debug(f"No document filter - using all {len(results)} results")
        results = results[:settings.TOP_K_RESULTS]
    
    # Log final retrieved chunks for source attribution verification
    for idx, (doc, score) in enumerate(results, 1):
        filename = doc.metadata.get("filename", "unknown")
        page = doc.metadata.get("page", "?")
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        ocr_used = doc.metadata.get("ocr_used", False)
        quality = doc.metadata.get("quality_score", "unknown")
        
        logger.debug(
            f"  [{idx}] {filename}:p{page} (chunk: {chunk_id}) "
            f"score={score:.3f} ocr={ocr_used} quality={quality} "
            f"content_len={len(doc.page_content)}"
        )
    
    logger.info(
        f"✓ Retrieved {len(results)} chunks for query. "
        f"Top score: {results[0][1]:.3f if results else 0:.3f}"
    )
    
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
