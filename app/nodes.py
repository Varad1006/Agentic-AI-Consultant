"""The agents in the consulting pipeline. Each node reads the shared state and returns an update."""

import json
import logging
from typing import Any, Type, TypeVar

import groq
from pydantic import BaseModel

from app import vector_store
from app.config import settings
from app.llm import LLMNotConfiguredError, describe_llm_error, structured_model
from app.prompts import ANALYST_PROMPT, ARCHITECT_PROMPT, REPORT_PROMPT, ROI_PROMPT
from app.schemas import ArchitecturePlan, CurrentStateAnalysis, FinalReport, ROIEstimate, compute_roi
from app.state import ConsultantState

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _as_json(model: BaseModel) -> str:
    return json.dumps(model.model_dump(), indent=1)


def _unescape_newlines(value: Any) -> Any:
    """gpt-oss sometimes double-escapes newlines inside JSON strings, leaving a literal "\\n"."""
    if isinstance(value, str):
        return value.replace("\\n", "\n")
    if isinstance(value, list):
        return [_unescape_newlines(item) for item in value]
    if isinstance(value, dict):
        return {key: _unescape_newlines(item) for key, item in value.items()}
    return value


def _generate(schema: Type[T], prompt: str) -> T:
    output = structured_model(schema).invoke(prompt)
    return schema.model_validate(_unescape_newlines(output.model_dump()))


def _failure(agent: str, exc: Exception) -> dict:
    expected = isinstance(exc, (LLMNotConfiguredError, groq.APIError))
    logger.warning("%s failed: %s", agent, exc, exc_info=not expected)
    return {"errors": [f"{agent}: {describe_llm_error(exc)}"]}


def retriever_node(state: ConsultantState) -> dict:
    """Context Retriever: selects the parts of the document the analyst should read."""
    try:
        context = vector_store.build_document_context(
            state["job_id"], state["client_document_text"], settings.max_context_chars
        )
    except Exception as exc:
        return _failure("Context Retriever", exc)

    if not context.strip():
        return {"errors": ["Context Retriever: no document content was found for this job."]}
    return {"document_context": context}


def analyst_node(state: ConsultantState) -> dict:
    """Business Analyst: extracts the business model, tech stack and bottlenecks."""
    try:
        analysis = _generate(
            CurrentStateAnalysis,
            ANALYST_PROMPT.format(context=state["document_context"]),
        )
    except Exception as exc:
        return _failure("Business Analyst", exc)

    if not analysis.identified_bottlenecks:
        return {"errors": ["Business Analyst: no operational bottlenecks were found in the document."]}
    return {"analysis_result": analysis}


def architect_node(state: ConsultantState) -> dict:
    """Solutions Architect: designs an automation solution for each bottleneck."""
    try:
        plan = _generate(
            ArchitecturePlan,
            ARCHITECT_PROMPT.format(analysis=_as_json(state["analysis_result"])),
        )
    except Exception as exc:
        return _failure("Solutions Architect", exc)
    return {"architecture_plan": plan}


def roi_node(state: ConsultantState) -> dict:
    """ROI Analyst: estimates cost and savings for the proposed architecture."""
    try:
        estimate = _generate(
            ROIEstimate,
            ROI_PROMPT.format(
                analysis=_as_json(state["analysis_result"]),
                architecture=_as_json(state["architecture_plan"]),
            ),
        )
    except Exception as exc:
        return _failure("ROI Analyst", exc)
    return {"roi_result": compute_roi(estimate)}


def report_node(state: ConsultantState) -> dict:
    """Report Writer: synthesises everything into an executive summary and priority actions."""
    try:
        report = _generate(
            FinalReport,
            REPORT_PROMPT.format(
                analysis=_as_json(state["analysis_result"]),
                architecture=_as_json(state["architecture_plan"]),
                roi=_as_json(state["roi_result"]),
            ),
        )
    except Exception as exc:
        return _failure("Report Writer", exc)
    return {"final_report": report}
