from celery import Celery
from app.graph import consultant_app
import json
from langgraph.graph import StateGraph, END
from app.state import ConsultantState
from app.nodes import planner_node, analyst_node, architect_node, roi_calculator_node, report_generator_node

workflow = StateGraph(ConsultantState)

# 1. Register all 5 agents
workflow.add_node("planner", planner_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("architect", architect_node)
workflow.add_node("roi_calculator", roi_calculator_node)
workflow.add_node("report_generator", report_generator_node)

# 2. Build the straight-line execution sequence
workflow.set_entry_point("planner")
workflow.add_edge("planner", "analyst")
workflow.add_edge("analyst", "architect")
workflow.add_edge("architect", "roi_calculator")
workflow.add_edge("roi_calculator", "report_generator")
workflow.add_edge("report_generator", END)

app_graph = workflow.compile()
# Configure Celery to use local Redis
celery_app = Celery(
    "consultant_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task(bind=True)
def run_consulting_job(self, document_text: str):
    # Initialize the state
    initial_state = {
        "job_id": self.request.id,
        "client_document_text": document_text,
        "analysis_result": None,
        "architecture_plan": None,
        "errors": []
    }
    
    # Execute the LangGraph
    final_state = app_graph.invoke(initial_state)
    
    # Celery requires JSON-serializable returns. 
    # Convert Pydantic objects to dicts if they exist.
    result = {
        "analysis": final_state.get("analysis_result").dict() if final_state.get("analysis_result") else None,
        "architecture": final_state.get("architecture_plan").dict() if final_state.get("architecture_plan") else None,
        "roi": final_state.get("roi_result").dict() if final_state.get("roi_result") else None,
        "report": final_state.get("final_report").dict() if final_state.get("final_report") else None,
        "errors": final_state.get("errors")
    }
    
    return result