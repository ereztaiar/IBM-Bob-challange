"""Async SQLAlchemy engine and session factory for the RAG service.

Usage in FastAPI route handlers::

    async def my_route(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(VulnerabilityDoc))
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request.

    The session is automatically closed when the request completes or an
    exception is raised.
    """
    async with AsyncSessionLocal() as session:
        yield session
