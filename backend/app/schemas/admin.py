"""Pydantic schemas for admin-only API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AdminScanItem(BaseModel):
    """Compact scan record used in paginated list responses.

    Does not include the full ``report_json`` to keep list responses lean.
    """

    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    url: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None


class AdminScanDetail(AdminScanItem):
    """Full scan record including the denormalised report JSON.

    Returned by ``GET /admin/scans/{id}``.
    """

    report_json: dict[str, Any] | None = None


class PaginatedScansResponse(BaseModel):
    """Paginated wrapper for scan list results."""

    items: list[AdminScanItem]
    total: int
    page: int
    page_size: int


class SeverityBreakdown(BaseModel):
    """Per-severity counts used inside :class:`AdminStatsResponse`."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class AdminStatsResponse(BaseModel):
    """Aggregate statistics for the admin dashboard header."""

    total: int
    by_severity: SeverityBreakdown
    today: int
