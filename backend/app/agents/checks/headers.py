"""Security headers check agent.

Checks for the presence and basic correctness of the most important
HTTP security response headers.
"""

from __future__ import annotations

from app.agents.checks.base import BaseCheckAgent
from app.agents.state import AgentState, Finding

# (header_name, severity_if_missing, title, description, remediation)
_REQUIRED_HEADERS: list[tuple[str, str, str, str, str]] = [
    (
        "strict-transport-security",
        "high",
        "Missing Strict-Transport-Security (HSTS)",
        "HSTS is absent. Browsers may connect over HTTP, enabling downgrade attacks.",
        "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' to all HTTPS responses.",
    ),
    (
        "x-content-type-options",
        "medium",
        "Missing X-Content-Type-Options Header",
        "Without 'nosniff', browsers may MIME-sniff responses and execute unexpected scripts.",
        "Add 'X-Content-Type-Options: nosniff' to all responses.",
    ),
    (
        "x-frame-options",
        "medium",
        "Missing X-Frame-Options Header",
        "Without X-Frame-Options or a CSP frame-ancestors directive the page may be framed (clickjacking).",
        "Add 'X-Frame-Options: DENY' or use CSP 'frame-ancestors \\'none\\''.",
    ),
    (
        "referrer-policy",
        "low",
        "Missing Referrer-Policy Header",
        "Without Referrer-Policy, sensitive URL fragments may be leaked to third-party sites.",
        "Add 'Referrer-Policy: strict-origin-when-cross-origin'.",
    ),
    (
        "permissions-policy",
        "low",
        "Missing Permissions-Policy Header",
        "Browser feature access (camera, microphone, geolocation) is unrestricted.",
        "Add a Permissions-Policy header restricting unused browser features.",
    ),
]


class HeadersAgent(BaseCheckAgent):
    """Check for the presence of critical HTTP security headers."""

    CATEGORY = "headers"

    async def run(self, state: AgentState) -> dict:
        """Fetch the root URL and audit security headers in the response.

        Args:
            state: Current agent state containing ``url``.

        Returns:
            State update dict with ``findings`` and ``raw_responses``.
        """
        url = state["url"]
        response = await self.fetch_target(url)

        if response is None:
            return {"findings": [self._error_finding("Could not fetch target URL.")],
                    "raw_responses": []}

        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        raw = {"check": self.CATEGORY, "url": url, "headers": dict(response.headers)}
        findings = self._audit_headers(headers_lower)

        return {"findings": findings, "raw_responses": [raw]}

    def _audit_headers(self, headers: dict[str, str]) -> list[Finding]:
        """Compare response headers against the required-headers list.

        Args:
            headers: Response headers with lower-cased keys.

        Returns:
            A finding for every missing or misconfigured header.
        """
        findings: list[Finding] = []
        for name, severity, title, description, remediation in _REQUIRED_HEADERS:
            if name not in headers:
                findings.append(
                    Finding(
                        category=self.CATEGORY,
                        severity=severity,
                        title=title,
                        description=description,
                        evidence=f"Header '{name}' absent from response",
                        remediation=remediation,
                    )
                )
        return findings
