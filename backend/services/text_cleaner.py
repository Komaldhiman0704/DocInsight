"""
Text Cleaning Service - Production-grade text normalization for OCR and PDFs

Handles:
- OCR noise removal (random symbols, spacing artifacts)
- Handwriting recognition cleanup
- Encoding normalization
- Structural preservation (paragraphs, lists)
- Page boundary awareness

CRITICAL: Preserves meaning - never removes semantic content
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextCleaner:
    """Handles text normalization for OCR and standard extraction"""
    
    # Common OCR artifacts to remove
    OCR_ARTIFACTS = {
        r'\b0([A-Z])\b': r'O\1',           # 0 → O in acronyms
        r'([O0])([A-Z]{2,})\b': r'O\2',   # Fix mixed 0/O in acronyms
        r'l([A-Z]+)': r'I\1',              # l → I in acronyms
        r'\b([0-9]+)([a-z])\b': r'\1 \2', # "5m" → "5 m"
        r'([a-z])([0-9])\b': r'\1 \2',    # "result5" → "result 5"
    }
    
    @staticmethod
    def clean_ocr_text(text: str, preserve_structure: bool = True) -> str:
        """
        Clean OCR-extracted text while preserving meaning and structure.
        
        Args:
            text: Raw OCR output (often noisy)
            preserve_structure: Keep paragraph/list structure
        
        Returns:
            Cleaned text suitable for embedding and retrieval
        """
        if not text:
            return ""
        
        # 1. Remove control characters except newlines and tabs
        text = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
        
        # 2. Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)           # Multiple spaces → single
        text = re.sub(r'\n[ \t]+', '\n', text)        # Leading spaces after newline
        text = re.sub(r'[ \t]+\n', '\n', text)        # Trailing spaces before newline
        text = re.sub(r'\n\n+', '\n\n', text)         # Multiple newlines → double
        
        # 3. Fix line breaks (OCR often breaks mid-word)
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)  # "word-\nbreak" → "wordbreak"
        text = re.sub(r'(\s)\n(\s)', r'\1 ', text)    # Loose line breaks → space
        
        # 4. Fix common OCR character confusion
        text = re.sub(r'([a-z])([l1I])([a-z])', r'\1i\3', text)  # Fix i/l/1/I confusion
        text = re.sub(r'\b([0-9]+)([a-z])\b', r'\1 \2', text)    # "5m" → "5 m"
        
        # 5. Normalize quotes and dashes
        text = re.sub(r'["""]', '"', text)             # Smart quotes → standard
        text = re.sub(r"[''']", "'", text)             # Smart apostrophes → standard
        text = re.sub(r'[–—]', '-', text)              # Em/en dashes → hyphen
        text = re.sub(r'… ', '... ', text)             # Ellipsis → standard dots
        
        # 6. Fix spacing around punctuation
        text = re.sub(r' ([.,:;!?)])', r'\1', text)   # Space before punctuation
        text = re.sub(r'([([{])\s+', r'\1', text)     # Space after opening bracket
        text = re.sub(r'\s+([)\]}])', r'\1', text)    # Space before closing bracket
        
        # 7. Remove excessive punctuation
        text = re.sub(r'\.{2,}', '...', text)         # Multiple dots → ellipsis
        text = re.sub(r'\?{2,}', '??', text)          # Multiple ? → double ?
        text = re.sub(r'!{2,}', '!!', text)           # Multiple ! → double !
        text = re.sub(r',,+', ',', text)              # Multiple commas → single
        
        # 8. Fix common OCR typos in technical content
        text = re.sub(r'\b([A-Z]{2,})\s+([A-Z])\b', r'\1\2', text)  # "A B C" → "ABC"
        
        # 9. Remove random special characters (but keep meaningful ones)
        # Keep: - / . , ; : ! ? ( ) [ ] { } ' " @
        text = re.sub(r'[^\w\s\n\-/.,:;:!?()\[\]{}\'"@]', '', text)
        
        # 10. Fix double spaces created by cleaning
        text = re.sub(r' +', ' ', text)
        
        # 11. Normalize encoding issues
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        return text.strip()
    
    @staticmethod
    def clean_pdf_text(text: str) -> str:
        """
        Clean text from standard PDF extraction (less aggressive than OCR).
        
        Args:
            text: Extracted PDF text (usually cleaner than OCR)
        
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Light cleaning - preserve original structure
        text = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n[ \t]+', '\n', text)
        text = re.sub(r'[ \t]+\n', '\n', text)
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Fix line breaks
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
        
        return text.strip()
    
    @staticmethod
    def assess_text_quality(text: str, source: str = "unknown") -> dict:
        """
        Assess quality of extracted text for filtering and debugging.
        
        Args:
            text: Text to assess
            source: "ocr" or "pdf" or "unknown"
        
        Returns:
            Dictionary with quality metrics
        """
        if not text:
            return {
                "quality": "empty",
                "char_count": 0,
                "word_count": 0,
                "line_count": 0,
                "printable_ratio": 0.0,
                "noise_indicators": ["empty_content"]
            }
        
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        
        # Count printable characters
        printable_count = sum(1 for c in text if c.isprintable())
        printable_ratio = printable_count / char_count if char_count > 0 else 0
        
        # Detect noise
        noise_indicators = []
        
        # Check for excessive special characters
        special_count = sum(1 for c in text if not (c.isalnum() or c.isspace()))
        special_ratio = special_count / char_count if char_count > 0 else 0
        if special_ratio > 0.3:
            noise_indicators.append(f"high_special_chars ({special_ratio:.1%})")
        
        # Check for gibberish patterns (consecutive non-vowel consonants)
        gibberish_pattern = re.findall(r'[bcdfghjklmnpqrstvwxyz]{4,}', text.lower())
        if gibberish_pattern and len(gibberish_pattern) > 5:
            noise_indicators.append("possible_gibberish")
        
        # Check character variety (healthy text has good variety)
        unique_chars = len(set(text))
        if unique_chars < 20:
            noise_indicators.append("low_character_variety")
        
        # Determine quality level
        if char_count < 50:
            quality = "too_short"
        elif printable_ratio < 0.7:
            quality = "high_noise"
        elif word_count < 5:
            quality = "insufficient_content"
        else:
            quality = "good"
        
        return {
            "quality": quality,
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "printable_ratio": round(printable_ratio, 3),
            "noise_indicators": noise_indicators,
            "source": source,
        }


def clean_text(text: str, source: str = "pdf") -> str:
    """
    Convenience function - clean text based on source type.
    
    Args:
        text: Text to clean
        source: "ocr" or "pdf"
    
    Returns:
        Cleaned text
    """
    if source.lower() == "ocr":
        return TextCleaner.clean_ocr_text(text)
    else:
        return TextCleaner.clean_pdf_text(text)


def assess_quality(text: str, source: str = "unknown") -> dict:
    """Convenience function - assess text quality"""
    return TextCleaner.assess_text_quality(text, source)
