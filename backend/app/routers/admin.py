"""Admin router — protected endpoints for dashboard and scan management.

All routes require a valid JWT issued by ``POST /auth/admin/login``.
The :func:`~app.dependencies.get_current_admin` dependency enforces this.

Routes
------
GET  /admin/scans          Paginated scan list with optional filters
GET  /admin/scans/{id}     Full scan detail
GET  /admin/stats          Aggregate dashboard statistics
DELETE /admin/scans/{id}   Soft-delete a scan record
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.admin import Admin
from app.dependencies import get_current_admin, get_db
from app.schemas.admin import (
    AdminScanDetail,
    AdminStatsResponse,
    PaginatedScansResponse,
)
from app.services import admin_service
from app.services.pagination import DEFAULT_PAGE_SIZE, PaginationParams

router = APIRouter(tags=["admin"])


@router.get(
    "/admin/scans",
    response_model=PaginatedScansResponse,
    summary="List all scans (paginated)",
)
async def list_scans(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE, ge=1, le=100, description="Items per page"
    ),
    status: str | None = Query(None, description="Filter by scan status"),
    severity: str | None = Query(
        None, description="Filter to scans containing this severity level"
    ),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> PaginatedScansResponse:
    """Return a paginated, filtered list of vulnerability scans.

    Args:
        page: 1-based page number.
        page_size: Number of results per page (max 100).
        status: Optional status filter (pending | running | completed | failed).
        severity: Optional severity filter — returns scans with at least one
            finding at this severity level.
        db: Async database session.
        current_admin: Authenticated admin (enforces JWT requirement).

    Returns:
        Paginated list of :class:`~app.schemas.admin.AdminScanItem` records.
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    return await admin_service.list_scans(db, pagination, status, severity)


@router.get(
    "/admin/scans/{scan_id}",
    response_model=AdminScanDetail,
    summary="Get full scan detail",
)
async def get_scan_detail(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> AdminScanDetail:
    """Return full detail for a single scan, including the report JSON.

    Args:
        scan_id: UUID of the scan to retrieve.
        db: Async database session.
        current_admin: Authenticated admin.

    Returns:
        Full :class:`~app.schemas.admin.AdminScanDetail` for the scan.

    Raises:
        HTTPException: 404 if the scan does not exist or has been soft-deleted.
    """
    detail = await admin_service.get_scan_detail(db, scan_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )
    return detail


@router.get(
    "/admin/stats",
    response_model=AdminStatsResponse,
    summary="Get dashboard aggregate statistics",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> AdminStatsResponse:
    """Return aggregate statistics for the admin dashboard.

    Args:
        db: Async database session.
        current_admin: Authenticated admin.

    Returns:
        :class:`~app.schemas.admin.AdminStatsResponse` with total, by_severity,
        and today counts.
    """
    return await admin_service.get_stats(db)


@router.delete(
    "/admin/scans/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a scan",
)
async def delete_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> None:
    """Soft-delete a scan by setting its ``deleted_at`` timestamp.

    The scan record is retained in the database but excluded from all list and
    stats queries.

    Args:
        scan_id: UUID of the scan to delete.
        db: Async database session.
        current_admin: Authenticated admin.

    Raises:
        HTTPException: 404 if the scan does not exist or is already deleted.
    """
    deleted = await admin_service.delete_scan(db, scan_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )
