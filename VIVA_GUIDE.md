# 🎓 Viva Preparation Guide — AI PDF Chatbot

A complete guide to confidently answering every question your examiner will ask.

---

## 🔑 30-Second Project Summary (say this when asked "what is your project?")

> "I built an AI-powered PDF chatbot using Retrieval-Augmented Generation. Users upload PDF documents — textbooks, research papers, reports — and the system answers their questions with exact page citations. It uses LangChain for orchestration, ChromaDB as a local vector database, HuggingFace sentence transformers for free embeddings, and Groq's free Llama3 API for generating responses. The entire system runs locally with no paid subscriptions required."

---

## 📊 Architecture Diagram (draw this on whiteboard)

```
┌─────────────────────────────────────────────────────────┐
│                    USER BROWSER                         │
│           React Frontend (Vite, port 5173)              │
└─────────────────────────┬───────────────────────────────┘
                          │  REST API / SSE Streaming
                          ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (port 8000)                 │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Upload Router│  │ Chat Router  │  │ Docs Router  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  │
│         │                  │                             │
│         ▼                  ▼                             │
│  ┌──────────────┐  ┌──────────────────────────────────┐ │
│  │  PDF Loader  │  │        RAG Chain (LangChain)      │ │
│  │  + Splitter  │  │  1. Rephrase question             │ │
│  └──────┬───────┘  │  2. Retrieve top-k chunks         │ │
│         │          │  3. Generate answer               │ │
│         ▼          └────────────┬─────────────────────┘ │
│  ┌──────────────┐               │                        │
│  │  HuggingFace │◄──────────────┤                        │
│  │  Embeddings  │               │                        │
│  │ (local, free)│               ▼                        │
│  └──────┬───────┘  ┌────────────────────┐               │
│         │          │  Groq API (free)   │               │
│         ▼          │  Llama3-8b-8192    │               │
│  ┌──────────────┐  └────────────────────┘               │
│  │  ChromaDB    │                                        │
│  │ (local disk) │                                        │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

---

## ❓ Expected Viva Questions & Model Answers

### BASICS

**Q: What is RAG?**
> RAG stands for Retrieval-Augmented Generation. It's a technique that enhances an LLM's responses by first retrieving relevant context from a document store, then feeding that context to the language model to generate grounded answers. This prevents hallucination because the model answers from actual document content rather than from memory alone.

**Q: Why use RAG instead of fine-tuning?**
> Fine-tuning requires thousands of examples, significant compute, and retraining whenever documents change. RAG is far more practical — you can add, remove, or update documents in seconds, it's cheaper, and it naturally cites its sources. For a document Q&A use case, RAG is almost always the right choice.

**Q: What is an embedding / vector?**
> An embedding is a numerical representation of text as a list of floating-point numbers (a vector). Semantically similar pieces of text produce similar vectors. For example, "machine learning algorithms" and "ML methods" would have vectors close together in vector space. This lets us find relevant document chunks by comparing vector similarity rather than exact keyword matching.

**Q: What is a vector database?**
> A vector database stores these embeddings and supports efficient similarity search — finding the most similar vectors to a query vector. I used ChromaDB, which runs entirely on local disk. It's much faster than doing brute-force cosine similarity over all chunks.

---

### TECHNICAL DEPTH

**Q: Explain your chunking strategy.**
> I used `RecursiveCharacterTextSplitter` from LangChain with a chunk size of 1000 characters and 200-character overlap. The recursive strategy tries to split on natural boundaries — paragraphs first, then sentences, then words — preserving semantic coherence. The overlap ensures that context at chunk boundaries isn't lost.

**Q: How does question rephrasing work?**
> If a user asks a follow-up like "What did it say about that?", the model has no idea what "that" refers to without the conversation history. My system first sends the current question and the last 6 messages to an LLM prompt that rewrites it as a standalone question — e.g. "What does the document say about gradient descent?" — then uses that rephrased question for retrieval.

**Q: What embedding model did you use and why?**
> I used `sentence-transformers/all-MiniLM-L6-v2` from HuggingFace. It's a 22MB model that runs efficiently on CPU, produces 384-dimensional embeddings, and is well-benchmarked for semantic similarity tasks. Crucially, it's free and runs locally — no API key required. For a production system with more budget, `text-embedding-3-small` from OpenAI would give better quality.

**Q: How does streaming work?**
> The frontend connects to `/api/chat/stream` which returns `text/event-stream` (Server-Sent Events). As the LLM generates each token, the backend yields it immediately using Python's `async generator`. The frontend's `EventSource`/`fetch` reader processes each chunk and appends it to the message bubble in real-time — this is why the text appears word-by-word like ChatGPT.

**Q: How do you filter answers to specific documents?**
> Each chunk stored in ChromaDB has a metadata field `doc_id`. When the user selects specific documents in the UI, their IDs are sent with the chat request. ChromaDB's retrieval query includes a `filter={"doc_id": {"$in": [selected_ids]}}` parameter, restricting similarity search to only those documents' chunks.

**Q: What is LangGraph and did you use it?**
> LangGraph is a framework for building stateful, multi-step agent workflows with cycles and conditional branches. In this project I used LangChain's sequential chain (LCEL — LangChain Expression Language) rather than full LangGraph, since the RAG pipeline is linear: rephrase → retrieve → generate. LangGraph would be appropriate for more complex agentic flows like self-correcting RAG or multi-hop reasoning.

---

### DESIGN DECISIONS

**Q: Why ChromaDB and not Pinecone or Supabase?**
> ChromaDB runs entirely locally with zero configuration — no account, no API key, no network dependency, no cost. For a student project or any privacy-sensitive application, this is far preferable. Pinecone and Supabase are excellent for production systems that need cloud-scale, but they're unnecessary complexity for this use case.

**Q: Why Groq and not OpenAI?**
> Groq provides a genuinely free API tier (10 million tokens/month) with extremely fast inference (typically 500+ tokens/second) thanks to their custom LPU hardware. OpenAI's API requires a credit card and charges per token. For a student project, Groq running Llama3 gives comparable quality at zero cost.

**Q: Why FastAPI and not Flask or Django?**
> FastAPI provides automatic OpenAPI documentation, native async support (critical for streaming), built-in Pydantic data validation, and is significantly faster than Flask. Django would be overkill for an API-only service. FastAPI is the modern standard for Python APIs.

**Q: Why React + Vite and not Next.js?**
> Vite is simpler to set up and doesn't require server-side rendering infrastructure. For a frontend-only SPA that talks to a separate backend, Vite is faster to develop with and easier to deploy. Next.js would be appropriate if I wanted server-side rendering or a unified full-stack framework.

---

### LIMITATIONS & IMPROVEMENTS

**Q: What are the limitations of your system?**
> 1. **Storage is ephemeral** — ChromaDB data is on local disk, so deploying to cloud requires persistent storage
> 2. **No authentication** — any user can access any document; a production system needs user accounts
> 3. **PDF quality dependency** — scanned PDFs without OCR won't be parsed correctly
> 4. **Context window limit** — very long documents may require better chunking strategies
> 5. **No evaluation metrics** — I don't automatically measure answer quality

**Q: What would you add if you had more time?**
> 1. Answer quality evaluation using RAGAS (RAG Assessment framework)
> 2. OCR support for scanned PDFs using Tesseract
> 3. User authentication with JWT tokens
> 4. Support for more file types — Word, Excel, PowerPoint
> 5. A feedback mechanism so users can rate answers (thumbs up/down)
> 6. Hybrid search combining vector similarity + BM25 keyword search for better retrieval

**Q: How would you scale this to production?**
> Replace ChromaDB with Pinecone or Weaviate for distributed vector search, add Redis for session/cache management, use a message queue (Celery + Redis) for PDF ingestion jobs, containerize with Docker, deploy backend on AWS/GCP with auto-scaling, and use a CDN for the frontend. I'd also add proper logging, monitoring (Prometheus/Grafana), and CI/CD pipelines.

---

## 🧮 Key Numbers to Remember

| Metric | Value |
|--------|-------|
| Chunk size | 1000 characters |
| Chunk overlap | 200 characters |
| Top-K retrieved chunks | 4 |
| Embedding dimensions | 384 (MiniLM-L6-v2) |
| Embedding model size | ~22 MB |
| LLM (Groq free tier) | Llama3-8b-8192 |
| Groq free token limit | 10M tokens/month |
| Max history messages | 6 (3 turns) |
| Max file size | 50 MB |

---

## 💡 Quick Tips for Demo Day

1. **Pre-upload your PDFs** before the demo — first upload triggers embedding model download
2. **Use a textbook or paper you know well** so you can verify the AI's answers are correct
3. **Show the source citations** — expand the source panel to show it found the right page
4. **Try a follow-up question** like "Can you elaborate on point 2?" to demonstrate chat history
5. **Toggle dark mode** — shows UI polish
6. **Try voice input** in Chrome — impressive feature

---

## 📖 Terminology Cheat Sheet

| Term | One-line definition |
|------|---------------------|
| RAG | Retrieval-Augmented Generation — combining retrieval + LLM generation |
| Embedding | A numerical vector representing the meaning of text |
| Vector DB | Database optimised for storing and searching vector embeddings |
| Chunk | A small piece of a document (e.g. 1000 characters) |
| Top-K | Retrieving the K most similar chunks to a query |
| SSE | Server-Sent Events — server pushes data to browser in real-time |
| LCEL | LangChain Expression Language — pipe-based chain composition |
| LLM | Large Language Model (e.g. Llama3, GPT-4) |
| Cosine similarity | Measure of angle between two vectors — used to find similar chunks |
| Semantic search | Finding text by meaning rather than exact keywords |
