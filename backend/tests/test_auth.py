"""Integration tests for authentication and protected routes.

Uses ``httpx.AsyncClient`` with the ASGI transport so no network port is
needed.  Settings are overridden via FastAPI's dependency-override mechanism
to inject predictable test credentials.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings, settings
from app.main import create_app
from app.services import auth_service

# ------------------------------------------------------------------ fixtures


TEST_USERNAME = "testadmin"
TEST_PASSWORD = "testpass123"


@pytest.fixture()
def test_settings() -> Settings:
    """Return a Settings instance with predictable test credentials.

    Returns:
        A ``Settings`` object configured for tests.
    """
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        ADMIN_USERNAME=TEST_USERNAME,
        ADMIN_PASSWORD=TEST_PASSWORD,
        JWT_SECRET="test-secret-key",
        JWT_EXPIRE_MINUTES=60,
    )


@pytest_asyncio.fixture()
async def client(test_settings: Settings):
    """Yield an async test client with settings overridden for the test.

    The ``get_current_admin`` dependency uses the live ``settings`` singleton,
    so we patch it via the app's dependency_overrides and by monkey-patching
    the module-level ``settings`` object in modules that imported it at load
    time.

    Yields:
        An ``httpx.AsyncClient`` pointed at the test app.
    """
    from app import dependencies
    from app.routers import auth as auth_router

    # Build a fresh app for each test
    application = create_app()

    # Patch settings references used at request time
    original_settings = dependencies.settings
    original_router_settings = auth_router.settings
    dependencies.settings = test_settings
    auth_router.settings = test_settings

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Restore original settings
    dependencies.settings = original_settings
    auth_router.settings = original_router_settings


@pytest.fixture()
def valid_token(test_settings: Settings) -> str:
    """Generate a valid JWT for the test admin account.

    Args:
        test_settings: Settings fixture providing secret and expiry config.

    Returns:
        A signed JWT string.
    """
    return auth_service.create_access_token(
        subject=TEST_USERNAME,
        secret=test_settings.JWT_SECRET,
        expires_minutes=test_settings.JWT_EXPIRE_MINUTES,
    )


# -------------------------------------------------------------------- tests


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    """GET /health should return 200 with ``{"status": "ok"}``."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient) -> None:
    """Valid credentials should return 200 with an ``access_token``."""
    response = await client.post(
        "/auth/admin/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_admin_login_wrong_password(client: AsyncClient) -> None:
    """Wrong password should return 401."""
    response = await client.post(
        "/auth/admin/login",
        json={"username": TEST_USERNAME, "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_login_wrong_username(client: AsyncClient) -> None:
    """Wrong username should return 401."""
    response = await client.post(
        "/auth/admin/login",
        json={"username": "notanadmin", "password": TEST_PASSWORD},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient) -> None:
    """GET /admin/scans without a token should return 401."""
    response = await client.get("/admin/scans")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(
    client: AsyncClient,
    valid_token: str,
    test_settings: Settings,
) -> None:
    """GET /admin/scans with a valid JWT should return 200.

    The ``get_current_admin`` dependency queries the DB for the username found
    in the token.  Because we are running against an in-memory SQLite DB with
    no seeded data, we override ``get_current_admin`` to bypass the DB lookup
    and return a synthetic Admin stub for this test only.
    """
    from unittest.mock import MagicMock

    from app.dependencies import get_current_admin
    from app.db.models.admin import Admin

    # Build a stub admin — no DB round-trip
    stub_admin = MagicMock(spec=Admin)
    stub_admin.username = TEST_USERNAME

    async def _stub_get_admin():
        return stub_admin

    application = create_app()
    application.dependency_overrides[get_current_admin] = _stub_get_admin

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/admin/scans",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["scans"] == []
    assert "message" in body
