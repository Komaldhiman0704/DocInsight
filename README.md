# 📄 DocInsight — Production-Ready PDF Chatbot

A **professional, production-grade RAG (Retrieval-Augmented Generation) chatbot** that enables you to have intelligent conversations with your PDF documents. Built with modern web technologies, real-time streaming, and a polished user interface.

**100% Free Stack** — Groq free tier LLM + Local ChromaDB vector database + HuggingFace embeddings. Deploy locally or to cloud with zero licensing costs.

---

## ✨ Features

### Core Capabilities
- 📤 **Intelligent Document Upload** — Drag-and-drop interface for PDFs, DOCX, and TXT files with validation
- 🤖 **Streaming AI Chat** — Real-time token-by-token responses powered by Llama3 via Groq (free tier)
- 📚 **Precise Source Citations** — Every answer includes page numbers and context from source documents
- 🗂️ **Smart Document Selection** — Query specific documents or search across your entire collection
- 💬 **Context-Aware Chat History** — Follow-up questions automatically include conversation context
- ✨ **Professional UI/UX** — Custom-designed logo, dark/light mode, polished animations, and responsive design
- 🎤 **Voice Input Support** — Speak your questions (Chrome/Edge browsers)
- 📊 **Confidence Indicators** — AI confidence scores help you evaluate answer reliability
- 🆓 **100% Free Deployment** — No API fees, database costs, or licensing required

---

## 🏗️ System Architecture

```
┌─────────────────────┐
│   User Browser      │
│  (React + Vite)     │
└──────────┬──────────┘
           │ HTTP/SSE (Port 5173)
           ▼
┌──────────────────────────────────┐
│   FastAPI Backend (Port 8000)    │
│  ┌────────────────────────────┐  │
│  │   LangChain RAG Pipeline   │  │
│  │  ┌──────────────────────┐  │  │
│  │  │ Document Processing  │  │  │
│  │  │ & Chunking (1000ch)  │  │  │
│  │  └──────────────────────┘  │  │
│  │  ┌──────────────────────┐  │  │
│  │  │ Embedding Generation │  │  │
│  │  │ (HuggingFace local)  │  │  │
│  │  └──────────────────────┘  │  │
│  │  ┌──────────────────────┐  │  │
│  │  │ Vector Retrieval     │  │  │
│  │  │ (ChromaDB)           │  │  │
│  │  └──────────────────────┘  │  │
│  │  ┌──────────────────────┐  │  │
│  │  │ LLM Response Gen     │  │  │
│  │  │ (Groq Free API)      │  │  │
│  │  └──────────────────────┘  │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │  Persistent Storage        │  │
│  │  • ChromaDB (vectors)      │  │
│  │  • Session JSON (history)  │  │
│  │  • Document uploads        │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### Data Flow
1. **Upload** → Documents chunked (1000 chars) with overlap
2. **Embed** → Chunks embedded locally with `sentence-transformers/all-MiniLM-L6-v2`
3. **Store** → Embeddings persisted in ChromaDB (./chroma_db/)
4. **Query** → Question re-ranked with conversation history, top-4 chunks retrieved
5. **Generate** → LLM synthesizes answer with citations → streamed to frontend
6. **Display** → Real-time UI updates with confidence scores and follow-up suggestions

---

## 📋 System Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Python** | 3.11+ | Backend runtime, virtual environment recommended |
| **Node.js** | 18+ | Frontend build tooling (npm) |
| **RAM** | 4GB min, 8GB+ rec | Embeddings model runs locally |
| **Disk** | 2GB+ available | ChromaDB + uploads + models cache |
| **OS** | Windows 10+, macOS, Linux | Tested on Windows 10/11 |
| **Groq API Key** | Free account | Get from https://console.groq.com/keys |

---

## 🚀 Quick Start (Windows)

### 1️⃣ Get Your Free Groq API Key
```
1. Visit: https://console.groq.com/keys
2. Create account (free, no credit card required)
3. Generate API key and copy to clipboard
```

### 2️⃣ Clone & Setup Project
```batch
REM Clone repository
git clone https://github.com/Komaldhiman0704/pdf-chatbot.git
cd pdf-chatbot

REM Create .env file in backend folder with your Groq key
REM backend\.env contents:
REM   GROQ_API_KEY=your_actual_api_key_here
```

### 3️⃣ Start the Application
```batch
REM One-command startup (installs dependencies automatically)
start.bat

REM This will:
REM   • Check Python & Node.js installation
REM   • Create Python virtual environment (if needed)
REM   • Install all dependencies (pip + npm)
REM   • Start backend (port 8000)
REM   • Start frontend dev server (port 5173)
```

### 4️⃣ Access the Application
Open your browser to: **http://localhost:5173**

---

## 🖥️ Manual Setup (Step-by-Step)

### Backend Setup

```bash
cd backend

# Create Python virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create and configure .env file
# Add: GROQ_API_KEY=your_actual_api_key_here
```

Edit `backend/.env` with your Groq API key.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Running Both Services Manually

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# Opens http://localhost:5173
```

---

## ⚙️ Environment Configuration

### Backend `.env` File

Create `backend/.env` with your settings:

```env
# ==================== REQUIRED ====================
# Get free API key from https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx

# ==================== OPTIONAL ====================
# Model selection (default: llama3-8b-8192)
# GROQ_MODEL=llama3-8b-8192        # Recommended: Fast + good quality
# GROQ_MODEL=mixtral-8x7b-32768    # Better reasoning
# GROQ_MODEL=llama3-70b-8192       # Best quality (slower)

# Alternative: Run Ollama locally (no internet needed)
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=llama3
```

### Use Ollama for Fully Offline Operation

To run completely offline without internet:

```bash
# 1. Install Ollama from https://ollama.ai
# 2. Pull a model
ollama pull llama3

# 3. Update backend/.env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3

# 4. Ollama server runs on http://localhost:11434
```

---

## 📁 Project Structure

```
pdf-chatbot/
│
├── 📂 backend/                     # FastAPI application
│   ├── main.py                     # Application entry point
│   ├── config.py                   # Settings & environment loading
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # API keys (ignored in git)
│   │
│   ├── 📂 routers/                 # API endpoints
│   │   ├── chat.py                 # POST /api/chat/stream (streaming)
│   │   ├── upload.py               # POST /api/upload (file handling)
│   │   ├── documents.py            # GET/DELETE /api/documents
│   │   └── sessions.py             # GET /api/sessions (history)
│   │
│   ├── 📂 services/                # Business logic
│   │   ├── rag_chain.py            # LangChain RAG orchestration
│   │   ├── vector_store.py         # ChromaDB + embeddings
│   │   ├── llm.py                  # LLM provider abstraction
│   │   ├── document_store.py       # Document persistence
│   │   ├── chat_store.py           # Session & message storage
│   │   ├── summarizer.py           # Document summarization
│   │   └── pdf_exporter.py         # Export capabilities
│   │
│   ├── 📂 uploads/                 # User uploaded documents
│   └── 📂 chroma_db/               # Vector embeddings (persistent)
│
├── 📂 frontend/                    # React + Vite application
│   ├── index.html                  # HTML entry point
│   ├── package.json                # npm dependencies
│   ├── vite.config.js              # Vite configuration + API proxy
│   ├── tailwind.config.js          # Custom animations & utilities
│   ├── postcss.config.js           # PostCSS setup
│   │
│   └── 📂 src/
│       ├── main.jsx                # React initialization
│       ├── App.jsx                 # Main layout & state management
│       │
│       ├── 📂 components/          # Reusable React components
│       │   ├── Logo.jsx            # Custom brand logo
│       │   ├── ChatMessage.jsx     # Message display with streaming
│       │   ├── ChatInput.jsx       # Input field + voice support
│       │   ├── UploadZone.jsx      # Drag-drop file upload
│       │   ├── DocumentList.jsx    # Sidebar document navigator
│       │   ├── DocumentSummaryCard.jsx  # Document preview
│       │   ├── SourceCard.jsx      # Citation with page numbers
│       │   ├── SessionList.jsx     # Chat history panel
│       │   ├── ConfidenceIndicator.jsx  # Answer confidence
│       │   ├── SuggestionsRow.jsx  # Follow-up question suggestions
│       │   └── PDFViewer.jsx       # PDF preview (if available)
│       │
│       ├── 📂 hooks/               # Custom React hooks
│       │   ├── useDarkMode.js      # Dark/light theme toggle
│       │   └── useVoiceInput.js    # Web Speech API integration
│       │
│       ├── 📂 utils/               # Utility functions
│       │   └── api.js              # API client & endpoints
│       │
│       └── 📂 styles/
│           └── globals.css         # Tailwind + custom CSS variables
│
├── start.bat                       # Windows startup script (all-in-one)
├── stop.bat                        # Service shutdown script
└── README.md                       # This file
```

---

## 🎨 Technology Stack

### Backend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI | High-performance Python web framework with async support |
| **LLM Orchestration** | LangChain | RAG pipeline, prompt management, and chain composition |
| **Vector Storage** | ChromaDB | Local vector database for embeddings (no setup needed) |
| **Embeddings** | Sentence Transformers | Text-to-vector conversion (runs locally, ~90MB download) |
| **LLM Provider** | Groq API | Free inference tier with Llama3, Mixtral models |
| **Document Processing** | PyPDF, python-docx | PDF and DOCX parsing |
| **Streaming** | Server-Sent Events | Token-by-token response streaming to frontend |

### Frontend
| Layer | Technology | Purpose |
|--------|-----------|---------|
| **Framework** | React 18 | Modern UI component library |
| **Build Tool** | Vite | Next-generation fast module bundler |
| **Styling** | Tailwind CSS 3 | Utility-first CSS framework |
| **Components** | Lucide React | Consistent icon library |
| **State** | React Hooks | useState, useEffect, useContext |
| **API Client** | Fetch API | Browser native HTTP client |
| **Voice** | Web Speech API | Browser speech-to-text recognition |
| **Theme** | CSS Variables | Dark/light mode implementation |

---

## 📖 How It Works

### Document Upload Flow
1. User drags PDF/DOCX/TXT file into upload zone
2. Frontend sends to `POST /api/upload`
3. Backend extracts text, splits into 1000-character chunks (with overlap)
4. Each chunk embedded using HuggingFace sentence transformer
5. Embeddings stored in ChromaDB with metadata (filename, page #)
6. Document added to sidebar, ready for queries

### Chat Flow
1. User types question and presses Send (or uses voice input)
2. Message added to session history
3. Last 5 messages sent to backend for context
4. Backend uses LangChain to:
   - Rephrase question with conversation context
   - Search ChromaDB for 4 most-similar chunks
   - Combine chunks as context window
   - Send to Groq LLM with system prompt
5. LLM streams response token-by-token via SSE
6. Frontend displays tokens in real-time as they arrive
7. Answer includes confidence score and source citations
8. Follow-up suggestions generated and displayed

---

## 🎓 Frequently Asked Questions

### Q: Why is the first upload slow?
**A:** The HuggingFace embedding model (~90MB) downloads on first use. This is cached locally, so subsequent uploads are fast.

### Q: Can I use this offline?
**A:** Yes! Install Ollama and configure it in `.env`. The entire stack then runs locally with zero internet.

### Q: How do I deploy this?
**A:** 
- **Backend:** Deploy FastAPI to Render, Railway, or Azure Container Apps (free tier available)
- **Frontend:** Deploy React build to Vercel, Netlify, or GitHub Pages (free)
- **Database:** ChromaDB data persists in deployed container

### Q: Is my data private?
**A:** With Groq, embeddings are calculated locally. Only the question text is sent to Groq's inference API. With Ollama, nothing leaves your machine.

### Q: Can I add more documents to an existing session?
**A:** Yes! Upload new documents anytime. They're added to the vector database and included in searches.

---

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY not found` | Create `backend/.env` with your Groq API key from console.groq.com |
| `ModuleNotFoundError: chromadb` | Activate venv: `venv\Scripts\activate` then `pip install -r requirements.txt` |
| `npm: command not found` | Install Node.js from https://nodejs.org (includes npm) |
| Port 8000 already in use | Edit `start.bat`: change `--port 8000` to `--port 8001`, update frontend proxy in `vite.config.js` |
| First embedding is slow | This is normal! ~30s for first document as model downloads. Subsequent are <5s |
| `Connection refused localhost:8000` | Ensure backend started: check terminal running `uvicorn` |
| Files not uploading | Check `backend/uploads/` folder exists and is writable |
| ChromaDB corrupted | Delete `backend/chroma_db/` folder, app recreates it on restart |

---

## 🚀 Performance Optimization

### For Large Documents
```python
# backend/services/rag_chain.py
CHUNK_SIZE = 1500          # Increase from 1000 for better context
CHUNK_OVERLAP = 200        # Reduce from 300 for speed vs accuracy tradeoff
RETRIEVAL_K = 6            # Get more context chunks (default: 4)
```

### Faster Responses
- Use `llama3-8b-8192` model (fastest on Groq free tier)
- Deploy backend geographically close to users
- Cache frequently asked questions

---

## 📜 License

This project is released under the **MIT License** — free to use, modify, and redistribute.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- [ ] User authentication & multi-user support
- [ ] Support for more file formats (Excel, PowerPoint, HTML)
- [ ] PDF page number extraction in citations
- [ ] Streaming document processing for very large files
- [ ] Local model quantization for faster inference
- [ ] Advanced analytics and usage metrics

---

## 📞 Support

- **Issues:** Found a bug? Open a GitHub issue with reproduction steps
- **Groq API Help:** https://console.groq.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/

---

**Made with ❤️ by the DocInsight team**

*Last Updated: April 2026 | Production Ready*
