"""Cookie flags check agent — audits Set-Cookie headers for security flags."""

from __future__ import annotations

from app.agents.checks.base import BaseCheckAgent
from app.agents.state import AgentState, Finding


def _parse_cookie_flags(set_cookie: str) -> dict[str, bool]:
    """Parse a Set-Cookie header value and extract security flag presence.

    Args:
        set_cookie: Raw ``Set-Cookie`` header string.

    Returns:
        Dict with boolean flags for ``httponly``, ``secure``, and ``samesite``.
    """
    parts = {p.strip().lower() for p in set_cookie.split(";")}
    return {
        "httponly": "httponly" in parts,
        "secure": "secure" in parts,
        "samesite": any(p.startswith("samesite") for p in parts),
    }


class CookiesAgent(BaseCheckAgent):
    """Inspect Set-Cookie headers for missing HttpOnly, Secure, and SameSite flags."""

    CATEGORY = "cookies"

    async def run(self, state: AgentState) -> dict:
        """Fetch the target URL and audit all Set-Cookie response headers.

        Args:
            state: Current agent state containing ``url``.

        Returns:
            State update dict with ``findings`` list.
        """
        url = state["url"]
        response = await self.fetch_target(url, follow_redirects=True)

        if response is None:
            return {"findings": [self._error_finding("Could not fetch target URL.")]}

        findings: list[Finding] = []
        cookies = response.headers.get_list("set-cookie") if hasattr(
            response.headers, "get_list"
        ) else [
            v for k, v in response.headers.items() if k.lower() == "set-cookie"
        ]

        if not cookies:
            return {"findings": findings}

        for cookie in cookies:
            findings.extend(self._audit_cookie(cookie))

        return {"findings": findings}

    def _audit_cookie(self, set_cookie: str) -> list[Finding]:
        """Produce findings for missing flags on a single cookie.

        Args:
            set_cookie: Raw ``Set-Cookie`` header value.

        Returns:
            List of findings (one per missing flag).
        """
        findings: list[Finding] = []
        name = set_cookie.split("=")[0].strip()
        flags = _parse_cookie_flags(set_cookie)

        if not flags["httponly"]:
            findings.append(
                Finding(
                    category=self.CATEGORY,
                    severity="high",
                    title=f"Cookie '{name}' Missing HttpOnly Flag",
                    description="Cookie is accessible via JavaScript; XSS can steal it.",
                    evidence=f"Set-Cookie: {set_cookie[:120]}",
                    remediation=f"Add the HttpOnly flag to cookie '{name}'.",
                )
            )
        if not flags["secure"]:
            findings.append(
                Finding(
                    category=self.CATEGORY,
                    severity="high",
                    title=f"Cookie '{name}' Missing Secure Flag",
                    description="Cookie may be transmitted over unencrypted HTTP connections.",
                    evidence=f"Set-Cookie: {set_cookie[:120]}",
                    remediation=f"Add the Secure flag to cookie '{name}'.",
                )
            )
        if not flags["samesite"]:
            findings.append(
                Finding(
                    category=self.CATEGORY,
                    severity="medium",
                    title=f"Cookie '{name}' Missing SameSite Attribute",
                    description="Cookie is sent with cross-site requests, enabling CSRF.",
                    evidence=f"Set-Cookie: {set_cookie[:120]}",
                    remediation=f"Add 'SameSite=Lax' or 'SameSite=Strict' to cookie '{name}'.",
                )
            )
        return findings
