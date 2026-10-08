"""Runtime configuration, read once from environment variables (and `.env`)."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    demo_mode: bool

    # LLM (Groq)
    groq_api_key: str
    groq_model: str
    groq_reasoning_effort: str

    # Task queue
    celery_broker_url: str
    celery_result_backend: str

    # Vector store: set CHROMA_HOST to use a Chroma server, otherwise an embedded DB is used
    chroma_host: str
    chroma_port: int

    # Storage & limits
    data_dir: Path
    max_upload_mb: int
    max_document_chars: int
    max_context_chars: int

    cors_origins: Tuple[str, ...]


def load_settings() -> Settings:
    return Settings(
        demo_mode=os.getenv("DEMO_MODE", "false").strip().lower() in ("1", "true", "yes"),
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        groq_reasoning_effort=os.getenv("GROQ_REASONING_EFFORT", "medium"),
        celery_broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        celery_result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
        chroma_host=os.getenv("CHROMA_HOST", ""),
        chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
        data_dir=Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data")),
        max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "10")),
        max_document_chars=int(os.getenv("MAX_DOCUMENT_CHARS", "150000")),
        # Groq's free tier allows 8K tokens/minute for gpt-oss-120b, so the analyst's
        # context is kept to ~3K tokens by default. Raise this on a paid plan.
        max_context_chars=int(os.getenv("MAX_CONTEXT_CHARS", "12000")),
        cors_origins=tuple(
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS", "http://localhost:3001,http://localhost:5173"
            ).split(",")
            if origin.strip()
        ),
    )


settings = load_settings()
