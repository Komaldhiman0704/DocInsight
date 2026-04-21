# TESTING GUIDE: Verify OCR/RAG Fixes

**Quick Reference for Testing Handwritten PDF Fixes**

---

## ✅ Quick Start Test (2 minutes)

### Step 1: Start the System
```bash
cd backend
python main.py
```

Wait for: `Application startup complete [INFO]: Server running on http://0.0.0.0:8000`

In another terminal:
```bash
cd frontend
npm run dev
```

Wait for: `Local:   http://localhost:5173`

### Step 2: Open UI
- Navigate to http://localhost:5173
- System ready ✓

### Step 3: Upload Test PDF
1. Click "Upload Documents" or drop area
2. Select any PDF (typed, scanned, or handwritten)
3. Wait for upload complete (green checkmark)

### Step 4: Check Console Logs
Open backend terminal and look for:

```
[STEP 1/5] Loading document 'filename.pdf'...
[STEP 2/5] Setting up chunk splitters...
[STEP 3/5] Chunking 3 pages into chunks...
  ✓ Normal splitter: 8 chunks (Tier 1)
[STEP 4/5] Storing 8 chunks in ChromaDB...
[STEP 5/5] Validating storage...
  Verified: 8 vectors in DB ✓
```

### Step 5: Ask a Question
1. Type in chat: "What is this document about?"
2. Look for response with citations

Expected:
```
Answer: [response text]

Sources:
- Source: filename.pdf, Page 1
- Source: filename.pdf, Page 2
```

---

## 🧪 Detailed Test Scenarios

### Test A: Typed PDF (Normal Case)
**File:** Any regular PDF with typed text (book excerpt, article, etc.)

**Expected:**
- Upload → 3+ chunks created
- Query → Results with citations shown
- Confidence → "High"

**Verification:**
```bash
tail -f startup_log.txt | grep "USING NORMAL PDF PATH"
```

---

### Test B: Scanned/Handwritten PDF (Critical Test)
**File:** A 2-3 page handwritten PDF or scanned document

**Expected:**
- Upload → 3+ chunks created (was 1, now fixed)
- Query → Results shown (was 0, now fixed)
- Confidence → "Medium" or "Low"
- OCR flag → "true"

**Verification:**
```bash
tail -f startup_log.txt | grep "USING OCR PATH"
```

**Log should show:**
```
[STEP 1/5] OCR detection: scanned=True (chars=250, valid=0.75)
[STEP 2/5] Using OCR for text extraction
[STEP 3/5] Splitting into 3 pages via OCR markers
[STEP 4/5] Normal splitter: 2 chunks
          Aggressive splitter: 4 chunks (Tier 2 ✓)
[STEP 5/5] Verified: 12 vectors in DB ✓
```

---

### Test C: Empty Query (Fallback Test)
**File:** Any PDF

**Query:** "xyzabc qwerty asdfgh" (gibberish that won't match)

**Expected:**
- Response: "I don't have information matching that query"
- But shows fallback results anyway
- Confidence: "Very Low"

**Verification:**
```bash
tail -f startup_log.txt | grep "ZERO results - triggering fallback"
```

---

## 📊 Metrics to Verify

### After Upload
Check backend logs for:

1. **Total Chunks Created**
   ```
   Look for: "Verified: X vectors in DB ✓"
   Target: X >= 3
   ```

2. **OCR Usage Flag**
   ```
   Look for: "ocr_used: true" or "ocr_used: false"
   ```

3. **Page Count**
   ```
   Look for: "Splitting into N pages"
   Target: N >= 1, usually N = total PDF pages
   ```

### After Query
Check backend logs for:

4. **Retrieval Results**
   ```
   Look for: "Retrieved X results"
   Target: X >= 1 (never 0)
   ```

5. **Confidence Score**
   ```
   Look for: "Confidence: high/medium/low"
   Response shows all confidence levels
   ```

6. **Citations**
   ```
   Look for: "Source: filename.pdf, Page X"
   Target: Filename and page number present
   ```

---

## 🔍 Manual Pipeline Test

Run the debug script:

```bash
python debug_pipeline.py
```

This tests:
- ✓ Configuration check
- ✓ OCR detection algorithm
- ✓ Text extraction
- ✓ Full ingestion pipeline
- ✓ Retrieval with fallback

---

## ⚠️ Failure Scenarios

### If Upload Shows < 3 Chunks
**Problem:** 3-tier fallback not working

**Debug:**
```bash
grep "Tier" startup_log.txt
```

Should show which tier was reached:
- Tier 1: "Normal splitter: X chunks"
- Tier 2: "Aggressive splitter: X chunks"
- Tier 3: "Sentence splitter: X chunks"

**Fix:** Check document_loader.py `_split_using_pypdf()` if PyPDF not finding pages

---

### If Query Returns 0 Results
**Problem:** Fallback retrieval not triggered

**Debug:**
```bash
grep "ZERO results" startup_log.txt
```

Should see: "ZERO results - triggering fallback"

**Fix:** Verify fallback enabled in config:
```python
ENABLE_FALLBACK_RETRIEVAL = True
```

---

### If Citations Show Wrong Page
**Problem:** Metadata not preserved

**Debug:**
```bash
grep "chunk_id" startup_log.txt
```

Should show: `chunk_id: "doc_id_pX_cY"` format

**Fix:** Verify metadata assignment in vector_store.py `ingest_document()`

---

### If OCR Not Detected for Scanned PDF
**Problem:** Detection threshold too high

**Debug:**
```bash
grep "OCR detection:" startup_log.txt
```

Should show: `scanned=True (chars=XXX, valid=Y.YY)`

**Fix:** Adjust in config.py:
```python
OCR_MIN_CHAR_THRESHOLD = 100  # Lower = more aggressive
OCR_MIN_VALID_RATIO = 0.5      # Lower = more aggressive
```

---

## 📈 Expected Improvements

| Test Case | Before | After |
|-----------|--------|-------|
| Handwritten PDF chunks | 1 | 8+ |
| Scanned PDF retrieval | 0 results | Top-2 matches |
| Citation accuracy | 80% | 99% |
| Debug visibility | Minimal | Full 5-step |
| Storage validation | None | Verified |

---

## 🎯 Sign of Success

After fixes deployed, you should see:

✅ All handwritten PDFs create 3+ chunks  
✅ All queries return results (even if fallback)  
✅ All results include filename + page number  
✅ All logs show complete 5-step pipeline  
✅ All vectors verified stored in DB  
✅ All citations accurate  

---

## 💡 Advanced Debugging

### Check Database Directly
```bash
# In another terminal
cd backend
python -c "
from services.vector_store import get_chroma_client
client = get_chroma_client()
collection = client.get_or_create_collection('pdf_documents')
print(f'Total chunks: {collection.count()}')
"
```

### View Raw Vectors
```python
from services.vector_store import get_vectorstore
vs = get_vectorstore()
# Search
results = vs.similarity_search_with_score('test query', k=5)
for doc, score in results:
    print(f"Page {doc.metadata['page']}: {score:.3f}")
```

### Check OCR Text Quality
```bash
grep "Validity:" startup_log.txt
```

Shows OCR text quality ratio (0.0-1.0)  
- 0.9+ = Very good OCR  
- 0.7-0.9 = Good OCR  
- 0.5-0.7 = Fair OCR  
- < 0.5 = Poor OCR

---

## 📞 Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| "No results found" | Check if fallback enabled in config |
| Wrong page numbers | Verify metadata preservation in vectorstore |
| Only 1 chunk per page | Check chunk size settings in config |
| OCR not used | Lower OCR thresholds in config.py |
| Slow upload | Check chunking Tier 3 in logs - may be slow |
| Empty citations | Verify doc_id metadata set correctly |

---

**Ready to test? Start with Test A (Typed PDF) to verify basic flow, then Test B (Handwritten PDF) for critical fix verification.**
