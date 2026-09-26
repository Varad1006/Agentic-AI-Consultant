"""Groq chat model used by every agent (default: openai/gpt-oss-120b)."""

from functools import lru_cache
from typing import Type, TypeVar

import groq
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMNotConfiguredError(RuntimeError):
    pass


@lru_cache(maxsize=4)
def get_chat_model(temperature: float = 0.2) -> ChatGroq:
    if not settings.groq_api_key:
        raise LLMNotConfiguredError(
            "GROQ_API_KEY is not set. Add it to your .env file and restart the API and worker."
        )
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=temperature,
        reasoning_effort=settings.groq_reasoning_effort,
        # The Groq SDK honours `retry-after` on 429s, which smooths over free-tier TPM limits.
        max_retries=5,
    )


def structured_model(schema: Type[T]) -> Runnable:
    """A model whose output is constrained to `schema` via Groq's strict structured outputs."""
    return get_chat_model().with_structured_output(schema, method="json_schema", strict=True)


def describe_llm_error(exc: Exception) -> str:
    """Turn provider exceptions into messages a user can act on."""
    if isinstance(exc, LLMNotConfiguredError):
        return str(exc)
    if isinstance(exc, groq.AuthenticationError):
        return "Groq rejected the API key. Check GROQ_API_KEY in your .env file."
    if isinstance(exc, groq.RateLimitError):
        return (
            "Groq rate limit reached (the free tier allows 8K tokens/minute for gpt-oss-120b). "
            "Wait a minute and try again, or upgrade your Groq plan."
        )
    if isinstance(exc, groq.APIStatusError) and exc.status_code == 413:
        return (
            "The request was too large for your Groq plan's tokens-per-minute limit. "
            "Lower MAX_CONTEXT_CHARS or upgrade your Groq plan."
        )
    if isinstance(exc, groq.APIConnectionError):
        return "Could not reach the Groq API. Check your internet connection."
    message = str(exc).strip() or type(exc).__name__
    return message if len(message) <= 300 else message[:297] + "..."
