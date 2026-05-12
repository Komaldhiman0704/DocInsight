"""
Advanced Features Router
UPGRADE FEATURES: Hybrid search + Multi-document analysis
New endpoints for innovative functionality
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
import json

from services.hybrid_search import HybridSearcher
from services.document_analyzer import DocumentAnalyzer
from services.vector_store import get_docs_with_scores
from services.llm import get_llm
from services.document_store import get_all_documents, get_document

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize hybrid searcher
hybrid_searcher = HybridSearcher()


class HybridSearchRequest(BaseModel):
    """Request for hybrid search"""
    query: str
    doc_ids: Optional[List[str]] = None


class DocumentComparisonRequest(BaseModel):
    """Request for multi-document comparison"""
    question: str
    doc_ids: List[str]  # At least 2 documents


@router.post("/hybrid-search")
async def hybrid_search(req: HybridSearchRequest):
    """
    UPGRADE 1: Hybrid Search using BM25 + Semantic search
    
    Combines keyword-based (BM25) and semantic (vector) search
    for more relevant results.
    
    Returns: List of documents with hybrid scores
    """
    try:
        if not req.query or len(req.query) < 2:
            raise HTTPException(400, "Query must be at least 2 characters")
        
        # Get semantic results
        semantic_results = get_docs_with_scores(req.query, req.doc_ids)
        
        if not semantic_results:
            return {
                "query": req.query,
                "results": [],
                "search_type": "hybrid",
                "note": "No relevant documents found"
            }
        
        # Convert to Document objects for hybrid search
        docs = [doc for doc, score in semantic_results]
        scores = [score for doc, score in semantic_results]
        
        # Build BM25 index
        hybrid_searcher.build_index(docs)
        
        # Perform hybrid search
        hybrid_results = hybrid_searcher.hybrid_search(
            req.query,
            list(zip(docs, scores)),
            top_k=5
        )
        
        # Format results
        results = []
        for doc, score in hybrid_results:
            results.append({
                "filename": doc.metadata.get("filename", "Unknown"),
                "page": doc.metadata.get("page", 0) + 1,
                "excerpt": doc.page_content[:300] + "...",
                "hybrid_score": float(score),
                "doc_id": doc.metadata.get("doc_id", "")
            })
        
        logger.info(f"Hybrid search: '{req.query}' → {len(results)} results")
        
        return {
            "query": req.query,
            "results": results,
            "search_type": "hybrid",
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        raise HTTPException(500, f"Hybrid search failed: {str(e)}")


@router.post("/compare-documents")
async def compare_documents(req: DocumentComparisonRequest):
    """
    UPGRADE 2: Multi-Document Comparison & Analysis
    
    Analyzes multiple documents together to find:
    - Differences and similarities
    - Contradictions
    - Cross-document insights
    
    Requires: At least 2 documents selected
    """
    try:
        # Validate
        if len(req.doc_ids) < 2:
            raise HTTPException(400, "Please select at least 2 documents for comparison")
        
        if not req.question or len(req.question) < 5:
            raise HTTPException(400, "Please ask a specific comparison question")
        
        # Fetch documents
        all_docs = get_all_documents()
        selected_docs = [d for d in all_docs if d["id"] in req.doc_ids]
        
        if len(selected_docs) < 2:
            raise HTTPException(400, "Could not find selected documents")
        
        # Prepare document data
        doc_data = []
        for doc in selected_docs:
            try:
                # Read file content
                with open(doc["file_path"], "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except:
                content = f"[File content not available: {doc['filename']}]"
            
            doc_data.append({
                "filename": doc["filename"],
                "content": content[:3000],  # Limit content
                "doc_id": doc["id"]
            })
        
        # Get LLM
        llm = get_llm()
        
        # Perform analysis
        analysis = await DocumentAnalyzer.analyze_documents(
            req.question,
            doc_data,
            llm
        )
        
        logger.info(f"Document comparison: {len(selected_docs)} docs analyzed")
        
        return {
            "question": req.question,
            "documents": [d["filename"] for d in doc_data],
            "analysis": analysis["analysis"],
            "key_differences": analysis["key_differences"],
            "similarities": analysis["similarities"],
            "contradictions": analysis["contradictions"],
            "insights": analysis.get("cross_document_insights", []),
            "confidence": analysis["confidence"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document comparison error: {e}", exc_info=True)
        raise HTTPException(500, f"Comparison failed: {str(e)}")


@router.get("/detect-contradictions")
async def detect_contradictions(doc_ids: List[str]):
    """
    UPGRADE 2 VARIANT: Detect contradictions between documents
    
    Identifies conflicting statements across documents
    """
    try:
        if len(doc_ids) < 2:
            raise HTTPException(400, "Please select at least 2 documents")
        
        # Fetch documents
        all_docs = get_all_documents()
        selected_docs = [d for d in all_docs if d["id"] in doc_ids]
        
        if len(selected_docs) < 2:
            raise HTTPException(400, "Could not find selected documents")
        
        # Prepare document data
        doc_data = []
        for doc in selected_docs:
            try:
                with open(doc["file_path"], "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except:
                content = ""
            
            doc_data.append({
                "filename": doc["filename"],
                "content": content[:2000],
                "doc_id": doc["id"]
            })
        
        # Get LLM
        llm = get_llm()
        
        # Find contradictions
        contradictions = await DocumentAnalyzer.find_contradictions(
            "Find any contradictions or conflicting information",
            doc_data,
            llm
        )
        
        logger.info(f"Contradiction detection: {len(contradictions)} found")
        
        return {
            "documents": [d["filename"] for d in doc_data],
            "contradictions": contradictions,
            "count": len(contradictions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contradiction detection error: {e}", exc_info=True)
        raise HTTPException(500, f"Detection failed: {str(e)}")
