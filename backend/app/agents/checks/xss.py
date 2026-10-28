"""XSS check agent — detects reflected XSS indicators in HTTP responses."""

from __future__ import annotations

import re

from app.agents.checks.base import BaseCheckAgent
from app.agents.state import AgentState, Finding

# Benign probe payloads — not executed, just reflected-detection markers.
_XSS_PROBES = [
    "<script>xsstest</script>",
    '"><img src=x onerror=xsstest>',
    "javascript:xsstest",
]

# Pattern to detect unencoded reflection of our marker string.
_REFLECTION_RE = re.compile(r"xsstest", re.IGNORECASE)

# Common security headers that mitigate XSS.
_XSS_HEADERS = {"content-security-policy", "x-xss-protection"}


class XSSAgent(BaseCheckAgent):
    """Check for reflected XSS indicators and missing XSS-mitigation headers."""

    CATEGORY = "xss"

    async def run(self, state: AgentState) -> dict:
        """Probe the target for reflected XSS and check CSP/X-XSS headers.

        Args:
            state: Current agent state containing ``url``.

        Returns:
            State update dict with ``findings`` list.
        """
        findings: list[Finding] = []
        url = state["url"]

        findings.extend(await self._check_reflection(url))
        findings.extend(self._check_headers_from_state(state))

        return {"findings": findings}

    async def _check_reflection(self, url: str) -> list[Finding]:
        """Append probe strings to the URL query and check for raw reflection.

        Args:
            url: The target URL.

        Returns:
            List of findings (empty if no reflection detected).
        """
        findings: list[Finding] = []
        base = url.rstrip("/")

        for probe in _XSS_PROBES:
            probe_url = f"{base}?q={probe}"
            response = await self.fetch_target(probe_url)
            if response is None:
                continue
            if _REFLECTION_RE.search(response.text):
                findings.append(
                    Finding(
                        category=self.CATEGORY,
                        severity="high",
                        title="Potential Reflected XSS",
                        description=(
                            "The application reflected an unencoded XSS probe "
                            "string back in the HTTP response body."
                        ),
                        evidence=f"Probe '{probe}' reflected in response from {probe_url}",
                        remediation=(
                            "Apply context-aware output encoding on all user-supplied "
                            "input before rendering it in HTML. Implement a strict "
                            "Content-Security-Policy header."
                        ),
                    )
                )
                break  # One finding per site is sufficient

        return findings

    def _check_headers_from_state(self, state: AgentState) -> list[Finding]:
        """Check XSS-mitigation headers from already-fetched raw responses.

        Args:
            state: Current agent state.

        Returns:
            List of findings for missing CSP header.
        """
        findings: list[Finding] = []
        for raw in state.get("raw_responses", []):
            headers = {k.lower() for k in raw.get("headers", {}).keys()}
            if "content-security-policy" not in headers:
                findings.append(
                    Finding(
                        category=self.CATEGORY,
                        severity="medium",
                        title="Missing Content-Security-Policy Header",
                        description=(
                            "No Content-Security-Policy header was found. "
                            "CSP is the primary browser-enforced defence against XSS."
                        ),
                        evidence="Header absent from response",
                        remediation=(
                            "Add a Content-Security-Policy header. Start with "
                            "'default-src \\'self\\';' and tighten iteratively."
                        ),
                    )
                )
            break  # Only check the first raw response

        return findings
