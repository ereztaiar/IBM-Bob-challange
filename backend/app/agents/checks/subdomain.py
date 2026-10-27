"""Subdomain takeover check agent.

Resolves the target hostname's CNAME chain and checks whether the ultimate
target appears to be an unclaimed third-party service resource.
"""

from __future__ import annotations

import socket
from urllib.parse import urlparse

from app.agents.checks.base import BaseCheckAgent
from app.agents.state import AgentState, Finding

# Service-specific fingerprints: (provider_name, domain_suffix, body_pattern)
# body_pattern is a substring that appears on "unclaimed resource" pages.
_TAKEOVER_FINGERPRINTS: list[tuple[str, str, str]] = [
    ("GitHub Pages", "github.io", "There isn't a GitHub Pages site here"),
    ("Heroku", "herokuapp.com", "No such app"),
    ("AWS S3", "s3.amazonaws.com", "NoSuchBucket"),
    ("Netlify", "netlify.app", "Not Found - Request ID"),
    ("Azure", "azurewebsites.net", "404 Web Site not found"),
    ("Fastly", "fastly.net", "Fastly error: unknown domain"),
    ("Surge.sh", "surge.sh", "project not found"),
    ("Cargo Collective", "cargocollective.com", "404 Not Found"),
]


def _resolve_cname(hostname: str) -> str | None:
    """Return the canonical hostname after following CNAME records.

    Uses ``getaddrinfo`` which follows the OS resolver chain.  We compare the
    resolved canonical name against known takeover-prone domains.

    Args:
        hostname: The hostname to resolve.

    Returns:
        The canonical hostname string, or ``None`` on resolution failure.
    """
    try:
        infos = socket.getaddrinfo(hostname, None, flags=socket.AI_CANONNAME)
        if infos:
            return infos[0][3] or hostname
    except socket.gaierror:
        return None
    return hostname


class SubdomainAgent(BaseCheckAgent):
    """Check whether the target hostname resolves to an unclaimed service resource."""

    CATEGORY = "subdomain"

    async def run(self, state: AgentState) -> dict:
        """Resolve the hostname and probe for known takeover fingerprints.

        Args:
            state: Current agent state containing ``url``.

        Returns:
            State update dict with ``findings`` list.
        """
        url = state["url"]
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        findings: list[Finding] = []

        canonical = _resolve_cname(hostname)
        if canonical is None:
            return {"findings": [self._error_finding(f"Could not resolve hostname '{hostname}'.")]}

        for provider, suffix, body_pattern in _TAKEOVER_FINGERPRINTS:
            if suffix in canonical:
                finding = await self._check_body(url, provider, suffix, body_pattern, canonical)
                if finding:
                    findings.append(finding)
                break

        return {"findings": findings}

    async def _check_body(
        self,
        url: str,
        provider: str,
        suffix: str,
        body_pattern: str,
        canonical: str,
    ) -> Finding | None:
        """Fetch the URL and look for an unclaimed-service body pattern.

        Args:
            url: The target URL.
            provider: Human-readable provider name.
            suffix: Domain suffix that triggered this check.
            body_pattern: String to look for in the response body.
            canonical: The resolved canonical hostname.

        Returns:
            A Finding if the takeover fingerprint is present, or ``None``.
        """
        response = await self.fetch_target(url)
        if response is None:
            return None
        if body_pattern.lower() in response.text.lower():
            return Finding(
                category=self.CATEGORY,
                severity="critical",
                title=f"Potential Subdomain Takeover via {provider}",
                description=(
                    f"The hostname resolves to {provider} ({suffix}) but the "
                    "resource appears unclaimed. An attacker could register it "
                    "and serve content under your domain."
                ),
                evidence=f"CNAME → {canonical}; body contains '{body_pattern}'",
                remediation=(
                    "Remove the stale DNS record immediately or re-provision "
                    f"the {provider} resource to reclaim the hostname."
                ),
            )
        return None
