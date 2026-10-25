"""Scan runner — background task entry point for the vulnerability scan pipeline.

This module owns the transition logic for a scan's lifecycle:
    pending → running → completed | failed

The agent pipeline call is **stubbed** in this sub-task and will be wired to the
real LangGraph pipeline in Sub-Task 6.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.services import scan_service

logger = logging.getLogger(__name__)


async def _stub_pipeline(url: str) -> dict:
    """Stub replacement for the real LangGraph agent pipeline.

    Simulates async work by sleeping for 2 seconds before returning a
    placeholder report.  This will be replaced in Sub-Task 6.

    Args:
        url: The URL that would be scanned.

    Returns:
        A minimal placeholder report dict.
    """
    await asyncio.sleep(2)
    return {"stub": True, "url": url, "findings": []}


async def run_scan(scan_id: str, url: str) -> None:
    """Background task: run the full agent pipeline for a given scan.

    Creates its own database session because the request-scoped session is
    closed by the time the background task executes.

    Status transitions:
      - ``pending`` → ``running`` (immediately on entry)
      - ``running`` → ``completed`` (on success, with ``report_json`` populated)
      - ``running`` → ``failed``   (on exception, with ``error_message`` set)

    Args:
        scan_id: UUID string of the ``Scan`` row to update.
        url: The URL to scan.
    """
    logger.info("Starting scan %s for %s", scan_id, url)

    async with AsyncSessionLocal() as db:
        await scan_service.update_scan_status(scan_id, "running", db)

    try:
        report = await _stub_pipeline(url)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Scan %s failed: %s", scan_id, exc)
        async with AsyncSessionLocal() as db:
            await scan_service.update_scan_status(
                scan_id,
                "failed",
                db,
                completed_at=datetime.now(timezone.utc),
                error_message=str(exc),
            )
        return

    async with AsyncSessionLocal() as db:
        await scan_service.update_scan_status(
            scan_id,
            "completed",
            db,
            completed_at=datetime.now(timezone.utc),
            report_json=report,
        )

    logger.info("Scan %s completed successfully", scan_id)
