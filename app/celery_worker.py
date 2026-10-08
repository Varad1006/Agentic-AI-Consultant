"""Celery worker that runs the consulting pipeline and records progress in the job store."""

import logging
from celery import Celery

from app.config import settings
from app.runner import run_consulting_job as run_pipeline

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

run_consulting_job = celery_app.task(name="consultant.run_consulting_job")(run_pipeline)
