"""Seed script — populate the RAG knowledge base with core vulnerability definitions.

Run this script once after the RAG service and database are up:

    python -m seeds.seed

The script is idempotent: each document is only inserted if a document with
the same ``category`` and ``title`` does not already exist.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

# ------------------------------------------------------------------ config

_SEEDS_DIR = Path(__file__).parent
_DEFINITIONS_PATH = _SEEDS_DIR / "vulnerability_definitions.json"
_RAG_BASE_URL = os.environ.get("RAG_SERVICE_URL", "http://localhost:8001")
_INGEST_URL = f"{_RAG_BASE_URL}/rag/knowledge/ingest"
_QUERY_URL = f"{_RAG_BASE_URL}/rag/knowledge/query"


# ------------------------------------------------------------------ helpers


def _load_definitions() -> list[dict]:
    """Load vulnerability definitions from the bundled JSON file.

    Returns:
        A list of dicts, each with ``category``, ``title``, and ``content`` keys.
    """
    with _DEFINITIONS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


async def _document_exists(client: httpx.AsyncClient, category: str, title: str) -> bool:
    """Query the knowledge base to check if a document already exists.

    Uses a precise title-match query and compares the top result.

    Args:
        client: An active ``httpx.AsyncClient``.
        category: The category to check.
        title: The title to check.

    Returns:
        ``True`` if a document with matching title exists in the knowledge base.
    """
    response = await client.post(
        _QUERY_URL,
        json={"query": title, "top_k": 1},
    )
    if response.status_code != 200:
        return False
    results = response.json().get("results", [])
    if not results:
        return False
    top = results[0]
    return top.get("category") == category and top.get("title") == title


async def _ingest_one(client: httpx.AsyncClient, doc: dict) -> bool:
    """Ingest a single document.

    Args:
        client: An active ``httpx.AsyncClient``.
        doc: Dict with ``category``, ``title``, and ``content``.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    response = await client.post(_INGEST_URL, json=doc)
    if response.status_code in (200, 201):
        logger.info("  ✓  [%s] %s", doc["category"], doc["title"])
        return True
    logger.error(
        "  ✗  [%s] %s — HTTP %d: %s",
        doc["category"],
        doc["title"],
        response.status_code,
        response.text,
    )
    return False


# ------------------------------------------------------------------ main


async def run_seed() -> None:
    """Load all definitions and ingest any that are not already in the store."""
    definitions = _load_definitions()
    logger.info("Seeding %d vulnerability definitions into %s", len(definitions), _INGEST_URL)

    inserted = 0
    skipped = 0
    failed = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        for doc in definitions:
            exists = await _document_exists(client, doc["category"], doc["title"])
            if exists:
                logger.info("  –  [%s] %s (already exists, skipping)", doc["category"], doc["title"])
                skipped += 1
                continue
            ok = await _ingest_one(client, doc)
            if ok:
                inserted += 1
            else:
                failed += 1

    logger.info(
        "Seed complete — inserted: %d, skipped: %d, failed: %d",
        inserted,
        skipped,
        failed,
    )

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_seed())
