"""Unit tests for the vector store service.

All embedding calls are patched to return a deterministic zero-vector so no
Ollama instance is required.  The database is an in-memory SQLite backed by
``aiosqlite``.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import scan_embedding as _se_models  # noqa: F401
from app.db.models import vulnerability_doc as _vd_models  # noqa: F401

SQLITE_URL = "sqlite+aiosqlite:///:memory:"
ZERO_VECTOR = [0.0] * 1536


# ------------------------------------------------------------------ fixtures


@pytest_asyncio.fixture()
async def _db_engine():
    """Create and tear down an in-memory SQLite engine with all tables.

    Yields:
        The async engine.
    """
    engine = create_async_engine(SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session backed by the in-memory SQLite engine.

    Yields:
        An ``AsyncSession``.
    """
    factory = async_sessionmaker(_db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


# ------------------------------------------------------------------ helpers


def _patch_embed():
    """Return a context manager that patches ``embed_text`` to return ZERO_VECTOR."""
    return patch(
        "app.services.vector_store.embed_text",
        new=AsyncMock(return_value=ZERO_VECTOR),
    )


def _patch_session_local(db_session: AsyncSession):
    """Return a context manager that patches ``AsyncSessionLocal`` to yield db_session.

    Args:
        db_session: The test session to inject.
    """
    from unittest.mock import MagicMock

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=db_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    return patch(
        "app.services.vector_store.AsyncSessionLocal",
        return_value=mock_cm,
    )


# -------------------------------------------------------------------- tests


@pytest.mark.asyncio
async def test_ingest_document_creates_row(db_session: AsyncSession) -> None:
    """ingest_document() should insert a VulnerabilityDoc row and return it."""
    from app.services import vector_store

    with _patch_embed(), _patch_session_local(db_session):
        doc = await vector_store.ingest_document(
            category="xss",
            title="Test XSS",
            content="Some XSS content",
        )

    assert doc.category == "xss"
    assert doc.title == "Test XSS"
    assert doc.id is not None


@pytest.mark.asyncio
async def test_document_exists_returns_false_when_empty(db_session: AsyncSession) -> None:
    """document_exists() should return False on an empty knowledge base."""
    from app.services import vector_store

    with _patch_embed(), _patch_session_local(db_session):
        exists = await vector_store.document_exists("xss", "Nonexistent")

    assert exists is False


@pytest.mark.asyncio
async def test_document_exists_returns_true_after_ingest(db_session: AsyncSession) -> None:
    """document_exists() should return True after the document is ingested."""
    from app.services import vector_store

    with _patch_embed(), _patch_session_local(db_session):
        await vector_store.ingest_document(
            category="cors",
            title="CORS Misconfiguration",
            content="CORS content",
        )
        exists = await vector_store.document_exists("cors", "CORS Misconfiguration")

    assert exists is True


@pytest.mark.asyncio
async def test_query_knowledge_returns_results(db_session: AsyncSession) -> None:
    """query_knowledge() returns a list from the vector store.

    The cosine-distance operator (<=> ) is pgvector-specific and unavailable
    in SQLite.  We verify the service builds the correct result shape by
    patching the raw DB execute so no real query hits SQLite.
    """
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services import vector_store
    from app.db.models.vulnerability_doc import VulnerabilityDoc

    fake_doc = MagicMock(spec=VulnerabilityDoc)
    fake_doc.id = uuid.uuid4()
    fake_doc.category = "headers"
    fake_doc.title = "Missing HSTS"
    fake_doc.content = "HSTS content"

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake_doc]

    with _patch_embed():
        with patch.object(db_session, "execute", new=AsyncMock(return_value=mock_result)):
            with _patch_session_local(db_session):
                results = await vector_store.query_knowledge("security headers", top_k=5)

    assert len(results) == 1
    assert results[0].title == "Missing HSTS"


@pytest.mark.asyncio
async def test_ingest_scan_embedding_creates_row(db_session: AsyncSession) -> None:
    """ingest_scan_embedding() should insert a ScanEmbedding row and return it."""
    from app.services import vector_store

    scan_id = str(uuid.uuid4())

    with _patch_embed(), _patch_session_local(db_session):
        row = await vector_store.ingest_scan_embedding(
            scan_id=scan_id,
            domain="example.com",
            summary="Found XSS vulnerability on login page.",
        )

    assert str(row.scan_id) == scan_id
    assert row.domain == "example.com"


@pytest.mark.asyncio
async def test_query_scan_history_returns_results(db_session: AsyncSession) -> None:
    """query_scan_history() returns a list from the vector store.

    Same rationale as ``test_query_knowledge_returns_results`` — the <=>
    operator is pgvector-only so we stub the DB execute call.
    """
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services import vector_store
    from app.db.models.scan_embedding import ScanEmbedding

    scan_id = uuid.uuid4()
    fake_row = MagicMock(spec=ScanEmbedding)
    fake_row.id = uuid.uuid4()
    fake_row.scan_id = scan_id
    fake_row.domain = "example.com"
    fake_row.summary = "SSL certificate expired."
    fake_row.created_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake_row]

    with _patch_embed():
        with patch.object(db_session, "execute", new=AsyncMock(return_value=mock_result)):
            with _patch_session_local(db_session):
                results = await vector_store.query_scan_history("example.com", top_k=5)

    assert len(results) == 1
    assert results[0].domain == "example.com"
