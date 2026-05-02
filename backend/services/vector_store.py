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

# Import document loader
from services.document_loader import load_document

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton instances (loads once, reuses)
_embeddings = None
_chroma_client = None
_vectorstore = None

# ✅ PART 5 IMPROVEMENT: Simple in-memory query cache for performance
_query_cache = {}
MAX_CACHE_SIZE = 100


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


def ingest_document(file_path: str, doc_id: str, filename: str) -> int:
    """
    Simple document ingestion with page-aware chunking.
    
    Supports: PDF, DOCX, TXT
    
    Returns number of chunks stored.
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    try:
        # Load document (PDF, DOCX, or TXT)
        logger.info(f"Loading {file_ext.upper()} file: {filename}")
        pages = load_document(file_path, filename)
        
        # Add doc_id to each page
        for page in pages:
            page.metadata["doc_id"] = doc_id
            page.metadata["filename"] = filename
        
        # Validate extraction
        if not pages or len(pages) == 0:
            logger.error(f"No pages extracted from {filename}")
            raise ValueError(f"No content could be extracted from {filename}")
        
        logger.info(f"✓ Extracted {len(pages)} pages from {filename}")
        
        # ─── SMART CHUNKING: Per-page to preserve source attribution ───
        all_chunks = []
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )
        
        pages_with_content = 0
        pages_empty = 0
        
        for page_num, page_doc in enumerate(pages, 1):
            page_number = page_doc.metadata.get("page", page_num)
            
            # Check page content before chunking
            if not page_doc.page_content or len(page_doc.page_content.strip()) == 0:
                logger.warning(f"Page {page_number} of {filename} has empty content - skipping")
                pages_empty += 1
                continue
            
            pages_with_content += 1
            
            # Chunk this page individually
            page_chunks = splitter.split_documents([page_doc])
            
            if not page_chunks or len(page_chunks) == 0:
                logger.warning(f"Chunking produced no output for page {page_number} of {filename}")
                continue
            
            logger.debug(
                f"Page {page_number}: {len(page_doc.page_content)} chars → "
                f"{len(page_chunks)} chunks"
            )
            
            # Add metadata to each chunk
            for chunk_idx, chunk in enumerate(page_chunks, 1):
                chunk.metadata["doc_id"] = doc_id
                chunk.metadata["filename"] = filename
                chunk.metadata["page"] = page_number
                chunk.metadata["chunk_id"] = f"{doc_id}_p{page_number}_c{chunk_idx}"
                chunk.metadata["chunk_index"] = chunk_idx
                chunk.metadata["chunks_on_page"] = len(page_chunks)
                
                all_chunks.append(chunk)
                
                logger.debug(
                    f"Created chunk: {chunk.metadata['chunk_id']} "
                    f"({len(chunk.page_content)} chars) "
                    f"on page {page_number}"
                )
        
        # Ensure we have chunks before storing
        if not all_chunks or len(all_chunks) == 0:
            logger.error(f"No chunks were created from {filename}")
            raise ValueError(f"Failed to create chunks from {filename}")
        
        logger.info(
            f"Split {filename} into {len(all_chunks)} chunks "
            f"across {pages_with_content} pages"
        )
        
        # Store all chunks in ChromaDB
        vectorstore = get_vectorstore()
        vectorstore.add_documents(all_chunks)
        
        logger.info(
            f"✓ Successfully stored {len(all_chunks)} chunks for {filename} "
            f"in vector store (doc_id: {doc_id})"
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
    
    Returns: list of (doc, score) tuples where score is 0.0-1.0
    
    ✅ PART 5 IMPROVEMENT: Query caching for frequently repeated searches
    """
    # ✅ PART 5: Check cache first
    cache_key = f"{query}:{','.join(sorted(doc_ids or []))}"
    if cache_key in _query_cache:
        logger.info(f"Cache hit for query: {query[:50]}...")
        return _query_cache[cache_key]
    
    vectorstore = get_vectorstore()
    
    # Get all results first
    results = vectorstore.similarity_search_with_score(
        query=query,
        k=settings.TOP_K_RESULTS * 2,
    )
    
    logger.debug(f"Query: '{query}' → Retrieved {len(results)} candidates")
    
    # Filter by doc_ids if specified
    if doc_ids:
        logger.debug(f"Filtering by doc_ids: {doc_ids}")
        results = [
            (doc, score) for doc, score in results 
            if doc.metadata.get("doc_id") in doc_ids
        ]
        logger.debug(f"After filtering: {len(results)} results match selected documents")
        results = results[:settings.TOP_K_RESULTS]
    else:
        logger.debug(f"No document filter - using all {len(results)} results")
        results = results[:settings.TOP_K_RESULTS]
    
    # Log final retrieved chunks
    for idx, (doc, score) in enumerate(results, 1):
        filename = doc.metadata.get("filename", "unknown")
        page = doc.metadata.get("page", "?")
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        
        logger.debug(
            f"  [{idx}] {filename}:p{page} (chunk: {chunk_id}) "
            f"score={score:.3f} content_len={len(doc.page_content)}"
        )
    
    # Safely get top score without index error
    top_score = results[0][1] if results and len(results) > 0 else 0.0
    
    logger.info(
        f"✓ Retrieved {len(results)} chunks for query. "
        f"Top score: {top_score:.3f}"
    )
    
    # ✅ PART 5: Store in cache (with size limit)
    if len(_query_cache) >= MAX_CACHE_SIZE:
        logger.debug(f"Query cache full ({MAX_CACHE_SIZE}), clearing...")
        _query_cache.clear()
    _query_cache[cache_key] = results
    
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
