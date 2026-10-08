"""Run in a fresh process with DEMO_MODE=true (see test_demo.py)."""

import sys
import threading
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from app import demo_store, main, storage, vector_store
from tests.conftest import SAMPLE_DOCUMENT


def wait_for_result(client, job_id):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        job = client.get(f"/api/v1/consult/{job_id}").json()
        if job["status"] not in ("queued", "running"):
            # Also wait for the worker's finally block to release admission.
            while main._demo_job_id == job_id and time.monotonic() < deadline:
                time.sleep(0.01)
            return job
        time.sleep(0.01)
    pytest.fail("Demo analysis did not finish")


def test_demo_needs_no_celery_redis_or_chroma():
    with TestClient(main.app) as client:
        health = client.get("/api/v1/health").json()
    assert health["execution_mode"] == "demo"
    assert health["celery"] == "disabled"
    assert all(name not in sys.modules for name in ("celery", "redis", "chromadb"))


def test_real_background_pipeline_report_and_chat(fake_llm, monkeypatch):
    with TestClient(main.app) as client:
        response = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT})
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        job = wait_for_result(client, job_id)
        assert job["status"] == "completed"
        assert job["completed_stages"] == ["retriever", "analyst", "architect", "roi", "report"]
        assert client.get(f"/api/v1/consult/{job_id}/report").json()["content"].startswith("# Executive Consulting Report")
        assert vector_store.search(job_id, "delivery routes")
        monkeypatch.setattr(main.advisor, "answer_question", lambda job, question: "Start with route planning.")
        response = client.post(f"/api/v1/consult/{job_id}/chat", json={"question": "Where do I start?"})
        assert response.status_code == 200
        assert len(storage.load_job(job_id)["chat"]) == 2


def test_busy_demo_rejects_another_job_and_releases_slot(fake_llm, monkeypatch):
    started, finish = threading.Event(), threading.Event()
    original = main.run_consulting_job

    def blocked(job_id, text):
        started.set()
        assert finish.wait(10)
        return original(job_id, text)

    monkeypatch.setattr(main, "run_consulting_job", blocked)
    with TestClient(main.app) as client:
        first = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT})
        assert started.wait(5)
        try:
            second = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT})
            assert second.status_code == 429
            assert client.get("/api/v1/health").status_code == 200
        finally:
            finish.set()
        assert wait_for_result(client, first.json()["job_id"])["status"] == "completed"
        third = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT})
        assert third.status_code == 202
        assert wait_for_result(client, third.json()["job_id"])["status"] == "completed"


def test_failed_submission_releases_slot(fake_llm, monkeypatch):
    original = vector_store.ingest_document
    monkeypatch.setattr(vector_store, "ingest_document", lambda *args: (_ for _ in ()).throw(RuntimeError("disk failure")))
    with TestClient(main.app) as client:
        assert client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT}).status_code == 500
        monkeypatch.setattr(vector_store, "ingest_document", original)
        response = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT})
        assert response.status_code == 202
        assert wait_for_result(client, response.json()["job_id"])["status"] == "completed"


def test_failed_runner_releases_slot(fake_llm, monkeypatch):
    original = main.run_consulting_job
    monkeypatch.setattr(main, "run_consulting_job", lambda *args: (_ for _ in ()).throw(RuntimeError("worker failure")))
    with TestClient(main.app) as client:
        response = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT})
        assert wait_for_result(client, response.json()["job_id"])["status"] == "failed"
        monkeypatch.setattr(main, "run_consulting_job", original)
        response = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT})
        assert wait_for_result(client, response.json()["job_id"])["status"] == "completed"


def test_interrupted_job_does_not_poll_forever():
    job_id = str(uuid.uuid4())
    storage.create_job(job_id, source="text", filename=None, characters=100, truncated=False)
    with TestClient(main.app) as client:
        job = client.get(f"/api/v1/consult/{job_id}").json()
    assert job["status"] == "failed"
    assert "restarted" in job["errors"][0]


def test_keyword_retrieval_and_invalid_ids():
    job_id = str(uuid.uuid4())
    demo_store.save(job_id, ["Employees manually plan delivery routes.", "Finance reconciles supplier invoices."])
    assert demo_store.search(job_id, "invoice")[0][0] == 1
    assert demo_store.search(job_id, "route")[0][0] == 0
    assert demo_store.search(job_id, "unrelated") == []
    with pytest.raises(ValueError):
        demo_store.save("../escape", ["test"])


def test_poll_during_completion_does_not_overwrite_finished_job(monkeypatch):
    job_id = str(uuid.uuid4())
    job = storage.create_job(job_id, source="text", filename=None, characters=100, truncated=False)
    finished = storage.update_job(job_id, status="completed")
    reads = iter([job, finished])
    monkeypatch.setattr(storage, "load_job", lambda job_id: next(reads))
    assert main._load_job(job_id)["status"] == "completed"


def test_vercel_origin_allowed_and_unrelated_origin_rejected():
    with TestClient(main.app) as client:
        headers = {"Origin": "https://agentic-ai-consultant.vercel.app", "Access-Control-Request-Method": "POST"}
        response = client.options("/api/v1/consult", headers=headers)
        assert response.headers["access-control-allow-origin"] == headers["Origin"]
        headers["Origin"] = "https://unrelated.example"
        assert client.options("/api/v1/consult", headers=headers).status_code == 400
