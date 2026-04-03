"""
LLM Service - supports multiple free providers:
  - Groq (recommended): Free API, fast Llama3/Mixtral
  - Ollama: Fully local, no internet needed
  - OpenAI: Paid fallback
"""
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

def get_llm():
    """Returns the configured LLM based on LLM_PROVIDER env var"""
    provider = settings.LLM_PROVIDER.lower()
    logger.info(f"Using LLM provider: {provider}")

    if provider == "groq":
        from langchain_groq import ChatGroq
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not set. Get a free key at https://console.groq.com"
            )
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.1,
            max_tokens=2048,
            streaming=True,
        )

    elif provider == "ollama":
        from langchain_community.llms import Ollama
        return Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.1,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            streaming=True,
        )

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Choose: groq | ollama | openai")
