# 📄 DocInsight — Production-Ready PDF Chatbot

A professional, production-grade RAG (Retrieval-Augmented Generation) chatbot that enables intelligent conversations with your PDF, DOCX, and TXT documents.

Built with FastAPI + React, streaming chat responses, source citations, chat sessions, document summaries, and PDF export.

**100% Free Core Stack** — Groq free tier LLM + local ChromaDB vector store + local HuggingFace embeddings.

---

## ✨ Features

### Core Capabilities

- 📤 **Intelligent Document Upload** — Drag-and-drop support for PDF, DOCX, and TXT with validation
- 🤖 **Streaming AI Chat** — Real-time token streaming with Server-Sent Events (SSE)
- 📚 **Source Citations** — Answers include source filename and page context
- 🗂️ **Smart Document Selection** — Query selected docs or your full uploaded collection
- 💬 **Session-Based Chat History** — Create, resume, rename, and delete chat sessions
- 📝 **Document Summaries** — Auto-generated document summary cards after upload
- 📊 **Confidence Indicators** — Confidence and relevance signals for assistant answers
- 🎤 **Voice Input Support** — Ask questions with browser speech input
- 📄 **Export to PDF** — Download full chat session as a PDF report
- 🆓 **Free to Run** — Local vector DB and embeddings, free Groq option for LLM

---

## 🏗️ System Architecture

```text
┌──────────────────────────────┐
│          Browser UI          │
│      React + Vite (5173)     │
└──────────────┬───────────────┘
               │ /api (proxy)
               ▼
┌──────────────────────────────────────────────┐
│         FastAPI Backend (8000)              │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │         LangChain RAG Pipeline         │  │
│  │ 1) Load & chunk document text          │  │
│  │ 2) Generate embeddings (HF local)      │  │
│  │ 3) Store/query vectors in ChromaDB     │  │
│  │ 4) Retrieve top-k chunks               │  │
│  │ 5) Generate answer with LLM            │  │
│  │ 6) Stream tokens + sources to client   │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  Persistent Local Data                       │
│  • uploads/ (files + metadata)              │
│  • chroma_db/ (vector index)                │
│  • chat_sessions/ (session JSON files)      │
└──────────────────────────────────────────────┘
```

### Data Flow

1. **Upload** → File saved and parsed (PDF/DOCX/TXT)
2. **Chunk** → Text split with overlap (default `1000/200`)
3. **Embed** → Chunks embedded by `sentence-transformers/all-MiniLM-L6-v2`
4. **Store** → Vectors persisted in `backend/chroma_db`
5. **Query** → Top-k relevant chunks retrieved (default `k=4`)
6. **Generate** → LLM creates grounded response with context
7. **Stream** → Tokens + sources + suggestions returned to frontend

---

## 📋 System Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend tooling |
| npm | Latest recommended | Package manager |
| RAM | 4 GB min, 8 GB recommended | Embeddings/model overhead |
| Disk | 2 GB+ available | Uploads + ChromaDB + cache |
| OS | Windows/macOS/Linux | Windows scripts included |
| Groq API Key | Free account | https://console.groq.com/keys |

---

## 🚀 Quick Start (Windows)

### 1️⃣ Get a free Groq API key

1. Open: https://console.groq.com/keys
2. Create free account
3. Generate API key

### 2️⃣ Add backend environment file

Create `backend/.env` and set:

```env
GROQ_API_KEY=your_actual_key_here
```

### 3️⃣ Start the app

```bat
start.bat
```

This script:
- checks Python and Node.js
- creates virtual environment if needed
- installs backend/frontend dependencies if needed
- starts backend on `8000`
- starts frontend on `5173`

### 4️⃣ Open the app

- App UI: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Stop services with:

```bat
stop.bat
```

---

## 🖥️ Manual Setup (Step-by-Step)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GROQ_API_KEY=your_actual_key_here
```

Run backend:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: http://localhost:5173

---

## ⚙️ Environment Configuration

Create `backend/.env` with the following:

```env
# ==================== REQUIRED ====================
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

# ==================== OPTIONAL ====================
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile

# Ollama (local/offline model option)
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3

# OpenAI fallback
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-3.5-turbo

# RAG tuning
MAX_FILE_SIZE_MB=50
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=4
```

### Use Ollama for Local-Only LLM

```bash
# Install Ollama first: https://ollama.ai
ollama pull llama3
```

Then in `backend/.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
```

---

## 📁 Project Structure

```text
pdf-chatbot/
│
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Environment and app settings
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── routers/                    # API route modules
│   │   ├── upload.py               # POST /api/upload
│   │   ├── chat.py                 # /api/chat, /api/chat/stream, export
│   │   ├── documents.py            # list/get/delete docs + summary/pdf
│   │   └── sessions.py             # chat session CRUD
│   │
│   ├── services/                   # Core business and RAG logic
│   │   ├── rag_chain.py            # retrieval + generation orchestration
│   │   ├── vector_store.py         # embeddings + Chroma operations
│   │   ├── llm.py                  # LLM provider factory
│   │   ├── document_loader.py      # PDF/DOCX/TXT extraction
│   │   ├── document_store.py       # documents metadata store
│   │   ├── chat_store.py           # session history JSON store
│   │   ├── summarizer.py           # async document summaries
│   │   └── pdf_exporter.py         # chat PDF export
│   │
│   ├── uploads/                    # Uploaded files + documents.json
│   ├── chroma_db/                  # Persistent vector index
│   └── chat_sessions/              # Session JSON files
│
├── frontend/
│   ├── index.html                  # HTML root
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.js              # Dev server + API proxy
│   └── src/
│       ├── App.jsx                 # Main state and app orchestration
│       ├── main.jsx                # React bootstrap
│       ├── components/             # UI components
│       ├── hooks/                  # Custom hooks (theme/voice)
│       ├── utils/api.js            # API client and SSE handling
│       └── styles/globals.css      # Global styles
│
├── start.bat                       # Start both backend + frontend (Windows)
├── stop.bat                        # Stop running services (Windows)
└── test_integration.py             # Integration validation script
```

---

## 🎨 Technology Stack

### Backend

| Layer | Technology | Purpose |
|------|------------|---------|
| API Framework | FastAPI | Async web API server |
| ASGI Server | Uvicorn | Runtime server for FastAPI |
| RAG Orchestration | LangChain | Prompting, retrieval, generation flow |
| Vector Storage | ChromaDB | Local persistent vector database |
| Embeddings | Sentence Transformers | Convert text to vectors locally |
| Document Parsing | pypdf, python-docx | Read PDF and DOCX content |
| Streaming | SSE | Real-time token stream to frontend |

### Frontend

| Layer | Technology | Purpose |
|------|------------|---------|
| UI Framework | React 18 | Component-based interface |
| Build Tool | Vite 5 | Fast local development/build |
| Styling | Tailwind CSS | Utility-first styling |
| Animation/UI | Framer Motion + Lucide | Motion and icon system |
| PDF Viewer | react-pdf | Inline PDF rendering |
| API Client | Fetch + custom SSE parser | Backend communication |

---

## 📖 How It Works

### Document Upload Pipeline

1. User uploads file from UI
2. Backend validates size/type
3. Text extracted and split into chunks
4. Chunks embedded locally
5. Embeddings + metadata stored in ChromaDB
6. Document appears in sidebar for querying

### Chat Pipeline

1. User asks question (typed or voice)
2. Chat history is included for context
3. Query may be rephrased for better retrieval
4. Top relevant chunks are retrieved
5. LLM generates contextual answer
6. Tokens stream to frontend in real-time
7. Sources, confidence, and follow-up suggestions are attached
8. Session is persisted as JSON

---

## 🔌 API Overview

Base URL: `http://localhost:8000`

### System
- `GET /` — status
- `GET /health` — health and config snapshot
- `GET /docs` — Swagger docs

### Upload
- `POST /api/upload` — upload and ingest document

### Chat
- `POST /api/chat` — non-streaming response
- `POST /api/chat/stream` — SSE streaming response
- `POST /api/chat/export?session_id=...` — export session as PDF

### Documents
- `GET /api/documents` — list documents
- `GET /api/documents/{doc_id}/summary` — document summary
- `GET /api/documents/{doc_id}/pdf` — PDF endpoint for viewer
- `DELETE /api/documents/{doc_id}` — delete document

### Sessions
- `GET /api/sessions` — list sessions
- `POST /api/sessions` — create session
- `GET /api/sessions/{session_id}` — get session detail
- `PATCH /api/sessions/{session_id}` — rename session
- `DELETE /api/sessions/{session_id}` — delete session

---

## 🎓 Frequently Asked Questions

**Q: Why is first upload/query slower?**
A: The embeddings model and vector store warm-up happen on first run. Later requests are faster.

**Q: Can I run without internet?**
A: Yes, use Ollama as `LLM_PROVIDER` for local inference.

**Q: Is my data private?**
A: Documents and embeddings are stored locally. If using Groq/OpenAI, prompts go to their APIs.

**Q: Where is chat history stored?**
A: In `backend/chat_sessions/` as JSON files.

**Q: How to reset all data?**
A: Stop app, then clear `backend/uploads`, `backend/chroma_db`, and `backend/chat_sessions`.

---

## 🐛 Common Issues & Fixes

| Issue | Fix |
|------|-----|
| `GROQ_API_KEY not set` | Add key in `backend/.env` |
| Backend import errors | Activate venv and reinstall: `pip install -r requirements.txt` |
| `npm` not found | Install Node.js from https://nodejs.org |
| Port conflict on 8000/5173 | Stop existing process or update ports in backend/frontend config |
| Upload fails | Check file type/size and ensure `backend/uploads` is writable |
| Empty answers | Confirm docs are uploaded and selected in UI |

---

## 🚀 Performance Tips

- Use smaller/faster LLM model if latency matters
- Tune `CHUNK_SIZE`, `CHUNK_OVERLAP`, and `TOP_K_RESULTS` based on document size
- Keep backend and frontend on same region/machine for low latency

---

## 📜 License

This project currently has no explicit LICENSE file in the repository.
If you want open-source reuse, add an MIT license file.

---

## 🤝 Contributing

Contributions are welcome. Good areas to improve:

- Authentication and multi-user support
- Additional file formats (XLSX, PPTX, HTML)
- Better retrieval strategies and reranking
- Advanced evaluation and analytics
- Cloud deployment templates

---

## 📞 Support

- Groq docs: https://console.groq.com/docs
- FastAPI docs: https://fastapi.tiangolo.com/
- React docs: https://react.dev/

---

Last Updated: April 2026
