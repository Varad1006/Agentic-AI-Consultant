from langgraph.graph import StateGraph, END
from app.state import ConsultantState
from app.nodes import analyst_node, architect_node

def build_consultant_graph():
    workflow = StateGraph(ConsultantState)

    # Add nodes
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("architect", architect_node)

    # Define edges (Sequential execution)
    workflow.set_entry_point("analyst")
    workflow.add_edge("analyst", "architect")
    workflow.add_edge("architect", END)

    # Compile the graph
    return workflow.compile()

# Instantiate for use
consultant_app = build_consultant_graph()