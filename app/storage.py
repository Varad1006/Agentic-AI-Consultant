"""Durable job records (status, progress, results and chat history) stored as JSON files.

Both the API and the Celery worker read and write these files, so they need a shared volume.
"""

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

_JOB_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def is_valid_job_id(job_id: str) -> bool:
    return bool(_JOB_ID.match(job_id))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _job_path(job_id: str) -> Path:
    if not is_valid_job_id(job_id):
        raise ValueError(f"Invalid job id: {job_id!r}")
    directory = settings.data_dir / "jobs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{job_id}.json"


def _write(job: Dict[str, Any]) -> None:
    path = _job_path(job["job_id"])
    # Write to a temp file and rename, so readers never see a half-written record.
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def create_job(
    job_id: str, *, source: str, filename: Optional[str], characters: int, truncated: bool
) -> Dict[str, Any]:
    job = {
        "job_id": job_id,
        "created_at": _now(),
        "updated_at": _now(),
        "source": source,
        "filename": filename,
        "characters": characters,
        "truncated": truncated,
        "status": "queued",
        "stage": None,
        "completed_stages": [],
        "failed_stage": None,
        "errors": [],
        "result": None,
        "chat": [],
    }
    _write(job)
    return job


def load_job(job_id: str) -> Optional[Dict[str, Any]]:
    try:
        with open(_job_path(job_id), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def update_job(job_id: str, **changes: Any) -> Dict[str, Any]:
    job = load_job(job_id)
    if job is None:
        raise KeyError(job_id)
    job.update(changes, updated_at=_now())
    _write(job)
    return job


def append_chat(job_id: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    job = load_job(job_id)
    if job is None:
        raise KeyError(job_id)
    stamped = [{**message, "created_at": _now()} for message in messages]
    return update_job(job_id, chat=job["chat"] + stamped)
