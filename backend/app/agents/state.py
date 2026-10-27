"""LangGraph agent state definition.

The ``AgentState`` TypedDict is the single shared data structure that flows
through every node in the scan graph.  All nodes read from and write to this
state; LangGraph merges per-node outputs using the ``add`` reducer on
``findings`` and ``raw_responses``.
"""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import add_messages
from typing_extensions import TypedDict


def _merge_list(existing: list, new: list) -> list:
    """Reducer that appends new items to the existing list.

    Args:
        existing: The current list value in state.
        new: New items returned by a node.

    Returns:
        The combined list.
    """
    return existing + new


class Finding(TypedDict):
    """Structured representation of a single vulnerability finding.

    Attributes:
        category: One of xss | headers | ssl | cors | cookies |
            map_files | env_exposure | subdomain.
        severity: One of critical | high | medium | low | info.
        title: Short human-readable title.
        description: Full explanation of the issue.
        evidence: Raw evidence string (HTTP header value, snippet, etc.).
        remediation: Actionable fix description.
    """

    category: str
    severity: str
    title: str
    description: str
    evidence: str
    remediation: str


class AgentState(TypedDict):
    """Shared state object passed between all LangGraph nodes.

    Attributes:
        url: The URL being scanned.
        raw_responses: Accumulated raw HTTP response data keyed by check name.
        findings: All findings collected across all check agents.
        rag_context: RAG-enriched context strings attached by the enricher node.
        report: Final structured JSON report produced by the report-writer node.
    """

    url: str
    raw_responses: Annotated[list[dict], _merge_list]
    findings: Annotated[list[Finding], _merge_list]
    rag_context: list[str]
    report: dict
