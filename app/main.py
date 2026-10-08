import logging
import threading
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import advisor, report, storage, vector_store
from app.config import settings
from app.documents import DocumentError, extract_text, prepare_text
from app.llm import describe_llm_error

if settings.demo_mode:
    from app.runner import run_consulting_job
else:
    from celery.result import AsyncResult
    from app.celery_worker import celery_app, run_consulting_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_demo_slot = threading.BoundedSemaphore(1)
_demo_job_id = None

app = FastAPI(title="Autonomous AI Consultant API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints are plain `def` on purpose: parsing, embedding and LLM calls are blocking, and
# FastAPI runs sync endpoints in a thread pool instead of on the event loop.


class ConsultRequest(BaseModel):
    document_text: str = Field(min_length=1)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.get("/api/v1/health")
def health_check() -> Dict[str, Any]:
    if settings.demo_mode:
        workers, celery_status = 0, "disabled"
    else:
        try:
            workers = len(celery_app.control.ping(timeout=1.0))
            celery_status = "connected" if workers else "no_workers"
        except Exception as exc:
            logger.warning("Celery ping failed: %s", exc)
            workers, celery_status = 0, "unreachable"

    return {
        "status": "ok",
        "execution_mode": "demo" if settings.demo_mode else "celery",
        "celery": celery_status,
        "workers": workers,
        "llm": {
            "provider": "groq",
            "model": settings.groq_model,
            "configured": bool(settings.groq_api_key),
        },
    }


@app.post("/api/v1/upload", status_code=202)
def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Accepts a PDF, DOCX, TXT, MD or CSV file and starts the consulting pipeline."""
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"The file is larger than the {settings.max_upload_mb} MB limit.")

    try:
        text = extract_text(file.filename or "", data)
    except DocumentError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _start_job(text, source="upload", filename=file.filename)


@app.post("/api/v1/consult", status_code=202)
def submit_text(request: ConsultRequest) -> Dict[str, Any]:
    """Starts the consulting pipeline on pasted text."""
    return _start_job(request.document_text, source="text", filename=None)


@app.get("/api/v1/consult/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    """Status, progress, results and chat history for a job."""
    return _load_job(job_id)


@app.get("/api/v1/consult/{job_id}/report")
def get_report(job_id: str) -> Dict[str, Any]:
    """The finished report as Markdown."""
    job = _load_job(job_id)
    if job["status"] != "completed":
        raise HTTPException(409, "The report isn't ready yet.")
    return {"job_id": job_id, "format": "markdown", "content": report.render_markdown(job)}


@app.post("/api/v1/consult/{job_id}/chat")
def chat_with_consultant(job_id: str, request: ChatRequest) -> Dict[str, Any]:
    """Ask the consultant a follow-up question about a finished report."""
    job = _load_job(job_id)
    if job["status"] != "completed":
        raise HTTPException(409, "The consultant is available once the report is ready.")

    question = request.question.strip()
    try:
        answer = advisor.answer_question(job, question)
    except Exception as exc:
        logger.exception("Chat failed for job %s", job_id)
        raise HTTPException(502, describe_llm_error(exc)) from exc

    job = storage.append_chat(
        job_id, [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
    )
    return {"job_id": job_id, "answer": answer, "chat": job["chat"]}


def _start_job(raw_text: str, *, source: str, filename: Optional[str]) -> Dict[str, Any]:
    try:
        text, truncated = prepare_text(raw_text)
    except DocumentError as exc:
        raise HTTPException(400, str(exc)) from exc

    if settings.demo_mode:
        if not _demo_slot.acquire(blocking=False):
            raise HTTPException(429, "The demo is processing another analysis. Please try again shortly.")
        try:
            return _create_and_dispatch(text, truncated, source=source, filename=filename)
        except Exception:
            _demo_slot.release()
            raise
    return _create_and_dispatch(text, truncated, source=source, filename=filename)


def _run_demo_job(job_id: str, text: str) -> None:
    global _demo_job_id
    try:
        run_consulting_job(job_id, text)
    except Exception:
        logger.exception("Demo analysis failed for job %s", job_id)
        storage.update_job(job_id, status="failed", stage=None, errors=["The analysis stopped unexpectedly. Please try again."])
    finally:
        _demo_job_id = None
        _demo_slot.release()


def _create_and_dispatch(text: str, truncated: bool, *, source: str, filename: Optional[str]) -> Dict[str, Any]:
    global _demo_job_id
    job_id = str(uuid.uuid4())
    try:
        chunks = vector_store.ingest_document(job_id, text)
    except Exception as exc:
        logger.exception("Failed to index document for job %s", job_id)
        raise HTTPException(500, f"Could not index the document: {exc}") from exc

    job = storage.create_job(
        job_id, source=source, filename=filename, characters=len(text), truncated=truncated
    )
    try:
        if settings.demo_mode:
            _demo_job_id = job_id
            threading.Thread(target=_run_demo_job, args=(job_id, text), daemon=True).start()
        else:
            run_consulting_job.apply_async(args=[job_id, text], task_id=job_id)
    except Exception as exc:
        logger.exception("Failed to queue job %s", job_id)
        message = "Could not start the analysis. Please try again." if settings.demo_mode else "Could not reach the task queue. Is Redis running?"
        if settings.demo_mode:
            _demo_job_id = None
        storage.update_job(job_id, status="failed", errors=[message])
        raise HTTPException(503, message) from exc

    logger.info("Queued job %s (%d characters, %d chunks)", job_id, len(text), chunks)
    return {"job_id": job_id, "status": job["status"]}


def _load_job(job_id: str) -> Dict[str, Any]:
    job = storage.load_job(job_id) if storage.is_valid_job_id(job_id) else None
    if job is None:
        raise HTTPException(404, "Job not found.")

    # If the worker died mid-run, the job file never got its final status; ask Celery.
    if job["status"] in ("queued", "running"):
        if settings.demo_mode:
            if job_id != _demo_job_id:
                # The worker may have finished after the first read of this file.
                job = storage.load_job(job_id)
                if job["status"] in ("queued", "running"):
                    job = storage.update_job(
                        job_id, status="failed", stage=None,
                        errors=["The demo restarted during this analysis. Please start a new one."],
                    )
            return job
        try:
            crashed = AsyncResult(job_id, app=celery_app).state == "FAILURE"
        except Exception:
            crashed = False
        if crashed:
            job = storage.update_job(
                job_id,
                status="failed",
                stage=None,
                errors=job["errors"] or ["The worker stopped unexpectedly while processing this job."],
            )
    return job
