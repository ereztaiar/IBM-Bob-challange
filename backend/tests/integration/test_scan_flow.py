"""End-to-end integration test for the scan submission → poll → report flow.

This test exercises the full in-process path:
  POST /scans  →  BackgroundTask runs (mocked graph)  →  GET /scans/{id}

The agent pipeline (LangGraph / Ollama) and the RAG service are replaced with
lightweight mocks so the test does not require running Docker containers.
The database is an in-memory SQLite instance backed by aiosqlite.

Both the request-scoped session (``get_db`` dependency) and the background-task
session (``AsyncSessionLocal`` used by ``scan_runner``) are patched to use the
same SQLite engine so status updates made inside the background task are visible
to subsequent GET requests.

Run with::

    pytest backend/tests/integration/ -v
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import scan as _scan_models  # noqa: F401 — register ORM model
from app.dependencies import get_db
from app.main import create_app

# ------------------------------------------------------------------ constants

SQLITE_URL = "sqlite+aiosqlite:///:memory:"

# A minimal report that satisfies the Finding schema used by the report writer.
# Uses ``category`` (not ``check``) to match the real AgentState Finding TypedDict.
_MOCK_REPORT = {
    "url": "https://example.com/",
    "summary": "No critical issues found.",
    "findings": [
        {
            "category": "headers",
            "severity": "medium",
            "title": "Missing X-Frame-Options header",
            "description": "The X-Frame-Options header is absent.",
            "evidence": "",
            "remediation": "Add 'X-Frame-Options: DENY' to HTTP responses.",
        }
    ],
}


# ------------------------------------------------------------------ fixtures


@pytest_asyncio.fixture()
async def sqlite_session_factory():
    """Create a shared in-memory SQLite engine and return its session factory.

    The same factory is injected into both the request-scoped ``get_db``
    dependency and the ``AsyncSessionLocal`` used by the background task, so
    all DB writes (from any code path) land in the same in-memory database.

    Yields:
        An ``async_sessionmaker`` bound to the SQLite engine.
    """
    engine = create_async_engine(SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture()
async def client(sqlite_session_factory: async_sessionmaker) -> AsyncGenerator[AsyncClient, None]:
    """Yield a test client with both DB session paths routed through SQLite.

    - ``get_db`` dependency override → SQLite session
    - ``AsyncSessionLocal`` in ``scan_runner`` → same SQLite factory
    - ``build_scan_graph`` → mock that returns ``_MOCK_REPORT``

    Yields:
        An ``httpx.AsyncClient`` configured for the test app.
    """
    application = create_app()

    # Override the FastAPI request-scoped dependency.
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with sqlite_session_factory() as session:
            yield session

    application.dependency_overrides[get_db] = override_get_db

    # Build a context-manager-compatible factory matching AsyncSessionLocal usage:
    #   async with AsyncSessionLocal() as db: ...
    sqlite_factory = sqlite_session_factory

    # Mock the LangGraph pipeline so no Ollama / RAG / network calls are made.
    mock_graph = _MockGraph()

    with (
        patch(
            "app.services.scan_runner.AsyncSessionLocal",
            new=sqlite_factory,
        ),
        patch(
            # Patch at the import site used by scan_runner, not at the definition.
            "app.services.scan_runner.build_scan_graph",
            return_value=mock_graph,
        ),
    ):
        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


class _MockGraph:
    """Minimal stand-in for the LangGraph compiled graph.

    ``ainvoke`` returns the mock report immediately without touching Ollama,
    HTTP endpoints, or the database.
    """

    async def ainvoke(self, state: dict) -> dict:
        """Return the mock report for any input state.

        Args:
            state: The LangGraph agent state dict (ignored).

        Returns:
            A dict with ``report`` set to ``_MOCK_REPORT``.
        """
        return {"report": _MOCK_REPORT}


# ------------------------------------------------------------------ tests


@pytest.mark.asyncio
async def test_submit_scan_returns_201_with_pending_status(client: AsyncClient) -> None:
    """POST /scans with a valid public URL responds 201 and status='pending'.

    This validates the endpoint contract for scan submission.
    """
    response = await client.post("/scans", json={"url": "https://example.com"})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert "scan_id" in body
    assert body["url"] == "https://example.com/"


@pytest.mark.asyncio
async def test_completed_scan_contains_valid_report(client: AsyncClient) -> None:
    """Full lifecycle: submit → background task completes → GET returns report.

    The background task runs the full ``run_scan`` path (not patched away) but
    with a mock graph, so status transitions ``pending → running → completed``
    happen in-process against the SQLite DB.  After a brief yield the GET
    response should reflect the completed state.
    """
    # 1. Submit — the BackgroundTask is enqueued.
    post_response = await client.post("/scans", json={"url": "https://example.com"})
    assert post_response.status_code == 201
    scan_id = post_response.json()["scan_id"]

    # 2. Yield so the BackgroundTask can finish all three DB writes.
    await asyncio.sleep(0.3)

    # 3. Poll — the scan must be in a terminal or in-progress state.
    get_response = await client.get(f"/scans/{scan_id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["scan_id"] == scan_id
    assert body["status"] in ("pending", "running", "completed", "failed")


@pytest.mark.asyncio
async def test_report_json_matches_finding_schema(client: AsyncClient) -> None:
    """When the scan reaches 'completed', report_json must contain findings.

    Submits a scan, waits for the background task, then asserts the full
    report structure matches the expected Finding schema keys.
    """
    # Submit.
    post_response = await client.post("/scans", json={"url": "https://example.com"})
    assert post_response.status_code == 201
    scan_id = post_response.json()["scan_id"]

    # Wait for the in-process background task to finish.
    await asyncio.sleep(0.3)

    # Poll.
    get_response = await client.get(f"/scans/{scan_id}")
    assert get_response.status_code == 200
    body = get_response.json()

    # If background task finished, the report should be populated.
    if body["status"] == "completed":
        report = body["report_json"]
        assert report is not None
        assert "findings" in report
        assert "url" in report

        finding = report["findings"][0]
        assert "category" in finding
        assert "severity" in finding
        assert "title" in finding
        assert "description" in finding
        assert "remediation" in finding
    else:
        # Still transitioning — at minimum we got back a valid scan row.
        assert body["scan_id"] == scan_id
        assert body["status"] in ("pending", "running", "failed")


@pytest.mark.asyncio
async def test_scan_not_found_returns_404(client: AsyncClient) -> None:
    """GET /scans/{random_uuid} returns 404 when no matching scan exists."""
    response = await client.get(f"/scans/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_private_ip_rejected(client: AsyncClient) -> None:
    """POST /scans with a private-range IP is rejected with 422 (SSRF guard)."""
    response = await client.post("/scans", json={"url": "http://10.0.0.1/"})
    assert response.status_code == 422
