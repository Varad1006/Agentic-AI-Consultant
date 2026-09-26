import uuid

import pytest
from fastapi.testclient import TestClient

from app import main, storage
from app.celery_worker import run_consulting_job
from tests.conftest import SAMPLE_DOCUMENT


@pytest.fixture
def client(monkeypatch):
    queued = []
    monkeypatch.setattr(main.run_consulting_job, "apply_async", lambda args, task_id: queued.append(args))
    test_client = TestClient(main.app)
    test_client.queued = queued
    return test_client


def test_submit_text_creates_a_queued_job(client):
    response = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT})
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job = client.get(f"/api/v1/consult/{job_id}").json()
    assert job["status"] == "queued"
    assert job["source"] == "text"
    assert client.queued == [[job_id, SAMPLE_DOCUMENT]]


def test_upload_rejects_unsupported_and_short_files(client):
    response = client.post("/api/v1/upload", files={"file": ("photo.png", b"data", "image/png")})
    assert response.status_code == 400
    response = client.post("/api/v1/upload", files={"file": ("notes.txt", b"hi", "text/plain")})
    assert response.status_code == 400
    assert "too short" in response.json()["detail"]


def test_upload_text_file(client):
    response = client.post(
        "/api/v1/upload", files={"file": ("sop.txt", SAMPLE_DOCUMENT.encode(), "text/plain")}
    )
    assert response.status_code == 202
    assert client.get(f"/api/v1/consult/{response.json()['job_id']}").json()["filename"] == "sop.txt"


def test_unknown_and_malformed_job_ids_return_404(client):
    assert client.get(f"/api/v1/consult/{uuid.uuid4()}").status_code == 404
    assert client.get("/api/v1/consult/..%2F..%2Fetc").status_code == 404


def test_report_and_chat_require_a_completed_job(client):
    job_id = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT}).json()["job_id"]
    assert client.get(f"/api/v1/consult/{job_id}/report").status_code == 409
    assert client.post(f"/api/v1/consult/{job_id}/chat", json={"question": "Hi"}).status_code == 409


def test_completed_job_serves_report_and_persists_chat(client, fake_llm, monkeypatch):
    job_id = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT}).json()["job_id"]
    run_consulting_job.run(job_id, SAMPLE_DOCUMENT)

    report = client.get(f"/api/v1/consult/{job_id}/report").json()
    assert report["content"].startswith("# Executive Consulting Report")

    monkeypatch.setattr(main.advisor, "answer_question", lambda job, question: f"Answer to: {question}")
    response = client.post(f"/api/v1/consult/{job_id}/chat", json={"question": "Where do we start?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Answer to: Where do we start?"

    chat = client.get(f"/api/v1/consult/{job_id}").json()["chat"]
    assert [message["role"] for message in chat] == ["user", "assistant"]


def test_chat_llm_errors_are_reported(client, fake_llm, monkeypatch):
    job_id = client.post("/api/v1/consult", json={"document_text": SAMPLE_DOCUMENT}).json()["job_id"]
    run_consulting_job.run(job_id, SAMPLE_DOCUMENT)

    response = client.post(f"/api/v1/consult/{job_id}/chat", json={"question": "Where do we start?"})
    assert response.status_code == 502
    assert "GROQ_API_KEY is not set" in response.json()["detail"]
    assert storage.load_job(job_id)["chat"] == []


def test_health_reports_llm_configuration(client, monkeypatch):
    monkeypatch.setattr(main.celery_app.control, "ping", lambda timeout: [{"worker@host": {"ok": "pong"}}])
    body = client.get("/api/v1/health").json()
    assert body["celery"] == "connected"
    assert body["llm"] == {"provider": "groq", "model": "openai/gpt-oss-120b", "configured": False}
