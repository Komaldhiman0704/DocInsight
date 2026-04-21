# DocInsight Project Analysis - Comprehensive System Flow

**Date:** April 21, 2026  
**Status:** Pre-implementation analysis (no changes made yet)  
**Objective:** Identify bottlenecks, design OCR improvements, fix chunking issues

---

## 1. CURRENT SYSTEM FLOW MAPPED

```
USER UPLOAD (PDF)
    ↓
[ROUTE: upload.py:upload_document]
    • Validate file (extension, size)
    • Save to disk
    • Generate doc_id (UUID)
    ↓
[SERVICE: vector_store.py:ingest_document]
    • Load PDF → detect file type
    • Call load_pdf_with_ocr() for PDFs
    • Returns: List[Document] (one per page)
    ↓
[SERVICE: document_loader.py:load_pdf_with_ocr]
    • extract_text_with_ocr()
    • Detects if PDF is scanned
    • If scanned → OCR fallback (if available)
    • Returns: str (full document text)
    ↓
[BACK TO: vector_store.py:ingest_document]
    • Chunking: RecursiveCharacterTextSplitter
    • chunk_size = 512, overlap = 100 (from config)
    • Creates chunks PER PAGE
    • Adds metadata: doc_id, filename, page, chunk_id
    ↓
[ChromaDB Vector Store]
    • Embeddings: HuggingFace (all-MiniLM-L6-v2)
    • Stores all chunks with metadata
    ↓
CHAT QUERY
    ↓
[SERVICE: rag_chain.py:run_rag_chain]
    • Step 1: Rephrase query (with history)
    • Step 2: Retrieve with scores
    • Step 3: Generate answer (with context)
    • Step 4: Extract sources
    • Step 5: Generate suggestions
    ↓
[RETRIEVAL: vector_store.py:get_docs_with_scores]
    • Similarity search (k=10)
    • Filter by doc_ids if selected
    • Return: List[(doc, score)]
    ↓
[FORMAT: rag_chain.py:format_docs]
    • Creates context string with source markers
    • Format: "[Source 1 — filename, Page X]:\n{content}"
    ↓
[EXTRACT: rag_chain.py:extract_sources]
    • Deduplicates by filename+page
    • Creates source cards
    • Includes filename, page, excerpt
    ↓
[FRONTEND: SourceCard.jsx]
    • Displays source cards with page jump button
    • Calls onViewPDF with doc_id and page
    ↓
[FRONTEND: PDFViewerPanel.jsx]
    • Opens PDF viewer
    • Jumps to page (with document switching fix)
```

---

## 2. IDENTIFIED ISSUES

### **ISSUE 1: OCR Detection Logic is Weak**
**Location:** `document_loader.py:detect_scanned_pdf()`  
**Problem:**
- Threshold: `OCR_MIN_CHAR_THRESHOLD = 100` (too low!)
- Only looks at TOTAL extracted text, not quality
- Mixed text/non-text PDFs often bypass OCR

**Current Flow:**
```python
text = extract_text_standard(file_path)
validity_ratio, char_count = assess_extraction_quality(text)

is_scanned = (char_count < 100) or (validity_ratio < 0.5)
```

**Issue:** A PDF with 200 chars but 80% garbage still doesn't trigger OCR!

---

### **ISSUE 2: Chunking Creates Too Few Chunks**
**Location:** `vector_store.py:ingest_document()`  
**Problem:**
- Settings: `chunk_size = 512, chunk_overlap = 100`
- One chunk per page if page < 512 chars
- No fallback if chunking produces ≤1 chunk

**Current Flow:**
```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,          # TOO LARGE for most pages
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
)

page_chunks = splitter.split_documents([page_doc])
# If page < 512 chars → produces 1 chunk (or 0 if empty!)
```

**Issue:** Scanned PDFs often have < 512 chars per page (due to spacing from OCR)
→ Results in 1 chunk per page, not multiple meaningful chunks

---

### **ISSUE 3: OCR Text is Not Normalized**
**Location:** `document_loader.py:extract_text_with_ocr()`  
**Problem:**
- Calls `TextCleaner.clean_ocr_text()` but then doesn't preserve structure
- "m ach ine" might not become "machine"
- "lOOP" might not become "loop"
- Common OCR errors: 0→o, 1→l, | → I

**Current Flow:**
```python
text = _normalize_text(ocr_text, source="ocr")
return text
# TextCleaner is imported but... let's verify it exists
```

---

### **ISSUE 4: Retrieval Falls Back Gracefully, But Doesn't Force Results**
**Location:** `rag_chain.py:run_rag_chain()`  
**Problem:**
- If `get_docs_with_scores()` returns 0 results → returns graceful error
- No fallback to "show top 2 matches anyway"
- User gets empty answer instead of partial match

**Current Flow:**
```python
docs_with_scores = get_docs_with_scores(standalone_question, doc_ids)

if not docs_with_scores or len(docs_with_scores) == 0:
    return { "answer": "⚠️ I couldn't find relevant information..." }
```

---

### **ISSUE 5: Metadata Preservation is Partial**
**Location:** `vector_store.py:ingest_document()`  
**Problem:**
- Metadata added to chunks but doesn't include `ocr_used` flag per chunk
- Only inherited from original page_doc if available
- Frontend doesn't know which source is from OCR

**Missing:**
```python
# Should add:
chunk.metadata["ocr_used"] = page_doc.metadata.get("ocr_used", False)
```

---

## 3. ARCHITECTURE ASSESSMENT

### **GOOD:**
✅ Per-page chunking (preserves page numbers)  
✅ Metadata preserved through pipeline  
✅ OCR detection logic exists  
✅ Source extraction is sophisticated  
✅ Graceful error handling  
✅ Defensive checks for empty docs  

### **PROBLEMATIC:**
❌ OCR detection threshold too low  
❌ Chunk size too large for scanned PDFs  
❌ No multi-chunk fallback  
❌ OCR normalization incomplete  
❌ Query preprocessing missing  
❌ Hybrid retrieval not implemented  
❌ Citations work but not optimized  

---

## 4. DATA FLOW - CITATIONS

```
Chunk Metadata:
{
  "doc_id": "a1b2c3d4",
  "filename": "report.pdf",
  "page": 5,
  "chunk_id": "a1b2c3d4_p5_c1",
  "ocr_used": True/False    ← MISSING IN SOME CHUNKS!
  "quality_score": "good"
}
        ↓
extract_sources() creates:
{
  "filename": "report.pdf",
  "page": 5,
  "doc_id": "a1b2c3d4",
  "excerpt": "...",
  "ocr_used": True/False    ← Extracted correctly
}
        ↓
Frontend SourceCard displays:
- filename: "report.pdf" ✓
- page: 5 ✓
- excerpt ✓
- OCR badge (if ocr_used) ✓
        ↓
User clicks → PDFViewerPanel opens
- filename ✓
- docPath ✓
- targetPage = 5 ✓
- docId (now passed!) ✓
```

**Citation Flow: WORKING BUT CAN BE BETTER**

---

## 5. CHUNKING ANALYSIS

### Current Config:
```python
CHUNK_SIZE = 512          # characters
CHUNK_OVERLAP = 100       # characters
TOP_K_RESULTS = 10        # for retrieval
```

### Problem Case: Scanned 10-page PDF

Page text average: 300 chars (due to OCR spacing)
```
Page 1: 287 chars
  → RecursiveSplitter produces: 1 chunk (under 512)
  → chunk_id: doc_id_p1_c1

Page 2: 295 chars
  → 1 chunk
  → chunk_id: doc_id_p2_c1

...

Total: 10 chunks across 10 pages (1 per page)
```

**Problem:** System can't differentiate within page!
- Page 5 has 3 concepts but all in 1 chunk
- Query matches chunk but doesn't know which part
- Source points to "p.5" (page level, not section level)

---

## 6. FIX PRIORITY

### **CRITICAL (Breaking Issues):**
1. ✅ Chunk size too large → reduce to 300-400 chars
2. ✅ No multi-chunk fallback → force 3+ chunks per page
3. ✅ OCR detection threshold → scale by page count
4. ✅ Query normalization missing → add query preprocessing

### **HIGH (Quality Issues):**
5. ✅ Hybrid retrieval not implemented → add keyword search
6. ✅ Fallback to top-2 when no results → implement
7. ✅ OCR text normalization incomplete → enhance
8. ✅ Metadata enrichment incomplete → ensure all chunks have ocr_used

### **MEDIUM (Optimization):**
9. ✅ Async retrieval → use asyncio.to_thread()
10. ✅ Frontend alignment → show chunk counts
11. ✅ Debug logging → enhance visibility

---

## 7. IMPLEMENTATION SEQUENCE (SAFE & INCREMENTAL)

**Phase 1: Configuration & Detection (30 min)**
- Update chunking config (300-400 chars)
- Improve OCR detection threshold
- Add query normalization

**Phase 2: Chunking Logic (45 min)**
- Implement multi-chunk fallback
- Force minimum 3 chunks per page
- Ensure all chunks get metadata

**Phase 3: Retrieval Enhancement (60 min)**
- Implement hybrid retrieval
- Add fallback to top-2 matches
- Improve confidence scoring

**Phase 4: Text Processing (30 min)**
- Enhance OCR normalization
- Add character fixes (0→o, etc.)
- Preserve document structure

**Phase 5: Testing & Validation (45 min)**
- Test typed PDFs (should work same)
- Test scanned PDFs (should improve)
- Test edge cases (blank pages, mixed PDFs)
- Verify citations always present

---

## 8. VERIFICATION CHECKLIST (POST-IMPLEMENTATION)

```
OCR & Detection:
[ ] OCR triggered for scanned PDFs
[ ] OCR NOT triggered for native PDFs
[ ] Text quality assessed correctly
[ ] Query preprocessing working

Chunking:
[ ] Multiple chunks created per page (min 3 when possible)
[ ] Metadata preserved on all chunks
[ ] Empty pages skipped safely
[ ] Chunk_id is unique and traceable

Retrieval:
[ ] Hybrid search working (vector + keyword)
[ ] Fallback to top-2 when zero results
[ ] Confidence scoring accurate
[ ] No crashes on edge cases

Citations:
[ ] Filename shown on every source
[ ] Page number shown on every source
[ ] Excerpt shown and preview works
[ ] PDF viewer jumps to correct page
[ ] Document switching works (multi-PDF)

Frontend:
[ ] Upload shows chunk count
[ ] Source cards show page numbers
[ ] PDF viewer responsive
[ ] No console errors

System Stability:
[ ] No crashes
[ ] No empty responses
[ ] No lost citations
[ ] Graceful errors with info
```

---

## 9. FILES REQUIRING CHANGES

### Backend:
1. `config.py` - Update chunking settings
2. `services/document_loader.py` - Improve OCR detection & normalization
3. `services/vector_store.py` - Enhanced chunking with fallbacks
4. `services/rag_chain.py` - Hybrid retrieval, better fallbacks
5. `services/ocr_utils.py` - If needed, enhance normalization

### Frontend:
1. `components/UploadZone.jsx` - Show chunk count after upload (optional)
2. Other components - Should work as-is due to existing source structure

---

## 10. RISK ASSESSMENT

### Low Risk Areas (Safe to Change):
- Configuration values (chunk_size, thresholds)
- Log messages
- Fallback handling

### Medium Risk Areas (Needs Testing):
- OCR detection logic (edge cases with mixed PDFs)
- Chunking algorithm (affects all PDFs)
- Query normalization (could affect retrieval quality)

### Mitigation:
- Keep all changes backward compatible
- Add feature flags/config for gradual rollout
- Test with existing PDFs before and after
- Logging captures all changes for debugging

---

## SUMMARY

**Current State:** System is stable and works well for typed PDFs. OCR support exists but:
- Detection is weak (low threshold)
- Chunking is coarse (too large for scanned)
- Retrieval falls back to empty instead of showing partial
- Some metadata not properly preserved

**After Fix:** System will:
- ✅ Auto-detect and OCR scanned PDFs reliably
- ✅ Create 3+ meaningful chunks per page
- ✅ Show best matches even when perfect match not found
- ✅ Always include proper citations
- ✅ Handle all edge cases gracefully

**Implementation Approach:** Incremental changes with comprehensive logging and testing.

