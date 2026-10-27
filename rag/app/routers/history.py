"""History router — ingest and query past-scan summaries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    HistoryIngestRequest,
    HistoryIngestResponse,
    HistoryQueryRequest,
    HistoryQueryResponse,
    HistoryQueryResult,
)
from app.services import vector_store

router = APIRouter(prefix="/rag/history", tags=["history"])


@router.post(
    "/ingest",
    response_model=HistoryIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_history(request: HistoryIngestRequest) -> HistoryIngestResponse:
    """Embed and store a completed scan summary for future history queries.

    Args:
        request: Ingest payload with ``scan_id``, ``domain``, and ``summary``.

    Returns:
        The id, scan_id, and domain of the stored scan embedding.
    """
    try:
        row = await vector_store.ingest_scan_embedding(
            scan_id=request.scan_id,
            domain=request.domain,
            summary=request.summary,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"History ingest failed: {exc}",
        ) from exc

    return HistoryIngestResponse(
        id=str(row.id),
        scan_id=str(row.scan_id),
        domain=row.domain,
    )


@router.post("/query", response_model=HistoryQueryResponse)
async def query_history(request: HistoryQueryRequest) -> HistoryQueryResponse:
    """Return the top-k most semantically similar past-scan summaries.

    Args:
        request: Query payload with ``domain`` and optional ``top_k`` (default 5).

    Returns:
        A ``HistoryQueryResponse`` with ranked past-scan results.
    """
    try:
        rows = await vector_store.query_scan_history(
            domain=request.domain,
            top_k=request.top_k,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"History query failed: {exc}",
        ) from exc

    results = [
        HistoryQueryResult(
            id=str(row.id),
            scan_id=str(row.scan_id),
            domain=row.domain,
            summary=row.summary,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return HistoryQueryResponse(results=results)
