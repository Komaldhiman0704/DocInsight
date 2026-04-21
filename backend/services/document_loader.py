"""
Document Loader Service
Handles text extraction from PDF, DOCX, and TXT files.

Features:
- Standard text extraction for PDFs using PyPDFLoader
- Support for DOCX and TXT files
- Text normalization and cleanup
- Comprehensive logging and error handling
"""

import os
import logging
from typing import Optional, Tuple

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def load_pdf(file_path: str, filename: str) -> list[Document]:
    """
    Load PDF file and return list of Document objects (one per page).
    
    Args:
        file_path: Path to PDF file
        filename: Original filename (for metadata)
    
    Returns:
        List of Document objects with metadata:
        - page: Page number (1-indexed)
        - filename: Original filename
    """
    try:
        logger.info(f"Loading PDF: {filename}")
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        if not pages or len(pages) == 0:
            logger.error(f"No pages extracted from {filename}")
            raise ValueError(f"No content could be extracted from {filename}")
        
        # Add metadata to each page
        for page in pages:
            page.metadata["filename"] = filename
        
        logger.info(f"✓ Extracted {len(pages)} pages from {filename}")
        return pages
        
    except Exception as e:
        logger.error(f"Failed to load PDF {filename}: {e}", exc_info=True)
        raise


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


def load_document(file_path: str, filename: str) -> list[Document]:
    """
    Load any supported document type (PDF, DOCX, TXT).
    
    Args:
        file_path: Path to file
        filename: Original filename
    
    Returns:
        List of Document objects
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext == '.pdf':
        return load_pdf(file_path, filename)
    elif file_ext == '.docx':
        return load_docx_file(file_path, filename)
    elif file_ext == '.txt':
        return load_txt_file(file_path, filename)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


# Backward compatibility alias for OCR removal
def load_pdf_with_ocr(file_path: str, filename: str) -> list[Document]:
    """
    Backward compatibility wrapper. 
    Now simply loads PDF without OCR support.
    """
    return load_pdf(file_path, filename)

