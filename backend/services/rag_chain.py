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
from services.vector_store import get_retriever

logger = logging.getLogger(__name__)

# ── Prompts ────────────────────────────────────────────────────────────────────

REPHRASE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Given a chat history and a follow-up question, rephrase the follow-up
question to be a standalone question that contains all necessary context.
If it is already standalone, return it unchanged.
Return ONLY the rephrased question, nothing else."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant answering questions based on PDF documents.

Use ONLY the context below to answer. If the answer is not in the context, say:
"I couldn't find information about that in the uploaded documents."

Be concise and accurate. When possible, mention the page number where you found the info.

Context from documents:
{context}
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
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


# ── Non-streaming RAG ─────────────────────────────────────────────────────────

async def run_rag_chain(
    question: str,
    chat_history: list[dict],
    doc_ids: list[str] | None = None,
) -> dict:
    llm = get_llm()
    retriever = get_retriever(doc_ids)
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

    # Step 2: Retrieve
    docs = await retriever.ainvoke(standalone_question)
    context = format_docs(docs)

    # Step 3: Generate
    qa_chain = QA_PROMPT | llm | StrOutputParser()
    answer = await qa_chain.ainvoke({
        "question": standalone_question,
        "chat_history": lc_history,
        "context": context,
    })

    return {
        "answer": answer,
        "sources": extract_sources(docs),
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
    - First: a __SOURCES__ prefixed JSON string
    - Then: answer tokens one by one
    """
    import json

    llm = get_llm()
    retriever = get_retriever(doc_ids)
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

    # Retrieve
    docs = await retriever.ainvoke(standalone_question)
    context = format_docs(docs)
    sources = extract_sources(docs)

    # Yield sources first (frontend picks this up as a special event)
    yield f"__SOURCES__{json.dumps(sources)}\n"

    # Stream answer tokens
    qa_chain = QA_PROMPT | llm | StrOutputParser()
    async for token in qa_chain.astream({
        "question": standalone_question,
        "chat_history": lc_history,
        "context": context,
    }):
        yield token
