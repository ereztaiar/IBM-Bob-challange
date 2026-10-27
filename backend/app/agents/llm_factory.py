"""LLM factory — constructs the chat model used by the report-writer node.

Isolating LLM construction here means swapping Ollama for IBM watsonx.ai
in a future build only requires changing this single module.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_ollama import ChatOllama

from app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOllama:
    """Return a cached ``ChatOllama`` instance.

    The instance is constructed once per process.  Model name and base URL
    are read from application settings so they can be overridden via env vars.

    Returns:
        A ``ChatOllama`` pointed at the configured Ollama server and model.
    """
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0,
    )
