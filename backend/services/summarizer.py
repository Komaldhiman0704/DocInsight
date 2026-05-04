"""
Document Summarizer - Generates AI summaries from documents asynchronously
Supports PDF, DOCX, and TXT files
"""
import logging
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate

from services.llm import get_llm
from services.document_store import update_document_summary

logger = logging.getLogger(__name__)


async def generate_summary(file_path: str, filename: str) -> str:
    """
    Generate a summary from a document (PDF, DOCX, or TXT).
    
    Args:
        file_path: Path to the document file
        filename: Original filename for logging
        
    Returns:
        Summary string (or empty string if generation fails)
    """
    try:
        logger.info(f"Generating summary for {filename}")
        
        file_ext = os.path.splitext(filename)[1].lower()
        text_content = ""
        
        if file_ext == '.pdf':
            # Load first 5 pages from PDF
            loader = PyPDFLoader(file_path)
            pages = loader.load()  # ✅ FIX: PyPDFLoader.load() is sync, not aload()
            for page in pages[:5]:
                text_content += page.page_content + "\n"
                
        elif file_ext == '.docx':
            # Load DOCX file
            try:
                from docx import Document as DocxDocument
                doc = DocxDocument(file_path)
                # Get first 20 paragraphs or all if less
                for para in doc.paragraphs[:20]:
                    if para.text.strip():
                        text_content += para.text + "\n"
            except ImportError:
                logger.error("python-docx not installed, cannot summarize DOCX")
                return ""
                
        elif file_ext == '.txt':
            # Load TXT file
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
                # Limit to first 2000 characters for summarization
                text_content = text_content[:2000]
        
        if not text_content.strip():
            logger.warning(f"No text extracted from {filename}")
            return ""
        
        # Truncate if too long (to avoid token limits)
        max_chars = 3000
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars]
        
        # Create prompt for summarization
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert document analyst creating executive summaries.

Generate a compelling 3-section summary (max 120 words total):
1) **Core Purpose**: What is this document fundamentally about and its significance?
2) **Key Insights**: What are the most important takeaways or findings?
3) **Practical Value**: Who should read this and what can they gain?

Requirements:
- Write engagingly but professionally
- Highlight the most valuable information
- Make it informative for quick understanding
- Use formatting with bold headers for clarity

Document text:
{text}"""),
            ("human", "Generate a professional executive summary of this document.")
        ])
        
        # Generate summary
        llm = get_llm()
        chain = summary_prompt | llm
        response = await chain.ainvoke({"text": text_content})
        summary = response.content.strip()
        
        logger.info(f"Summary generated for {filename}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to summarize {filename}: {e}", exc_info=True)
        return ""
