"""
RAG Chain Service - LangGraph-style agentic RAG
Flow: User Query -> Rephrase (with history) -> Retrieve -> Generate Answer -> Return with sources
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from typing import AsyncGenerator
import logging

from services.llm import get_llm
from services.vector_store import get_retriever, get_docs_with_scores

logger = logging.getLogger(__name__)

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

CRITICAL INSTRUCTIONS:
- NEVER include "Sources:", "Page references:", citations, links, URLs, or any source attribution in your answer
- NEVER mention page numbers, document names, or where information came from
- Provide ONLY the factual content and analysis
- Format with headers, bullet points, or sections when appropriate
- Include context and connections between ideas
- Highlight key insights and important details
- Maintain a professional, informative tone
- If information isn't in the documents, state clearly: "I couldn't find specific information about that in the uploaded documents."

Context from documents:
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
    parts = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        filename = doc.metadata.get("filename", "document")
        parts.append(f"[Source {i} — {filename}, Page {page}]:\n{doc.page_content}")
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
    sources = []
    seen = set()
    for doc in docs:
        key = f"{doc.metadata.get('filename','?')}-p{doc.metadata.get('page','?')}"
        if key not in seen:
            seen.add(key)
            excerpt = doc.page_content[:300]
            if len(doc.page_content) > 300:
                excerpt += "..."
            sources.append({
                "filename": doc.metadata.get("filename", "Unknown"),
                "page": doc.metadata.get("page", 1),
                "doc_id": doc.metadata.get("doc_id", ""),
                "excerpt": excerpt,
            })
    return sources


def calculate_confidence(similarity_scores: list[float]) -> dict:
    """
    Calculate confidence level from similarity scores with multi-factor analysis.
    
    Args:
        similarity_scores: List of retrieval similarity scores (typically 0.0-1.0)
        
    Returns:
        dict with: confidence (str), relevance_score (float), source_count (int)
    """
    if not similarity_scores:
        return {
            "confidence": "low",
            "relevance_score": 0.0,
            "source_count": 0,
        }
    
    # Normalize scores to 0-1 range
    normalized_scores = []
    for score in similarity_scores:
        normalized = max(0.0, min(1.0, score))
        normalized_scores.append(normalized)
    
    # Calculate average relevance score
    avg_score = sum(normalized_scores) / len(normalized_scores) if normalized_scores else 0.0
    max_score = max(normalized_scores) if normalized_scores else 0.0
    
    # Multi-factor confidence calculation:
    # 1. Average relevance of retrieved chunks
    # 2. Peak relevance of best matching chunk  
    # 3. Number of relevant sources (more sources = more reliable)
    source_factor = min(1.0, len(normalized_scores) / 5.0)  # Bonus for multiple sources (max 5)
    
    # Composite confidence score
    composite_score = (avg_score * 0.6) + (max_score * 0.3) + (source_factor * 0.1)
    
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

    # Step 2: Retrieve with scores
    docs_with_scores = get_docs_with_scores(standalone_question, doc_ids)
    docs = [doc for doc, score in docs_with_scores]
    scores = [score for doc, score in docs_with_scores]
    context = format_docs(docs)

    # Step 3: Generate
    qa_chain = QA_PROMPT | llm | StrOutputParser()
    answer = await qa_chain.ainvoke({
        "question": standalone_question,
        "chat_history": lc_history,
        "context": context,
    })

    # Step 4: Calculate confidence metrics
    confidence_data = calculate_confidence(scores)

    # Step 5: Generate follow-up suggestions
    suggestions = await generate_suggestions(question, answer)

    return {
        "answer": answer,
        "sources": extract_sources(docs),
        "suggestions": suggestions,
        "confidence": confidence_data["confidence"],
        "relevance_score": confidence_data["relevance_score"],
        "source_count": confidence_data["source_count"],
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

    # Retrieve with scores
    docs_with_scores = get_docs_with_scores(standalone_question, doc_ids)
    docs = [doc for doc, score in docs_with_scores]
    scores = [score for doc, score in docs_with_scores]
    context = format_docs(docs)
    sources = extract_sources(docs)

    # Calculate confidence metrics
    confidence_data = calculate_confidence(scores)

    # Yield sources with confidence metrics
    sources_payload = {
        "sources": sources,
        "confidence": confidence_data["confidence"],
        "relevance_score": confidence_data["relevance_score"],
        "source_count": confidence_data["source_count"],
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
