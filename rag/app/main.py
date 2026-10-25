"""
RAG micro-service — application entry point.

This module creates and configures the FastAPI application instance for the
Retrieval-Augmented Generation service. Embedding and retrieval routers are
registered here as they are implemented in later sub-tasks.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Website Vulnerability Checker — RAG Service",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a simple liveness signal so Docker health checks and load
    balancers can verify the RAG service is running.

    Returns:
        A JSON object ``{"status": "ok"}``.
    """
    return {"status": "ok"}
