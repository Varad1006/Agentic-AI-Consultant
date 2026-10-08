"""Shared consulting pipeline, callable by Celery or the single-process demo."""

import logging
from typing import Any, Dict, List

from pydantic import BaseModel

from app import storage
from app.graph import PIPELINE, build_graph, next_stage

logger = logging.getLogger(__name__)

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
