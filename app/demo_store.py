"""Small, file-backed keyword index for the free demo; no embedding model required."""

import json
import math
import re
from collections import Counter
from typing import List, Tuple

from app.config import settings
from app.storage import is_valid_job_id

_STOP_WORDS = set("a an and are as at be by do does for from how in is it of on or the to what when where which with".split())


def _path(job_id: str):
    if not is_valid_job_id(job_id):
        raise ValueError("Invalid job id")
    directory = settings.data_dir / "documents"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{job_id}.json"


def _tokens(text: str):
    # A small plural normalization keeps "routes" searchable as "route".
    return [word[:-1] if word.endswith("s") and len(word) > 3 else word
            for word in re.findall(r"\w+", text.lower()) if word not in _STOP_WORDS]


def save(job_id: str, chunks: List[str]) -> None:
    _path(job_id).write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")


def search(job_id: str, query: str, top_k: int = 5) -> List[Tuple[int, str]]:
    if top_k <= 0:
        return []
    chunks = json.loads(_path(job_id).read_text(encoding="utf-8"))
    terms = set(_tokens(query))
    counters = [Counter(_tokens(chunk)) for chunk in chunks]
    document_frequency = {term: sum(term in counter for counter in counters) for term in terms}
    scored = []
    for index, counter in enumerate(counters):
        score = sum(
            (1 + math.log(counter[term])) * math.log(1 + len(chunks) / (1 + document_frequency[term]))
            for term in terms if counter[term]
        ) / math.sqrt(max(1, sum(counter.values())))
        if score:
            scored.append((score, index))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [(index, chunks[index]) for _, index in scored[:top_k]]
