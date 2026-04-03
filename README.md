# 📄 AI PDF Chatbot — Full Stack (Free)

A production-ready RAG chatbot that lets you chat with your PDF documents using AI.  
**100% free stack** — no paid APIs required (uses Groq's free tier + local ChromaDB + HuggingFace embeddings).

---

## ✨ Features

- 📤 **Multi-PDF Upload** — drag & drop multiple PDFs at once
- 🤖 **AI Chat** — streaming answers powered by Llama3 via Groq (free)
- 📚 **Source Citations** — every answer shows which page it came from
- 🗂️ **Document Selection** — choose which PDFs to query
- 💬 **Chat History** — context-aware follow-up questions
- 🌙 **Dark Mode** — toggle dark/light theme
- 🎤 **Voice Input** — speak your questions (Chrome/Edge)
- 🆓 **Fully Free** — Groq API + ChromaDB + HuggingFace = $0/month

---

## 🏗️ Architecture

```
User Browser
     │
     ▼
React Frontend (Vite, port 5173)
     │  HTTP/SSE
     ▼
FastAPI Backend (port 8000)
     ├── LangChain RAG Chain
     │        ├── HuggingFace Embeddings (local CPU)
     │        ├── ChromaDB (local vector DB)
     │        └── Groq LLM (free API → Llama3)
     └── File Storage (./uploads/)
```

**RAG Flow:**
1. PDF uploaded → split into 1000-char chunks
2. Chunks embedded with `sentence-transformers/all-MiniLM-L6-v2` (runs locally)
3. Embeddings stored in ChromaDB (local folder)
4. User asks question → question rephrased with history → top 4 chunks retrieved
5. LLM generates answer from chunks → streamed token by token to browser

---

## 📋 Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| Groq API key | Free | https://console.groq.com/keys |

---

## 🚀 Windows Quick Start

### Step 1 — Get Free Groq API Key
1. Go to https://console.groq.com/keys
2. Sign up (free, no credit card)
3. Create a new API key → copy it

### Step 2 — Install & Run

```bat
REM 1. Clone or download this project
cd pdf-chatbot

REM 2. Run setup (installs all dependencies)
setup.bat

REM 3. Add your Groq key to backend\.env
REM    Open backend\.env and replace:
REM    GROQ_API_KEY=your_groq_api_key_here
REM    with your actual key

REM 4. Start both servers
start.bat
```

### Step 3 — Open App
Visit **http://localhost:5173** in your browser.

---

## 🖥️ Manual Setup (Step by Step)

### Backend

```bash
cd backend

# Create Python virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Edit .env - add your GROQ_API_KEY
notepad .env

# Start backend
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install Node dependencies
npm install

# Start dev server
npm run dev
```

---

## 🔧 Configuration

Edit `backend/.env`:

```env
# Required: Get free key at https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# LLM model (free options on Groq)
GROQ_MODEL=llama3-8b-8192        # Fast, good quality
# GROQ_MODEL=mixtral-8x7b-32768  # Better reasoning
# GROQ_MODEL=llama3-70b-8192     # Best quality (slower)
```

### Use Ollama Instead (Fully Offline)

If you want zero internet dependency:

```bash
# Install Ollama from https://ollama.ai
# Then pull a model:
ollama pull llama3

# Edit backend/.env:
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
```

---

## 📁 Project Structure

```
pdf-chatbot/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings from .env
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Your API keys (never commit!)
│   ├── routers/
│   │   ├── upload.py            # POST /api/upload
│   │   ├── chat.py              # POST /api/chat/stream
│   │   └── documents.py         # GET/DELETE /api/documents
│   └── services/
│       ├── vector_store.py      # ChromaDB + HuggingFace embeddings
│       ├── llm.py               # LLM provider switcher
│       ├── rag_chain.py         # LangChain RAG pipeline
│       └── document_store.py    # PDF metadata (JSON file)
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx              # Main layout + state
│       ├── main.jsx             # React entry point
│       ├── components/
│       │   ├── ChatMessage.jsx  # Message bubble
│       │   ├── ChatInput.jsx    # Input bar + voice
│       │   ├── UploadZone.jsx   # Drag & drop upload
│       │   ├── DocumentList.jsx # Sidebar document list
│       │   └── SourceCard.jsx   # PDF source citations
│       ├── hooks/
│       │   ├── useDarkMode.js   # Dark/light mode
│       │   └── useVoiceInput.js # Web Speech API
│       ├── utils/
│       │   └── api.js           # All backend API calls
│       └── styles/
│           └── globals.css      # Tailwind + custom CSS
│
├── uploads/                     # Uploaded PDFs stored here
├── chroma_db/                   # Vector embeddings stored here
├── setup.bat                    # One-click Windows setup
└── start.bat                    # Launch both servers
```

---

## 🎓 How to Explain in Viva

### "What does this project do?"
> "It's an AI chatbot that reads PDF documents and answers questions about them. You upload any PDF — a textbook, research paper, or report — and the system breaks it into chunks, creates vector embeddings, and uses a large language model to answer questions with exact page references."

### "What is RAG?"
> "RAG stands for Retrieval-Augmented Generation. Instead of the AI answering from memory, it first retrieves the most relevant passages from your documents, then generates an answer grounded in that content. This makes answers accurate and traceable."

### "What technologies did you use?"
> - **FastAPI** — Python web framework for the REST API
> - **LangChain** — orchestrates the RAG pipeline
> - **ChromaDB** — local vector database that stores embeddings
> - **HuggingFace Sentence Transformers** — converts text to vectors (runs locally, free)
> - **Groq + Llama3** — free LLM API for generating answers
> - **React + Vite** — modern frontend
> - **Server-Sent Events** — for streaming token-by-token responses

### "Why did you choose ChromaDB over Pinecone/Supabase?"
> "ChromaDB runs entirely locally — no cloud account, no cost, no data leaving the machine. For a student project and privacy-sensitive documents, this is the better choice."

### "What improvements could you make?"
> - Add user authentication
> - Support more file types (Word, Excel)
> - Add answer quality evaluation metrics
> - Deploy to cloud (Render + Vercel — both have free tiers)

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `GROQ_API_KEY not set` | Edit `backend/.env`, add your Groq key |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in the `backend` folder with venv activated |
| `npm: command not found` | Install Node.js from https://nodejs.org |
| Port 8000 in use | Change `--port 8001` in start.bat and update `vite.config.js` proxy |
| First upload is slow | HuggingFace model downloads ~90MB on first run, cached after that |
| ChromaDB error on Windows | Run `pip install chromadb --upgrade` |

---

## 📜 License
MIT — free to use, modify, and present as your own project.
