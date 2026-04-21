#!/usr/bin/env python
"""
CRITICAL DEBUG SCRIPT: OCR + RAG Pipeline Validation

Tests:
1. OCR detection for handwritten PDFs
2. Page splitting and chunking
3. Vector storage
4. Retrieval fallback
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import logging
import asyncio
from pathlib import Path

# Configure logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s | %(name)-30s | %(message)s'
)

logger = logging.getLogger(__name__)

from config import get_settings
from services.document_loader import load_pdf_with_ocr, detect_scanned_pdf, extract_text_with_ocr
from services.vector_store import ingest_document, get_docs_with_scores, get_document_count, get_chroma_client
from services.rag_chain import normalize_query

settings = get_settings()

print("\n" + "="*80)
print("OCR + RAG PIPELINE DEBUG SUITE".center(80))
print("="*80 + "\n")

# ────────────────────────────────────────────────────────────────────────────────
# TEST 1: Configuration Check
# ────────────────────────────────────────────────────────────────────────────────

print("\n[TEST 1/5] CONFIGURATION CHECK")
print("-" * 80)

print(f"  CHUNK_SIZE: {settings.CHUNK_SIZE}")
print(f"  CHUNK_OVERLAP: {settings.CHUNK_OVERLAP}")
print(f"  MIN_CHUNKS_PER_PAGE: {settings.MIN_CHUNKS_PER_PAGE}")
print(f"  MIN_CHUNK_SIZE: {settings.MIN_CHUNK_SIZE}")
print(f"  TOP_K_RESULTS: {settings.TOP_K_RESULTS}")
print(f"  OCR_MIN_CHAR_THRESHOLD: {settings.OCR_MIN_CHAR_THRESHOLD}")
print(f"  OCR_MIN_VALID_RATIO: {settings.OCR_MIN_VALID_RATIO}")
print(f"  ENABLE_FALLBACK_RETRIEVAL: {settings.ENABLE_FALLBACK_RETRIEVAL}")

# ────────────────────────────────────────────────────────────────────────────────
# TEST 2: Find a Handwritten PDF in uploads
# ────────────────────────────────────────────────────────────────────────────────

print("\n[TEST 2/5] FINDING TEST DOCUMENT")
print("-" * 80)

test_pdf = None
uploads_dir = settings.UPLOAD_DIR

if os.path.exists(uploads_dir):
    pdf_files = list(Path(uploads_dir).glob("*.pdf"))
    if pdf_files:
        # Pick first PDF
        test_pdf = str(pdf_files[0])
        print(f"  Found PDF: {Path(test_pdf).name}")
    else:
        print(f"  ** No PDFs in {uploads_dir}")
else:
    print(f"  ** Upload dir not found: {uploads_dir}")

if not test_pdf:
    print("\n** No test PDF found. Create a simple test document...")
    # Create a test PDF path (won't exist, but we can test the logic)
    test_pdf = os.path.join(uploads_dir, "test_handwritten.pdf")
    print(f"  (Would test with: {test_pdf})")

# ────────────────────────────────────────────────────────────────────────────────
# TEST 3: OCR Detection
# ────────────────────────────────────────────────────────────────────────────────

print("\n[TEST 3/5] OCR DETECTION")
print("-" * 80)

if os.path.exists(test_pdf):
    try:
        print(f"  Testing: {Path(test_pdf).name}")
        is_scanned = detect_scanned_pdf(test_pdf)
        print(f"  Result: {'SCANNED (needs OCR)' if is_scanned else 'NATIVE TEXT'}")
    except Exception as e:
        print(f"  ** Error: {e}")
else:
    print(f"  ** Skipped (PDF not found)")

# ────────────────────────────────────────────────────────────────────────────────
# TEST 4: Text Extraction
# ────────────────────────────────────────────────────────────────────────────────

print("\n[TEST 4/5] TEXT EXTRACTION")
print("-" * 80)

if os.path.exists(test_pdf):
    try:
        print(f"  Extracting text...")
        text = extract_text_with_ocr(test_pdf)
        
        print(f"  OK Extracted {len(text)} characters")
        print(f"  First 200 chars: {text[:200]}")
        print(f"  Quality: {'Good' if len(text) > 500 else 'Poor' if len(text) > 50 else 'Very Poor'}")
        
    except Exception as e:
        print(f"  ** Error: {e}")
else:
    print(f"  ** Skipped (PDF not found)")

# ────────────────────────────────────────────────────────────────────────────────
# TEST 5: Full Pipeline (Load -> Chunk -> Store -> Retrieve)
# ────────────────────────────────────────────────────────────────────────────────

print("\n[TEST 5/5] FULL PIPELINE TEST")
print("-" * 80)

if os.path.exists(test_pdf):
    try:
        doc_id = "test_doc_123"
        filename = Path(test_pdf).name
        
        print(f"\n  Step 1: Loading PDF...")
        pages = load_pdf_with_ocr(test_pdf, filename)
        print(f"  OK Loaded {len(pages)} pages")
        
        for idx, page in enumerate(pages, 1):
            print(f"    Page {idx}: {len(page.page_content)} chars")
        
        print(f"\n  Step 2: Ingesting document...")
        chunk_count = ingest_document(test_pdf, doc_id, filename)
        print(f"  OK Created {chunk_count} chunks")
        
        print(f"\n  Step 3: Verifying in DB...")
        stored_count = get_document_count(doc_id)
        print(f"  OK Verified {stored_count} vectors in DB")
        
        print(f"\n  Step 4: Testing retrieval...")
        test_queries = [
            "What is this document?",
            "Tell me about the content",
            "Important information"
        ]
        
        for query in test_queries:
            print(f"\n    Query: '{query}'")
            docs_with_scores = get_docs_with_scores(query, [doc_id])
            print(f"    Results: {len(docs_with_scores)}")
            
            if len(docs_with_scores) == 0:
                print(f"    ** ZERO RESULTS!")
            else:
                for idx, (doc, score) in enumerate(docs_with_scores, 1):
                    print(f"      [{idx}] Page {doc.metadata.get('page')}, score={score:.3f}")
        
        print(f"\n  OK Pipeline test COMPLETE")
        
    except Exception as e:
        logger.exception(f"** Pipeline error: {e}")
else:
    print(f"  ** Skipped (PDF not found)")

print("\n" + "="*80)
print("DEBUG COMPLETE".center(80))
print("="*80 + "\n")

print("\nNEXT STEPS:")
print("1. Upload a handwritten PDF through the UI")
print("2. Check logs for detailed pipeline trace")
print("3. Verify chunks are created (should be > 1)")
print("4. Test retrieval with various queries")
print("5. Check that results show page numbers and content\n")
