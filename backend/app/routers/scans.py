"""Scans router — endpoints for submitting and polling vulnerability scans."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.scan import ScanReportResponse, ScanStatusResponse, ScanSubmitRequest
from app.services import scan_runner, scan_service
from app.utils.url_validator import validate_scan_url

router = APIRouter(tags=["scans"])


def _scan_to_status_response(scan) -> ScanStatusResponse:
    """Convert a ``Scan`` ORM instance to a ``ScanStatusResponse``.

    Normalises the ``id`` UUID to a plain string for the API response.

    Args:
        scan: A ``Scan`` ORM instance.

    Returns:
        A populated ``ScanStatusResponse``.
    """
    return ScanStatusResponse(
        scan_id=str(scan.id),
        url=scan.url,
        status=scan.status,
        created_at=scan.created_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
    )


def _scan_to_report_response(scan) -> ScanReportResponse:
    """Convert a ``Scan`` ORM instance to a ``ScanReportResponse``.

    Args:
        scan: A ``Scan`` ORM instance.

    Returns:
        A populated ``ScanReportResponse`` including ``report_json``.
    """
    return ScanReportResponse(
        scan_id=str(scan.id),
        url=scan.url,
        status=scan.status,
        created_at=scan.created_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        report_json=scan.report_json,
    )


@router.post("/scans", response_model=ScanStatusResponse, status_code=201)
async def submit_scan(
    request: ScanSubmitRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ScanStatusResponse:
    """Accept a URL for scanning.

    Validates the URL (scheme + SSRF check), creates a ``Scan`` row with
    ``status='pending'``, enqueues the background scan task, and returns
    immediately with the ``scan_id`` and ``status='pending'``.

    Args:
        request: Request body containing the URL to scan.
        background_tasks: FastAPI background task queue.
        db: Async database session injected by ``get_db``.

    Returns:
        A ``ScanStatusResponse`` with ``status='pending'``.

    Raises:
        HTTPException: 422 if the URL fails SSRF or scheme validation.
    """
    url_str = str(request.url)

    try:
        validate_scan_url(url_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    scan = await scan_service.create_scan(url_str, db)
    background_tasks.add_task(scan_runner.run_scan, str(scan.id), url_str)

    return _scan_to_status_response(scan)


@router.get("/scans/{scan_id}", response_model=ScanReportResponse)
async def get_scan_status(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
) -> ScanReportResponse:
    """Poll scan status and retrieve the report when complete.

    Returns the ``Scan`` row including ``report_json`` once
    ``status='completed'``.

    Args:
        scan_id: UUID string of the scan to query.
        db: Async database session injected by ``get_db``.

    Returns:
        A ``ScanReportResponse`` with the current scan state.

    Raises:
        HTTPException: 404 if no scan with the given ``scan_id`` exists.
    """
    scan = await scan_service.get_scan(scan_id, db)
    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan '{scan_id}' not found.",
        )
    return _scan_to_report_response(scan)
