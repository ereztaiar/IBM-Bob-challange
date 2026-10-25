"""Env exposure check agent — probes for publicly accessible config files."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from app.agents.checks.base import BaseCheckAgent
from app.agents.state import AgentState, Finding

# Paths to probe, relative to the target origin
_CONFIG_PATHS = [
    "/.env",
    "/.env.local",
    "/.env.production",
    "/.env.development",
    "/config.yml",
    "/config.json",
    "/.git/config",
    "/web.config",
    "/settings.py",
    "/application.properties",
    "/.htaccess",
    "/docker-compose.yml",
    "/Dockerfile",
]

# Patterns that strongly indicate real credentials / config
_CREDENTIAL_PATTERNS = [
    re.compile(r"(?:password|passwd|secret|api_key|token)\s*[=:]", re.IGNORECASE),
    re.compile(r"DB_(?:HOST|USER|PASS|NAME)", re.IGNORECASE),
    re.compile(r"\[core\]", re.IGNORECASE),  # git config
    re.compile(r"APP_(?:KEY|SECRET|ENV)", re.IGNORECASE),
]


def _looks_like_config(body: str) -> bool:
    """Return True if the response body looks like a real config file.

    Args:
        body: HTTP response body text.

    Returns:
        ``True`` if any credential pattern matches.
    """
    return any(p.search(body) for p in _CREDENTIAL_PATTERNS)


class EnvExposureAgent(BaseCheckAgent):
    """Probe common configuration file paths for public accessibility."""

    CATEGORY = "env_exposure"

    async def run(self, state: AgentState) -> dict:
        """Request each known config path and flag files that appear accessible.

        Args:
            state: Current agent state containing ``url``.

        Returns:
            State update dict with ``findings`` list.
        """
        from urllib.parse import urlparse

        url = state["url"]
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        findings: list[Finding] = []

        for path in _CONFIG_PATHS:
            probe_url = urljoin(origin, path)
            finding = await self._probe_path(probe_url, path)
            if finding:
                findings.append(finding)

        return {"findings": findings}

    async def _probe_path(self, url: str, path: str) -> Finding | None:
        """Fetch a single config path and return a finding if it is exposed.

        Args:
            url: Full URL to probe.
            path: The path component (used in evidence string).

        Returns:
            A Finding if the file is accessible and looks like real config, or ``None``.
        """
        response = await self.fetch_target(url, follow_redirects=False)
        if response is None or response.status_code != 200:
            return None

        body = response.text
        if not _looks_like_config(body):
            return None

        return Finding(
            category=self.CATEGORY,
            severity="critical",
            title=f"Exposed Configuration File: {path}",
            description=(
                f"The configuration file '{path}' is publicly accessible and "
                "appears to contain credentials or sensitive settings."
            ),
            evidence=f"HTTP 200 from {url}; body contains credential patterns.",
            remediation=(
                "Remove the file from the web root, add an explicit deny rule "
                "in your web server config, and rotate any exposed secrets immediately."
            ),
        )
