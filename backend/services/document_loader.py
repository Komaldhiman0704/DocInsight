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
    
    Handles:
    - Whitespace normalization
    - UTF-8 encoding fixes
    - Hyphenation repair (for OCR text)
    - Line break standardization
    - Artifact removal
    
    Args:
        text: Raw extracted text
        source: Either "standard" (PyPDF) or "ocr" (Tesseract)
    
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Remove control characters except newline/tab
    text = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
    
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n\n+', '\n\n', text)  # Multiple newlines to double
    text = re.sub(r' +\n', '\n', text)  # Trailing spaces before newline
    
    if source == "ocr":
        # OCR-specific cleaning
        
        # Fix common OCR errors
        text = re.sub(r'\b0([A-Z])\b', r'O\1', text)  # 0 → O in acronyms
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)  # Repair hyphenated line breaks
        
        # Fix spaces before punctuation
        text = re.sub(r' ([.,:;!?)])', r'\1', text)
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        # Remove excessive punctuation
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\?{2,}', '?', text)
    
    return text.strip()


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
    
    Strategy:
    1. Attempt standard text extraction
    2. Assess quality (character count, printable ratio)
    3. If below thresholds, classify as scanned
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        True if PDF appears to be scanned, False if native text
    """
    logger.info(f"Detecting PDF type: {file_path}")
    
    try:
        text = _extract_text_standard(file_path)
        validity_ratio, char_count = _assess_extraction_quality(text)
        
        logger.debug(
            f"Extraction assessment - "
            f"Chars: {char_count}, "
            f"Validity: {validity_ratio:.1%}"
        )
        
        # Classify as scanned if below thresholds
        is_scanned = (
            char_count < OCR_MIN_CHAR_THRESHOLD or 
            validity_ratio < OCR_MIN_VALID_RATIO
        )
        
        if is_scanned:
            logger.info("PDF classified as SCANNED - OCR required")
        else:
            logger.info("PDF classified as NATIVE TEXT - Standard extraction sufficient")
        
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
    
    This is the primary interface used by vector_store.py
    
    Args:
        file_path: Path to PDF file
        filename: Original filename (for metadata)
    
    Returns:
        List of Document objects with metadata
    """
    text = extract_text_with_ocr(file_path)
    
    # Split into logical sections (by page markers from OCR)
    # Extract page numbers if present
    pages = []
    current_page = 1
    page_content_parts = []
    
    for line in text.split('\n'):
        if line.startswith('--- Page'):
            # New page marker detected
            if page_content_parts:
                pages.append({
                    'page': current_page,
                    'content': '\n'.join(page_content_parts)
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
        pages.append({
            'page': current_page,
            'content': '\n'.join(page_content_parts)
        })
    
    # Create Document objects
    documents = []
    for page_data in pages:
        if page_data['content'].strip():
            doc = Document(
                page_content=page_data['content'],
                metadata={
                    "page": page_data['page'],
                    "filename": filename,
                    "source": "pdf_with_ocr"
                }
            )
            documents.append(doc)
    
    logger.info(f"Created {len(documents)} documents from {filename}")
    return documents
