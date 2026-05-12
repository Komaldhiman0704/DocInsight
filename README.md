# 📄 DocInsight — Advanced RAG PDF Chatbot

> **Enterprise-grade Retrieval-Augmented Generation (RAG) chatbot** for intelligent conversations with PDF, DOCX, and TXT documents.

![DocInsight](https://img.shields.io/badge/Version-1.0.0-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Python](https://img.shields.io/badge/Python-3.11+-blue) ![React](https://img.shields.io/badge/React-18.3+-blue)

## Overview

DocInsight is a full-stack, production-ready document intelligence platform that combines modern RAG techniques with a user-friendly interface. It enables organizations to unlock insights from unstructured documents through natural language conversation.

**Core Value Proposition:**
- 🚀 **Fully Free** — Groq free-tier LLM + local ChromaDB + HuggingFace embeddings
- ⚡ **Production-Ready** — Streaming responses, session management, source tracking
- 🔒 **Privacy-First** — All data stored locally, no external vector store required
- 📊 **Enterprise Features** — Document summaries, confidence scoring, multi-document queries, PDF export

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

Double-click `start.bat` (or run commands below):

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
# Runs on http://localhost:8000
```

**Frontend (new terminal):**
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

Access at: **http://localhost:5173**

---

## 📚 Documentation

- **[Architecture & API Reference](./docs/API.md)** — Endpoint documentation and system design
- **[Deployment Guide](./docs/DEPLOYMENT.md)** — Production setup (Docker, cloud platforms)
- **[Configuration](./docs/CONFIG.md)** — Environment variables and customization
- **[Troubleshooting](./docs/TROUBLESHOOTING.md)** — Common issues and solutions
- **[Development Guide](./docs/DEVELOPMENT.md)** — Local setup, testing, contributing

---

## ⚙️ Technology Stack

### Backend
| Technology | Purpose | Version |
|-----------|---------|---------|
| **FastAPI** | Web framework | 0.115+ |
| **LangChain** | RAG orchestration | 0.3.7+ |
| **ChromaDB** | Vector database | 0.5.15+ |
| **Sentence-Transformers** | Embeddings | 3.2.1+ |
| **Groq API** | LLM inference | Latest |
| **Uvicorn** | ASGI server | 0.30.6+ |

### Frontend
| Technology | Purpose | Version |
|-----------|---------|---------|
| **React** | UI library | 18.3+ |
| **Vite** | Build tool | Latest |
| **Tailwind CSS** | Styling | 3+ |
| **React PDF** | PDF rendering | 10.4+ |
| **Lucide Icons** | Icons | Latest |

---

## 🎯 Key Features Explained

### 1. **Intelligent Document Processing**
- Automatic text extraction from PDF, DOCX, TXT
- Smart chunking with overlap (configurable)
- Metadata preservation (filename, page numbers)

### 2. **Semantic Search & Retrieval**
- Hybrid search combining BM25 + semantic similarity
- Top-k retrieval with relevance scoring
- Source attribution with page context

### 3. **Streaming Responses**
- Real-time token streaming via Server-Sent Events (SSE)
- Partial response handling
- Cancellable requests

### 4. **Session Management**
- Persistent chat history (JSON-based)
- Session creation, renaming, deletion
- Multi-conversation support

### 5. **Document Intelligence**
- Auto-generated summaries per document
- Confidence scoring for answers
- Relevance indicators

---

## 📊 API Overview

All API endpoints are documented in [API.md](./docs/API.md). Quick reference:

```
POST   /api/documents/upload        — Upload documents
GET    /api/documents               — List uploaded documents
DELETE /api/documents/{doc_id}      — Delete document

POST   /api/chat/stream             — Stream chat response
GET    /api/sessions                — List chat sessions
POST   /api/sessions                — Create new session
PUT    /api/sessions/{id}           — Rename session
DELETE /api/sessions/{id}           — Delete session

GET    /api/documents/{doc_id}/summary — Get document summary
POST   /api/advanced/export-pdf     — Export session to PDF
```

---

## 🔧 Configuration & Customization

### Required Environment Variables

Create `backend/.env`:

```env
# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=mixtral-8x7b-32768  # or other Groq model

# Retrieval Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=4

# Advanced Options
ENABLE_HYBRID_SEARCH=true
CONFIDENCE_THRESHOLD=0.5
```

See [CONFIG.md](./docs/CONFIG.md) for all options.

---

## 🚀 Production Deployment

### Docker (Recommended)
```bash
docker build -f backend/Dockerfile -t docinsight-backend .
docker build -f frontend/Dockerfile -t docinsight-frontend .
docker-compose up
```

### Cloud Platforms
- **Azure Container Apps** — See [DEPLOYMENT.md](./docs/DEPLOYMENT.md)
- **AWS ECS/Fargate** — Containerized approach
- **Railway** — One-click deployment
- **Fly.io** — Global edge deployment

---

## 💾 Data Storage

- **Documents:** `backend/uploads/` (file storage)
- **Vectors:** `backend/chroma_db/` (ChromaDB index)
- **Sessions:** `backend/chat_sessions/` (JSON files)

### Backup Strategy
```bash
# Backup all persistent data
cp -r backend/uploads backend/chroma_db backend/chat_sessions ./backup/
```

---

## 📈 Performance Considerations

| Metric | Expected Value | Notes |
|--------|---|---|
| **Embedding Time** | 2-5s per document | Local HF embeddings |
| **Query Latency** | 1-3s | Includes retrieval + LLM |
| **Token Speed** | 20-50 tokens/sec | Groq streaming |
| **Max Document Size** | Tested to 100MB | Depends on RAM |
| **Concurrent Users** | 10-20 | With 8GB RAM |

---

## 🔐 Security Notes

- ✅ **Local-first architecture** — No document transmission to third parties
- ✅ **API key management** — Never commit `.env` files
- ✅ **CORS configured** — Restricted to localhost in dev
- ⚠️ **Production HTTPS** — Required for production deployment
- ⚠️ **Rate limiting** — Implement in production reverse proxy

See [Deployment Guide](./docs/DEPLOYMENT.md) for security hardening.

---

## 📝 Usage Examples

### Example 1: Upload & Query
```bash
# 1. Upload a PDF
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@myfile.pdf"

# 2. Ask a question
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main topics?",
    "session_id": "session-uuid",
    "document_ids": []
  }'
```

### Example 2: Create & Export Session
```bash
# 1. Create session
curl -X POST "http://localhost:8000/api/sessions" \
  -H "Content-Type: application/json" \
  -d '{"name": "Q&A Session"}'

# 2. Export to PDF
curl -X POST "http://localhost:8000/api/advanced/export-pdf" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-uuid"}' \
  --output session.pdf
```

---

## 🐛 Troubleshooting

Common issues? See [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) for:
- CORS errors
- Memory issues
- Slow response times
- API errors
- PDF parsing failures

---

## 🧪 Development & Testing

```bash
# Run tests
pytest backend/tests/

# Code formatting
black backend/
pylint backend/

# Frontend linting
npm run lint
```

See [DEVELOPMENT.md](./docs/DEVELOPMENT.md) for detailed setup.

---

## 📊 Project Structure

```
docinsight/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration loader
│   ├── requirements.txt         # Python dependencies
│   ├── routers/                # API route handlers
│   │   ├── chat.py            # Chat endpoint
│   │   ├── documents.py       # Document management
│   │   ├── upload.py          # File upload handler
│   │   ├── sessions.py        # Session management
│   │   └── advanced.py        # Export, summaries
│   ├── services/              # Business logic
│   │   ├── rag_chain.py       # RAG pipeline
│   │   ├── document_loader.py # Document parsing
│   │   ├── vector_store.py    # ChromaDB wrapper
│   │   ├── llm.py             # Groq integration
│   │   └── hybrid_search.py   # Search logic
│   ├── uploads/               # Document storage
│   └── chroma_db/             # Vector index
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Root component
│   │   ├── components/        # UI components
│   │   ├── hooks/             # Custom hooks
│   │   └── utils/             # Utilities
│   ├── index.html             # HTML entry
│   └── package.json           # Dependencies
├── docs/                      # Documentation
├── README.md                  # This file
└── docker-compose.yml         # Container orchestration
```

---

## 🤝 Contributing

We welcome contributions! To get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

See [DEVELOPMENT.md](./docs/DEVELOPMENT.md) for contributor guidelines.

---

## 📋 Roadmap

- [ ] **User authentication** — Multi-user support with role-based access
- [ ] **Advanced RAG** — Query expansion, re-ranking, knowledge graphs
- [ ] **Web crawler** — Ingest web content directly
- [ ] **Multi-modal** — Image and table understanding
- [ ] **Fine-tuning** — Custom model adaptation
- [ ] **Analytics dashboard** — Usage metrics and insights
- [ ] **Mobile app** — iOS/Android native support
- [ ] **Enterprise SSO** — Okta/Azure AD integration

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) file for details.

---

## 💬 Support & Community

- **Issues** — Report bugs on [GitHub Issues](../../issues)
- **Discussions** — Join community [Discussions](../../discussions)
- **Documentation** — Full docs in `/docs` folder
- **Email** — For enterprise inquiries, contact support

---

## 🙏 Acknowledgments

Built with:
- [LangChain](https://langchain.com/) — RAG orchestration
- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
- [ChromaDB](https://www.trychroma.com/) — Vector database
- [Groq](https://groq.com/) — Ultra-fast LLM inference
- [React](https://react.dev/) — Frontend library

---

**Made with ❤️ for the AI community**

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
MAX_FILE_SIZE_MB=100
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
