"""Vector store service — pgvector CRUD via raw SQLAlchemy.

Provides ``ingest_document`` and ``query_similar`` for the knowledge base,
and ``ingest_scan_embedding`` and ``query_scan_history`` for past-scan
summaries.  Each function opens its own DB session so callers only need to
pass data — no session management required at the router layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scan_embedding import ScanEmbedding
from app.db.models.vulnerability_doc import VulnerabilityDoc
from app.db.session import AsyncSessionLocal
from app.services.embedder import embed_text


# ------------------------------------------------------------------ knowledge


async def ingest_document(
    category: str,
    title: str,
    content: str,
) -> VulnerabilityDoc:
    """Store a vulnerability knowledge-base document with its embedding.

    Generates the embedding from ``content`` and persists a new
    ``VulnerabilityDoc`` row.

    Args:
        category: Vulnerability category (e.g. ``"xss"``, ``"ssl"``).
        title: Short human-readable title for the document.
        content: Full text that will be embedded and returned as RAG context.

    Returns:
        The newly created ``VulnerabilityDoc`` ORM instance.
    """
    vector = await embed_text(content)
    async with AsyncSessionLocal() as db:
        doc = VulnerabilityDoc(
            category=category,
            title=title,
            content=content,
            embedding=vector,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
    return doc


async def query_knowledge(query: str, top_k: int = 5) -> list[VulnerabilityDoc]:
    """Return the top-k most semantically similar vulnerability docs.

    Uses the pgvector ``<=>`` cosine-distance operator to rank results.

    Args:
        query: Free-text query string to embed and compare against the store.
        top_k: Maximum number of results to return (default 5).

    Returns:
        A list of ``VulnerabilityDoc`` rows ordered by ascending cosine distance
        (most similar first).
    """
    vector = await embed_text(query)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(VulnerabilityDoc)
            .order_by(VulnerabilityDoc.embedding.cosine_distance(vector))
            .limit(top_k)
        )
        return list(result.scalars().all())


async def document_exists(category: str, title: str) -> bool:
    """Check whether a knowledge-base document already exists (idempotency).

    Args:
        category: Vulnerability category to check.
        title: Document title to check.

    Returns:
        ``True`` if a document with that category and title already exists.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(VulnerabilityDoc.id)
            .where(VulnerabilityDoc.category == category)
            .where(VulnerabilityDoc.title == title)
            .limit(1)
        )
        return result.scalars().first() is not None


async def get_document_by_category_title(
    category: str, title: str
) -> VulnerabilityDoc | None:
    """Fetch an existing knowledge-base document by category and title.

    Args:
        category: Vulnerability category to look up.
        title: Document title to look up.

    Returns:
        The matching ``VulnerabilityDoc`` row, or ``None`` if not found.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(VulnerabilityDoc)
            .where(VulnerabilityDoc.category == category)
            .where(VulnerabilityDoc.title == title)
            .limit(1)
        )
        return result.scalars().first()


# ---------------------------------------------------------------- scan history


async def ingest_scan_embedding(
    scan_id: str,
    domain: str,
    summary: str,
) -> ScanEmbedding:
    """Store a completed scan summary embedding in the history table.

    Args:
        scan_id: UUID string of the completed scan (from the backend DB).
        domain: Extracted hostname of the scanned URL (e.g. ``"example.com"``).
        summary: Text summary of the scan findings to embed.

    Returns:
        The newly created ``ScanEmbedding`` ORM instance.
    """
    vector = await embed_text(summary)
    async with AsyncSessionLocal() as db:
        row = ScanEmbedding(
            scan_id=uuid.UUID(scan_id),
            domain=domain,
            summary=summary,
            embedding=vector,
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


async def query_scan_history(domain: str, top_k: int = 5) -> list[ScanEmbedding]:
    """Return past scan summaries semantically similar to the given domain query.

    Embeds ``domain`` as the query vector and performs a cosine-distance
    search over ``scan_embeddings``.

    Args:
        domain: Hostname string to use as the query (e.g. ``"example.com"``).
        top_k: Maximum number of results to return (default 5).

    Returns:
        A list of ``ScanEmbedding`` rows ordered by ascending cosine distance.
    """
    vector = await embed_text(domain)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScanEmbedding)
            .order_by(ScanEmbedding.embedding.cosine_distance(vector))
            .limit(top_k)
        )
        return list(result.scalars().all())
