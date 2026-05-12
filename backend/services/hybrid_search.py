"""
Hybrid Search Service - Combines BM25 keyword search with semantic vector search
UPGRADE 1: Innovative feature for better search relevance
"""

from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class HybridSearcher:
    """
    Combines BM25 (keyword-based ranking) with semantic (vector) search.
    
    This approach:
    1. Retrieves candidates from both BM25 and semantic search
    2. Uses reciprocal rank fusion (RRF) to combine scores intelligently
    3. Returns top-k results ranked by hybrid score
    
    Innovation: Handles both semantic queries ("concept-based") and
    keyword queries ("exact match") effectively.
    """
    
    def __init__(self):
        self.bm25_index = None
        self.documents = []
        self.chunk_to_doc_id = {}
    
    def build_index(self, documents: List[Document]):
        """Build BM25 index from documents"""
        try:
            # Extract and tokenize text
            tokenized_docs = []
            self.documents = documents
            
            for i, doc in enumerate(documents):
                # Simple tokenization
                tokens = doc.page_content.lower().split()
                tokenized_docs.append(tokens)
                self.chunk_to_doc_id[i] = doc.metadata.get("chunk_id", f"chunk_{i}")
            
            # Build BM25 index
            self.bm25_index = BM25Okapi(tokenized_docs)
            logger.info(f"Built BM25 index for {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            self.bm25_index = None
    
    def bm25_search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Search using BM25 keyword ranking.
        Returns: List of (doc_index, score) tuples
        """
        if not self.bm25_index or not self.documents:
            return []
        
        try:
            # Tokenize query
            query_tokens = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Return top-k with non-zero scores
            ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            return ranked[:top_k]
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def reciprocal_rank_fusion(
        self,
        semantic_results: List[Tuple[Document, float]],
        bm25_results: List[Tuple[int, float]],
        k: int = 60,
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Combine semantic and BM25 results using Reciprocal Rank Fusion (RRF).
        
        RRF Formula: Score = 1 / (k + rank)
        This intelligently weights both ranking approaches.
        
        Args:
            semantic_results: List of (Document, score) from vector search
            bm25_results: List of (index, score) from BM25 search
            k: Constant for RRF formula (default 60)
            top_k: Number of top results to return
        
        Returns:
            List of (Document, combined_score) tuples
        """
        try:
            # Create score dictionaries
            semantic_scores = {}
            for rank, (doc, score) in enumerate(semantic_results):
                doc_id = doc.metadata.get("chunk_id", id(doc))
                semantic_scores[doc_id] = 1.0 / (k + rank + 1)
            
            bm25_scores = {}
            for rank, (idx, score) in enumerate(bm25_results):
                if idx < len(self.documents):
                    doc_id = self.documents[idx].metadata.get("chunk_id", id(self.documents[idx]))
                    bm25_scores[doc_id] = 1.0 / (k + rank + 1)
            
            # Combine scores (equal weight: 50/50)
            combined_scores = {}
            all_doc_ids = set(semantic_scores.keys()) | set(bm25_scores.keys())
            
            for doc_id in all_doc_ids:
                semantic_score = semantic_scores.get(doc_id, 0.0)
                bm25_score = bm25_scores.get(doc_id, 0.0)
                # Weighted combination: 60% semantic, 40% BM25
                # (Semantic usually more important for RAG)
                combined_scores[doc_id] = (0.6 * semantic_score) + (0.4 * bm25_score)
            
            # Rebuild result documents with combined scores
            result_map = {}
            for doc, _ in semantic_results:
                doc_id = doc.metadata.get("chunk_id", id(doc))
                result_map[doc_id] = doc
            
            for idx, _ in bm25_results:
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    doc_id = doc.metadata.get("chunk_id", id(doc))
                    result_map[doc_id] = doc
            
            # Sort by combined score
            ranked = sorted(
                combined_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Return top-k with documents
            results = []
            for doc_id, score in ranked[:top_k]:
                if doc_id in result_map:
                    results.append((result_map[doc_id], score))
            
            logger.debug(f"RRF combined {len(all_doc_ids)} results into top {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"RRF fusion failed: {e}")
            return [(doc, score) for doc, score in semantic_results[:top_k]]
    
    def hybrid_search(
        self,
        query: str,
        semantic_results: List[Tuple[Document, float]],
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Perform hybrid search combining semantic and BM25.
        
        Args:
            query: User's search query
            semantic_results: Results from semantic (vector) search
            top_k: Number of results to return
        
        Returns:
            Hybrid-ranked results with better relevance
        """
        try:
            # Get BM25 results
            bm25_results = self.bm25_search(query, top_k=10)
            
            if not bm25_results:
                # Fallback to semantic if BM25 fails
                logger.debug("BM25 returned no results, using semantic only")
                return semantic_results[:top_k]
            
            # Use RRF to combine both
            hybrid_results = self.reciprocal_rank_fusion(
                semantic_results,
                bm25_results,
                top_k=top_k
            )
            
            return hybrid_results
            
        except Exception as e:
            logger.warning(f"Hybrid search failed, using semantic: {e}")
            return semantic_results[:top_k]
