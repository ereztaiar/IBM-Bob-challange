"""Knowledge router — ingest and query the vulnerability knowledge base."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeQueryResult,
)
from app.services import vector_store

router = APIRouter(prefix="/rag/knowledge", tags=["knowledge"])


@router.post(
    "/ingest",
    response_model=KnowledgeIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_knowledge(request: KnowledgeIngestRequest) -> KnowledgeIngestResponse:
    """Embed and store a vulnerability knowledge document.

    If a document with the same ``category`` and ``title`` already exists the
    request is treated as a duplicate and the existing document's metadata is
    returned with HTTP 200 instead of 201.

    Args:
        request: Ingest payload containing ``category``, ``title``, and ``content``.

    Returns:
        The id, category, and title of the stored document.
    """
    try:
        doc = await vector_store.ingest_document(
            category=request.category,
            title=request.title,
            content=request.content,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingest failed: {exc}",
        ) from exc

    return KnowledgeIngestResponse(
        id=str(doc.id),
        category=doc.category,
        title=doc.title,
    )


@router.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(request: KnowledgeQueryRequest) -> KnowledgeQueryResponse:
    """Return the top-k most semantically relevant vulnerability documents.

    Args:
        request: Query payload containing the free-text ``query`` and optional
            ``top_k`` (default 5).

    Returns:
        A ``KnowledgeQueryResponse`` with the ranked list of matching documents.
    """
    try:
        docs = await vector_store.query_knowledge(
            query=request.query,
            top_k=request.top_k,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {exc}",
        ) from exc

    results = [
        KnowledgeQueryResult(
            id=str(doc.id),
            category=doc.category,
            title=doc.title,
            content=doc.content,
        )
        for doc in docs
    ]
    return KnowledgeQueryResponse(results=results)
