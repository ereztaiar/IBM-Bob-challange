"""Business logic for admin authentication.

No FastAPI imports are used here so this module is framework-agnostic and
fully unit-testable without spinning up an ASGI app.
"""

import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import Settings


def verify_admin_credentials(username: str, password: str, settings: Settings) -> bool:
    """Compare plain-text credentials against the env-configured admin account.

    Uses ``secrets.compare_digest`` for both comparisons to prevent timing
    attacks — comparison time is constant regardless of how early a mismatch
    occurs.

    Args:
        username: Username submitted by the client.
        password: Plain-text password submitted by the client.
        settings: Application settings carrying ``ADMIN_USERNAME`` and
            ``ADMIN_PASSWORD``.

    Returns:
        ``True`` if both username and password match; ``False`` otherwise.
    """
    username_ok = secrets.compare_digest(
        username.encode("utf-8"),
        settings.ADMIN_USERNAME.encode("utf-8"),
    )
    password_ok = secrets.compare_digest(
        password.encode("utf-8"),
        settings.ADMIN_PASSWORD.encode("utf-8"),
    )
    return username_ok and password_ok


def create_access_token(subject: str, secret: str, expires_minutes: int = 60) -> str:
    """Create a signed JWT containing an expiry claim.

    Args:
        subject: Value embedded as the ``sub`` claim — typically the admin
            username.
        secret: HMAC-SHA256 signing key (from ``settings.JWT_SECRET``).
        expires_minutes: Token lifetime in minutes; defaults to 60.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)
    payload: dict = {
        "sub": subject,
        "exp": expire,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> dict:
    """Decode and validate a JWT, returning its claims.

    Args:
        token: Encoded JWT string.
        secret: HMAC-SHA256 signing key used to verify the signature.

    Returns:
        Decoded claims dictionary (e.g. ``{"sub": "admin", "exp": ...}``).

    Raises:
        jose.JWTError: If the token is invalid, expired, or the signature does
            not match.
    """
    return jwt.decode(token, secret, algorithms=["HS256"])
