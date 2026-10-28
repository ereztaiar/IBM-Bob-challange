"""Scan runner — background task entry point for the vulnerability scan pipeline.

This module owns the transition logic for a scan's lifecycle:
    pending → running → completed | failed

It delegates the actual scan work to the LangGraph pipeline built by
:func:`~app.agents.graph.build_scan_graph`.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.agents.graph import build_scan_graph
from app.agents.prompt_sanitiser import (
    PromptServiceUnavailableError,
    sanitise_user_prompt,
)
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.services import scan_service

logger = logging.getLogger(__name__)


async def run_scan(scan_id: str, url: str, user_prompt: str | None = None) -> None:
    """Background task: run the full agent pipeline for a given scan.

    Creates its own database session because the request-scoped session is
    closed by the time the background task executes.

    Status transitions:
      - ``pending`` → ``running`` (immediately on entry)
      - ``running`` → ``completed`` (on success, with ``report_json`` populated)
      - ``running`` → ``failed``   (on exception, with ``error_message`` set)

    Args:
        scan_id: UUID string of the ``Scan`` row to update.
        url: The URL to scan.
        user_prompt: Optional raw focus hint from the user; will be sanitised
            before being forwarded to the LLM report writer.
    """
    logger.info("Starting scan %s for %s", scan_id, url)

    async with AsyncSessionLocal() as db:
        await scan_service.update_scan_status(scan_id, "running", db)

    # Sanitise the user prompt before passing it into the LLM pipeline.
    prompt_service_down = False
    sanitised_prompt: str | None = None
    if user_prompt:
        try:
            sanitised_prompt = await sanitise_user_prompt(user_prompt)
        except PromptServiceUnavailableError:
            logger.warning(
                "Scan %s: AI sanitisation service unreachable; "
                "proceeding without user prompt.",
                scan_id,
            )
            prompt_service_down = True

    try:
        graph = build_scan_graph()
        result = await graph.ainvoke({
            "url": url,
            "raw_responses": [],
            "findings": [],
            "rag_context": [],
            "report": {},
            "user_prompt": sanitised_prompt,
            "prompt_service_down": prompt_service_down,
        })
        report = result.get("report", {})
    except Exception as exc:  # noqa: BLE001
        logger.exception("Scan %s failed: %s", scan_id, exc)
        async with AsyncSessionLocal() as db:
            await scan_service.update_scan_status(
                scan_id,
                "failed",
                db,
                completed_at=datetime.now(timezone.utc),
                error_message=str(exc),
            )
        return

    async with AsyncSessionLocal() as db:
        await scan_service.update_scan_status(
            scan_id,
            "completed",
            db,
            completed_at=datetime.now(timezone.utc),
            report_json=report,
            prompt_service_down=prompt_service_down,
        )

    logger.info("Scan %s completed successfully", scan_id)

    # Persist scan summary to RAG history (fire-and-forget — failure is non-fatal)
    summary = report.get("summary", "")
    if summary:
        domain = urlparse(url).hostname or url
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.post(
                    f"{settings.RAG_SERVICE_URL}/rag/history/ingest",
                    json={"scan_id": scan_id, "domain": domain, "summary": summary},
                )
                resp.raise_for_status()
            logger.info("Scan %s history ingested for domain %s", scan_id, domain)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scan %s history ingest failed (non-fatal): %s", scan_id, exc)
