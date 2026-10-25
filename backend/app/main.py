"""Backend API — application entry point.

This module creates and configures the FastAPI application instance,
registers middleware (CORS, request logging), and mounts all routers.
"""

import logging
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, auth, health

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Runs setup logic before the server starts accepting requests and teardown
    logic after it stops.  Reserved for future hooks such as DB initialisation
    and connection-pool warm-up.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the running application.
    """
    # --- startup ---
    logger.info("Starting Website Vulnerability Checker API")
    yield
    # --- shutdown ---
    logger.info("Shutting down Website Vulnerability Checker API")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Centralising construction in a factory function makes the app trivially
    importable in tests without side effects.

    Returns:
        A fully configured ``FastAPI`` instance.
    """
    application = FastAPI(
        title="Website Vulnerability Checker — Backend API",
        description=(
            "REST API for submitting URLs for vulnerability scanning, "
            "retrieving findings, and managing scans via an admin dashboard."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------ CORS
    allowed_origins = [
        settings.FRONTEND_USER_URL,
        settings.FRONTEND_ADMIN_URL,
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ----------------------------------------------------------- Middleware
    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log method, path, status code, and response time for every request.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            The HTTP response.
        """
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d  (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    # --------------------------------------------------------------- Routers
    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(admin.router)

    return application


app = create_app()
