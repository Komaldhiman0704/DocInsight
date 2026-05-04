"""
Document Analyzer Service - Multi-document analysis and cross-document insights
UPGRADE 2: Innovative feature for document comparison and analysis
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    Analyzes multiple documents together to find:
    - Common themes and patterns
    - Contradictions and differences
    - Cross-document insights
    - Comparative analysis
    
    Innovation: Enables questions like:
    "What are the differences between Document A and B?"
    "Find contradictions in these 3 documents"
    "What insights can you draw across all documents?"
    """
    
    @staticmethod
    async def analyze_documents(
        question: str,
        documents: List[Dict[str, Any]],
        llm
    ) -> Dict[str, Any]:
        """
        Analyze multiple documents to answer a question.
        
        Args:
            question: Comparative question (e.g., "Compare these documents")
            documents: List of {filename, content, chunks} dicts
            llm: Language model instance
        
        Returns:
            {
                analysis: str,
                key_differences: [str],
                similarities: [str],
                contradictions: [str],
                confidence: float
            }
        """
        try:
            if not documents or len(documents) < 2:
                return {
                    "analysis": "Please select at least 2 documents for comparison",
                    "key_differences": [],
                    "similarities": [],
                    "contradictions": [],
                    "confidence": 0.0
                }
            
            # Prepare document context
            doc_context = DocumentAnalyzer._prepare_context(documents)
            
            # Analyze with LLM
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert document analyst specializing in comparative analysis.

Analyze the provided documents to answer the user's question. Focus on:
1. Key differences between documents
2. Similarities and common themes
3. Contradictions or conflicts
4. Cross-document insights

Provide your analysis in a structured format with specific references to document sources.

IMPORTANT:
- Reference document names and specific sections
- Be precise and factual
- Highlight contradictions explicitly
- Show where documents agree or disagree

Prepare your response as JSON with this structure:
{
  "summary": "Brief overall analysis",
  "key_differences": ["difference 1", "difference 2", ...],
  "similarities": ["similarity 1", "similarity 2", ...],
  "contradictions": ["contradiction 1", ...],
  "cross_document_insights": ["insight 1", ...],
  "confidence_score": 0.85
}"""),
                ("user", """Documents to analyze:

{doc_context}

User question: {question}

Provide comparative analysis in JSON format.""")
            ])
            
            chain = analysis_prompt | llm | StrOutputParser()
            
            response = await chain.ainvoke({
                "doc_context": doc_context,
                "question": question,
            })
            
            # Parse response
            try:
                import re
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
                else:
                    analysis_data = {
                        "summary": response,
                        "key_differences": [],
                        "similarities": [],
                        "contradictions": [],
                        "cross_document_insights": [],
                        "confidence_score": 0.7
                    }
            except json.JSONDecodeError:
                analysis_data = {
                    "summary": response,
                    "key_differences": [],
                    "similarities": [],
                    "contradictions": [],
                    "cross_document_insights": [],
                    "confidence_score": 0.6
                }
            
            return {
                "analysis": analysis_data.get("summary", response),
                "key_differences": analysis_data.get("key_differences", []),
                "similarities": analysis_data.get("similarities", []),
                "contradictions": analysis_data.get("contradictions", []),
                "cross_document_insights": analysis_data.get("cross_document_insights", []),
                "confidence": analysis_data.get("confidence_score", 0.7)
            }
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}", exc_info=True)
            return {
                "analysis": f"Analysis failed: {str(e)}",
                "key_differences": [],
                "similarities": [],
                "contradictions": [],
                "confidence": 0.0
            }
    
    @staticmethod
    def _prepare_context(documents: List[Dict[str, Any]]) -> str:
        """Prepare document context for analysis"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            filename = doc.get("filename", f"Document {i}")
            content = doc.get("content", "")
            
            # Limit content to first 2000 chars per document
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            context_parts.append(
                f"---\n"
                f"Document {i}: {filename}\n"
                f"---\n"
                f"{content}\n"
            )
        
        return "\n".join(context_parts)
    
    @staticmethod
    async def find_contradictions(
        question: str,
        documents: List[Dict[str, Any]],
        llm
    ) -> List[Dict[str, str]]:
        """
        Find contradictions between documents.
        
        Returns list of contradictions with source documents.
        """
        try:
            analysis = await DocumentAnalyzer.analyze_documents(question, documents, llm)
            
            contradictions = []
            for contra in analysis.get("contradictions", []):
                contradictions.append({
                    "contradiction": contra,
                    "severity": "high" if "directly contradicts" in contra.lower() else "medium"
                })
            
            return contradictions
            
        except Exception as e:
            logger.error(f"Contradiction detection failed: {e}")
            return []
    
    @staticmethod
    def extract_document_summary(
        content: str,
        filename: str,
        max_length: int = 500
    ) -> str:
        """Extract key points from document for comparison"""
        try:
            # Simple extraction: first N sentences
            sentences = content.split(". ")
            key_points = []
            
            for sentence in sentences[:5]:
                if len(sentence.strip()) > 20:
                    key_points.append(sentence.strip())
            
            summary = ". ".join(key_points)
            return summary[:max_length] if len(summary) > max_length else summary
            
        except Exception as e:
            logger.debug(f"Summary extraction failed: {e}")
            return content[:max_length]
