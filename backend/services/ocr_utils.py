"""
OCR Utilities - Safe OCR dependency detection and wrapper functions.

Provides graceful fallback when OCR dependencies are missing or misconfigured.
Prevents system crashes and provides clear user guidance.
"""

import os
import sys
import logging
import shutil
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class OCRConfig:
    """Configuration and detection for OCR environment"""
    
    _pytesseract_available = None
    _pdf2image_available = None
    _tesseract_binary_available = None
    _warnings = []
    
    @classmethod
    def check_pytesseract(cls) -> bool:
        """
        Check if pytesseract is installed.
        
        Returns:
            True if pytesseract is available, False otherwise
        """
        if cls._pytesseract_available is not None:
            return cls._pytesseract_available
        
        try:
            import pytesseract
            cls._pytesseract_available = True
            logger.debug("✓ pytesseract library available")
            return True
        except ImportError:
            cls._pytesseract_available = False
            msg = "pytesseract not installed - OCR will be skipped"
            logger.warning(f"✗ {msg}")
            cls._warnings.append(msg)
            return False
    
    @classmethod
    def check_pdf2image(cls) -> bool:
        """
        Check if pdf2image is installed.
        
        Returns:
            True if pdf2image is available, False otherwise
        """
        if cls._pdf2image_available is not None:
            return cls._pdf2image_available
        
        try:
            import pdf2image
            cls._pdf2image_available = True
            logger.debug("✓ pdf2image library available")
            return True
        except ImportError:
            cls._pdf2image_available = False
            msg = "pdf2image not installed - OCR will be skipped"
            logger.warning(f"✗ {msg}")
            cls._warnings.append(msg)
            return False
    
    @classmethod
    def check_tesseract_binary(cls) -> bool:
        """
        Check if Tesseract binary is available in system PATH.
        
        Returns:
            True if tesseract binary is found, False otherwise
        """
        if cls._tesseract_binary_available is not None:
            return cls._tesseract_binary_available
        
        tesseract_binary = "tesseract.exe" if sys.platform == "win32" else "tesseract"
        
        if shutil.which(tesseract_binary):
            cls._tesseract_binary_available = True
            logger.debug(f"✓ Tesseract binary found: {tesseract_binary}")
            return True
        
        cls._tesseract_binary_available = False
        msg = f"Tesseract binary not found in PATH - OCR will be skipped"
        logger.warning(f"✗ {msg}")
        cls._warnings.append(msg)
        return False
    
    @classmethod
    def is_ocr_available(cls) -> bool:
        """
        Check if all OCR requirements are available.
        
        Returns:
            True if pytesseract + pdf2image + tesseract binary all available
        """
        return (
            cls.check_pytesseract() and
            cls.check_pdf2image() and
            cls.check_tesseract_binary()
        )
    
    @classmethod
    def get_installation_guide(cls) -> str:
        """
        Get platform-specific OCR installation instructions.
        
        Returns:
            Multi-line string with installation commands
        """
        guide = "\n⚠️  OCR SETUP REQUIRED\n"
        guide += "=" * 50 + "\n\n"
        
        guide += "1. Install Python dependencies:\n"
        guide += "   pip install pytesseract pdf2image pillow\n\n"
        
        guide += "2. Install Tesseract binary:\n"
        
        if sys.platform == "win32":
            guide += "   Windows (Scoop):\n"
            guide += "     scoop install tesseract\n\n"
            guide += "   Windows (Manual):\n"
            guide += "     Download: https://github.com/UB-Mannheim/tesseract/wiki\n"
            guide += "     Install to: C:\\Program Files\\Tesseract-OCR\n"
            guide += "     Add to PATH environment variable\n"
        
        elif sys.platform == "darwin":
            guide += "   macOS (Homebrew):\n"
            guide += "     brew install tesseract\n"
        
        else:  # Linux
            guide += "   Linux (Ubuntu/Debian):\n"
            guide += "     sudo apt-get install tesseract-ocr\n\n"
            guide += "   Linux (Fedora/RHEL):\n"
            guide += "     sudo dnf install tesseract\n\n"
            guide += "   Linux (Arch):\n"
            guide += "     sudo pacman -S tesseract\n"
        
        guide += "\n3. Verify installation:\n"
        guide += "   python -c \"import pytesseract; print(pytesseract.pytesseract.pytesseract_cmd)\"\n"
        guide += "\n" + "=" * 50
        
        return guide
    
    @classmethod
    def get_warnings(cls) -> list[str]:
        """Get list of OCR configuration warnings"""
        return cls._warnings
    
    @classmethod
    def log_setup_status(cls):
        """Log detailed OCR setup status"""
        logger.info("=" * 60)
        logger.info("OCR ENVIRONMENT DETECTION")
        logger.info("=" * 60)
        
        pytesseract_ok = cls.check_pytesseract()
        pdf2image_ok = cls.check_pdf2image()
        tesseract_ok = cls.check_tesseract_binary()
        
        logger.info(f"  pytesseract:       {'✓ OK' if pytesseract_ok else '✗ MISSING'}")
        logger.info(f"  pdf2image:         {'✓ OK' if pdf2image_ok else '✗ MISSING'}")
        logger.info(f"  tesseract binary:  {'✓ OK' if tesseract_ok else '✗ MISSING'}")
        
        if cls.is_ocr_available():
            logger.info("\n  ✓ OCR is FULLY CONFIGURED")
        else:
            logger.warning("\n  ⚠ OCR is NOT CONFIGURED")
            logger.warning(f"  Scanned PDFs will fall back to standard extraction")
            if cls._warnings:
                for warning in cls._warnings:
                    logger.warning(f"    - {warning}")
        
        logger.info("=" * 60)


def safe_ocr_extract(file_path: str) -> Optional[str]:
    """
    Safely extract text from PDF using OCR.
    
    Returns None if OCR dependencies are not available.
    Never crashes the system - graceful fallback only.
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        Extracted text if successful, None if OCR not available
    """
    
    # Check if OCR is available
    if not OCRConfig.is_ocr_available():
        logger.debug("OCR dependencies not available - skipping OCR extraction")
        return None
    
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as e:
        logger.warning(f"Failed to import OCR libraries: {e}")
        return None
    
    filename = os.path.basename(file_path)
    
    try:
        logger.info(f"🔄 Starting OCR extraction: {filename}")
        
        # Convert PDF pages to images
        logger.debug("Converting PDF to images for OCR...")
        images = convert_from_path(file_path, dpi=200)
        
        logger.debug(f"Converting {len(images)} pages for OCR processing")
        
        # Extract text from each page
        all_text = []
        successful_pages = 0
        failed_pages = 0
        
        for page_num, image in enumerate(images, 1):
            try:
                page_text = pytesseract.image_to_string(image, lang='eng')
                
                if page_text.strip():
                    all_text.append(f"--- Page {page_num} ---\n{page_text}")
                    successful_pages += 1
                else:
                    logger.debug(f"  Page {page_num}: No text extracted")
                    failed_pages += 1
            
            except Exception as e:
                logger.debug(f"  Page {page_num}: OCR error - {e}")
                failed_pages += 1
                continue
        
        text = "\n\n".join(all_text)
        
        logger.info(
            f"✓ OCR extraction complete: {successful_pages}/{len(images)} pages, "
            f"{len(text)} characters"
        )
        
        return text if text.strip() else None
    
    except FileNotFoundError as e:
        logger.error(
            f"Tesseract binary not found: {e}\n"
            f"Install via: "
            f"Windows: scoop install tesseract | "
            f"macOS: brew install tesseract | "
            f"Linux: sudo apt install tesseract-ocr"
        )
        return None
    
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return None


def get_ocr_status() -> dict:
    """
    Get current OCR configuration status.
    
    Returns:
        Dictionary with OCR capability details
    """
    return {
        "pytesseract_available": OCRConfig.check_pytesseract(),
        "pdf2image_available": OCRConfig.check_pdf2image(),
        "tesseract_binary_available": OCRConfig.check_tesseract_binary(),
        "ocr_fully_available": OCRConfig.is_ocr_available(),
        "warnings": OCRConfig.get_warnings(),
    }
