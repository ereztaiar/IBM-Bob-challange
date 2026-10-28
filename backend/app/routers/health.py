"""Health-check router.

Provides a lightweight liveness endpoint used by Docker health checks,
load balancers, and orchestration platforms.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Return service liveness status.

    Returns:
        ``{"status": "ok"}`` when the service is running.
    """
    return {"status": "ok"}
