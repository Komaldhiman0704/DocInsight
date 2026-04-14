"""
PDF Export Service - Export chat sessions with sources as PDF files
Uses reportlab for clean, professional PDF generation
"""

import os
from io import BytesIO
from datetime import datetime
from typing import Optional
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def create_chat_export_pdf(session_title: str, messages: list[dict]) -> bytes:
    """
    Create a PDF from a chat session.
    
    Args:
        session_title: Title of the chat session
        messages: List of message dicts with keys: role, content, sources, timestamp, confidence
        
    Returns:
        PDF bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )
    
    # Custom styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    
    timestamp_style = ParagraphStyle(
        'Timestamp',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
    )
    
    user_style = ParagraphStyle(
        'UserMessage',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=8,
        leftIndent=20,
        fontName='Helvetica-Bold',
    )
    
    assistant_style = ParagraphStyle(
        'AssistantMessage',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8,
        leftIndent=20,
        alignment=TA_JUSTIFY,
    )
    
    source_style = ParagraphStyle(
        'Source',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=4,
        leftIndent=40,
        fontName='Helvetica-Oblique',
    )
    
    confidence_style = ParagraphStyle(
        'Confidence',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#059669'),
        spaceAfter=12,
        leftIndent=40,
        fontName='Helvetica',
    )
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph(session_title or "Chat Export", title_style))
    story.append(Paragraph(f"Exported on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", timestamp_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Process messages
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        sources = msg.get("sources", [])
        confidence = msg.get("confidence")
        timestamp = msg.get("timestamp")
        
        # Message header
        if role == "user":
            story.append(Paragraph(f"<b>You:</b>", user_style))
            story.append(Paragraph(content, user_style))
        else:
            story.append(Paragraph(f"<b>Assistant:</b>", user_style))
            story.append(Paragraph(content, assistant_style))
        
        # Sources
        if sources:
            for source in sources:
                if isinstance(source, dict):
                    doc_name = source.get("filename", "Unknown")
                    page = source.get("page", "N/A")
                    story.append(Paragraph(f"📄 {doc_name} (Page {page})", source_style))
                else:
                    story.append(Paragraph(f"📄 {source}", source_style))
        
        # Confidence
        if confidence:
            conf_level = confidence.get("confidence", "").upper() if isinstance(confidence, dict) else str(confidence).upper()
            if isinstance(confidence, dict):
                relevance = confidence.get("relevance_score", 0)
                story.append(Paragraph(f"✓ Confidence: {conf_level} ({relevance:.0%})", confidence_style))
            else:
                story.append(Paragraph(f"✓ Confidence: {conf_level}", confidence_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Page break every 5 messages to keep pages readable
        if (i + 1) % 5 == 0:
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def save_chat_export(session_id: str, session_title: str, messages: list[dict]) -> str:
    """
    Save chat export to disk (optional).
    
    Args:
        session_id: Session ID for filename
        session_title: Title of session
        messages: List of messages
        
    Returns:
        File path where PDF was saved
    """
    export_dir = "./chat_exports"
    os.makedirs(export_dir, exist_ok=True)
    
    pdf_bytes = create_chat_export_pdf(session_title, messages)
    
    filename = f"chat_export_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(export_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
    
    logger.info(f"Chat exported to {filepath}")
    return filepath
