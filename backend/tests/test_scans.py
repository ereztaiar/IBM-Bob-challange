"""Integration tests for scan submission and polling endpoints.

Uses ``httpx.AsyncClient`` with an in-memory SQLite (aiosqlite) database so
no real database or network connection is required.  The ``get_db`` dependency
is overridden per-test to inject the in-memory session.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import scan as _scan_models  # noqa: F401 — ensure model is registered
from app.dependencies import get_db
from app.main import create_app

# ------------------------------------------------------------------ fixtures

SQLITE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database with all tables and yield a session.

    Yields:
        An ``AsyncSession`` backed by a fresh in-memory SQLite database.
    """
    engine = create_async_engine(SQLITE_URL, echo=False)

    # Create tables — only the scans table is needed (findings FK uses PG_UUID,
    # so we import the scan model directly and create just that table).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an async test client with ``get_db`` overridden to use SQLite.

    Background tasks (``run_scan``) are patched to a no-op so tests are
    instant and do not depend on async timing.

    Yields:
        An ``httpx.AsyncClient`` pointed at the test app.
    """
    application = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db

    # Patch run_scan so background tasks complete without sleeping or touching
    # the real DB engine (which uses postgres URLs from settings).
    with patch("app.routers.scans.scan_runner.run_scan", return_value=None):
        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# -------------------------------------------------------------------- helpers


def _make_client_no_bg_patch(db_session: AsyncSession) -> tuple:
    """Return an app + override dict for tests that need full lifecycle control.

    Args:
        db_session: The in-memory SQLite session to inject.

    Returns:
        A tuple of (application, override_dict).
    """
    application = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    return application


# -------------------------------------------------------------------- tests


@pytest.mark.asyncio
async def test_submit_scan_returns_pending(client: AsyncClient) -> None:
    """POST /scans with a valid public URL returns 201 and status='pending'."""
    response = await client.post("/scans", json={"url": "https://example.com"})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert "scan_id" in body
    assert body["url"] == "https://example.com/"


@pytest.mark.asyncio
async def test_submit_scan_invalid_scheme(client: AsyncClient) -> None:
    """POST /scans with an ftp:// URL is rejected with 422."""
    response = await client.post("/scans", json={"url": "ftp://example.com/file"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_scan_private_ip(client: AsyncClient) -> None:
    """POST /scans with a private IP URL is rejected with 422 (SSRF protection)."""
    response = await client.post("/scans", json={"url": "http://192.168.1.1/"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_scan_not_found(client: AsyncClient) -> None:
    """GET /scans/{random_uuid} returns 404 when the scan does not exist."""
    missing_id = str(uuid.uuid4())
    response = await client.get(f"/scans/{missing_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scan_returns_status(client: AsyncClient) -> None:
    """After submitting a scan, GET /scans/{id} returns the scan row."""
    # Submit
    post_response = await client.post("/scans", json={"url": "https://example.com"})
    assert post_response.status_code == 201
    scan_id = post_response.json()["scan_id"]

    # Poll
    get_response = await client.get(f"/scans/{scan_id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["scan_id"] == scan_id
    assert body["url"] == "https://example.com/"
    assert body["status"] in ("pending", "running", "completed", "failed")
