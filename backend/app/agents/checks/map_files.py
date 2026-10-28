"""Map files check agent — detects exposed JavaScript source maps."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from app.agents.checks.base import BaseCheckAgent
from app.agents.state import AgentState, Finding

# Regex to find JS file references in HTML
_SCRIPT_SRC_RE = re.compile(
    r'<script[^>]+src=["\']([^"\']+\.js(?:\?[^"\']*)?)["\']',
    re.IGNORECASE,
)

# Signature that identifies a valid source map JSON body
_SOURCEMAP_SIGNATURE = '"sources"'

# Maximum JS files to probe (keeps the check fast)
_MAX_PROBES = 5


class MapFilesAgent(BaseCheckAgent):
    """Check whether JavaScript source map (.js.map) files are publicly accessible."""

    CATEGORY = "map_files"

    async def run(self, state: AgentState) -> dict:
        """Fetch the target page, extract JS URLs, and probe for .map files.

        Args:
            state: Current agent state containing ``url``.

        Returns:
            State update dict with ``findings`` list.
        """
        url = state["url"]
        findings: list[Finding] = []

        response = await self.fetch_target(url)
        if response is None:
            return {"findings": [self._error_finding("Could not fetch target URL.")]}

        js_urls = self._extract_js_urls(url, response.text)
        for js_url in js_urls[:_MAX_PROBES]:
            finding = await self._probe_map(js_url)
            if finding:
                findings.append(finding)

        return {"findings": findings}

    def _extract_js_urls(self, base_url: str, html: str) -> list[str]:
        """Parse HTML and return a list of absolute JS URLs.

        Args:
            base_url: The page URL used to resolve relative paths.
            html: HTML body of the target page.

        Returns:
            List of absolute JS URLs found in ``<script src>`` tags.
        """
        matches = _SCRIPT_SRC_RE.findall(html)
        return [urljoin(base_url, m.split("?")[0]) for m in matches]

    async def _probe_map(self, js_url: str) -> Finding | None:
        """Request ``<js_url>.map`` and check for a valid source map body.

        Args:
            js_url: Absolute URL of a JavaScript bundle file.

        Returns:
            A Finding if the source map is accessible, or ``None``.
        """
        map_url = f"{js_url}.map"
        response = await self.fetch_target(map_url)
        if response is None or response.status_code != 200:
            return None
        if _SOURCEMAP_SIGNATURE not in response.text:
            return None

        return Finding(
            category=self.CATEGORY,
            severity="medium",
            title="Exposed JavaScript Source Map",
            description=(
                "A JavaScript source map file is publicly accessible. "
                "It contains the original, unminified source code including "
                "comments, variable names, and potentially hardcoded secrets."
            ),
            evidence=f"Source map accessible at {map_url}",
            remediation=(
                "Remove source maps from production builds or restrict access "
                "to .map files at the web server level."
            ),
        )
