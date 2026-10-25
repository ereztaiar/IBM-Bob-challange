"""Authentication router.

Exposes the admin login endpoint which validates credentials and returns a
signed JWT.  All business logic is delegated to ``auth_service``.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.schemas.auth import AdminLoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/auth/admin/login", response_model=TokenResponse)
async def admin_login(
    request: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate an admin with username and password.

    Credentials are compared in constant time to prevent timing attacks.
    A signed JWT is returned on success.

    Args:
        request: Login payload containing ``username`` and ``password``.
        db: Database session (injected; reserved for future credential
            look-ups from the DB).

    Returns:
        A ``TokenResponse`` containing the signed JWT.

    Raises:
        HTTPException: 401 if the credentials are invalid.
    """
    valid = auth_service.verify_admin_credentials(
        request.username,
        request.password,
        settings,
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token(
        subject=request.username,
        secret=settings.JWT_SECRET,
        expires_minutes=settings.JWT_EXPIRE_MINUTES,
    )
    return TokenResponse(access_token=token)
