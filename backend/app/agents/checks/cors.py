"""CORS check agent — detects permissive Cross-Origin Resource Sharing policies."""

from __future__ import annotations

from app.agents.checks.base import BaseCheckAgent
from app.agents.state import AgentState, Finding

# Origins to probe for CORS reflection
_PROBE_ORIGINS = [
    "https://evil.example.com",
    "null",
]


class CORSAgent(BaseCheckAgent):
    """Check for overly permissive CORS headers."""

    CATEGORY = "cors"

    async def run(self, state: AgentState) -> dict:
        """Send OPTIONS preflight requests with crafted origins and inspect headers.

        Args:
            state: Current agent state containing ``url``.

        Returns:
            State update dict with ``findings`` list.
        """
        url = state["url"]
        findings: list[Finding] = []

        for origin in _PROBE_ORIGINS:
            result = await self._probe_cors(url, origin)
            if result:
                findings.append(result)

        return {"findings": findings}

    async def _probe_cors(self, url: str, origin: str) -> Finding | None:
        """Send a preflight request with a crafted Origin and inspect the response.

        Args:
            url: The target URL.
            origin: The spoofed origin to send.

        Returns:
            A Finding if CORS is misconfigured, or ``None``.
        """
        response = await self.fetch_target(
            url,
            method="OPTIONS",
            extra_headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        if response is None:
            return None

        headers = {k.lower(): v for k, v in response.headers.items()}
        acao = headers.get("access-control-allow-origin", "")
        acac = headers.get("access-control-allow-credentials", "").lower()

        if acao == "*" and acac == "true":
            return Finding(
                category=self.CATEGORY,
                severity="critical",
                title="Wildcard CORS With Credentials",
                description=(
                    "The server returns Access-Control-Allow-Origin: * combined "
                    "with Access-Control-Allow-Credentials: true, which browsers "
                    "block but can indicate a server-side misconfiguration."
                ),
                evidence=f"ACAO: {acao}, ACAC: {acac}",
                remediation="Use an explicit origin allowlist; never combine wildcard with credentials.",
            )

        if acao == origin and origin != "null":
            return Finding(
                category=self.CATEGORY,
                severity="high",
                title="CORS Reflects Arbitrary Origin",
                description=(
                    f"The server reflected the crafted origin '{origin}' back "
                    "without validation, allowing any site to make authenticated requests."
                ),
                evidence=f"Sent Origin: {origin} → Received ACAO: {acao}",
                remediation="Validate the Origin header against an explicit allowlist.",
            )

        if acao == "null":
            return Finding(
                category=self.CATEGORY,
                severity="medium",
                title="CORS Allows Null Origin",
                description=(
                    "The server allows the 'null' origin, which is used by "
                    "sandboxed iframes and local files — a potential attack vector."
                ),
                evidence=f"ACAO: {acao}",
                remediation="Remove 'null' from the CORS origin allowlist.",
            )

        return None
