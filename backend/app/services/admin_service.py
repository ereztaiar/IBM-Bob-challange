"""Admin service — database queries for admin-only endpoints.

All queries filter out soft-deleted scans (``deleted_at IS NOT NULL``) by
default.  Stats and detail endpoints respect this too.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.finding import Finding
from app.db.models.scan import Scan
from app.schemas.admin import (
    AdminScanDetail,
    AdminScanItem,
    AdminStatsResponse,
    PaginatedScansResponse,
    SeverityBreakdown,
)
from app.services.pagination import PaginationParams


async def list_scans(
    db: AsyncSession,
    pagination: PaginationParams,
    status: str | None = None,
    severity: str | None = None,
) -> PaginatedScansResponse:
    """Return a paginated list of non-deleted scans.

    Args:
        db: Async database session.
        pagination: Page / page-size parameters.
        status: Optional status filter (``pending``, ``running``, etc.).
        severity: Optional severity filter — returns scans that have at least
            one finding with the given severity.

    Returns:
        A :class:`~app.schemas.admin.PaginatedScansResponse` with ``items``,
        ``total``, ``page``, and ``page_size``.
    """
    base_q = select(Scan).where(Scan.deleted_at.is_(None))

    if status:
        base_q = base_q.where(Scan.status == status)

    if severity:
        # Subquery: scan IDs that have a finding with the requested severity
        severity_sub = (
            select(Finding.scan_id)
            .where(Finding.severity == severity)
            .distinct()
            .scalar_subquery()
        )
        base_q = base_q.where(Scan.id.in_(severity_sub))

    # Total count (without LIMIT/OFFSET)
    count_q = select(func.count()).select_from(base_q.subquery())
    total: int = (await db.execute(count_q)).scalar_one()

    # Paginated rows — newest first
    rows_q = (
        base_q.order_by(Scan.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    scans = (await db.execute(rows_q)).scalars().all()

    items = [
        AdminScanItem(
            scan_id=str(scan.id),
            url=scan.url,
            status=scan.status,
            created_at=scan.created_at,
            completed_at=scan.completed_at,
            error_message=scan.error_message,
        )
        for scan in scans
    ]

    return PaginatedScansResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.limit,
    )


async def get_scan_detail(db: AsyncSession, scan_id: str) -> AdminScanDetail | None:
    """Return full scan detail including report JSON, or ``None`` if not found.

    Args:
        db: Async database session.
        scan_id: UUID string of the scan to retrieve.

    Returns:
        :class:`~app.schemas.admin.AdminScanDetail` or ``None``.
    """
    try:
        scan_uuid = _uuid.UUID(scan_id)
    except ValueError:
        return None

    result = await db.execute(
        select(Scan).where(Scan.id == scan_uuid, Scan.deleted_at.is_(None))
    )
    scan = result.scalars().first()
    if scan is None:
        return None

    return AdminScanDetail(
        scan_id=str(scan.id),
        url=scan.url,
        status=scan.status,
        created_at=scan.created_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        report_json=scan.report_json,
    )


async def get_stats(db: AsyncSession) -> AdminStatsResponse:
    """Return aggregate dashboard statistics using SQL aggregates.

    Args:
        db: Async database session.

    Returns:
        :class:`~app.schemas.admin.AdminStatsResponse` with total scan count,
        per-severity finding counts, and scans created today.
    """
    # Total non-deleted scans
    total: int = (
        await db.execute(
            select(func.count(Scan.id)).where(Scan.deleted_at.is_(None))
        )
    ).scalar_one()

    # Per-severity counts via CASE aggregates — single query round-trip
    severity_q = select(
        func.sum(case((Finding.severity == "critical", 1), else_=0)).label("critical"),
        func.sum(case((Finding.severity == "high", 1), else_=0)).label("high"),
        func.sum(case((Finding.severity == "medium", 1), else_=0)).label("medium"),
        func.sum(case((Finding.severity == "low", 1), else_=0)).label("low"),
        func.sum(case((Finding.severity == "info", 1), else_=0)).label("info"),
    ).join(Scan, Scan.id == Finding.scan_id).where(Scan.deleted_at.is_(None))

    sev_row = (await db.execute(severity_q)).one()

    # Scans created today (UTC)
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today: int = (
        await db.execute(
            select(func.count(Scan.id)).where(
                Scan.deleted_at.is_(None),
                Scan.created_at >= today_start,
            )
        )
    ).scalar_one()

    return AdminStatsResponse(
        total=total,
        by_severity=SeverityBreakdown(
            critical=sev_row.critical or 0,
            high=sev_row.high or 0,
            medium=sev_row.medium or 0,
            low=sev_row.low or 0,
            info=sev_row.info or 0,
        ),
        today=today,
    )


async def delete_scan(db: AsyncSession, scan_id: str) -> bool:
    """Soft-delete a scan by setting ``deleted_at`` to now (UTC).

    Args:
        db: Async database session.
        scan_id: UUID string of the scan to delete.

    Returns:
        ``True`` if the scan was found and marked deleted, ``False`` if not found.
    """
    try:
        scan_uuid = _uuid.UUID(scan_id)
    except ValueError:
        return False

    result = await db.execute(
        select(Scan).where(Scan.id == scan_uuid, Scan.deleted_at.is_(None))
    )
    scan = result.scalars().first()
    if scan is None:
        return False

    scan.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return True
