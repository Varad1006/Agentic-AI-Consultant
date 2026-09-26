"""LangGraph workflow: a sequential pipeline that stops at the first agent that fails."""

from typing import Callable, Dict, Optional

from langgraph.graph import END, START, StateGraph

from app import nodes
from app.state import ConsultantState

# Order matters: each agent builds on the previous agents' output.
PIPELINE = ("retriever", "analyst", "architect", "roi", "report")

DEFAULT_NODES: Dict[str, Callable[[ConsultantState], dict]] = {
    "retriever": nodes.retriever_node,
    "analyst": nodes.analyst_node,
    "architect": nodes.architect_node,
    "roi": nodes.roi_node,
    "report": nodes.report_node,
}


def _continue_unless_failed(state: ConsultantState) -> str:
    return "stop" if state.get("errors") else "continue"


def build_graph(node_functions: Optional[Dict[str, Callable[[ConsultantState], dict]]] = None):
    node_functions = node_functions or DEFAULT_NODES
    workflow = StateGraph(ConsultantState)

    for name in PIPELINE:
        workflow.add_node(name, node_functions[name])

    workflow.add_edge(START, PIPELINE[0])
    for current, following in zip(PIPELINE, PIPELINE[1:]):
        workflow.add_conditional_edges(
            current, _continue_unless_failed, {"continue": following, "stop": END}
        )
    workflow.add_edge(PIPELINE[-1], END)

    return workflow.compile()


def next_stage(stage: str) -> Optional[str]:
    index = PIPELINE.index(stage)
    return PIPELINE[index + 1] if index + 1 < len(PIPELINE) else None
