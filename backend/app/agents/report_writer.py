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


def _build_prompt(url: str, findings: list[dict], rag_context: list[str]) -> str:
    """Construct the LLM prompt from findings and RAG context.

    Args:
        url: The scanned URL.
        findings: List of Finding dicts.
        rag_context: RAG-retrieved context snippets.

    Returns:
        A formatted prompt string.
    """
    findings_text = json.dumps(findings, indent=2)
    context_text = "\n\n".join(rag_context) if rag_context else "No additional context available."

    return f"""You are a senior web-application security analyst. A vulnerability scan
was performed against: {url}

RAG KNOWLEDGE CONTEXT:
{context_text}

RAW FINDINGS (JSON):
{findings_text}

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
    risk_score = min(100, critical_count * 30 + high_count * 15)

    return {
        "url": url,
        "summary": (
            f"Scan completed. Found {len(findings)} issue(s) including "
            f"{critical_count} critical and {high_count} high severity."
        ),
        "risk_score": risk_score,
        "findings": sorted_findings,
        "recommendations": [
            f["remediation"]
            for f in sorted_findings[:3]
            if f.get("remediation")
        ],
    }


async def report_writer_node(state: AgentState) -> dict:
    """Call the LLM to generate a narrative report from findings + RAG context.

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

    if not findings:
        return {"report": _fallback_report(url, [])}

    prompt = _build_prompt(url, findings, rag_context)

    try:
        llm = get_llm()
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw_text = response.content if hasattr(response, "content") else str(response)
        report = _extract_json(raw_text)
        logger.info("[report_writer] LLM report generated successfully")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[report_writer] LLM call failed (%s) — using fallback report", exc)
        report = _fallback_report(url, findings)

    return {"report": report}
