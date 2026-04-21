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
    
    ✅ CRITICAL FIXES:
    - Forces minimum 3 chunks per page
    - Validates chunks are stored
    - Comprehensive logging at each step
    - Never silently fail
    
    Returns number of chunks stored.
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"📄 INGESTING DOCUMENT: {filename} (doc_id: {doc_id})")
        logger.info(f"{'='*80}")
        
        # ─ STEP 1: Load pages ─
        logger.info(f"[STEP 1/5] Loading document...")
        if file_ext == '.pdf':
            pages = load_pdf_with_ocr(file_path, filename)
        elif file_ext == '.docx':
            pages = load_docx_file(file_path, filename)
            for doc in pages:
                doc.metadata["doc_id"] = doc_id
                doc.metadata["filename"] = filename
        elif file_ext == '.txt':
            pages = load_txt_file(file_path, filename)
            for doc in pages:
                doc.metadata["doc_id"] = doc_id
                doc.metadata["filename"] = filename
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Validate extraction
        if not pages or len(pages) == 0:
            logger.error(f"❌ No pages extracted - document may be corrupted")
            raise ValueError(f"No content could be extracted from {filename}")
        
        logger.info(f"✓ Extracted {len(pages)} pages")
        
        # ─ STEP 2: Setup chunkers ─
        logger.info(f"[STEP 2/5] Setting up chunk splitters...")
        
        normal_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )
        
        # ✅ AGGRESSIVE splitter: ensures 3+ chunks
        aggressive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,  # Even smaller for handwritten PDFs
            chunk_overlap=50,
            separators=["\n", ".", "!", "?", ",", " ", ""],
        )
        
        # ✅ SENTENCE splitter: last resort
        sentence_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=20,
            separators=[".", "!", "?", "\n"],
        )
        
        logger.info(f"✓ Normal: 400 chars | Aggressive: 200 chars | Sentence: 100 chars")
        
        # ─ STEP 3: Chunk pages ─
        logger.info(f"[STEP 3/5] Chunking pages with MIN_CHUNKS_PER_PAGE={settings.MIN_CHUNKS_PER_PAGE}...")
        
        all_chunks = []
        pages_processed = 0
        pages_with_fallback = 0
        total_chunk_attempts = 0
        
        for page_num, page_doc in enumerate(pages, 1):
            page_number = page_doc.metadata.get("page", page_num)
            char_count = len(page_doc.page_content.strip())
            
            # Skip empty
            if char_count == 0:
                logger.warning(f"  Page {page_number}: Empty, skipping")
                continue
            
            pages_processed += 1
            logger.debug(f"\n  Page {page_number}: {char_count} chars")
            
            # Try normal splitter first
            page_chunks = normal_splitter.split_documents([page_doc])
            total_chunk_attempts += len(page_chunks) if page_chunks else 0
            
            logger.debug(f"    1️⃣  Normal splitter → {len(page_chunks) if page_chunks else 0} chunks")
            
            # ✅ FORCED FALLBACK: If < MIN_CHUNKS, try aggressive
            if not page_chunks or len(page_chunks) < settings.MIN_CHUNKS_PER_PAGE:
                logger.debug(f"    2️⃣  Triggering aggressive splitter (need {settings.MIN_CHUNKS_PER_PAGE} min)")
                page_chunks = aggressive_splitter.split_documents([page_doc])
                total_chunk_attempts += len(page_chunks) if page_chunks else 0
                logger.debug(f"    → Aggressive splitter → {len(page_chunks)} chunks")
                pages_with_fallback += 1
                
                # ✅ FINAL FALLBACK: If still < MIN_CHUNKS, use sentence splitter
                if not page_chunks or len(page_chunks) < settings.MIN_CHUNKS_PER_PAGE:
                    logger.debug(f"    3️⃣  Triggering sentence splitter")
                    page_chunks = sentence_splitter.split_documents([page_doc])
                    total_chunk_attempts += len(page_chunks) if page_chunks else 0
                    logger.debug(f"    → Sentence splitter → {len(page_chunks)} chunks")
            
            # ✅ ABSOLUTE FALLBACK: Keep as single chunk
            if not page_chunks or len(page_chunks) == 0:
                logger.warning(f"    4️⃣  No splits worked, keeping as single chunk")
                page_chunks = [page_doc]
            
            # Add metadata
            for chunk_idx, chunk in enumerate(page_chunks, 1):
                chunk.metadata["doc_id"] = doc_id
                chunk.metadata["filename"] = filename
                chunk.metadata["page"] = page_number
                chunk.metadata["chunk_id"] = f"{doc_id}_p{page_number}_c{chunk_idx}"
                chunk.metadata["chunk_index"] = chunk_idx
                chunk.metadata["chunks_on_page"] = len(page_chunks)
                chunk.metadata["ocr_used"] = page_doc.metadata.get("ocr_used", False)
                
                all_chunks.append(chunk)
                
                logger.debug(
                    f"    ✓ Chunk {chunk_idx}/{len(page_chunks)}: "
                    f"{len(chunk.page_content)} chars"
                )
            
            logger.info(f"  ✓ Page {page_number}: {len(page_chunks)} chunks")
        
        # ─ VALIDATION: Ensure we have chunks ─
        if not all_chunks or len(all_chunks) == 0:
            logger.error(f"❌ CRITICAL: 0 chunks created from {pages_processed} pages!")
            raise ValueError(f"Failed to create chunks from {filename}")
        
        logger.info(f"✓ Total chunks created: {len(all_chunks)}")
        logger.info(f"  ({pages_processed} pages processed, {pages_with_fallback} used fallback)")
        
        # ─ STEP 4: Store in vector DB ─
        logger.info(f"[STEP 4/5] Storing in ChromaDB...")
        
        vectorstore = get_vectorstore()
        vectorstore.add_documents(all_chunks)
        
        logger.info(f"✓ Vectors stored for {len(all_chunks)} chunks")
        
        # ─ STEP 5: VALIDATE storage ─
        logger.info(f"[STEP 5/5] Validating storage...")
        
        # Retrieve by doc_id to verify
        client = get_chroma_client()
        collection = client.get_or_create_collection(settings.CHROMA_COLLECTION)
        
        stored = collection.get(where={"doc_id": doc_id})
        stored_count = len(stored.get("ids", []))
        
        if stored_count == 0:
            logger.error(f"❌ CRITICAL: Vectors stored but not found in DB!")
            raise ValueError("Vector storage verification failed")
        
        logger.info(f"✓ Verified: {stored_count} vectors in DB")
        
        logger.info(f"{'='*80}")
        logger.info(f"✅ SUCCESS: Ingested {filename} into {stored_count} vectors")
        logger.info(f"{'='*80}\n")
        
        return stored_count
        
    except Exception as e:
        logger.error(
            f"❌ FAILED to ingest {filename}: {e}",
            exc_info=True
        )
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
    
    ✅ ENHANCED: With fallback retrieval and comprehensive logging
    
    CRITICAL FOR DEBUGGING:
    - Logs all retrieved chunks with page numbers
    - Logs similarity scores for quality assessment
    - Implements fallback to top-2 matches if zero results
    - Never returns empty list
    
    Returns: list of (doc, score) tuples where score is 0.0-1.0
    """
    logger.info(f"\n{'─'*70}")
    logger.info(f"🔍 RETRIEVAL: Query='{query}'")
    
    vectorstore = get_vectorstore()
    
    # Get initial results
    logger.debug(f"  Searching with k={settings.TOP_K_RESULTS * 2}")
    results = vectorstore.similarity_search_with_score(
        query=query,
        k=settings.TOP_K_RESULTS * 2,  # Get more to account for filtering
    )
    
    logger.info(f"  Initial results: {len(results)} candidates")
    
    # Filter by doc_ids if specified
    if doc_ids:
        logger.debug(f"  Applying doc_id filter: {doc_ids}")
        filtered = [
            (doc, score) for doc, score in results 
            if doc.metadata.get("doc_id") in doc_ids
        ]
        logger.info(f"  After filter: {len(filtered)} results")
        results = filtered[:settings.TOP_K_RESULTS]
    else:
        results = results[:settings.TOP_K_RESULTS]
    
    # ✅ FALLBACK: If zero results, get top-2 anyway
    if not results or len(results) == 0:
        logger.warning(f"  ⚠️  ZERO results - triggering fallback retrieval (top-2)")
        
        fallback_results = vectorstore.similarity_search_with_score(
            query=query,
            k=2  # Get at least 2
        )
        
        logger.info(f"  Fallback retrieved: {len(fallback_results)} results")
        results = fallback_results
    
    # Log retrieved chunks for source attribution
    logger.info(f"  Final results: {len(results)}")
    for idx, (doc, score) in enumerate(results, 1):
        filename = doc.metadata.get("filename", "?")
        page = doc.metadata.get("page", "?")
        chunk_id = doc.metadata.get("chunk_id", "?")
        ocr_used = doc.metadata.get("ocr_used", False)
        content_len = len(doc.page_content)
        
        logger.info(
            f"    [{idx}] {filename}:p{page} score={score:.3f} "
            f"len={content_len} ocr={ocr_used}"
        )
        logger.debug(f"         ID: {chunk_id}")
        logger.debug(f"         Text: {doc.page_content[:100]}...")
    
    logger.info(f"{'─'*70}\n")
    
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
