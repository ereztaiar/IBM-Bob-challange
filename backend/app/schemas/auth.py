"""Pydantic schemas for admin authentication requests and responses."""

from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    """Payload expected on the admin login endpoint.

    Attributes:
        username: The admin account username.
        password: The admin account plain-text password (transmitted over HTTPS only).
    """

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT bearer token returned after successful authentication.

    Attributes:
        access_token: Signed JWT string.
        token_type: Always ``"bearer"`` per the OAuth2 spec.
    """

    access_token: str
    token_type: str = "bearer"
