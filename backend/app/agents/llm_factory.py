"""LLM factory — constructs the chat model used by the report-writer node.

Isolating LLM construction here means swapping Ollama for IBM watsonx.ai
in a future build only requires changing this single module.
"""

from __future__ import annotations

from langchain_ollama import ChatOllama

from app.config import settings


def get_llm() -> ChatOllama:
    """Return a ``ChatOllama`` instance configured from application settings.

    A fresh instance is constructed on each call so that runtime setting
    changes (e.g. model swap) are picked up without a process restart.
    ``temperature=0.3`` gives the LLM enough creative latitude to produce
    meaningfully different narratives across scans of the same target.

    Returns:
        A ``ChatOllama`` pointed at the configured Ollama server and model.
    """
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.3,
    )
