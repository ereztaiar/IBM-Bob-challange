"""Supervisor node — initialises state and fans out to check agents.

In the LangGraph graph the supervisor is the first node after START.  Its job
is to set default values on the state so downstream nodes never see missing keys.
The actual fan-out is wired structurally in ``graph.py`` — each check agent
is a separate node connected in parallel from the supervisor.
"""

from __future__ import annotations

from app.agents.state import AgentState


async def supervisor_node(state: AgentState) -> dict:
    """Initialise default state fields before the parallel check agents run.

    Args:
        state: Current shared agent state.

    Returns:
        State updates ensuring all keys have safe defaults.
    """
    return {
        "raw_responses": [],
        "findings": [],
        "rag_context": [],
        "report": {},
    }
