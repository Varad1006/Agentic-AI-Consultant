"""
Celery Worker for AI Consultant App
Handles background task execution using LangGraph workflow
"""

import os
import logging
from celery import Celery
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from app.consultant_memory import save_consulting_memory

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import nodes and state
from app.state import ConsultantState
from app.nodes import (
    planner_node,
    analyst_node,
    architect_node,
    roi_calculator_node,
    report_generator_node
)

# ============================================================================
# 1. BUILD LANGGRAPH WORKFLOW 
# ============================================================================

workflow = StateGraph(ConsultantState)

workflow.add_node("planner", planner_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("architect", architect_node)
workflow.add_node("roi_calculator", roi_calculator_node)
workflow.add_node("report_generator", report_generator_node)

# 1. Linear Start
workflow.set_entry_point("planner")
workflow.add_edge("planner", "analyst")

# 2. THE FAN-OUT (Parallel Execution)
# Both agents start simultaneously the moment the Analyst finishes
workflow.add_edge("analyst", "architect")
workflow.add_edge("analyst", "roi_calculator")

# 3. THE FAN-IN (Synchronization)
# The Report Generator waits for BOTH parallel nodes to finish before starting
workflow.add_edge(["architect", "roi_calculator"], "report_generator")

# 4. Finish
workflow.add_edge("report_generator", END)

app_graph = workflow.compile()

# ============================================================================
# 2. CONFIGURE CELERY
# ============================================================================

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_BACKEND_URL = os.getenv('CELERY_BACKEND_URL', 'redis://redis:6379/0')

logger.info(f"Celery Broker: {CELERY_BROKER_URL}")
logger.info(f"Celery Backend: {CELERY_BACKEND_URL}")

celery_app = Celery(
    "consultant_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,  # Track when tasks start
    task_time_limit=30 * 60,  # 30 minute hard limit
    task_soft_time_limit=25 * 60,  # 25 minute soft limit
)

logger.info("✅ Celery configured successfully")

# ============================================================================
# 3. CELERY TASK DEFINITION
# ============================================================================

def convert_pydantic_to_dict(obj):
    """
    Converts Pydantic model to dict, handling both Pydantic v1 and v2.
    
    Pydantic v1: uses .dict()
    Pydantic v2: uses .model_dump()
    """
    if obj is None:
        return None
    
    # Try Pydantic v2 first
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    # Fall back to Pydantic v1
    elif hasattr(obj, 'dict'):
        return obj.dict()
    # If not a Pydantic model, return as-is
    else:
        return obj


@celery_app.task(bind=True, name='app.celery_worker.run_consulting_job')
def run_consulting_job(self, document_text: str):
    """
    Background task that executes the consulting workflow.
    
    Args:
        document_text (str): The client's operational documentation
        
    Returns:
        dict: Results from all 5 agents
    """
    job_id = self.request.id
    logger.info(f"[{job_id}] 🚀 Starting consulting job")
    logger.info(f"[{job_id}] Document length: {len(document_text)} characters")
    
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'current': 'Initializing workflow...'})
        
        # =====================================================================
        # INITIALIZE STATE WITH ALL REQUIRED FIELDS
        # =====================================================================
        initial_state = {
            "job_id": job_id,
            "client_document_text": document_text,
            "analysis_result": None,
            "architecture_plan": None,
            "roi_result": None,              # ✅ ADDED: Was missing
            "final_report": None,            # ✅ ADDED: For completeness
            "errors": []
        }
        
        logger.info(f"[{job_id}] 📋 Initial state prepared")
        logger.info(f"[{job_id}] ⏳ Starting workflow execution...")
        
        # =====================================================================
        # EXECUTE WORKFLOW
        # =====================================================================
        final_state = app_graph.invoke(initial_state)
        
        logger.info(f"[{job_id}] ✅ Workflow completed")
        logger.info(f"[{job_id}] Errors: {final_state.get('errors', [])}")
        
        # =====================================================================
        # SERIALIZE RESULTS FOR CELERY
        # =====================================================================
        
        # Check if workflow had errors
        if final_state.get("errors"):
            logger.warning(f"[{job_id}] ⚠️  Workflow completed with errors: {final_state['errors']}")
        
        # Convert Pydantic models to dicts (handles both Pydantic v1 and v2)
        result = {
            "analysis": convert_pydantic_to_dict(final_state.get("analysis_result")),
            "architecture": convert_pydantic_to_dict(final_state.get("architecture_plan")),
            "roi": convert_pydantic_to_dict(final_state.get("roi_result")),
            "report": convert_pydantic_to_dict(final_state.get("final_report")),
            "errors": final_state.get("errors", [])
        }
        logger.info(f"[{job_id}] 💾 Saving consulting memory...")
        save_consulting_memory(job_id=job_id, result=result)
        logger.info(f"[{job_id}] ✅ Consulting memory saved")
        logger.info(f"[{job_id}] 📊 Results serialized successfully")
        # logger.info(f"[{job_id}] Result keys: {list(result.keys())}")
        
        return result
        
    except Exception as e:
        logger.error(f"[{job_id}] ❌ TASK FAILED: {str(e)}", exc_info=True)
        
        # Return error result
        return {
            "analysis": None,
            "architecture": None,
            "roi": None,
            "report": None,
            "errors": [f"Workflow execution failed: {str(e)}"]
        }


@celery_app.task(bind=True)
def test_celery_connection(self):
    """
    Simple test task to verify Celery is working.
    
    Run with:
        celery -A app.celery_worker call test_celery_connection
    """
    logger.info(f"[TEST] Celery connection test - Task ID: {self.request.id}")
    return {
        "status": "ok",
        "message": "Celery is connected and working!",
        "task_id": self.request.id
    }


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

logger.info("=" * 70)
logger.info("🎯 CELERY WORKER READY")
logger.info("=" * 70)
logger.info("Start worker with:")
logger.info("  celery -A app.celery_worker worker --loglevel=info")
logger.info("=" * 70)