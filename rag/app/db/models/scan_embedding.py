"""ScanEmbedding model — past-scan summaries for domain-level history queries."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScanEmbedding(Base):
    """A vector embedding of a completed scan's text summary.

    ``scan_id`` references the backend's ``scans.id`` (no cross-DB FK —
    stored as a plain UUID for correlation only).  ``domain`` is the
    extracted hostname (e.g. ``example.com``) and is used to retrieve
    past-scan history for the same site.  ``embedding`` is a 1536-dimensional
    pgvector column populated after each scan completes.
    """

    __tablename__ = "scan_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[object] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
