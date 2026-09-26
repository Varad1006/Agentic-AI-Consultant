import uuid

from app import storage
from app.celery_worker import run_consulting_job
from app.report import render_markdown
from tests.conftest import SAMPLE_DOCUMENT


def _new_job():
    job_id = str(uuid.uuid4())
    storage.create_job(job_id, source="text", filename=None, characters=len(SAMPLE_DOCUMENT), truncated=False)
    return job_id


def test_full_pipeline_records_progress_and_results(fake_llm):
    job_id = _new_job()

    assert run_consulting_job.run(job_id, SAMPLE_DOCUMENT) == {"job_id": job_id, "status": "completed"}

    job = storage.load_job(job_id)
    assert job["status"] == "completed"
    assert job["completed_stages"] == ["retriever", "analyst", "architect", "roi", "report"]
    assert job["result"]["roi"]["payback_period_months"] == 15.0
    assert job["result"]["report"]["priority_actions"][0] == "Automate route planning."

    # Short documents reach the analyst whole; the ROI agent sees the architect's plan.
    from app.schemas import CurrentStateAnalysis, ROIEstimate

    assert SAMPLE_DOCUMENT in fake_llm[CurrentStateAnalysis].prompts[0]
    assert "Route optimisation API" in fake_llm[ROIEstimate].prompts[0]

    markdown = render_markdown(job)
    assert "| Payback period | 15 months |" in markdown
    assert "### Route planning" in markdown


def test_agent_failure_stops_the_pipeline(fake_llm, monkeypatch):
    from app.schemas import ArchitecturePlan

    def broken(prompt):
        raise RuntimeError("boom")

    monkeypatch.setattr(fake_llm[ArchitecturePlan], "invoke", broken)
    job_id = _new_job()

    assert run_consulting_job.run(job_id, SAMPLE_DOCUMENT)["status"] == "failed"
    job = storage.load_job(job_id)
    assert job["completed_stages"] == ["retriever", "analyst"]
    assert job["failed_stage"] == "architect"
    assert job["errors"] == ["Solutions Architect: boom"]
    assert job["result"]["roi"] is None


def test_missing_api_key_gives_an_actionable_error():
    job_id = _new_job()
    run_consulting_job.run(job_id, SAMPLE_DOCUMENT)
    job = storage.load_job(job_id)
    assert job["failed_stage"] == "analyst"
    assert "GROQ_API_KEY is not set" in job["errors"][0]


def test_double_escaped_newlines_are_repaired(fake_llm):
    from app.schemas import FinalReport

    fake_llm[FinalReport].output = FinalReport(
        executive_summary="First paragraph.\\n\\nSecond paragraph.",
        priority_actions=["Automate route planning."],
    )
    job_id = _new_job()
    run_consulting_job.run(job_id, SAMPLE_DOCUMENT)

    summary = storage.load_job(job_id)["result"]["report"]["executive_summary"]
    assert summary == "First paragraph.\n\nSecond paragraph."
