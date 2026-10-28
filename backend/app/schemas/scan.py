"""Pydantic schemas for scan submission, status polling, and report retrieval."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScanSubmitRequest(BaseModel):
    """Request body for submitting a URL for vulnerability scanning."""

    url: HttpUrl
    user_prompt: str | None = Field(None, max_length=300)


class ScanStatusResponse(BaseModel):
    """Response for scan status polling.

    Returned immediately after submission and on every subsequent poll.
    """

    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    url: str
    status: str  # pending | running | completed | failed
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    prompt_service_down: bool = False


class ScanReportResponse(ScanStatusResponse):
    """Full scan response including the completed report JSON."""

    report_json: dict | None = None
