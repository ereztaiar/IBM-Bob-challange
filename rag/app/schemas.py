"""Pydantic schemas for RAG knowledge and history endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ------------------------------------------------------------------ knowledge


class KnowledgeIngestRequest(BaseModel):
    """Request body for ingesting a vulnerability knowledge document."""

    category: str
    title: str
    content: str


class KnowledgeIngestResponse(BaseModel):
    """Response after successfully ingesting a document."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    title: str


class KnowledgeQueryRequest(BaseModel):
    """Request body for querying the knowledge base."""

    query: str
    top_k: int = 5


class KnowledgeQueryResult(BaseModel):
    """A single result from a knowledge-base similarity query."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    title: str
    content: str


class KnowledgeQueryResponse(BaseModel):
    """Response containing the top-k knowledge-base results."""

    results: list[KnowledgeQueryResult]


# ----------------------------------------------------------------- scan history


class HistoryIngestRequest(BaseModel):
    """Request body for ingesting a completed scan summary."""

    scan_id: str
    domain: str
    summary: str


class HistoryIngestResponse(BaseModel):
    """Response after successfully ingesting a scan summary."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    scan_id: str
    domain: str


class HistoryQueryRequest(BaseModel):
    """Request body for querying past-scan history."""

    domain: str
    top_k: int = 5


class HistoryQueryResult(BaseModel):
    """A single result from a scan-history similarity query."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    scan_id: str
    domain: str
    summary: str
    created_at: datetime


class HistoryQueryResponse(BaseModel):
    """Response containing the top-k scan-history results."""

    results: list[HistoryQueryResult]
