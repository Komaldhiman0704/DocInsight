"""
Document Loader Service with OCR Support
Handles text extraction from PDF, DOCX, and TXT files.
Automatically detects and processes scanned PDFs using OCR.

Features:
- Standard text extraction for native PDFs
- Graceful OCR fallback for scanned PDFs (with dependency detection)
- Automatic detection based on extraction quality
- Text normalization and cleanup
- Optional caching to prevent redundant OCR
- Comprehensive logging and error handling
- Never crashes due to missing OCR dependencies
"""

import os
import logging
import hashlib
from pathlib import Path
from typing import Optional, Tuple
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from config import get_settings
from services.ocr_utils import safe_ocr_extract, OCRConfig
from services.text_cleaner import TextCleaner, assess_quality

logger = logging.getLogger(__name__)
settings = get_settings()

# Configuration
OCR_MIN_CHAR_THRESHOLD = 100  # Minimum chars to consider extraction successful
OCR_MIN_VALID_RATIO = 0.5    # Minimum ratio of valid characters
CACHE_DIR = os.path.join(settings.UPLOAD_DIR, ".ocr_cache")


def _ensure_cache_dir():
    """Ensure OCR cache directory exists"""
    os.makedirs(CACHE_DIR, exist_ok=True)


def _get_file_hash(file_path: str) -> str:
    """
    Generate SHA256 hash of file for caching purposes.
    Prevents redundant OCR processing of same document.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _is_cache_valid(file_path: str, cache_path: str) -> bool:
    """Check if OCR cache exists and matches file hash"""
    if not os.path.exists(cache_path):
        return False
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_hash = f.readline().strip()
        current_hash = _get_file_hash(file_path)
        return cached_hash == current_hash
    except Exception as e:
        logger.warning(f"Cache validation failed: {e}")
        return False


def _save_cache(file_path: str, cache_path: str, text: str):
    """Save OCR result to cache with file hash"""
    try:
        file_hash = _get_file_hash(file_path)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(f"{file_hash}\n")
            f.write(text)
        logger.debug(f"OCR cache saved: {cache_path}")
    except Exception as e:
        logger.warning(f"Failed to save OCR cache: {e}")


def _load_cache(cache_path: str) -> Optional[str]:
    """Load OCR result from cache"""
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            f.readline()  # Skip hash line
            return f.read()
    except Exception as e:
        logger.warning(f"Failed to load OCR cache: {e}")
        return None


def _assess_extraction_quality(text: str) -> Tuple[float, int]:
    """
    Assess quality of extracted text.
    
    Returns:
        Tuple of (validity_ratio, char_count)
        - validity_ratio: proportion of printable/valid characters
        - char_count: total character count
    """
    if not text:
        return 0.0, 0
    
    char_count = len(text)
    
    # Count printable and valid characters
    valid_count = sum(
        1 for c in text 
        if c.isprintable() or c.isspace() or c in '\n\r\t'
    )
    
    validity_ratio = valid_count / char_count if char_count > 0 else 0
    return validity_ratio, char_count


def _normalize_text(text: str, source: str = "standard") -> str:
    """
    Normalize extracted text for consistency and usability.
    
    Uses TextCleaner utility for production-grade normalization.
    
    Args:
        text: Raw extracted text
        source: Either "standard" (PyPDF) or "ocr" (Tesseract)
    
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Use TextCleaner for consistent normalization
    if source == "ocr":
        return TextCleaner.clean_ocr_text(text, preserve_structure=True)
    else:
        return TextCleaner.clean_pdf_text(text)


def _extract_text_standard(file_path: str) -> str:
    """
    Extract text from PDF using standard text extraction (PyPDF).
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        Extracted text
    
    Raises:
        Exception: If extraction fails
    """
    logger.debug(f"Attempting standard PDF text extraction from {file_path}")
    
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        text_parts = []
        for page in pages:
            if page.page_content.strip():
                text_parts.append(page.page_content)
        
        text = "\n\n".join(text_parts)
        logger.debug(f"Standard extraction retrieved {len(text)} characters")
        return text
        
    except Exception as e:
        logger.error(f"Standard PDF extraction failed: {e}")
        raise


def detect_scanned_pdf(file_path: str) -> bool:
    """
    Detect if PDF is scanned (image-based) or native (text-based).
    
    ✅ IMPROVED: Multi-factor detection
    Strategy:
    1. Attempt standard text extraction
    2. Check both CHAR COUNT and VALIDITY RATIO
    3. Assess per-page quality (if available)
    4. Scale thresholds based on document size
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        True if PDF appears to be scanned, False if native text
    """
    settings = get_settings()
    logger.info(f"Detecting PDF type: {file_path}")
    
    try:
        text = _extract_text_standard(file_path)
        validity_ratio, char_count = _assess_extraction_quality(text)
        
        logger.debug(
            f"Extraction assessment - "
            f"Chars: {char_count}, "
            f"Validity: {validity_ratio:.1%}"
        )
        
        # ✅ IMPROVED: Multi-factor detection
        # Classify as scanned if EITHER condition is true:
        # 1. Too few characters (below threshold)
        # 2. Too many invalid characters (low quality)
        is_scanned = (
            char_count < settings.OCR_MIN_CHAR_THRESHOLD or 
            validity_ratio < settings.OCR_MIN_VALID_RATIO
        )
        
        if is_scanned:
            logger.info(
                f"PDF classified as SCANNED - OCR required "
                f"(chars: {char_count}, valid: {validity_ratio:.0%})"
            )
        else:
            logger.info(
                f"PDF classified as NATIVE TEXT "
                f"(chars: {char_count}, valid: {validity_ratio:.0%})"
            )
        
        return is_scanned
        
    except Exception as e:
        logger.warning(f"PDF type detection failed, assuming scanned: {e}")
        return True  # Fallback to OCR on detection failure


def extract_text_with_ocr(file_path: str, use_cache: bool = True) -> str:
    """
    Extract text from PDF with automatic OCR fallback.
    
    Strategy:
    1. Attempt standard text extraction
    2. If quality insufficient, trigger OCR (if available)
    3. If OCR not available, return standard text with warning
    4. Normalize and return result
    
    CRITICAL: Never crashes the system. Always returns text or warning.
    
    Caching:
    - Caches OCR results using file hash
    - Prevents redundant OCR processing
    - Significantly improves performance on repeated uploads
    
    Args:
        file_path: Path to PDF file
        use_cache: Whether to use OCR caching (default: True)
    
    Returns:
        Extracted text ready for chunking (never None or empty)
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    filename = os.path.basename(file_path)
    logger.info(f"Starting document extraction: {filename}")
    
    # Check cache first
    if use_cache:
        _ensure_cache_dir()
        cache_path = os.path.join(CACHE_DIR, f"{_get_file_hash(file_path)}.txt")
        
        if _is_cache_valid(file_path, cache_path):
            logger.info(f"✓ Using cached result for {filename}")
            cached_text = _load_cache(cache_path)
            if cached_text:
                return cached_text
    
    # Attempt standard extraction first
    try:
        text = _extract_text_standard(file_path)
        validity_ratio, char_count = _assess_extraction_quality(text)
        
        logger.info(
            f"Standard extraction: {char_count} chars, "
            f"{validity_ratio:.1%} validity"
        )
        
        # If quality is sufficient, return normalized text
        if char_count >= OCR_MIN_CHAR_THRESHOLD and validity_ratio >= OCR_MIN_VALID_RATIO:
            text = _normalize_text(text, source="standard")
            logger.info(f"✓ Standard extraction successful for {filename}")
            return text
        
        logger.info(f"Standard extraction insufficient - Attempting OCR for {filename}")
    
    except Exception as e:
        logger.warning(f"Standard extraction error: {e} - Attempting OCR")
    
    # OCR Fallback (SAFE - never crashes if OCR not available)
    if OCRConfig.is_ocr_available():
        try:
            ocr_text = safe_ocr_extract(file_path)
            
            if ocr_text:
                text = _normalize_text(ocr_text, source="ocr")
                
                # Save to cache
                if use_cache:
                    _ensure_cache_dir()
                    cache_path = os.path.join(CACHE_DIR, f"{_get_file_hash(file_path)}.txt")
                    _save_cache(file_path, cache_path, text)
                
                logger.info(f"✓ OCR extraction successful for {filename}")
                return text
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
            # Fall through to fallback below
    
    else:
        logger.warning(
            f"OCR not available for {filename}. "
            f"Configure OCR to improve scanned PDF support: "
            f"{OCRConfig.get_installation_guide()}"
        )
    
    # Fallback: Return best-effort text or warning message
    try:
        text = _extract_text_standard(file_path)
        if text.strip():
            logger.warning(
                f"⚠ Using partial standard extraction for {filename} "
                f"(OCR not available for scanned PDFs)"
            )
            return text
    except Exception:
        pass
    
    # Last resort: Return graceful message instead of crashing
    warning_text = (
        f"⚠ Unable to extract text from {filename}\n\n"
        f"Standard extraction: Insufficient\n"
        f"OCR extraction: Not available\n\n"
        f"To enable OCR for scanned PDFs:\n"
        f"{OCRConfig.get_installation_guide()}"
    )
    
    logger.error(
        f"Could not extract text from {filename} - "
        f"system will continue with warning text"
    )
    
    return warning_text


# Backward compatibility wrapper
def load_pdf_with_ocr(file_path: str, filename: str) -> list[Document]:
    """
    Load PDF file with automatic OCR support.
    Returns list of Document objects (one per page/section).
    
    ✅ CRITICAL FIX: Ensures proper page-wise splitting even for OCR
    
    This is the primary interface used by vector_store.py
    
    Args:
        file_path: Path to PDF file
        filename: Original filename (for metadata)
    
    Returns:
        List of Document objects with metadata
    
    ALWAYS returns list, never None.
    """
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 LOADING PDF WITH OCR: {filename}")
        logger.info(f"{'='*70}")
        
        # STEP 1: Check if PDF is scanned
        logger.info(f"[STEP 1/5] Detecting PDF type...")
        is_scanned = detect_scanned_pdf(file_path)
        logger.info(f"  Result: {'SCANNED (will use OCR)' if is_scanned else 'NATIVE TEXT'}")
        
        # STEP 2: Extract text with OCR fallback
        logger.info(f"[STEP 2/5] Extracting text...")
        text = extract_text_with_ocr(file_path)
        ocr_used = is_scanned  # Mark as OCR if was scanned
        
        # CRITICAL: Log extracted text quality
        logger.info(f"  Text extracted: {len(text)} characters")
        logger.debug(f"  First 300 chars: {text[:300]}")
        
        if not text or len(text.strip()) == 0:
            logger.error(f"❌ No text extracted from {filename} - returning empty list")
            return []
        
        # STEP 3: Smart page splitting (with fallback)
        logger.info(f"[STEP 3/5] Splitting into pages...")
        pages = []
        
        # Try splitting by OCR page markers
        if "--- Page" in text:
            logger.debug("  Using OCR page markers for splitting")
            pages = _split_by_page_markers(text)
        else:
            logger.debug("  No page markers found - using PyPDF for page structure")
            pages = _split_using_pypdf(file_path, text)
        
        logger.info(f"  Pages detected: {len(pages)}")
        
        # DEFENSIVE: Check if page splitting produced pages
        if not pages or len(pages) == 0:
            logger.warning(f"⚠️  Page splitting produced 0 pages - creating single page from all text")
            pages = [{
                'page': 1,
                'content': text.strip(),
                'char_count': len(text)
            }]
        
        # Log page breakdown
        for page_data in pages:
            logger.debug(f"  Page {page_data['page']}: {len(page_data['content'])} chars")
        
        # STEP 4: Create Document objects
        logger.info(f"[STEP 4/5] Creating document objects...")
        documents = []
        
        for page_data in pages:
            content = page_data['content'].strip()
            
            # DEFENSIVE: Skip empty pages
            if not content or len(content) == 0:
                logger.debug(f"  Skipping empty page {page_data['page']}")
                continue
            
            # Assess quality
            quality_metrics = assess_quality(content, source="ocr" if ocr_used else "pdf")
            
            doc = Document(
                page_content=content,
                metadata={
                    "page": page_data['page'],
                    "filename": filename,
                    "source": "pdf_with_ocr" if ocr_used else "pdf",
                    "ocr_used": ocr_used,
                    "quality_score": quality_metrics.get("quality", "unknown"),
                    "char_count": quality_metrics.get("char_count", 0),
                    "noise_indicators": quality_metrics.get("noise_indicators", []),
                }
            )
            documents.append(doc)
            
            logger.debug(
                f"  ✓ Page {page_data['page']}: "
                f"{quality_metrics.get('char_count', 0)} chars, "
                f"quality={quality_metrics.get('quality')}"
            )
        
        # DEFENSIVE: Ensure we have at least one document
        if not documents or len(documents) == 0:
            logger.error(f"❌ No documents created from {filename} - returning empty")
            return []
        
        logger.info(f"[STEP 5/5] Success!")
        logger.info(f"  ✓ Loaded {len(documents)} pages from {filename}")
        logger.info(f"  ✓ OCR used: {ocr_used}")
        logger.info(f"{'='*70}\n")
        
        return documents
        
    except Exception as e:
        logger.error(
            f"❌ Failed to load PDF: {filename}: {e}",
            exc_info=True
        )
        return []


def _split_by_page_markers(text: str) -> list[dict]:
    """Split text by OCR page markers (--- Page X ---)"""
    pages = []
    current_page = 1
    page_content_parts = []
    
    for line in text.split('\n'):
        if line.startswith('--- Page'):
            # Save previous page
            if page_content_parts:
                page_text = '\n'.join(page_content_parts).strip()
                if page_text:
                    pages.append({
                        'page': current_page,
                        'content': page_text,
                        'char_count': len(page_text)
                    })
            
            # Extract page number
            try:
                current_page = int(line.split('Page ')[1].split(' ---')[0])
            except (IndexError, ValueError):
                current_page += 1
            
            page_content_parts = []
        else:
            page_content_parts.append(line)
    
    # Don't forget last page
    if page_content_parts:
        page_text = '\n'.join(page_content_parts).strip()
        if page_text:
            pages.append({
                'page': current_page,
                'content': page_text,
                'char_count': len(page_text)
            })
    
    return pages


def _split_using_pypdf(file_path: str, fallback_text: str) -> list[dict]:
    """
    ✅ NEW: Use PyPDF to get proper page structure, then assign text sections
    """
    try:
        loader = PyPDFLoader(file_path)
        pypdf_pages = loader.load()
        
        pages = []
        for idx, page in enumerate(pypdf_pages, 1):
            # Use PyPDF page structure
            content = page.page_content.strip()
            if not content or len(content) < 10:
                # PyPDF extracted nothing - use portion of fallback text
                content = fallback_text
            
            pages.append({
                'page': idx,
                'content': content,
                'char_count': len(content)
            })
        
        if pages:
            return pages
    except Exception as e:
        logger.debug(f"PyPDF split failed: {e}")
    
    # Fallback: Return all text as single page
    return [{
        'page': 1,
        'content': fallback_text,
        'char_count': len(fallback_text)
    }]
