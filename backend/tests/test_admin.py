"""Tests for admin-only endpoints.

Uses an in-memory SQLite database (same pattern as test_scans.py).
The ``get_current_admin`` dependency is overridden to return a stub Admin so
tests are not coupled to the JWT/auth flow.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.admin import Admin
from app.db.models.scan import Scan  # noqa: F401 — registers model
from app.dependencies import get_current_admin, get_db
from app.main import create_app

SQLITE_URL = "sqlite+aiosqlite:///:memory:"

# ------------------------------------------------------------------ fixtures


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fresh in-memory SQLite session with all tables created.

    Yields:
        An ``AsyncSession`` backed by an ephemeral in-memory database.
    """
    engine = create_async_engine(SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with DB and auth dependencies overridden.

    ``get_current_admin`` returns a stub Admin so all admin routes are
    accessible without a real JWT.

    Yields:
        An ``httpx.AsyncClient`` pointed at the test app.
    """
    application = create_app()

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_admin() -> Admin:
        admin = Admin()
        admin.id = uuid.uuid4()
        admin.username = "test_admin"
        admin.password_hash = "irrelevant"
        return admin

    application.dependency_overrides[get_db] = override_db
    application.dependency_overrides[get_current_admin] = override_admin

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ------------------------------------------------------------------ helpers


async def _insert_scan(
    db: AsyncSession,
    url: str = "https://example.com",
    status: str = "completed",
) -> Scan:
    """Insert a minimal Scan row and return it.

    Args:
        db: Database session.
        url: Target URL for the scan.
        status: Scan status string.

    Returns:
        The persisted :class:`~app.db.models.scan.Scan` instance.
    """
    scan = Scan()
    scan.id = uuid.uuid4()
    scan.url = url
    scan.status = status
    scan.created_at = datetime.now(timezone.utc)
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan


# -------------------------------------------------------------------- tests


@pytest.mark.asyncio
async def test_list_scans_empty(client: AsyncClient) -> None:
    """GET /admin/scans returns an empty list when no scans exist."""
    response = await client.get("/admin/scans")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1


@pytest.mark.asyncio
async def test_list_scans_returns_inserted(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /admin/scans returns scans after insertion."""
    await _insert_scan(db_session, "https://test.com", "completed")
    response = await client.get("/admin/scans")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["url"] == "https://test.com"


@pytest.mark.asyncio
async def test_list_scans_status_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /admin/scans?status=pending only returns pending scans."""
    await _insert_scan(db_session, "https://a.com", "completed")
    await _insert_scan(db_session, "https://b.com", "pending")
    response = await client.get("/admin/scans?status=pending")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["url"] == "https://b.com"


@pytest.mark.asyncio
async def test_get_scan_detail_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /admin/scans/{id} returns 200 and the scan data."""
    scan = await _insert_scan(db_session)
    response = await client.get(f"/admin/scans/{scan.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["scan_id"] == str(scan.id)
    assert body["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_get_scan_detail_not_found(client: AsyncClient) -> None:
    """GET /admin/scans/{random_id} returns 404."""
    response = await client.get(f"/admin/scans/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_stats_empty_db(client: AsyncClient) -> None:
    """GET /admin/stats returns zeros when there are no scans."""
    response = await client.get("/admin/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["today"] == 0
    assert body["by_severity"]["critical"] == 0


@pytest.mark.asyncio
async def test_get_stats_counts_scans(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /admin/stats returns correct total after inserting scans."""
    await _insert_scan(db_session, "https://x.com")
    await _insert_scan(db_session, "https://y.com")
    response = await client.get("/admin/stats")
    assert response.status_code == 200
    assert response.json()["total"] == 2


@pytest.mark.asyncio
async def test_delete_scan_returns_204(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """DELETE /admin/scans/{id} returns 204 and the scan is no longer listed."""
    scan = await _insert_scan(db_session)
    response = await client.delete(f"/admin/scans/{scan.id}")
    assert response.status_code == 204

    # The scan should no longer appear in list
    list_response = await client.get("/admin/scans")
    assert list_response.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_scan_not_found(client: AsyncClient) -> None:
    """DELETE /admin/scans/{random_id} returns 404."""
    response = await client.delete(f"/admin/scans/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_endpoints_require_auth() -> None:
    """All admin endpoints return 401 when no JWT is provided."""
    application = create_app()
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for method, path in [
            ("GET", "/admin/scans"),
            ("GET", f"/admin/scans/{uuid.uuid4()}"),
            ("GET", "/admin/stats"),
            ("DELETE", f"/admin/scans/{uuid.uuid4()}"),
        ]:
            response = await ac.request(method, path)
            assert response.status_code == 401, (
                f"{method} {path} should return 401, got {response.status_code}"
            )
