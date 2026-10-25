"""Embedder service — thin wrapper around LangChain OllamaEmbeddings.

Isolates the embedding provider so that swapping to a different backend
(e.g. IBM watsonx.ai) in the future only requires changing this module.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_community.embeddings import OllamaEmbeddings

from app.config import settings


@lru_cache(maxsize=1)
def get_embedder() -> OllamaEmbeddings:
    """Return a cached ``OllamaEmbeddings`` instance.

    The instance is constructed once per process and reused on every
    subsequent call, avoiding repeated initialisation overhead.

    Returns:
        An ``OllamaEmbeddings`` instance pointed at the configured Ollama
        server and model.
    """
    return OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_EMBED_MODEL,
    )


async def embed_text(text: str) -> list[float]:
    """Embed a single string and return the resulting vector.

    Delegates to ``OllamaEmbeddings.aembed_query`` so the call is
    non-blocking inside an async request handler.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding vector.
    """
    embedder = get_embedder()
    return await embedder.aembed_query(text)


async def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings and return their vectors.

    Args:
        texts: A list of strings to embed.

    Returns:
        A list of embedding vectors, one per input string.
    """
    embedder = get_embedder()
    return await embedder.aembed_documents(texts)
