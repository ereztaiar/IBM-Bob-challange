"""Scan model — one row per URL submission."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.finding import Finding


class Scan(Base):
    """Represents a single vulnerability scan request for a URL.

    ``status`` lifecycle: ``pending`` → ``running`` → ``completed`` | ``failed``

    ``report_json`` holds the full denormalised report once the scan completes,
    enabling fast retrieval without joining to the ``findings`` table.
    ``findings`` holds the normalised rows for admin filtering / querying.
    """

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="pending",
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    report_json: Mapped[object] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_service_down: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    deleted_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    findings: Mapped[list[Finding]] = relationship(
        "Finding",
        back_populates="scan",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_scans_status", "status"),
        Index("ix_scans_created_at", "created_at"),
    )
