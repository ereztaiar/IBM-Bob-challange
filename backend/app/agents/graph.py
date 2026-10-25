"""LangGraph scan pipeline — wires all nodes into an executable graph.

Graph topology (simplified):

    START → supervisor
        → xss_check   ┐
        → headers_check│
        → ssl_check    │ (parallel fan-out)
        → cors_check   │
        → cookies_check│
        → map_files_check│
        → env_check    │
        → subdomain_check┘
        → rag_enricher
        → report_writer
    → END

All check-agent nodes run in parallel.  LangGraph collects their outputs
(merged via the ``_merge_list`` reducer on ``findings`` and ``raw_responses``)
before advancing to the RAG enricher.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app.agents.checks.cookies import CookiesAgent
from app.agents.checks.cors import CORSAgent
from app.agents.checks.env_exposure import EnvExposureAgent
from app.agents.checks.headers import HeadersAgent
from app.agents.checks.map_files import MapFilesAgent
from app.agents.checks.ssl_tls import SSLTLSAgent
from app.agents.checks.subdomain import SubdomainAgent
from app.agents.checks.xss import XSSAgent
from app.agents.rag_enricher import rag_enricher_node
from app.agents.report_writer import report_writer_node
from app.agents.state import AgentState
from app.agents.supervisor import supervisor_node

logger = logging.getLogger(__name__)

# Instantiate agents once — they are stateless between runs
_xss_agent = XSSAgent()
_headers_agent = HeadersAgent()
_ssl_agent = SSLTLSAgent()
_cors_agent = CORSAgent()
_cookies_agent = CookiesAgent()
_map_files_agent = MapFilesAgent()
_env_agent = EnvExposureAgent()
_subdomain_agent = SubdomainAgent()

# Node name constants (avoids string literals scattered across the file)
_SUPERVISOR = "supervisor"
_XSS = "xss_check"
_HEADERS = "headers_check"
_SSL = "ssl_check"
_CORS = "cors_check"
_COOKIES = "cookies_check"
_MAP_FILES = "map_files_check"
_ENV = "env_check"
_SUBDOMAIN = "subdomain_check"
_RAG = "rag_enricher"
_REPORT = "report_writer"

_CHECK_NODES = [_XSS, _HEADERS, _SSL, _CORS, _COOKIES, _MAP_FILES, _ENV, _SUBDOMAIN]


def build_scan_graph() -> StateGraph:
    """Construct and compile the LangGraph vulnerability scan pipeline.

    Returns:
        A compiled ``StateGraph`` ready to be invoked with an initial
        ``AgentState`` dict containing at minimum a ``url`` key.
    """
    graph = StateGraph(AgentState)

    # --- Register nodes ---
    graph.add_node(_SUPERVISOR, supervisor_node)
    graph.add_node(_XSS, _xss_agent.run)
    graph.add_node(_HEADERS, _headers_agent.run)
    graph.add_node(_SSL, _ssl_agent.run)
    graph.add_node(_CORS, _cors_agent.run)
    graph.add_node(_COOKIES, _cookies_agent.run)
    graph.add_node(_MAP_FILES, _map_files_agent.run)
    graph.add_node(_ENV, _env_agent.run)
    graph.add_node(_SUBDOMAIN, _subdomain_agent.run)
    graph.add_node(_RAG, rag_enricher_node)
    graph.add_node(_REPORT, report_writer_node)

    # --- Wire edges ---
    graph.add_edge(START, _SUPERVISOR)

    # Fan-out: supervisor → all check agents in parallel
    for node in _CHECK_NODES:
        graph.add_edge(_SUPERVISOR, node)

    # Fan-in: all check agents → rag enricher
    for node in _CHECK_NODES:
        graph.add_edge(node, _RAG)

    graph.add_edge(_RAG, _REPORT)
    graph.add_edge(_REPORT, END)

    compiled = graph.compile()
    logger.info("Scan graph compiled with %d check nodes", len(_CHECK_NODES))
    return compiled
