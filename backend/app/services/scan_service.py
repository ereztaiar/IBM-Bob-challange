"""Scan service — pure async business logic for scan lifecycle management.

No FastAPI imports; this module is intentionally framework-agnostic so that it
can be called from both route handlers and background tasks.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scan import Scan


async def create_scan(url: str, db: AsyncSession) -> Scan:
    """Insert a new Scan row with status='pending' and return it.

    Args:
        url: The URL that will be scanned.
        db: An active async database session.

    Returns:
        The newly created ``Scan`` ORM instance (already flushed to the DB).
    """
    scan = Scan(url=url, status="pending")
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan


async def get_scan(scan_id: str, db: AsyncSession) -> Scan | None:
    """Fetch a Scan row by UUID string.

    Args:
        scan_id: UUID string of the scan to look up.
        db: An active async database session.

    Returns:
        The matching ``Scan`` ORM instance, or ``None`` if not found.
    """
    try:
        uid = uuid.UUID(scan_id)
    except ValueError:
        return None

    result = await db.execute(select(Scan).where(Scan.id == uid))
    return result.scalars().first()


async def update_scan_status(
    scan_id: str,
    status: str,
    db: AsyncSession,
    completed_at: datetime | None = None,
    report_json: dict | None = None,
    error_message: str | None = None,
) -> None:
    """Update status and optional fields on a Scan row.

    Only the fields that are explicitly passed (non-``None`` for optional
    parameters) are written.  ``status`` is always updated.

    Args:
        scan_id: UUID string of the scan to update.
        status: New status string (e.g. ``"running"``, ``"completed"``,
            ``"failed"``).
        db: An active async database session.
        completed_at: Timestamp to record when the scan finished.
        report_json: Full report payload to store on completion.
        error_message: Error description to store on failure.
    """
    try:
        uid = uuid.UUID(scan_id)
    except ValueError:
        return

    result = await db.execute(select(Scan).where(Scan.id == uid))
    scan = result.scalars().first()
    if scan is None:
        return

    scan.status = status
    if completed_at is not None:
        scan.completed_at = completed_at
    if report_json is not None:
        scan.report_json = report_json
    if error_message is not None:
        scan.error_message = error_message

    await db.commit()
