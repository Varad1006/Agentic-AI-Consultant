import json
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent

MEMORY_DIR = BASE_DIR / "storage" / "consulting_memory"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def save_consulting_memory(job_id, result):
    filepath = MEMORY_DIR / f"{job_id}.json"

    print(f"SAVING TO: {filepath}")

    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)

    print(f"FILE EXISTS AFTER SAVE: {filepath.exists()}")
MEMORY_DIR = Path("app/storage/consulting_memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def save_consulting_memory(job_id: str, result: Dict[str, Any]) -> None:
    """
    Persist the completed consulting engagement.
    """

    filepath = MEMORY_DIR / f"{job_id}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def load_consulting_memory(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Load previously generated consulting memory.
    """

    filepath = MEMORY_DIR / f"{job_id}.json"

    if not filepath.exists():
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)