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
    ("system", """You are an expert AI analyst providing accurate, evidence-based answers STRICTLY from the provided documents.

🔒 CRITICAL RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ONLY use information explicitly stated in the context below
2. If the answer is NOT in the documents, respond EXACTLY:
   "I couldn't find specific information about this in the uploaded documents."
3. Do NOT use external knowledge, assumptions, or general information
4. Do NOT fabricate page numbers, dates, names, or facts
5. When uncertain, acknowledge it clearly
6. Quote directly from documents when making factual claims

ANSWER GUIDELINES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Source attribution is HANDLED SEPARATELY by the system
✓ Focus on providing accurate answers from the documents
✓ NEVER include "Sources:", "Page:", citations, or URLs in your answer
✓ NEVER mention page numbers or document names in the answer text
✓ Provide ONLY the factual content and analysis

Format Guidelines:
- Use headers, bullet points, or sections when appropriate
- Include context and connections between ideas
- Highlight key insights and important details
- Maintain a professional, informative tone

Context from documents (with page references):
{context}
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

FOLLOWUP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """As an expert analyst, generate exactly 2 concise follow-up questions that deepen understanding of the topic.

Guidelines for follow-up questions:
- Each should naturally extend the conversation and explore related concepts
- Focus on deeper insights, implications, or practical applications
- Make questions specific to the document content, not generic
- Keep each under 15 words for clarity
- Ensure they're both answerable from the document
- Arrange from most relevant to exploratory

Return ONLY a JSON array of exactly 2 strings without numbering.
Example: ["How do these factors interact with market conditions?", "What are the long-term implications?"]

Original question: {question}
Answer given: {answer}"""),
    ("human", "Generate 2 concise follow-up questions as a JSON array.")
])



# ── Helpers ────────────────────────────────────────────────────────────────────

def format_docs(docs: list[Document]) -> str:
    """
    Format documents for LLM context with clear source attribution.
    
    This context includes page numbers and filenames so:
    1. LLM understands where each piece of information comes from
    2. Sources are extractable for display (handled by extract_sources)
    3. Traceability is maintained through the entire pipeline
    
    OPTIMIZED: Truncates each chunk to max 500 chars (keeps relevance, saves tokens)
    
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
    seen_chunks = set()  # Track duplicates
    
    for i, doc in enumerate(docs, 1):
        page_num = doc.metadata.get("page", 0)
        # Convert 0-indexed page numbering to 1-indexed for display
        if isinstance(page_num, int):
            page = page_num + 1
        else:
            page = "?"
        filename = doc.metadata.get("filename", "document")
        chunk_id = doc.metadata.get("chunk_id", "")
        
        # Skip duplicate chunks (same file + page + similar content)
        if chunk_id and chunk_id in seen_chunks:
            logger.debug(f"Skipping duplicate chunk: {chunk_id}")
            continue
        if chunk_id:
            seen_chunks.add(chunk_id)
        
        # Optimize: Truncate content to 500 chars (keeps relevance, reduces tokens)
        content = doc.page_content[:500]
        if len(doc.page_content) > 500:
            content += "..."
        
        # Format with prominent source markers
        parts.append(
            f"[Source {i} — {filename}, Page {page}]:\n"
            f"{content}"
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
    
    Returns filename, page number, and excerpt for frontend display.
    
    Args:
        docs: Retrieved document chunks
    
    Returns:
        List of dictionaries with source information:
        {
            "filename": str,
            "page": int,
            "doc_id": str,
            "excerpt": str,
        }
    """
    sources = []
    seen = set()
    
    # Check for empty docs list
    if not docs or len(docs) == 0:
        logger.debug("extract_sources called with empty docs list")
        return sources
    
    for doc in docs:
        # Create unique key to deduplicate (same file + same page = same source)
        filename = doc.metadata.get("filename", "Unknown")
        page_num = doc.metadata.get("page", 0)
        # Convert 0-indexed page numbering to 1-indexed for display
        page = page_num + 1 if isinstance(page_num, int) else 1
        key = f"{filename}-p{page}"
        
        if key not in seen:
            seen.add(key)
            
            # Extract meaningful excerpt
            excerpt = doc.page_content[:300]
            if len(doc.page_content) > 300:
                excerpt += "..."
            
            source_dict = {
                "filename": filename,
                "page": page,
                "doc_id": doc.metadata.get("doc_id", ""),
                "excerpt": excerpt,
            }
            
            sources.append(source_dict)
    
    logger.debug(f"Extracted {len(sources)} unique sources from {len(docs)} chunks")
    return sources


def filter_sources_by_semantic_similarity(
    sources: list[dict],
    answer_text: str,
    docs: list[Document],
    top_k: int = 3
) -> list[dict]:
    """
    Filter sources by semantic similarity to the generated answer.
    
    Uses existing HuggingFace embedding model (all-MiniLM-L6-v2) to compute
    cosine similarity between answer embeddings and source chunk embeddings.
    
    This enhances source relevance: sources are now selected based on
    ANSWER content, not just QUERY keywords.
    
    Args:
        sources: Raw sources from extract_sources()
        answer_text: Generated answer (complete)
        docs: Original retrieved Document objects
        top_k: Number of top sources to return (default 3)
    
    Returns:
        Filtered and ranked sources with:
        - relevance_score: Semantic similarity to answer (0-1)
        - evidence: Answer-relevant sentence from source
        - keywords: Answer-based keywords
    """
    if not sources or not answer_text or not docs:
        return sources[:top_k]
    
    import re
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    
    try:
        # Get existing embedding model (singleton, already loaded)
        from services.vector_store import get_embeddings
        embeddings_model = get_embeddings()
        
        # Embed the answer once
        logger.debug(f"Computing answer embedding for semantic filtering...")
        answer_embedding = embeddings_model.embed_query(answer_text)
        
        # Extract meaningful answer keywords
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'not', 'no', 'yes', 'its', 'about', 'from', 'with', 'by', 'as'
        }
        answer_words = [
            w for w in re.findall(r'\b\w+\b', answer_text.lower())
            if len(w) >= 4 and w not in stop_words
        ]
        answer_word_set = set(answer_words)
        
        # Score each source by semantic similarity
        scored_sources = []
        
        for idx, source in enumerate(sources):
            # Find corresponding document chunk
            doc = None
            for d in docs:
                if (d.metadata.get("filename") == source["filename"] and
                    d.metadata.get("page") == (source["page"] - 1)):
                    doc = d
                    break
            
            if not doc:
                logger.debug(f"Doc not found for {source.get('filename')} p{source.get('page')}, using excerpt")
                # Fallback: use the excerpt from source
                source_text = source.get("excerpt", "")
            else:
                source_text = doc.page_content
            
            if not source_text:
                continue
            
            # Embed source chunk
            source_embedding = embeddings_model.embed_query(source_text)
            
            # Compute cosine similarity
            similarity = cosine_similarity(
                [answer_embedding],
                [source_embedding]
            )[0][0]
            
            # Find best answer-relevant sentence from source
            sentences = re.split(r'[.!?]+', source_text)
            best_sentence = ""
            best_score = 0
            
            for sentence in sentences:
                if len(sentence.strip()) < 20:
                    continue
                
                # Score by keyword overlap with answer
                sent_words = set(re.findall(r'\b\w+\b', sentence.lower()))
                overlap = len(answer_word_set & sent_words)
                score = overlap / max(len(answer_word_set), 1)
                
                if score > best_score:
                    best_score = score
                    best_sentence = sentence.strip()
            
            # Fallback to first substantial sentence
            if not best_sentence:
                for sentence in sentences:
                    if len(sentence.strip()) >= 20:
                        best_sentence = sentence.strip()
                        break
            
            # Extract matching keywords (from answer, not query!)
            source_text_lower = source_text.lower()
            matching_keywords = [
                w for w in answer_words[:15]
                if w in source_text_lower
            ][:5]
            
            # Update source with semantic fields
            enriched_source = dict(source)
            enriched_source["relevance_score"] = float(similarity)
            enriched_source["evidence"] = best_sentence
            enriched_source["keywords"] = matching_keywords
            
            scored_sources.append(enriched_source)
        
        # Sort by semantic similarity (highest first)
        scored_sources.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Return top_k
        top_sources = scored_sources[:top_k]
        
        if top_sources:
            avg_sim = np.mean([s["relevance_score"] for s in top_sources])
            logger.info(
                f"Semantic filtering: {len(sources)} sources → {len(top_sources)} top sources "
                f"(avg similarity: {avg_sim:.3f})"
            )
        
        return top_sources
        
    except Exception as e:
        logger.warning(f"Semantic filtering failed, falling back to basic sources: {e}")
        return sources[:top_k]


def filter_and_rank_sources(sources: list[dict], answer_text: str, question: str, top_k: int = 3) -> list[dict]:
    """
    Filter sources by answer relevance using keyword overlap scoring.
    
    Returns top_k sources with:
    - evidence: exact supporting sentence from source
    - keywords: matching keywords for UI highlighting
    - relevance_score: keyword overlap score (0-1)
    """
    if not sources or not answer_text.strip():
        return sources[:top_k]
    
    import re
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                  'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                  'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                  'not', 'no', 'yes', 'its', 'about', 'from', 'with', 'by', 'as'}
    
    try:
        answer_lower = answer_text.lower()
        answer_words = [w for w in re.findall(r'\b\w+\b', answer_lower) 
                        if len(w) >= 3 and w not in stop_words]
        answer_word_set = set(answer_words)
        
        question_lower = question.lower()
        question_words = [w for w in re.findall(r'\b\w+\b', question_lower)
                          if len(w) >= 3 and w not in stop_words]
        question_word_set = set(question_words)
        
        logger.debug(f"Answer keywords: {answer_words[:10]}")
        logger.debug(f"Question keywords: {question_words[:10]}")
        
        scored_sources = []
        for source in sources:
            excerpt = source.get("excerpt", "").lower()
            if not excerpt:
                continue
            
            excerpt_words = set(re.findall(r'\b\w+\b', excerpt))
            answer_overlap = len(answer_word_set & excerpt_words)
            answer_coverage = answer_overlap / max(len(answer_word_set), 1)
            
            question_overlap = len(question_word_set & excerpt_words)
            question_coverage = question_overlap / max(len(question_word_set), 1)
            
            relevance_score = (0.7 * answer_coverage) + (0.3 * question_coverage)
            
            if relevance_score < 0.1:
                logger.debug(f"Skipping {source.get('filename', '?')} - low relevance")
                continue
            
            sentences = re.split(r'[.!?]+', source["excerpt"])
            best_sentence = ""
            best_sentence_score = 0
            
            for sentence in sentences:
                if len(sentence.strip()) < 20:
                    continue
                sentence_lower = sentence.strip().lower()
                sentence_words = set(re.findall(r'\b\w+\b', sentence_lower))
                sent_overlap = len(answer_word_set & sentence_words)
                sent_score = sent_overlap / max(len(answer_word_set), 1)
                
                if sent_score > best_sentence_score:
                    best_sentence_score = sent_score
                    best_sentence = sentence.strip()
            
            if not best_sentence:
                for sentence in sentences:
                    if len(sentence.strip()) >= 20:
                        best_sentence = sentence.strip()
                        break
            
            matching_keywords = [w for w in answer_words if w in excerpt][:5]
            
            enriched_source = dict(source)
            enriched_source["evidence"] = best_sentence
            enriched_source["keywords"] = matching_keywords
            enriched_source["relevance_score"] = round(relevance_score, 2)
            
            scored_sources.append(enriched_source)
        
        scored_sources.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_sources = scored_sources[:top_k]
        logger.info(f"Filtered {len(sources)} sources → {len(top_sources)} relevant")
        
        return top_sources
        
    except Exception as e:
        logger.warning(f"Source filtering failed: {e}")
        return sources[:top_k]


def calculate_confidence(similarity_scores: list[float], docs: list) -> dict:
    """
    Calculate confidence level from similarity scores.
    
    Accounts for:
    1. Similarity scores (relevance of retrieved chunks)
    2. Number of sources (more sources = more reliable)
        
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
    
    # Calculate average and peak relevance
    avg_score = sum(normalized_scores) / len(normalized_scores) if normalized_scores else 0.0
    max_score = max(normalized_scores) if normalized_scores else 0.0
    
    # Multi-factor confidence calculation:
    # 1. Average relevance of retrieved chunks (0.6 weight)
    # 2. Peak relevance of best matching chunk (0.3 weight)
    # 3. Number of relevant sources - bonus for multiple sources (0.1 weight)
    source_factor = min(1.0, len(normalized_scores) / 5.0)  # Max bonus at 5+ sources
    
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
        
        # Validate it's a list of strings (expecting exactly 2)
        if isinstance(suggestions, list) and len(suggestions) == 2:
            if all(isinstance(s, str) for s in suggestions):
                return suggestions
        
        logger.warning(f"Invalid suggestions format: {response}")
        return []
        
    except Exception as e:
        logger.warning(f"Failed to generate suggestions: {e}")
        return []


async def explain_source_relevance(
    question: str,
    answer: str,
    source_dict: dict,
) -> str:
    """
    Generate a 1-sentence explanation of why a source supports the answer.
    
    Educational focus: explains WHY the source is relevant, not just WHAT it says.
    
    Args:
        question: Original user question
        answer: Generated answer text
        source_dict: Source dict with 'filename', 'page', 'excerpt', 'evidence'
        
    Returns:
        1-sentence explanation (15-25 words) or fallback if generation fails
    """
    try:
        llm = get_llm()
        
        # Use evidence if available (from semantic filtering), otherwise excerpt
        source_text = source_dict.get("evidence") or source_dict.get("excerpt", "")
        if not source_text:
            return "This source supports the answer."
        
        EXPLAIN_PROMPT = ChatPromptTemplate.from_messages([
            ("system", """You are an educational assistant explaining source relevance.

Generate ONE sentence (15–25 words) explaining:
- What part of the answer this source supports
- Why it matters for understanding

Keep it simple, specific, and student-friendly.
Return ONLY the sentence, nothing else."""),
            ("user", """Question: {question}
Answer (first 300 chars): {answer}
Source text: {source_text}

Explain:""")
        ])
        
        chain = EXPLAIN_PROMPT | llm | StrOutputParser()
        
        explanation = await chain.ainvoke({
            "question": question[:100],  # Truncate for efficiency
            "answer": answer[:300],
            "source_text": source_text[:200],
        })
        
        explanation = explanation.strip()
        
        # Validate explanation (should be a sentence)
        if not explanation or len(explanation) < 10:
            return "This source supports the answer."
        
        logger.debug(f"Generated explanation for {source_dict.get('filename')}: {explanation}")
        return explanation
        
    except Exception as e:
        logger.debug(f"Explanation generation failed: {e}")
        return "This source supports the answer."  # Safe fallback


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

    # Step 2: Retrieve with scores - CRITICAL: Check for empty results
    docs_with_scores = get_docs_with_scores(standalone_question, doc_ids)
    
    # DEFENSIVE: No relevant documents found
    if not docs_with_scores or len(docs_with_scores) == 0:
        logger.warning(
            f"No relevant documents retrieved for query: {standalone_question}"
        )
        return {
            "answer": "⚠️ I couldn't find relevant information in the uploaded documents to answer your question. Try rephrasing your query or uploading additional documents.",
            "sources": [],
            "suggestions": [],
            "confidence": "low",
            "relevance_score": 0.0,
            "source_count": 0,
            "ocr_sources": False,
            "standalone_question": standalone_question,
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
            "standalone_question": standalone_question,
        }
    
    context = format_docs(docs)

    # Step 3: Generate
    qa_chain = QA_PROMPT | llm | StrOutputParser()
    answer = await qa_chain.ainvoke({
        "question": standalone_question,
        "chat_history": lc_history,
        "context": context,
    })

    # Step 4: Calculate confidence metrics (accounting for OCR sources)
    confidence_data = calculate_confidence(scores, docs)

    # Step 5: Extract raw sources
    raw_sources = extract_sources(docs)
    
    # Step 6: Filter sources by semantic similarity to answer (for maximum relevance)
    try:
        sources = filter_sources_by_semantic_similarity(
            sources=raw_sources,
            answer_text=answer,
            docs=docs,
            top_k=3
        )
    except Exception as e:
        logger.warning(f"Semantic filtering failed, using keyword-based: {e}")
        sources = filter_and_rank_sources(raw_sources, answer, question, top_k=3)
    
    # Step 7: Enrich sources with explanations (WHY this source supports the answer)
    enriched_sources = []
    for source in sources:
        try:
            explanation = await explain_source_relevance(
                question=question,
                answer=answer,
                source_dict=source
            )
            source["explanation"] = explanation
        except Exception as e:
            logger.warning(f"Failed to generate explanation for {source.get('filename')}: {e}")
            source["explanation"] = "This source supports the answer."
        
        enriched_sources.append(source)
    
    sources = enriched_sources

    # Step 8: Generate follow-up suggestions
    suggestions = await generate_suggestions(question, answer)

    return {
        "answer": answer,
        "sources": sources,
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
    
    # Extract raw sources first
    raw_sources = extract_sources(docs)

    # Calculate confidence metrics (accounting for OCR sources)
    confidence_data = calculate_confidence(scores, docs)
    
    # For streaming, send preliminary sources based on question
    # (answer not available yet, but this provides instant feedback)
    preliminary_sources = filter_and_rank_sources(raw_sources, "", question, top_k=3)

    # Yield preliminary sources with confidence metrics
    # (UX: sources appear early while answer streams)
    sources_payload = {
        "sources": preliminary_sources,
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
    
    # NOW filter sources by answer semantic similarity (answer is complete!)
    try:
        refined_sources = filter_sources_by_semantic_similarity(
            sources=raw_sources,
            answer_text=full_answer,
            docs=docs,
            top_k=3
        )
    except Exception as e:
        logger.warning(f"Semantic filtering failed in streaming, using preliminary: {e}")
        refined_sources = preliminary_sources
    
    # Enrich refined sources with explanations (WHY this source supports the answer)
    enriched_refined_sources = []
    for source in refined_sources:
        try:
            explanation = await explain_source_relevance(
                question=question,
                answer=full_answer,
                source_dict=source
            )
            source["explanation"] = explanation
        except Exception as e:
            logger.warning(f"Failed to generate explanation for {source.get('filename')}: {e}")
            source["explanation"] = "This source supports the answer."
        
        enriched_refined_sources.append(source)
    
    refined_sources = enriched_refined_sources

    # Yield refined sources with explanations (frontend will replace preliminary ones)
    refined_payload = {
        "sources": refined_sources,
        "confidence": confidence_data["confidence"],
        "relevance_score": confidence_data["relevance_score"],
        "source_count": confidence_data["source_count"],
        "ocr_sources": confidence_data.get("ocr_sources", False),
    }
    yield f"__SOURCES_ENHANCED__{json.dumps(refined_payload)}\n"

    # Generate and yield follow-up suggestions AFTER streaming completes
    suggestions = await generate_suggestions(question, full_answer, refined_sources)
    yield f"__SUGGESTIONS__{json.dumps(suggestions)}\n"
