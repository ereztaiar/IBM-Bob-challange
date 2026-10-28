"""SSL/TLS check agent — validates certificate and protocol configuration."""

from __future__ import annotations

import logging
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.agents.checks.base import BaseCheckAgent
from app.agents.state import AgentState, Finding

logger = logging.getLogger(__name__)

# Protocols considered insecure (Python ssl module constants)
_WEAK_PROTOCOLS = {
    "SSLv2",
    "SSLv3",
    "TLSv1",
    "TLSv1.1",
}

# Days before expiry that we flag as "expiring soon"
_EXPIRY_WARNING_DAYS = 30


def _get_cert_info(hostname: str, port: int = 443) -> dict | None:
    """Open a TLS connection and retrieve certificate metadata.

    Args:
        hostname: The hostname to connect to.
        port: The port to use (default 443).

    Returns:
        A dict with ``protocol``, ``cipher``, ``not_after``, and ``subject``
        keys, or ``None`` if the connection failed.
    """
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                return {
                    "protocol": ssock.version(),
                    "cipher": ssock.cipher(),
                    "not_after": cert.get("notAfter", ""),
                    "subject": dict(x[0] for x in cert.get("subject", [])),
                }
    except ssl.SSLCertVerificationError as exc:
        return {"error": f"Certificate verification failed: {exc}"}
    except (OSError, ssl.SSLError) as exc:
        logger.warning("[ssl] Could not connect to %s:%d — %s", hostname, port, exc)
        return None


def _check_expiry(not_after: str) -> Finding | None:
    """Return a finding if the certificate is expired or expiring soon.

    Args:
        not_after: The ``notAfter`` string from the certificate.

    Returns:
        A Finding or ``None``.
    """
    try:
        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None

    now = datetime.now(timezone.utc)
    delta = expiry - now

    if delta.days < 0:
        return Finding(
            category="ssl",
            severity="critical",
            title="SSL Certificate Expired",
            description=f"The certificate expired on {not_after}.",
            evidence=f"notAfter={not_after}",
            remediation="Renew the certificate immediately.",
        )
    if delta.days < _EXPIRY_WARNING_DAYS:
        return Finding(
            category="ssl",
            severity="high",
            title="SSL Certificate Expiring Soon",
            description=f"Certificate expires in {delta.days} days ({not_after}).",
            evidence=f"notAfter={not_after}",
            remediation=f"Renew the certificate before {not_after}.",
        )
    return None


class SSLTLSAgent(BaseCheckAgent):
    """Inspect SSL/TLS certificate validity and protocol version."""

    CATEGORY = "ssl"

    async def run(self, state: AgentState) -> dict:
        """Connect to the target over TLS and audit the certificate.

        Only runs for HTTPS URLs; HTTP URLs produce an informational finding.

        Args:
            state: Current agent state containing ``url``.

        Returns:
            State update dict with ``findings`` list.
        """
        url = state["url"]
        parsed = urlparse(url)
        findings: list[Finding] = []

        if parsed.scheme != "https":
            findings.append(
                Finding(
                    category=self.CATEGORY,
                    severity="high",
                    title="Site Not Served Over HTTPS",
                    description="The target URL uses HTTP instead of HTTPS.",
                    evidence=f"scheme={parsed.scheme}",
                    remediation="Redirect all HTTP traffic to HTTPS and enable HSTS.",
                )
            )
            return {"findings": findings}

        hostname = parsed.hostname or ""
        cert_info = _get_cert_info(hostname)

        if cert_info is None:
            return {"findings": [self._error_finding("Could not establish TLS connection.")]}

        if "error" in cert_info:
            findings.append(
                Finding(
                    category=self.CATEGORY,
                    severity="critical",
                    title="Invalid SSL Certificate",
                    description=cert_info["error"],
                    evidence=cert_info["error"],
                    remediation="Obtain a valid certificate from a trusted CA.",
                )
            )
            return {"findings": findings}

        expiry_finding = _check_expiry(cert_info.get("not_after", ""))
        if expiry_finding:
            findings.append(expiry_finding)

        protocol = cert_info.get("protocol", "")
        if protocol in _WEAK_PROTOCOLS:
            findings.append(
                Finding(
                    category=self.CATEGORY,
                    severity="high",
                    title=f"Deprecated TLS Protocol in Use: {protocol}",
                    description=f"The server negotiated {protocol}, which is considered insecure.",
                    evidence=f"Negotiated protocol: {protocol}",
                    remediation="Disable all TLS versions below 1.2. Support only TLS 1.2 and 1.3.",
                )
            )

        if not findings:
            findings.append(
                Finding(
                    category=self.CATEGORY,
                    severity="info",
                    title="SSL/TLS Configuration Looks Good",
                    description=f"Certificate is valid. Protocol: {protocol}.",
                    evidence=f"notAfter={cert_info.get('not_after')}",
                    remediation="No action required.",
                )
            )

        return {"findings": findings}
