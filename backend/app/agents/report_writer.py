"""Report writer node — generates the final structured report via the LLM.

Takes all findings and RAG context from state, builds a structured prompt,
calls the Ollama LLM, and parses the JSON response into the ``report`` field.
"""

from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage

from app.agents.llm_factory import get_llm
from app.agents.state import AgentState

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]+?)\s*```", re.IGNORECASE)


def _build_prompt(
    url: str,
    findings: list[dict],
    rag_context: list[str],
    user_prompt: str | None = None,
) -> str:
    """Construct the LLM prompt from findings, RAG context, and an optional user focus hint.

    When ``user_prompt`` is provided the LLM is instructed to pay particular
    attention to that area of the target site.  The block is inserted between
    the raw findings and the output-format instruction so the LLM sees it as
    context before receiving the schema constraint.

    Args:
        url: The scanned URL.
        findings: List of Finding dicts.
        rag_context: RAG-retrieved context snippets.
        user_prompt: Optional sanitised focus hint from the user.

    Returns:
        A formatted prompt string.
    """
    findings_text = json.dumps(findings, indent=2)
    context_text = "\n\n".join(rag_context) if rag_context else "No additional context available."

    user_focus_block = ""
    if user_prompt:
        user_focus_block = f"\nUSER FOCUS REQUEST:\n{user_prompt}\n"

    return f"""You are a senior web-application security analyst. A vulnerability scan
was performed against: {url}

RAG KNOWLEDGE CONTEXT:
{context_text}

RAW FINDINGS (JSON):
{findings_text}
{user_focus_block}
Based on the findings and context above, produce a structured security report.
Your response MUST be valid JSON matching this exact schema:
{{
  "url": "<scanned url>",
  "summary": "<2-3 sentence executive summary>",
  "risk_score": <integer 0-100>,
  "findings": [
    {{
      "category": "<category>",
      "severity": "<critical|high|medium|low|info>",
      "title": "<title>",
      "description": "<description>",
      "evidence": "<evidence>",
      "remediation": "<remediation>"
    }}
  ],
  "recommendations": ["<top recommendation 1>", "<top recommendation 2>"]
}}

Respond with ONLY the JSON object. Do not include any text outside the JSON."""


def _extract_json(raw: str) -> dict:
    """Extract and parse a JSON object from the LLM response.

    Handles responses with or without markdown code fences.

    Args:
        raw: Raw LLM response string.

    Returns:
        Parsed JSON dict.

    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    # Try fenced block first
    match = _JSON_FENCE_RE.search(raw)
    if match:
        return json.loads(match.group(1))

    # Try the whole string
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Last resort: find first { ... } block
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        return json.loads(raw[start:end])

    raise ValueError(f"No JSON found in LLM response: {raw[:200]}")


# Severity weights used by _compute_risk_score.  Module-level so they are
# easy to tune without hunting inside function bodies.
_SEVERITY_WEIGHTS: dict[str, int] = {
    "critical": 30,
    "high": 15,
    "medium": 7,
    "low": 3,
    "info": 0,
}


def _compute_risk_score(findings: list[dict]) -> int:
    """Compute a deterministic risk score (0–100) from a list of findings.

    Each finding contributes its severity weight.  The result is clamped to
    100 so callers never need to guard against out-of-range values.

    Args:
        findings: List of Finding dicts, each expected to have a ``severity`` key.

    Returns:
        Integer risk score in the range [0, 100].
    """
    total = sum(_SEVERITY_WEIGHTS.get(f.get("severity", "info"), 0) for f in findings)
    return min(100, total)


def _fallback_report(url: str, findings: list[dict]) -> dict:
    """Build a minimal report from raw findings without LLM involvement.

    Used when the LLM call fails or returns unparseable output.

    Args:
        url: The scanned URL.
        findings: List of Finding dicts.

    Returns:
        A minimal structured report dict.
    """
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.get("severity", "info"), 4))
    critical_count = sum(1 for f in findings if f.get("severity") == "critical")
    high_count = sum(1 for f in findings if f.get("severity") == "high")

    return {
        "url": url,
        "summary": (
            f"Scan completed. Found {len(findings)} issue(s) including "
            f"{critical_count} critical and {high_count} high severity."
        ),
        "risk_score": _compute_risk_score(findings),
        "findings": sorted_findings,
        "recommendations": [
            f["remediation"]
            for f in sorted_findings[:3]
            if f.get("remediation")
        ],
    }


async def report_writer_node(state: AgentState) -> dict:
    """Call the LLM to generate a narrative report from findings + RAG context.

    The risk score is always computed deterministically from the findings via
    ``_compute_risk_score`` and injected into the final report — the LLM is
    never trusted to produce a numerically consistent score on its own.

    Falls back to a structured-but-narrative-free report if the LLM is
    unavailable or returns unparseable output.

    Args:
        state: Current agent state with ``url``, ``findings``, ``rag_context``.

    Returns:
        State update dict with ``report`` populated.
    """
    url = state["url"]
    findings = state.get("findings", [])
    rag_context = state.get("rag_context", [])
    user_prompt: str | None = state.get("user_prompt")  # type: ignore[assignment]

    # Compute once — injected into both the LLM and fallback paths.
    risk_score = _compute_risk_score(findings)

    if not findings:
        return {"report": _fallback_report(url, [])}

    prompt = _build_prompt(url, findings, rag_context, user_prompt)

    try:
        llm = get_llm()
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw_text = response.content if hasattr(response, "content") else str(response)
        report = _extract_json(raw_text)
        # Override whatever score the LLM produced with the deterministic one.
        report["risk_score"] = risk_score
        logger.info("[report_writer] LLM report generated successfully (risk_score=%d)", risk_score)
    except Exception as exc:  # noqa: BLE001
        logger.error("[report_writer] LLM call failed — using fallback report", exc_info=exc)
        report = _fallback_report(url, findings)

    return {"report": report}
