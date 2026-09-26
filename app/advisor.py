"""Follow-up chat with the consultant, grounded in the finished report and the source document."""

import json
import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app import vector_store
from app.llm import get_chat_model
from app.prompts import CONSULTANT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

HISTORY_MESSAGES = 6
HISTORY_MESSAGE_CHARS = 1500
EVIDENCE_CHUNKS = 3


def answer_question(job: Dict[str, Any], question: str) -> str:
    engagement = json.dumps(job["result"], separators=(",", ":"), ensure_ascii=False)
    messages = [SystemMessage(content=CONSULTANT_SYSTEM_PROMPT.format(engagement=engagement))]

    for message in job.get("chat", [])[-HISTORY_MESSAGES:]:
        content = message["content"][:HISTORY_MESSAGE_CHARS]
        messages.append(HumanMessage(content=content) if message["role"] == "user" else AIMessage(content=content))

    try:
        excerpts = vector_store.search(job["job_id"], question, top_k=EVIDENCE_CHUNKS)
    except Exception:
        logger.warning("Document search failed for job %s; answering from the report only", job["job_id"])
        excerpts = []
    evidence = "\n---\n".join(text for _, text in excerpts) or "(no matching excerpts)"

    messages.append(
        HumanMessage(content=f"Relevant excerpts from my documents:\n{evidence}\n\nMy question: {question}")
    )
    response = get_chat_model(temperature=0.5).invoke(messages)
    return _text(response.content)


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [block.get("text", "") if isinstance(block, dict) else str(block) for block in content]
        return "\n".join(part for part in parts if part).strip()
    return str(content)
