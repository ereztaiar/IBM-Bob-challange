"""RAG enricher node — queries the RAG service and attaches context to state.

Calls the internal RAG micro-service to retrieve:
  1. Relevant vulnerability knowledge docs for each unique finding category.
  2. Past-scan summaries for the same domain (historical context).

The retrieved text snippets are stored in ``state["rag_context"]`` and later
consumed by the report-writer node to ground the LLM narrative.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

from app.agents.state import AgentState
from app.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(15.0)


async def _query_knowledge(client: httpx.AsyncClient, query: str) -> list[str]:
    """Fetch top knowledge docs for a query string.

    Args:
        client: Active httpx client.
        query: The query text to embed and search.

    Returns:
        List of content strings from matching knowledge docs.
    """
    try:
        resp = await client.post(
            f"{settings.RAG_SERVICE_URL}/rag/knowledge/query",
            json={"query": query, "top_k": 3},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return [r["content"] for r in resp.json().get("results", [])]
    except Exception as exc:  # noqa: BLE001
        logger.warning("[rag_enricher] Knowledge query failed: %s", exc)
        return []


async def _query_history(client: httpx.AsyncClient, domain: str) -> list[str]:
    """Fetch past scan summaries for a domain.

    Args:
        client: Active httpx client.
        domain: Hostname string to use as the history query.

    Returns:
        List of summary strings from matching past scans.
    """
    try:
        resp = await client.post(
            f"{settings.RAG_SERVICE_URL}/rag/history/query",
            json={"domain": domain, "top_k": 3},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return [r["summary"] for r in resp.json().get("results", [])]
    except Exception as exc:  # noqa: BLE001
        logger.warning("[rag_enricher] History query failed: %s", exc)
        return []


async def rag_enricher_node(state: AgentState) -> dict:
    """Query the RAG service and attach context snippets to the state.

    Args:
        state: Current agent state with ``url`` and ``findings``.

    Returns:
        State update dict with ``rag_context`` populated.
    """
    url = state["url"]
    domain = urlparse(url).hostname or url
    findings = state.get("findings", [])

    # Build one query per unique category found
    categories = list({f["category"] for f in findings})

    context_snippets: list[str] = []

    async with httpx.AsyncClient() as client:
        for category in categories:
            snippets = await _query_knowledge(client, category)
            context_snippets.extend(snippets)

        history = await _query_history(client, domain)
        context_snippets.extend(history)

    logger.info("[rag_enricher] Attached %d context snippets", len(context_snippets))
    return {"rag_context": context_snippets}
