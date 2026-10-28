"""Base class for all vulnerability check agents.

Every check agent subclasses ``BaseCheckAgent``, implements ``run()``, and
returns a list of :class:`~app.agents.state.Finding` dicts.  The base class
provides a shared async HTTP client and a safe ``fetch_target`` helper.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from app.agents.state import AgentState, Finding

logger = logging.getLogger(__name__)

# Shared timeout for all outbound HTTP requests made by check agents.
_REQUEST_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# Headers that mimic a common browser to reduce bot-detection false positives.
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; VulnChecker/1.0; "
        "+https://github.com/ereztaiar/IBM-Bob-challange)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class BaseCheckAgent(ABC):
    """Abstract base for all vulnerability check agents.

    Subclasses must implement :meth:`run` and declare a ``CATEGORY`` class
    attribute matching one of the values in the Finding schema.
    """

    CATEGORY: str = "unknown"

    async def fetch_target(
        self,
        url: str,
        *,
        method: str = "GET",
        follow_redirects: bool = True,
        extra_headers: dict | None = None,
    ) -> httpx.Response | None:
        """Perform an async HTTP request against the target URL.

        Network errors and timeouts are caught and logged — the caller
        receives ``None`` instead of an exception so the pipeline continues.

        Args:
            url: The URL to request.
            method: HTTP method (default ``"GET"``).
            follow_redirects: Whether to follow HTTP redirects (default True).
            extra_headers: Additional headers to merge with the defaults.

        Returns:
            An ``httpx.Response`` on success, or ``None`` on any error.
        """
        headers = {**_DEFAULT_HEADERS, **(extra_headers or {})}
        try:
            async with httpx.AsyncClient(
                timeout=_REQUEST_TIMEOUT,
                follow_redirects=follow_redirects,
                verify=False,  # We intentionally check certs ourselves in ssl_tls.py
            ) as client:
                response = await client.request(method, url, headers=headers)
            return response
        except httpx.TimeoutException:
            logger.warning("[%s] Timeout fetching %s", self.CATEGORY, url)
            return None
        except httpx.RequestError as exc:
            logger.warning("[%s] Request error for %s: %s", self.CATEGORY, url, exc)
            return None

    def _error_finding(self, message: str) -> Finding:
        """Construct a standard error finding when a check cannot complete.

        Args:
            message: Human-readable description of what went wrong.

        Returns:
            A Finding with severity ``info`` and category matching this agent.
        """
        return Finding(
            category=self.CATEGORY,
            severity="info",
            title=f"{self.CATEGORY.upper()} check could not complete",
            description=message,
            evidence="",
            remediation="Retry the scan or check network connectivity.",
        )

    @abstractmethod
    async def run(self, state: AgentState) -> dict:
        """Execute the vulnerability check and return state updates.

        Args:
            state: The current shared agent state.

        Returns:
            A dict with at minimum a ``findings`` key containing a list of
            :class:`~app.agents.state.Finding` dicts.
        """
