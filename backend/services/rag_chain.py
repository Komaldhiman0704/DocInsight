"""
RAG Chain Service - LangGraph-style agentic RAG
Flow: User Query -> Rephrase (with history) -> Retrieve -> Generate Answer -> Return with sources

✅ ENHANCEMENTS:
- Query normalization for OCR text matching
- Fallback retrieval (show best matches even if no perfect match)
- Hybrid retrieval (vector + keyword search)
- Improved confidence scoring
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from typing import AsyncGenerator
import logging
import re

from services.llm import get_llm
from services.vector_store import get_retriever, get_docs_with_scores
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Query Normalization ────────────────────────────────────────────────────────

def normalize_query(query: str) -> str:
    """
    ✅ NEW: Normalize query for better OCR text matching
    
    Fixes common OCR-like patterns in user queries:
    - Lowercase (standardization)
    - Fix OCR confusions: 0→o, 1→l, |→i
    - Remove extra spaces
    - Normalize punctuation
    
    Args:
        query: Raw user query
    
    Returns:
        Normalized query optimized for retrieval
    """
    if not query or settings.QUERY_NORMALIZE is False:
        return query
    
    # Lowercase
    query = query.lower()
    
    # Fix common OCR confusions (smart replacement)
    # 0 → o (but not in numbers like "2023")
    query = re.sub(r'\b0([a-z])', r'o\1', query)  # "0pen" → "open"
    
    # 1 → l (in words, not numbers)
    query = re.sub(r'\b1([a-z])', r'l\1', query)  # "1ight" → "light"
    
    # | → i (pipe to letter i)
    query = query.replace('|', 'i')
    
    # Multiple spaces → single space
    query = re.sub(r'\s+', ' ', query).strip()
    
    # Remove extra punctuation
    query = re.sub(r'([.!?]){2,}', r'\1', query)
    
    logger.debug(f"Query normalized for retrieval")
    return query

# ── Prompts ────────────────────────────────────────────────────────────────────

REPHRASE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at reformulating ambiguous questions into clear, specific, retrieval-optimized queries.

Your task:
- Take a follow-up question (possibly vague or context-dependent) and rephrase it into a standalone question
- Preserve the original intent while making it more specific and search-friendly
- Add necessary context from chat history to make the question self-contained
- If the original is already clear and standalone, return it unchanged
- Use technical and domain-specific terminology when appropriate for better document matching
- Make the rephrased question concise but comprehensive (typically 10-30 words)

Guidelines:
✓ Make vague pronouns specific (e.g., "it" → "the topic/document name")
✓ Add domain context when needed for retrieval quality
✓ Expand abbreviations and acronyms only when helpful
✓ Keep the core question intent unchanged
✓ Optimize for search and vector similarity matching

Return ONLY the rephrased question, nothing else."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert AI analyst providing comprehensive, engaging answers based on PDF documents.

CRITICAL INSTRUCTIONS FOR SOURCE ATTRIBUTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ IMPORTANT: Source attribution is HANDLED SEPARATELY by the system
✓ Focus on providing the best possible answer from the documents
✓ Use the provided context from specified page numbers

ANSWER GUIDELINES:
- NEVER include "Sources:", "Page references:", citations, links, URLs, or any source attribution in your answer
- NEVER mention page numbers, document names, or where information came from in the answer text
- Provide ONLY the factual content and analysis
- Format with headers, bullet points, or sections when appropriate
- Include context and connections between ideas
- Highlight key insights and important details
- Maintain a professional, informative tone
- If information isn't in the documents, state clearly: "I couldn't find specific information about that in the uploaded documents."

NOTE ON SOURCES:
The system has already extracted and structured source information from the retrieved chunks.
Your answer content will be paired with source citations automatically on the frontend.
This ensures proper attribution of each claim to its source document and page number.

Context from documents (with page references):
{context}
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

FOLLOWUP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """As an expert analyst, generate exactly 3 insightful follow-up questions that deepen understanding of the topic.

Guidelines for follow-up questions:
- Each should naturally extend the conversation and explore related concepts
- Focus on deeper insights, implications, relationships, or practical applications
- Make questions specific to the document content, not generic
- Keep each under 12 words for clarity
- Ensure they're all answerable from the document
- Arrange from most relevant to exploratory

Return ONLY a JSON array of exactly 3 strings without numbering.
Example: ["How do these factors interact with market conditions?", "What are the long-term implications?", "How does this compare to industry standards?"]

Original question: {question}
Answer given: {answer}"""),
    ("human", "Generate 3 insightful follow-up questions as a JSON array.")
])



# ── Helpers ────────────────────────────────────────────────────────────────────

def format_docs(docs: list[Document]) -> str:
    """
    Format documents for LLM context with clear source attribution.
    
    This context includes page numbers and filenames so:
    1. LLM understands where each piece of information comes from
    2. Sources are extractable for display (handled by extract_sources)
    3. Traceability is maintained through the entire pipeline
    
    Args:
        docs: Retrieved document chunks with metadata
    
    Returns:
        Formatted context string suitable for LLM prompt
    
    DEFENSIVE: Safely handles empty docs list without crashing
    """
    # CRITICAL: Check for empty docs - prevents crashes downstream
    if not docs or len(docs) == 0:
        logger.warning("format_docs called with empty docs list")
        return "[No relevant content found in documents]"
    
    parts = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        filename = doc.metadata.get("filename", "document")
        chunk_id = doc.metadata.get("chunk_id", f"chunk_{i}")
        ocr_note = ""
        
        # Add OCR quality note if available
        if doc.metadata.get("ocr_used"):
            quality = doc.metadata.get("quality_score", "good")
            ocr_note = f" [OCR: {quality}]"
        
        # Format with prominent source markers
        parts.append(
            f"[Source {i} — {filename}, Page {page}]{ocr_note}:\n"
            f"{doc.page_content}"
        )
    
    return "\n\n---\n\n".join(parts)

def build_chat_history(history: list[dict]) -> list:
    messages = []
    for msg in history[-6:]:  # Keep last 6 messages (3 turns)
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages

def extract_sources(docs: list[Document]) -> list[dict]:
    """
    Extract source information from retrieved documents.
    
    CRITICAL FOR SOURCE ATTRIBUTION:
    - Returns filename, page number, doc_id for frontend display
    - Includes OCR confidence for uncertain sources
    - Deduplicates by filename + page to avoid duplicates
    - Extracts meaningful excerpt from chunk
    
    Args:
        docs: Retrieved document chunks
    
    Returns:
        List of dictionaries with source information:
        {
            "filename": str,
            "page": int,
            "doc_id": str,
            "excerpt": str,
            "ocr_used": bool,
            "quality_score": str
        }
    """
    sources = []
    seen = set()
    
    # DEFENSIVE: Check for empty docs list
    if not docs or len(docs) == 0:
        logger.debug("extract_sources called with empty docs list")
        return sources
    
    for doc in docs:
        # Create unique key to deduplicate (same file + same page = same source)
        filename = doc.metadata.get("filename", "Unknown")
        page = doc.metadata.get("page", 1)
        key = f"{filename}-p{page}"
        
        if key not in seen:
            seen.add(key)
            
            # Extract meaningful excerpt
            excerpt = doc.page_content[:300]
            if len(doc.page_content) > 300:
                excerpt += "..."
            
            # Get quality metrics for OCR sources
            source_dict = {
                "filename": filename,
                "page": page,
                "doc_id": doc.metadata.get("doc_id", ""),
                "excerpt": excerpt,
            }
            
            # Add OCR information if available
            if doc.metadata.get("ocr_used"):
                source_dict["ocr_used"] = True
                source_dict["quality_score"] = doc.metadata.get("quality_score", "medium")
            
            sources.append(source_dict)
    
    logger.debug(f"Extracted {len(sources)} unique sources from {len(docs)} chunks")
    return sources


def calculate_confidence(similarity_scores: list[float], docs: list[Document] = None) -> dict:
    """
    Calculate confidence level from similarity scores with multi-factor analysis.
    
    Accounts for:
    1. Similarity scores (relevance of retrieved chunks)
    2. Number of sources (more sources = more reliable)
    3. OCR quality (OCR sources slightly lower confidence)
    
    Args:
        similarity_scores: List of retrieval similarity scores (typically 0.0-1.0)
        docs: Optional list of documents to check for OCR usage
        
    Returns:
        dict with: confidence (str), relevance_score (float), source_count (int), ocr_sources (bool)
    """
    if not similarity_scores:
        return {
            "confidence": "low",
            "relevance_score": 0.0,
            "source_count": 0,
            "ocr_sources": False,
        }
    
    # Normalize scores to 0-1 range
    normalized_scores = []
    for score in similarity_scores:
        normalized = max(0.0, min(1.0, score))
        normalized_scores.append(normalized)
    
    # Calculate average and peak relevance
    avg_score = sum(normalized_scores) / len(normalized_scores) if normalized_scores else 0.0
    max_score = max(normalized_scores) if normalized_scores else 0.0
    
    # Check if any sources used OCR
    ocr_used = False
    if docs:
        ocr_used = any(doc.metadata.get("ocr_used", False) for doc in docs)
    
    # Multi-factor confidence calculation:
    # 1. Average relevance of retrieved chunks (0.6 weight)
    # 2. Peak relevance of best matching chunk (0.3 weight)
    # 3. Number of relevant sources - bonus for multiple sources (0.1 weight)
    source_factor = min(1.0, len(normalized_scores) / 5.0)  # Max bonus at 5+ sources
    
    # Composite confidence score
    composite_score = (avg_score * 0.6) + (max_score * 0.3) + (source_factor * 0.1)
    
    # Adjust for OCR sources (reduce confidence slightly if OCR was used)
    if ocr_used:
        composite_score *= 0.95  # 5% confidence penalty for OCR sources
    
    # Determine confidence level with smoother thresholds
    if composite_score >= 0.70:
        confidence = "high"
    elif composite_score >= 0.45:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        "confidence": confidence,
        "relevance_score": round(avg_score, 2),
        "source_count": len(similarity_scores),
        "ocr_sources": ocr_used,
    }


async def generate_suggestions(question: str, answer: str, sources: list[dict] = None) -> list[str]:
    """
    Generate follow-up question suggestions.
    
    Args:
        question: The original question asked
        answer: The generated answer
        sources: Optional list of source documents used
        
    Returns:
        List of 3 follow-up questions (or empty list on failure)
    """
    try:
        llm = get_llm()
        followup_chain = FOLLOWUP_PROMPT | llm | StrOutputParser()
        
        # Build context for suggestions, including sources if available
        sources_context = ""
        if sources:
            source_files = set(s.get("filename", "unknown") for s in sources)
            sources_context = f"(Sources: {', '.join(source_files)})"
        
        response = await followup_chain.ainvoke({
            "question": question,
            "answer": answer,
        })
        
        # Try to parse JSON response
        import json
        suggestions = json.loads(response.strip())
        
        # Validate it's a list of strings
        if isinstance(suggestions, list) and len(suggestions) == 3:
            if all(isinstance(s, str) for s in suggestions):
                return suggestions
        
        logger.warning(f"Invalid suggestions format: {response}")
        return []
        
    except Exception as e:
        logger.warning(f"Failed to generate suggestions: {e}")
        return []


# ── Non-streaming RAG ─────────────────────────────────────────────────────────

async def run_rag_chain(
    question: str,
    chat_history: list[dict],
    doc_ids: list[str] | None = None,
) -> dict:
    llm = get_llm()
    lc_history = build_chat_history(chat_history)

    # Step 1: Rephrase if there's history
    if lc_history:
        rephrase_chain = REPHRASE_PROMPT | llm | StrOutputParser()
        standalone_question = await rephrase_chain.ainvoke({
            "question": question,
            "chat_history": lc_history,
        })
        logger.info(f"Rephrased: '{question}' -> '{standalone_question}'")
    else:
        standalone_question = question
    
    # ✅ NEW: Normalize query for OCR text matching
    normalized_question = normalize_query(standalone_question)
    if normalized_question != standalone_question:
        logger.info(f"Query normalized: '{standalone_question}' → '{normalized_question}'")

    # Step 2: Retrieve with scores - CRITICAL: Check for empty results
    docs_with_scores = get_docs_with_scores(normalized_question, doc_ids)
    
    # ✅ IMPROVED: Fallback retrieval (never return empty)
    if not docs_with_scores or len(docs_with_scores) == 0:
        logger.warning(
            f"No relevant documents retrieved for query: {normalized_question}"
        )
        
        # ✅ Fallback: Get top-2 closest matches anyway (if enabled)
        if settings.ENABLE_FALLBACK_RETRIEVAL:
            logger.info("Attempting fallback retrieval (top-2 closest matches)...")
            # Re-retrieve with larger k and no filtering
            from services.vector_store import get_vectorstore
            vectorstore = get_vectorstore()
            
            fallback_results = vectorstore.similarity_search_with_score(
                query=normalized_question,
                k=2  # Get top 2 even if low similarity
            )
            
            if fallback_results:
                docs_with_scores = fallback_results
                logger.info(f"✓ Fallback retrieved {len(fallback_results)} matches (lower confidence expected)")
            else:
                logger.error("Fallback retrieval also returned no results")
                return {
                    "answer": "⚠️ Unable to find relevant information. Please try rephrasing your question or upload additional documents that might contain the information you're looking for.",
                    "sources": [],
                    "suggestions": [],
                    "confidence": "low",
                    "relevance_score": 0.0,
                    "source_count": 0,
                    "ocr_sources": False,
                    "standalone_question": normalized_question,
                }
        else:
            return {
                "answer": "⚠️ No relevant documents found. Try rephrasing or upload additional documents.",
                "sources": [],
                "suggestions": [],
                "confidence": "low",
                "relevance_score": 0.0,
                "source_count": 0,
                "ocr_sources": False,
                "standalone_question": normalized_question,
            }
    
    docs = [doc for doc, score in docs_with_scores]
    scores = [score for doc, score in docs_with_scores]
    
    # Extra safety check (should never happen, but defensive coding)
    if not docs or len(docs) == 0:
        logger.error("docs_with_scores returned results but docs list is empty - this should not happen")
        return {
            "answer": "⚠️ An error occurred while processing the documents.",
            "sources": [],
            "suggestions": [],
            "confidence": "low",
            "relevance_score": 0.0,
            "source_count": 0,
            "ocr_sources": False,
            "standalone_question": normalized_question,
        }
    
    context = format_docs(docs)

    # Step 3: Generate
    qa_chain = QA_PROMPT | llm | StrOutputParser()
    answer = await qa_chain.ainvoke({
        "question": normalized_question,
        "chat_history": lc_history,
        "context": context,
    })

    # Step 4: Calculate confidence metrics (accounting for OCR sources)
    confidence_data = calculate_confidence(scores, docs)

    # Step 5: Generate follow-up suggestions
    suggestions = await generate_suggestions(question, answer)

    return {
        "answer": answer,
        "sources": extract_sources(docs),
        "suggestions": suggestions,
        "confidence": confidence_data["confidence"],
        "relevance_score": confidence_data["relevance_score"],
        "source_count": confidence_data["source_count"],
        "ocr_sources": confidence_data.get("ocr_sources", False),
        "standalone_question": standalone_question,
    }


# ── Streaming RAG ─────────────────────────────────────────────────────────────

async def stream_rag_chain(
    question: str,
    chat_history: list[dict],
    doc_ids: list[str] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Streaming RAG chain. Yields:
    - First: a __SOURCES__ prefixed JSON string with confidence metrics
    - Then: answer tokens one by one
    - Finally: __SUGGESTIONS__ prefixed JSON array
    """
    import json

    llm = get_llm()
    lc_history = build_chat_history(chat_history)

    # Rephrase
    if lc_history:
        rephrase_chain = REPHRASE_PROMPT | llm | StrOutputParser()
        standalone_question = await rephrase_chain.ainvoke({
            "question": question,
            "chat_history": lc_history,
        })
    else:
        standalone_question = question

    # Retrieve with scores - CRITICAL: Check for empty results
    docs_with_scores = get_docs_with_scores(standalone_question, doc_ids)
    
    # DEFENSIVE: No relevant documents found - return safe empty response
    if not docs_with_scores or len(docs_with_scores) == 0:
        logger.warning(
            f"No relevant documents retrieved for streaming query: {standalone_question}"
        )
        
        # Yield safe empty sources
        empty_sources_payload = {
            "sources": [],
            "confidence": "low",
            "relevance_score": 0.0,
            "source_count": 0,
            "ocr_sources": False,
        }
        yield f"__SOURCES__{json.dumps(empty_sources_payload)}\n"
        
        # Yield warning message
        yield "⚠️ I couldn't find relevant information in the uploaded documents to answer your question. Try rephrasing your query or uploading additional documents.\n"
        
        # Yield empty suggestions
        yield f"__SUGGESTIONS__{json.dumps([])}\\n"
        return
    
    docs = [doc for doc, score in docs_with_scores]
    scores = [score for doc, score in docs_with_scores]
    
    # Extra safety check
    if not docs or len(docs) == 0:
        logger.error("docs_with_scores returned results but docs list is empty")
        empty_sources_payload = {
            "sources": [],
            "confidence": "low",
            "relevance_score": 0.0,
            "source_count": 0,
            "ocr_sources": False,
        }
        yield f"__SOURCES__{json.dumps(empty_sources_payload)}\\n"
        yield "⚠️ An error occurred while processing the documents.\\n"
        yield f"__SUGGESTIONS__{json.dumps([])}\\n"
        return
    
    context = format_docs(docs)
    sources = extract_sources(docs)

    # Calculate confidence metrics (accounting for OCR sources)
    confidence_data = calculate_confidence(scores, docs)

    # Yield sources with confidence metrics
    sources_payload = {
        "sources": sources,
        "confidence": confidence_data["confidence"],
        "relevance_score": confidence_data["relevance_score"],
        "source_count": confidence_data["source_count"],
        "ocr_sources": confidence_data.get("ocr_sources", False),
    }
    yield f"__SOURCES__{json.dumps(sources_payload)}\n"

    # Stream answer tokens
    qa_chain = QA_PROMPT | llm | StrOutputParser()
    full_answer = ""
    async for token in qa_chain.astream({
        "question": standalone_question,
        "chat_history": lc_history,
        "context": context,
    }):
        full_answer += token
        yield token

    # Generate and yield follow-up suggestions AFTER streaming completes
    suggestions = await generate_suggestions(question, full_answer, sources)
    yield f"__SUGGESTIONS__{json.dumps(suggestions)}\n"
