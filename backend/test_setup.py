"""
Quick health check script — run before your demo to make sure everything works.

Usage (with venv activated):
    python test_setup.py
"""
import sys
import os

def check(label, fn):
    try:
        fn()
        print(f"  ✓  {label}")
        return True
    except Exception as e:
        print(f"  ✗  {label}")
        print(f"       → {e}")
        return False

print("\n" + "="*55)
print("  AI PDF Chatbot — Pre-Demo Health Check")
print("="*55 + "\n")

failures = 0

# 1. Config loads
def test_config():
    from config import get_settings
    s = get_settings()
    assert s.CHROMA_PERSIST_DIR

failures += 0 if check("Config loads from .env", test_config) else 1

# 2. Groq key present
def test_groq_key():
    from config import get_settings
    s = get_settings()
    if s.LLM_PROVIDER == "groq":
        assert s.GROQ_API_KEY and s.GROQ_API_KEY != "your_groq_api_key_here", \
            "GROQ_API_KEY is not set in backend/.env"

failures += 0 if check("LLM API key configured", test_groq_key) else 1

# 3. HuggingFace embeddings load
def test_embeddings():
    from services.vector_store import get_embeddings
    emb = get_embeddings()
    result = emb.embed_query("hello world")
    assert len(result) > 0

failures += 0 if check("HuggingFace embeddings load (may download ~90MB first time)", test_embeddings) else 1

# 4. ChromaDB initialises
def test_chroma():
    from services.vector_store import get_vectorstore
    vs = get_vectorstore()
    assert vs is not None

failures += 0 if check("ChromaDB vector store initialises", test_chroma) else 1

# 5. LLM connects
def test_llm():
    from services.llm import get_llm
    llm = get_llm()
    assert llm is not None

failures += 0 if check("LLM client initialises", test_llm) else 1

# 6. Upload dir exists
def test_dirs():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("chroma_db", exist_ok=True)
    assert os.path.isdir("uploads")
    assert os.path.isdir("chroma_db")

failures += 0 if check("Upload and chroma_db directories exist", test_dirs) else 1

# 7. FastAPI app imports
def test_app():
    import main
    assert main.app is not None

failures += 0 if check("FastAPI app imports without errors", test_app) else 1

# Summary
print()
if failures == 0:
    print("  🎉  All checks passed! You're ready to demo.\n")
    print("  Run: uvicorn main:app --reload --port 8000\n")
else:
    print(f"  ⚠   {failures} check(s) failed. Fix the issues above before demoing.\n")

sys.exit(failures)
