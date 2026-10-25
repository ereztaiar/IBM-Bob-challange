"""Admin router — protected endpoints requiring a valid JWT.

Full endpoint implementations arrive in Sub-Task 9.  This stub proves that
the auth dependency chain is wired correctly end-to-end.
"""

from fastapi import APIRouter, Depends

from app.db.models.admin import Admin
from app.dependencies import get_current_admin

router = APIRouter(tags=["admin"])


@router.get("/admin/scans")
async def list_scans(
    current_admin: Admin = Depends(get_current_admin),
) -> dict:
    """List all scans.

    Requires a valid admin JWT in the ``Authorization: Bearer <token>`` header.
    Full implementation arrives in Sub-Task 9.

    Args:
        current_admin: Authenticated admin injected by ``get_current_admin``.

    Returns:
        A placeholder payload confirming the endpoint is active.
    """
    return {"scans": [], "message": "Admin endpoint active"}
