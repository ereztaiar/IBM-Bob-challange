"""RAG micro-service — application entry point.

This module creates and configures the FastAPI application instance,
registers the knowledge and history routers, and exposes a health endpoint.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.routers import history, knowledge

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Reserved for future startup/shutdown hooks (e.g. pre-warming the embedder).

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the running application.
    """
    logger.info("Starting RAG service")
    yield
    logger.info("Shutting down RAG service")


def create_app() -> FastAPI:
    """Construct and configure the RAG FastAPI application.

    Factory pattern keeps the app importable in tests without side effects.

    Returns:
        A fully configured ``FastAPI`` instance.
    """
    application = FastAPI(
        title="Website Vulnerability Checker — RAG Service",
        description=(
            "Internal micro-service for vulnerability knowledge-base ingestion/"
            "retrieval and past-scan history search via pgvector."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(knowledge.router)
    application.include_router(history.router)

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Return a simple liveness signal.

        Returns:
            ``{"status": "ok"}``
        """
        return {"status": "ok"}

    return application


app = create_app()
