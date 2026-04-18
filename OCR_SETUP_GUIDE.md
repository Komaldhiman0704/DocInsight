"""
OCR Setup and Testing Guide for DocInsight
==========================================

This document provides step-by-step instructions for setting up OCR support
and validating the implementation.
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: TESSERACT INSTALLATION
# ─────────────────────────────────────────────────────────────────────────────

## Windows Installation

### Option 1: Using Scoop (Recommended)
```bash
# Install scoop if not already installed
iwr -useb get.scoop.sh | iex

# Install tesseract-ocr
scoop install tesseract-ocr

# Verify installation
tesseract --version
```

### Option 2: Using Windows Installer
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer (e.g., tesseract-ocr-w64-setup-v5.3.1.exe)
3. Note the installation path (default: C:\Program Files\Tesseract-OCR)
4. Add to Python environment:

```python
# In backend/config.py or before using pytesseract:
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## macOS Installation

```bash
brew install tesseract-ocr
tesseract --version
```

## Linux Installation

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Fedora
sudo dnf install tesseract

# Verify
tesseract --version
```

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: PYTHON DEPENDENCIES
# ─────────────────────────────────────────────────────────────────────────────

## Install OCR Dependencies

```bash
cd backend

# Ensure virtual environment is activated
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install requirements (includes OCR libraries)
pip install -r requirements.txt

# Verify installations
pip show pytesseract pdf2image Pillow
```

## Key Dependencies

- **pytesseract** (0.3.13+): Python wrapper for Tesseract OCR
- **pdf2image** (1.17.1+): Converts PDF pages to images for OCR
- **Pillow** (11.0.0+): Image processing library
- **Other**: All existing dependencies unchanged

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: ARCHITECTURE OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

## Document Processing Pipeline (with OCR)

```
Upload PDF
    ↓
[document_loader.py]
    ├─ Standard Extraction (PyPDF)
    │   ├─ Success & High Quality? → Use Result
    │   └─ Low Quality or Fail? → Proceed to OCR
    │
    └─ OCR Extraction (Tesseract)
        ├─ Convert Pages → Images (200 DPI)
        ├─ OCR Each Page
        ├─ Normalize Text
        ├─ Cache Result
        └─ Return Text
    ↓
[vector_store.py - ingest_document()]
    ├─ Split into Chunks (1000 chars, 200 overlap)
    ├─ Generate Embeddings (HuggingFace)
    ├─ Store in ChromaDB
    └─ Return Chunk Count
    ↓
Stored in Vector Database (Ready for RAG)
```

## Quality Detection Logic

```
Extract Text (Standard)
    ↓
Assess Quality:
    - Character Count ≥ 100?
    - Valid Character Ratio ≥ 50%?
    ↓
Both Yes? → Use Standard Extraction
    ↓
Trigger OCR Fallback
    ↓
Normalize & Cache
```

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: IMPLEMENTATION DETAILS
# ─────────────────────────────────────────────────────────────────────────────

## Key Functions in document_loader.py

### 1. detect_scanned_pdf(file_path: str) -> bool
- Determines if PDF is scanned (image-based) or native (text-based)
- Attempts standard extraction and assesses quality
- Returns True if OCR needed, False if standard extraction sufficient

### 2. extract_text_with_ocr(file_path: str, use_cache: bool = True) -> str
- Main entry point for document extraction
- Handles both text-based and scanned PDFs
- Implements caching using SHA256 file hashing
- Returns processed text ready for chunking

### 3. _extract_text_with_tesseract(file_path: str) -> str
- Low-level OCR extraction using Tesseract
- Converts PDF to images (200 DPI for balance)
- Processes page-by-page to manage memory
- Returns aggregated text with page markers

### 4. _normalize_text(text: str, source: str = "standard") -> str
- Cleans extracted text for consistency
- Source-specific normalization (standard vs OCR)
- Handles common OCR artifacts

### 5. _get_file_hash(file_path: str) -> str
- Generates SHA256 hash of file for caching
- Enables detection of duplicate uploads

## Caching Mechanism

- **Location**: `backend/uploads/.ocr_cache/`
- **Format**: `{SHA256_HASH}.txt`
- **Structure**: First line = file hash, remaining = OCR result
- **Validation**: Compares stored hash with current file hash
- **Benefit**: Repeated OCR on same file takes <100ms (vs 30-60s)

## Integration Points

### Modified: backend/services/vector_store.py
- Imports `load_pdf_with_ocr` from `document_loader`
- PDF processing now uses OCR-enabled loader
- All downstream processes unchanged (chunking, embedding, storage)
- Backward compatible - existing text-based PDFs process unchanged

### New: backend/services/document_loader.py
- Complete OCR implementation
- Handles all extraction logic
- Maintains separation of concerns

### Updated: backend/requirements.txt
- Added pytesseract, pdf2image, Pillow
- No version conflicts with existing dependencies

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

## Tuning OCR Quality Detection

In document_loader.py, adjust these constants:

```python
OCR_MIN_CHAR_THRESHOLD = 100    # Minimum chars to consider extraction successful
                                 # Increase to be more aggressive with OCR
                                 # Decrease to relax threshold

OCR_MIN_VALID_RATIO = 0.5       # Minimum ratio of valid/printable characters
                                 # Range: 0.0 to 1.0
                                 # Increase for stricter quality checks
```

## Tesseract Language Support

Current implementation: English (eng)

To add multilingual support:

```python
# In _extract_text_with_tesseract():
page_text = pytesseract.image_to_string(image, lang='eng+fra+deu')
# Supported: eng, fra, deu, spa, chi_sim, etc.
```

## Optional: Custom Tesseract Path

```python
# In document_loader.py (if needed):
import pytesseract

pytesseract.pytesseract.pytesseract_cmd = r'/path/to/tesseract'
```

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: TESTING & VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

## Test Scenario 1: Text-Based PDF (Standard Extraction)

```bash
# Upload a typical PDF (born digital, selectable text)
# Expected:
# - Standard extraction used
# - No OCR triggered
# - Logs show: "PDF classified as NATIVE TEXT"
# - Processing time: <5 seconds
```

## Test Scenario 2: Scanned PDF (OCR Required)

```bash
# Upload a scanned/image-based PDF
# Expected:
# - Standard extraction returns insufficient content
# - OCR fallback triggered
# - Logs show: "PDF classified as SCANNED - OCR required"
# - Processing time: 30-60 seconds (first run), <100ms (cached)
```

## Test Scenario 3: Hybrid PDF (Mixed Content)

```bash
# Upload a PDF with both text and images
# Expected:
# - Standard extraction used (sufficient quality)
# - Text regions processed normally
# - Image regions skipped (acceptable for RAG)
```

## Test Scenario 4: Large Document (1000+ pages)

```bash
# Upload a large PDF
# Expected:
# - Processed page-by-page (memory efficient)
# - Progress visible in logs
# - Final result chunked and stored successfully
```

## Validation Checklist

- [ ] Tesseract installed and binary in PATH
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] OCR cache directory created (`backend/uploads/.ocr_cache/`)
- [ ] Logging shows OCR pipeline operations
- [ ] Chat answers use text from scanned documents
- [ ] No memory issues with large documents
- [ ] Cached OCR repeats quickly
- [ ] Dark mode UI shows document sources correctly

## Manual Testing with Python

```python
import os
from backend.services.document_loader import extract_text_with_ocr, detect_scanned_pdf

# Test 1: Detect PDF type
file_path = "path/to/test.pdf"
is_scanned = detect_scanned_pdf(file_path)
print(f"Scanned PDF: {is_scanned}")

# Test 2: Extract text
text = extract_text_with_ocr(file_path)
print(f"Extracted {len(text)} characters")

# Test 3: Verify cache
text_cached = extract_text_with_ocr(file_path)  # Should be instant
print(f"Cached extraction: {len(text_cached)} characters")
```

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: TROUBLESHOOTING
# ─────────────────────────────────────────────────────────────────────────────

## Issue: "Tesseract is not installed"

**Solution**: Follow Section 1 installation steps for your OS

```bash
# Verify installation
tesseract --version

# If still not found, set path explicitly in config.py
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\path\to\tesseract.exe'
```

## Issue: "pdf2image requires poppler"

**Solution**: Install poppler library

```bash
# Windows (Scoop)
scoop install poppler

# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils
```

## Issue: "Very slow OCR processing"

**Possible causes**:
- High DPI setting (increase OCR_MIN_CHAR_THRESHOLD to skip OCR)
- Large PDF (>500 pages)
- Low system RAM

**Solutions**:
```python
# Reduce DPI in _extract_text_with_tesseract():
images = convert_from_path(file_path, dpi=150)  # 200 → 150

# Or increase quality threshold to skip OCR on borderline PDFs
OCR_MIN_CHAR_THRESHOLD = 500
```

## Issue: "Low quality OCR results"

**Solution**: Adjust tesseract configuration

```python
# In _extract_text_with_tesseract():
config = '--psm 3 --oem 3'  # PSM=page segmentation mode
page_text = pytesseract.image_to_string(image, lang='eng', config=config)
```

## Issue: "Memory error with large PDFs"

**Cause**: Page-by-page processing already implemented

**Verify**: Check logs for page processing steps

```python
# If still issues, reduce DPI or implement lazy loading
images = convert_from_path(file_path, dpi=150, first_page=1, last_page=50)
```

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: PERFORMANCE METRICS
# ─────────────────────────────────────────────────────────────────────────────

## Expected Performance

| Document Type | Size | Standard Time | OCR Time | Cached Time |
|---------------|------|---------------|----------|-------------|
| Text-based PDF | 10MB | <5s | N/A | N/A |
| Scanned PDF (50p) | 25MB | <1s (detected) | 30-45s | <100ms |
| Hybrid PDF | 15MB | <5s | N/A | N/A |
| Large scanned PDF | 100MB | <2s (detected) | 90-120s | <200ms |

## Optimization Tips

1. **Increase OCR threshold**: Skip OCR for borderline quality PDFs
2. **Lower DPI**: Use 150 DPI instead of 200 for faster processing
3. **Batch processing**: Process multiple documents in queue
4. **Caching**: Always enabled to speed up repeated uploads

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: BACKWARD COMPATIBILITY
# ─────────────────────────────────────────────────────────────────────────────

## Verified Compatibility

✓ Text-based PDFs: Use standard extraction (no change in behavior)
✓ DOCX files: Unchanged processing
✓ TXT files: Unchanged processing
✓ Chunking: Same logic, processes OCR output identically
✓ Embeddings: No changes, works with any text input
✓ ChromaDB: No schema changes
✓ Metadata: Backward compatible
✓ Chat interface: No changes needed
✓ RAG pipeline: Seamless integration

## Migration Notes

- No database migration required
- No frontend changes needed
- Existing documents remain unchanged
- OCR only triggered for new uploads (if needed)
- System handles both old and new document types in same session

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10: DEPLOYMENT CHECKLIST
# ─────────────────────────────────────────────────────────────────────────────

Pre-Production:

- [ ] Tesseract installed on deployment machine
- [ ] All OCR dependencies in requirements.txt
- [ ] Backend starts without errors
- [ ] Test upload with scanned PDF succeeds
- [ ] Chat returns answers from scanned document
- [ ] Logs show OCR pipeline operations
- [ ] No memory issues observed
- [ ] Cache directory structure correct

Post-Deployment:

- [ ] Monitor logs for OCR errors
- [ ] Track OCR processing times
- [ ] Verify cache hit rates
- [ ] Monitor disk space (cache files)
- [ ] Test with various PDF types

# ─────────────────────────────────────────────────────────────────────────────

For questions or issues, check logs in: backend/startup_log.txt or application output

"""
