# Configuration Guide

Complete reference for DocInsight configuration options.

---

## Environment Variables

### Backend Configuration

Create `backend/.env`:

```env
# ============================================
# LLM Configuration
# ============================================
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=mixtral-8x7b-32768

# Alternative models:
# - mixtral-8x7b-32768 (fastest, recommended)
# - llama2-70b-4096
# - neural-chat-7b-v3-1
# - gemma-7b-it

# ============================================
# Retrieval Configuration
# ============================================
CHUNK_SIZE=1000              # Size of document chunks
CHUNK_OVERLAP=200            # Overlap between chunks
RETRIEVAL_K=4                # Number of chunks to retrieve
ENABLE_HYBRID_SEARCH=true    # Enable BM25 + semantic search

# ============================================
# Model Configuration
# ============================================
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32      # Batch size for embedding
MAX_SEQUENCE_LENGTH=512      # Max tokens per embedding

# ============================================
# Generation Configuration
# ============================================
TEMPERATURE=0.7              # LLM creativity (0.0-2.0)
TOP_P=0.9                    # Nucleus sampling parameter
MAX_TOKENS=1000              # Max tokens per response
CONFIDENCE_THRESHOLD=0.5     # Min confidence for sources

# ============================================
# Server Configuration
# ============================================
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR

# ============================================
# Storage Configuration
# ============================================
UPLOADS_DIR=./uploads        # Document storage
CHROMA_DB_DIR=./chroma_db    # Vector store
SESSIONS_DIR=./chat_sessions # Session storage
MAX_UPLOAD_SIZE=104857600    # Max file size (100MB)

# ============================================
# Advanced Options
# ============================================
API_KEY_ENABLED=false        # Enable API key authentication
API_KEY=your-secret-api-key  # If enabled
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60         # Seconds

# ============================================
# Document Processing
# ============================================
SUPPORTED_FORMATS=pdf,docx,txt
EXTRACT_IMAGES=true
EXTRACT_TABLES=true
PRESERVE_FORMATTING=true

# ============================================
# Performance Tuning
# ============================================
NUM_WORKERS=4                # Uvicorn workers
BACKGROUND_TASKS=true        # Async task processing
CACHE_EMBEDDINGS=true        # Cache generated embeddings

# ============================================
# Monitoring
# ============================================
ENABLE_METRICS=false
METRICS_PORT=9090
SENTRY_DSN=                  # Error tracking
```

---

## Frontend Configuration

Create `frontend/.env.local`:

```env
# API Configuration
VITE_API_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000       # Request timeout (ms)

# UI Configuration
VITE_THEME=light             # light or dark
VITE_ITEMS_PER_PAGE=10

# Features
VITE_ENABLE_VOICE_INPUT=true
VITE_ENABLE_PDF_EXPORT=true
VITE_ENABLE_DARK_MODE=true

# Analytics (optional)
VITE_GA_ID=                  # Google Analytics ID
```

---

## Advanced Configuration

### Custom Embedding Model

To use a different embedding model, update `backend/services/vector_store.py`:

```python
from langchain_community.embeddings import HuggingFaceEmbeddings

# Available models (see https://www.sbert.net/docs/models/sentence-transformer)
EMBEDDING_MODELS = {
    "fast": "all-MiniLM-L6-v2",           # 22M params, fastest
    "balanced": "all-mpnet-base-v2",      # 109M params, balanced
    "accurate": "all-deberta-v3-large",   # 335M params, most accurate
}

embeddings = HuggingFaceEmbeddings(
    model_name=os.getenv("EMBEDDING_MODEL", EMBEDDING_MODELS["fast"])
)
```

### Custom LLM Provider

To use a different LLM provider instead of Groq, update `backend/services/llm.py`:

```python
# Using OpenAI
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=float(os.getenv("TEMPERATURE", 0.7)),
    api_key=os.getenv("OPENAI_API_KEY")
)

# Using Ollama (local)
from langchain.llms import Ollama

llm = Ollama(
    model="mistral:latest",
    base_url="http://localhost:11434"
)

# Using Azure OpenAI
from langchain.chat_models import AzureChatOpenAI

llm = AzureChatOpenAI(
    deployment_name="docinsight",
    model_name="gpt-4",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_base=os.getenv("AZURE_OPENAI_BASE")
)
```

### Custom Vector Store

To use a managed vector store instead of local ChromaDB:

```python
# Using Pinecone
from langchain.vectorstores import Pinecone
from pinecone import Pinecone as PineconeClient

pc = PineconeClient(api_key=os.getenv("PINECONE_API_KEY"))
vector_store = Pinecone(
    index=pc.Index("docinsight"),
    embedding=embeddings,
    text_key="text"
)

# Using Weaviate
from langchain.vectorstores import Weaviate
import weaviate

client = weaviate.Client(os.getenv("WEAVIATE_URL"))
vector_store = Weaviate(
    client=client,
    index_name="Docinsight",
    text_key="text",
    embedding=embeddings
)

# Using Milvus
from langchain.vectorstores import Milvus

vector_store = Milvus(
    embedding_function=embeddings,
    collection_name="docinsight",
    connection_args={
        "host": os.getenv("MILVUS_HOST", "localhost"),
        "port": int(os.getenv("MILVUS_PORT", 19530))
    }
)
```

### Custom Chunk Strategy

Modify chunking in `backend/services/document_loader.py`:

```python
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter
)

# Recursive splitting (recommended)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=int(os.getenv("CHUNK_SIZE", 1000)),
    chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 200)),
    separators=["\n\n", "\n", ". ", " ", ""]
)

# Token-based splitting
splitter = TokenTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    encoding_name="cl100k_base"
)

# Markdown-aware splitting
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
```

### Retrieval Customization

Modify search in `backend/services/hybrid_search.py`:

```python
# Enable re-ranking
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMListCompressor

compression_retriever = ContextualCompressionRetriever(
    base_compressor=LLMListCompressor(llm=llm),
    base_retriever=vector_store.as_retriever(search_kwargs={"k": 10})
)

# Query expansion
from langchain.retrievers import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=vector_store.as_retriever(),
    llm=llm,
    prompt=custom_query_prompt
)

# Parent document retrieval
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore

retriever = ParentDocumentRetriever(
    vectorstore=vector_store,
    docstore=InMemoryStore(),
    child_splitter=child_splitter,
    parent_splitter=parent_splitter
)
```

---

## Performance Tuning

### For Large Documents

```env
# Increase chunk size to reduce processing time
CHUNK_SIZE=2000
CHUNK_OVERLAP=400

# Reduce retrieval count for faster responses
RETRIEVAL_K=2

# Use faster embedding model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Increase embedding batch size
EMBEDDING_BATCH_SIZE=64
```

### For Memory-Constrained Systems

```env
# Reduce chunk size
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Use lightweight embedding model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Single worker
NUM_WORKERS=1

# Disable caching
CACHE_EMBEDDINGS=false
```

### For Accuracy

```env
# Larger chunks preserve more context
CHUNK_SIZE=2000
CHUNK_OVERLAP=400

# Retrieve more chunks for better context
RETRIEVAL_K=8

# Use accurate embedding model
EMBEDDING_MODEL=sentence-transformers/all-deberta-v3-large

# Higher temperature for diverse responses
TEMPERATURE=0.9

# Better LLM model
LLM_MODEL=llama2-70b-4096
```

### For Speed

```env
# Smaller chunks process faster
CHUNK_SIZE=500

# Fewer chunks to retrieve
RETRIEVAL_K=2

# Fast embedding model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Lower temperature for deterministic responses
TEMPERATURE=0.3

# Fast LLM model
LLM_MODEL=neural-chat-7b-v3-1

# Parallel processing
NUM_WORKERS=8
EMBEDDING_BATCH_SIZE=128
```

---

## Security Configuration

### Enable API Authentication

```env
API_KEY_ENABLED=true
API_KEY=generate-a-secure-random-key

# Client must include header:
# X-API-Key: generate-a-secure-random-key
```

### Enable Rate Limiting

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100    # Requests per period
RATE_LIMIT_PERIOD=60       # Seconds

# Optional: Different limits per endpoint
UPLOAD_RATE_LIMIT=5
CHAT_RATE_LIMIT=50
```

### Configure CORS

```env
# Comma-separated list of allowed origins
CORS_ORIGINS=https://example.com,https://app.example.com

# In backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Enable HTTPS

Use a reverse proxy (Nginx):

```nginx
server {
    listen 443 ssl http2;
    server_name docinsight.example.com;

    ssl_certificate /etc/letsencrypt/live/docinsight.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docinsight.example.com/privkey.pem;

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }

    location / {
        proxy_pass http://frontend:3000;
    }
}
```

---

## Logging Configuration

### Backend Logging

```python
# backend/config.py
import logging

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": "logs/docinsight.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

---

## Database Configuration (Future)

For production deployments with multiple instances:

```env
# PostgreSQL for sessions
DATABASE_URL=postgresql://user:pass@localhost/docinsight
DATABASE_POOL_SIZE=20

# Redis for caching
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# MongoDB for document metadata
MONGODB_URL=mongodb://localhost:27017/docinsight
```

---

## Validation

Test configuration:

```bash
# Check environment variables
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['GROQ_API_KEY', 'LLM_MODEL']
for var in required_vars:
    if var not in os.environ:
        print(f'❌ Missing: {var}')
    else:
        print(f'✅ {var} is set')
"

# Start backend with validation
python backend/config.py --validate
```

---

## Configuration Examples

### Minimal Setup
```env
GROQ_API_KEY=your_key
LLM_MODEL=mixtral-8x7b-32768
```

### Development Setup
```env
GROQ_API_KEY=your_key
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_METRICS=true
```

### Production Setup
```env
GROQ_API_KEY=your_key
DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=https://app.example.com
API_KEY_ENABLED=true
API_KEY=your-secret-key
RATE_LIMIT_ENABLED=true
ENABLE_METRICS=true
```

---

## Troubleshooting Configuration

### Configuration not loading

```bash
# Verify .env file exists
ls -la backend/.env

# Check for syntax errors
python -m dotenv list -p backend/.env

# Reload environment
source backend/.env
```

### Invalid values

```bash
# Validate numeric values
python -c "print(int(os.getenv('CHUNK_SIZE', '1000')))"

# Validate model names
python -c "from transformers import AutoModel; AutoModel.from_pretrained('all-MiniLM-L6-v2')"
```

---

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more help.
