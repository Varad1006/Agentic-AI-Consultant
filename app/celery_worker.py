"""Celery worker that runs the consulting pipeline and records progress in the job store."""

import logging
from typing import Any, Dict, List

from celery import Celery
from pydantic import BaseModel

from app import storage
from app.config import settings
from app.graph import PIPELINE, build_graph, next_stage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery(
    "consultant",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    # Fail fast when Redis is down, so the API can tell the user instead of hanging.
    broker_connection_timeout=2,
    task_publish_retry_policy={"max_retries": 1, "interval_start": 0, "interval_step": 0.5, "interval_max": 0.5},
    result_backend_transport_options={
        "retry_policy": {"max_retries": 1, "interval_start": 0, "interval_step": 0.5, "interval_max": 0.5}
    },
)

pipeline = build_graph()


def _dump(value: Any) -> Any:
    return value.model_dump() if isinstance(value, BaseModel) else value


def serialize_result(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "analysis": _dump(state.get("analysis_result")),
        "architecture": _dump(state.get("architecture_plan")),
        "roi": _dump(state.get("roi_result")),
        "report": _dump(state.get("final_report")),
    }


@celery_app.task(name="consultant.run_consulting_job")
def run_consulting_job(job_id: str, document_text: str) -> Dict[str, Any]:
    logger.info("[%s] Starting consulting pipeline (%d characters)", job_id, len(document_text))
    storage.update_job(job_id, status="running", stage=PIPELINE[0])

    final_state: Dict[str, Any] = {}
    completed: List[str] = []
    try:
        initial_state = {"job_id": job_id, "client_document_text": document_text, "errors": []}
        for mode, chunk in pipeline.stream(initial_state, stream_mode=["updates", "values"]):
            if mode == "values":
                final_state = chunk
                continue
            for node_name, update in chunk.items():
                if (update or {}).get("errors"):
                    logger.warning("[%s] %s failed: %s", job_id, node_name, update["errors"])
                    storage.update_job(job_id, stage=None, failed_stage=node_name)
                else:
                    completed.append(node_name)
                    logger.info("[%s] %s finished", job_id, node_name)
                    storage.update_job(job_id, stage=next_stage(node_name), completed_stages=list(completed))
    except Exception as exc:
        logger.exception("[%s] Pipeline crashed", job_id)
        storage.update_job(job_id, status="failed", stage=None, errors=[f"Unexpected error: {exc}"])
        raise

    errors = final_state.get("errors", [])
    result = serialize_result(final_state)
    status = "completed" if not errors and result["report"] else "failed"
    storage.update_job(job_id, status=status, stage=None, errors=errors, result=result)
    logger.info("[%s] Pipeline %s", job_id, status)
    return {"job_id": job_id, "status": status}
