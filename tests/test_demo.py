"""Test demo imports and execution in isolation from the normal Celery test suite."""

import os
from pathlib import Path
import subprocess
import sys


def test_demo_process():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/demo_cases.py"],
        cwd=Path(__file__).resolve().parent.parent,
        env={**os.environ, "DEMO_MODE": "true", "CORS_ORIGINS": "https://agentic-ai-consultant.vercel.app"},
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
