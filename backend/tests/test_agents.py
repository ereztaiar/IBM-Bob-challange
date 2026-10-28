"""Unit tests for individual check agents.

All outbound HTTP calls are mocked via ``unittest.mock.AsyncMock`` so no
real network traffic is generated.  Each test verifies that the agent
produces the correct finding structure given a crafted mock response.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import AgentState


def _make_state(url: str = "https://example.com") -> AgentState:
    """Build a minimal AgentState for testing.

    Args:
        url: URL to include in the state.

    Returns:
        An ``AgentState`` with safe defaults.
    """
    return AgentState(url=url, raw_responses=[], findings=[], rag_context=[], report={})


def _mock_response(
    status_code: int = 200,
    text: str = "",
    headers: dict | None = None,
) -> MagicMock:
    """Create a mock ``httpx.Response``.

    Args:
        status_code: HTTP status code.
        text: Response body text.
        headers: Response headers dict.

    Returns:
        A MagicMock configured as an httpx.Response.
    """
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = text
    mock.headers = MagicMock()
    mock.headers.items.return_value = list((headers or {}).items())
    mock.headers.__iter__ = lambda self: iter(headers or {})
    mock.headers.get_list = MagicMock(return_value=[])
    return mock


# ------------------------------------------------------------------ XSS Agent


@pytest.mark.asyncio
async def test_xss_agent_detects_reflection() -> None:
    """XSSAgent should produce a high-severity finding when probe is reflected."""
    from app.agents.checks.xss import XSSAgent

    agent = XSSAgent()
    state = _make_state()

    reflected_response = _mock_response(text="<html>xsstest</html>")

    with patch.object(agent, "fetch_target", new=AsyncMock(return_value=reflected_response)):
        result = await agent.run(state)

    findings = result["findings"]
    assert any(f["severity"] == "high" and "XSS" in f["title"] for f in findings)


@pytest.mark.asyncio
async def test_xss_agent_no_reflection() -> None:
    """XSSAgent should produce no high-severity finding when probe is not reflected."""
    from app.agents.checks.xss import XSSAgent

    agent = XSSAgent()
    state = _make_state()
    clean_response = _mock_response(text="<html>Hello World</html>")

    with patch.object(agent, "fetch_target", new=AsyncMock(return_value=clean_response)):
        result = await agent.run(state)

    findings = result["findings"]
    assert not any(f["severity"] == "high" and "Reflected XSS" in f["title"] for f in findings)


# ---------------------------------------------------------------- Headers Agent


@pytest.mark.asyncio
async def test_headers_agent_flags_missing_hsts() -> None:
    """HeadersAgent should flag HSTS missing when the header is absent."""
    from app.agents.checks.headers import HeadersAgent

    agent = HeadersAgent()
    state = _make_state()
    response = _mock_response(headers={"content-type": "text/html"})

    with patch.object(agent, "fetch_target", new=AsyncMock(return_value=response)):
        result = await agent.run(state)

    titles = [f["title"] for f in result["findings"]]
    assert any("Strict-Transport-Security" in t for t in titles)


@pytest.mark.asyncio
async def test_headers_agent_no_findings_when_all_present() -> None:
    """HeadersAgent should produce no findings when all security headers are set."""
    from app.agents.checks.headers import HeadersAgent

    agent = HeadersAgent()
    state = _make_state()
    all_headers = {
        "strict-transport-security": "max-age=31536000",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "geolocation=()",
        "content-type": "text/html",
    }
    response = _mock_response(headers=all_headers)

    with patch.object(agent, "fetch_target", new=AsyncMock(return_value=response)):
        result = await agent.run(state)

    assert result["findings"] == []


# ------------------------------------------------------------------ CORS Agent


@pytest.mark.asyncio
async def test_cors_agent_detects_reflected_origin() -> None:
    """CORSAgent should flag high severity when origin is reflected back."""
    from app.agents.checks.cors import CORSAgent

    agent = CORSAgent()
    state = _make_state()
    response = _mock_response(
        headers={"access-control-allow-origin": "https://evil.example.com"}
    )

    with patch.object(agent, "fetch_target", new=AsyncMock(return_value=response)):
        result = await agent.run(state)

    findings = result["findings"]
    assert any(f["severity"] == "high" for f in findings)


@pytest.mark.asyncio
async def test_cors_agent_no_finding_for_restricted_cors() -> None:
    """CORSAgent should produce no findings when CORS is restricted."""
    from app.agents.checks.cors import CORSAgent

    agent = CORSAgent()
    state = _make_state()
    response = _mock_response(headers={"access-control-allow-origin": "https://myapp.com"})

    with patch.object(agent, "fetch_target", new=AsyncMock(return_value=response)):
        result = await agent.run(state)

    assert result["findings"] == []


# --------------------------------------------------------------- Cookies Agent


@pytest.mark.asyncio
async def test_cookies_agent_flags_missing_httponly() -> None:
    """CookiesAgent should flag a cookie without the HttpOnly flag."""
    from app.agents.checks.cookies import CookiesAgent

    agent = CookiesAgent()
    state = _make_state()

    mock_resp = _mock_response()
    mock_resp.headers.items.return_value = [
        ("set-cookie", "session=abc123; Path=/; Secure; SameSite=Lax")
    ]
    mock_resp.headers.get_list.return_value = [
        "session=abc123; Path=/; Secure; SameSite=Lax"
    ]

    with patch.object(agent, "fetch_target", new=AsyncMock(return_value=mock_resp)):
        result = await agent.run(state)

    titles = [f["title"] for f in result["findings"]]
    assert any("HttpOnly" in t for t in titles)


# ------------------------------------------------------------ Map Files Agent


@pytest.mark.asyncio
async def test_map_files_agent_detects_exposed_map() -> None:
    """MapFilesAgent should flag a source map that returns valid map content."""
    from app.agents.checks.map_files import MapFilesAgent

    agent = MapFilesAgent()
    state = _make_state()
    html_response = _mock_response(
        text='<script src="/static/app.js"></script>'
    )
    map_response = _mock_response(
        text='{"version":3,"sources":["app.tsx"],"mappings":"..."}',
        status_code=200,
    )

    async def _side_effect(url, **kwargs):
        if url.endswith(".map"):
            return map_response
        return html_response

    with patch.object(agent, "fetch_target", new=AsyncMock(side_effect=_side_effect)):
        result = await agent.run(state)

    assert any("Source Map" in f["title"] for f in result["findings"])


# ----------------------------------------------------------- Env Exposure Agent


@pytest.mark.asyncio
async def test_env_exposure_agent_detects_exposed_env() -> None:
    """EnvExposureAgent should flag a .env file that contains credential patterns."""
    from app.agents.checks.env_exposure import EnvExposureAgent

    agent = EnvExposureAgent()
    state = _make_state()

    async def _side_effect(url, **kwargs):
        if "/.env" in url and not any(
            x in url for x in [".local", ".production", ".development"]
        ):
            return _mock_response(text="DB_PASSWORD=supersecret\nAPI_KEY=abc123")
        return _mock_response(status_code=404)

    with patch.object(agent, "fetch_target", new=AsyncMock(side_effect=_side_effect)):
        result = await agent.run(state)

    assert any(f["severity"] == "critical" for f in result["findings"])


# ----------------------------------------------------------------- Report Writer


@pytest.mark.asyncio
async def test_report_writer_fallback_on_llm_failure() -> None:
    """report_writer_node should return a fallback report when the LLM is unavailable."""
    from app.agents.report_writer import report_writer_node

    state = _make_state()
    state["findings"] = [
        {
            "category": "headers",
            "severity": "high",
            "title": "Missing HSTS",
            "description": "desc",
            "evidence": "ev",
            "remediation": "Fix it",
        }
    ]

    with patch("app.agents.report_writer.get_llm", side_effect=Exception("Ollama offline")):
        result = await report_writer_node(state)

    report = result["report"]
    assert "url" in report
    assert "findings" in report
    assert len(report["findings"]) == 1
