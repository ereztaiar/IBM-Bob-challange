"""FastAPI dependency functions shared across routers.

Centralising dependencies here prevents circular imports and keeps router
modules thin.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.admin import Admin
from app.db.session import get_db as _get_db
from app.services import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/admin/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Re-export the database session dependency from ``db.session``.

    Yields:
        An ``AsyncSession`` scoped to the current request.
    """
    async for session in _get_db():
        yield session


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """Validate a Bearer JWT and return the corresponding Admin row.

    The token is decoded and the ``sub`` claim (admin username) is looked up
    in the database to confirm the account still exists.

    Args:
        token: JWT extracted from the ``Authorization: Bearer <token>`` header
            by ``OAuth2PasswordBearer``.
        db: Async database session injected by ``get_db``.

    Returns:
        The ``Admin`` ORM instance for the authenticated user.

    Raises:
        HTTPException: 401 if the token is missing, invalid, expired, or the
            admin username cannot be found in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = auth_service.decode_access_token(token, settings.JWT_SECRET)
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Admin).where(Admin.username == username))
    admin = result.scalars().first()
    if admin is None:
        raise credentials_exception

    return admin
