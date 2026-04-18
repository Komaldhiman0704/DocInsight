"""
RAG Source Attribution Testing & Debugging Guide

This guide provides test cases and verification steps for the source attribution system.
Use these tests to validate that source mapping works correctly throughout the pipeline.
"""

# ═════════════════════════════════════════════════════════════════════════════
# TEST CASE 1: Native PDF with Multiple Pages
# ═════════════════════════════════════════════════════════════════════════════

TEST_1_SCENARIO = """
File: typed_document.pdf (3 pages, native text-based)
Query: "What are the main findings?"
Expected: 
  - All sources should show 'p.1', 'p.2', or 'p.3'
  - No OCR badge displayed
  - High confidence score (>70%)
  - ocr_sources = false
Verification:
  1. Check console: grep "Quality score: high" or "ocr_used: false"
  2. Frontend: No [OCR] badge on source cards
  3. Confidence indicator shows "High"
"""

# ═════════════════════════════════════════════════════════════════════════════
# TEST CASE 2: Scanned/Handwritten PDF
# ═════════════════════════════════════════════════════════════════════════════

TEST_2_SCENARIO = """
File: handwritten_notes.pdf (2 pages, image-based)
Query: "Extract the key points"
Expected:
  - Source cards show [OCR] badge
  - Page numbers preserved correctly
  - Medium or medium-low confidence score
  - Quality indicators present
  - OCR warning shown below confidence indicator
Verification:
  1. Check console logs for "PDF classified as SCANNED"
  2. Check logs for "OCR extraction successful"
  3. Frontend: [OCR] badge visible on sources
  4. Confidence indicator shows medium with OCR warning
"""

# ═════════════════════════════════════════════════════════════════════════════
# TEST CASE 3: Mixed Content (Typed + Scanned Pages)
# ═════════════════════════════════════════════════════════════════════════════

TEST_3_SCENARIO = """
File: mixed_document.pdf (pages 1-2 typed, pages 3-4 scanned)
Query: "Find all mentions of X"
Expected:
  - Pages 1-2 sources: No OCR badge
  - Pages 3-4 sources: [OCR] badge present
  - All page numbers correct (p.1-4)
  - If query matches both: confidence should reflect mixed sources
Verification:
  1. Check which pages have OCR badge
  2. Verify page numbers match actual PDF
  3. Check that both typed and OCR text are retrievable
"""

# ═════════════════════════════════════════════════════════════════════════════
# TEST CASE 4: Multiple Documents
# ═════════════════════════════════════════════════════════════════════════════

TEST_4_SCENARIO = """
Files: 
  - doc1.pdf (3 pages, typed)
  - doc2.pdf (2 pages, scanned)
Query: "Compare information across documents"
Expected:
  - Sources show correct filenames: "doc1.pdf" and "doc2.pdf"
  - Page numbers correct within each document
  - doc2.pdf sources have [OCR] badge, doc1.pdf don't
  - No cross-source confusion
Verification:
  1. Check that sources display correct filenames
  2. Verify page numbers reset per document (p.1-3 for doc1, p.1-2 for doc2)
  3. Confirm source filtering works correctly
"""

# ═════════════════════════════════════════════════════════════════════════════
# DEBUGGING CHECKLIST
# ═════════════════════════════════════════════════════════════════════════════

DEBUGGING_STEPS = """
1. EXTRACTION PHASE
   ✓ Check backend logs at startup:
     - Look for "OCR ENVIRONMENT DETECTION"
     - Verify pytesseract, pdf2image, tesseract binary status
   
   ✓ After uploading document:
     - Should see: "Extracted N pages from filename"
     - For OCR files: "PDF classified as SCANNED"
     - Quality metrics logged: "Quality score: good/medium/low"

2. CHUNKING PHASE
   ✓ In debug logs, search for "Created chunk":
     - Each chunk should have: chunk_id, page number, char count
     - Format: "chunk_id": "doc_id_p1_c1" (document_page_chunk)
     - Metadata includes: filename, page, ocr_used, quality_score

3. RETRIEVAL PHASE
   ✓ Before answering, logs show:
     - Query: '[query text] → Retrieved X candidates'
     - Each chunk logged with: filename, page, chunk_id, similarity score
     - OCR flag visible in debug output
   
   ✓ Final results show:
     - "[i] filename:pN (chunk: chunk_id) score=0.XXX"
     - Format shows page number and similarity score

4. RESPONSE PHASE
   ✓ Frontend receives:
     - sources array with: filename, page, doc_id, excerpt, ocr_used, quality_score
     - confidence data: confidence, relevance_score, source_count, ocr_sources
   
   ✓ SourceCard shows:
     - Filename and page number
     - [OCR] badge if ocr_used=true
     - Quality note if available

5. FRONTEND VERIFICATION
   ✓ Click citation eye icon → PDF opens on correct page
   ✓ ConfidenceIndicator shows:
     - Confidence level badge
     - Relevance percentage
     - Source count
     - OCR warning if applicable

COMMON ISSUES & FIXES
═════════════════════════════════════════════════════════════════════════════

Issue: Wrong page numbers in sources
  Root causes:
    1. Page number not preserved during extraction
    2. Chunking resets page metadata
  Fix:
    - Check load_pdf_with_ocr preserves page in metadata
    - Verify ingest_document chunk loop maintains page
    - Check extract_sources correctly reads page from metadata

Issue: All sources marked as OCR (false positive)
  Root causes:
    1. detect_scanned_pdf incorrectly classifying typed PDFs
    2. OCR quality assessment too aggressive
  Fix:
    - Check OCR_MIN_CHAR_THRESHOLD (should be 100+)
    - Check OCR_MIN_VALID_RATIO (should be 0.5+)
    - Verify TextCleaner not corrupting text

Issue: OCR sources not appearing in results
  Root causes:
    1. OCR extraction failed silently
    2. OCR quality too low, filtered out
    3. Page metadata missing after OCR
  Fix:
    - Check backend logs for OCR failures
    - Verify safe_ocr_extract returning text
    - Ensure metadata preserved through pipeline

Issue: Sources from wrong document appearing
  Root causes:
    1. Document filtering not working
    2. Chunk metadata corrupted
    3. Vector store returning wrong results
  Fix:
    - Verify doc_id added to all chunks
    - Check get_docs_with_scores filters correctly
    - Confirm ChromaDB metadata filtering works

═════════════════════════════════════════════════════════════════════════════
LOGGING FOR DEBUGGING
═════════════════════════════════════════════════════════════════════════════

Backend Environment Variables (for debugging):
  set DEBUG=true          → Enable debug logging
  set LOG_LEVEL=DEBUG     → Set logging to debug level

Frontend Console Logging:
  - Check browser console (F12) for errors
  - Look for warnings during streaming response parsing
  - Verify sources array structure in console

Enable Full Debug Mode:
  1. Backend: Add LOG_LEVEL=DEBUG to environment
  2. Frontend: Add console.log() in streamChat callback
  3. Network tab: Monitor API responses
  4. Check: Response JSON contains ocr_sources and other fields

═════════════════════════════════════════════════════════════════════════════
EXPECTED OUTPUT EXAMPLES
═════════════════════════════════════════════════════════════════════════════

Debug Log Example (Extraction):
\"\"\"
Loading PDF with OCR support: report.pdf
Extracted 4 pages from report.pdf - now chunking per-page
Split report.pdf into 12 chunks across 4 pages
✓ Stored 12 chunks for report.pdf in vector store
\"\"\"

Debug Log Example (Retrieval):
\"\"\"
Query: 'What are the key metrics' → Retrieved 8 candidates
Filtering by doc_ids: ['abc12345']
After filtering: 4 results match selected documents
  [1] report.pdf:p2 (chunk: abc12345_p2_c1) score=0.892 ocr=false quality=good
  [2] report.pdf:p3 (chunk: abc12345_p3_c2) score=0.845 ocr=true quality=medium
  [3] report.pdf:p1 (chunk: abc12345_p1_c3) score=0.812 ocr=false quality=good
  [4] report.pdf:p4 (chunk: abc12345_p4_c1) score=0.734 ocr=true quality=good
✓ Retrieved 4 chunks for query. Top score: 0.892
\"\"\"

Frontend Response Example:
\"\"\"
{
  "sources": [
    {
      "filename": "report.pdf",
      "page": 2,
      "doc_id": "abc12345",
      "excerpt": "The quarterly results show...",
      "ocr_used": false,
    },
    {
      "filename": "report.pdf",
      "page": 3,
      "doc_id": "abc12345",
      "excerpt": "Key metrics include...",
      "ocr_used": true,
      "quality_score": "medium"
    }
  ],
  "confidence": "high",
  "relevance_score": 0.87,
  "source_count": 4,
  "ocr_sources": true
}
\"\"\"

Frontend Display Expected:
  - Source card showing: "report.pdf  p.2" with excerpt
  - Second source showing: "report.pdf  p.3  [OCR]" with quality note
  - Confidence indicator: "High • 87%" with OCR warning below
\"\"\"
"""

print(__doc__)
print(TEST_1_SCENARIO)
print(TEST_2_SCENARIO)
print(TEST_3_SCENARIO)
print(TEST_4_SCENARIO)
print(DEBUGGING_STEPS)
