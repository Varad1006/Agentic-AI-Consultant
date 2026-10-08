"""Per-job document chunks in ChromaDB, embedded locally with all-MiniLM-L6-v2 (no API key needed)."""

import logging
from itertools import zip_longest
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)

# Questions the retriever asks of long documents, so the analyst sees every kind of evidence it needs.
ANALYSIS_QUERIES = (
    "What does the company do, who are its customers and how does it make money?",
    "Which software, tools, spreadsheets and systems does the team use?",
    "Which processes are manual, repetitive, slow or error-prone, and how many hours do they take?",
    "What volumes, costs, headcount, delays or error rates are mentioned?",
)

_client = None
_embedding_function = None


def _get_client():
    import chromadb

    global _client
    if _client is None:
        if settings.chroma_host:
            _client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        else:
            _client = chromadb.PersistentClient(path=str(settings.data_dir / "chroma"))
    return _client


def _get_embedding_function():
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    global _embedding_function
    if _embedding_function is None:
        _embedding_function = DefaultEmbeddingFunction()
    return _embedding_function


def _collection_name(job_id: str) -> str:
    return f"job_{job_id}"


def ingest_document(job_id: str, text: str) -> int:
    """Chunk and embed a document into a collection for this job. Returns the number of chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(text)

    if settings.demo_mode:
        from app import demo_store

        demo_store.save(job_id, chunks)
        return len(chunks)

    collection = _get_client().get_or_create_collection(
        _collection_name(job_id), embedding_function=_get_embedding_function()
    )
    collection.add(
        ids=[str(i) for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"chunk": i} for i in range(len(chunks))],
    )
    logger.info("Ingested %d chunks for job %s", len(chunks), job_id)
    return len(chunks)


def search(job_id: str, query: str, top_k: int = 5) -> List[Tuple[int, str]]:
    """Return up to `top_k` (chunk_index, text) pairs, most relevant first."""
    if settings.demo_mode:
        from app import demo_store

        return demo_store.search(job_id, query, top_k)

    collection = _get_client().get_collection(
        _collection_name(job_id), embedding_function=_get_embedding_function()
    )
    n_results = min(top_k, collection.count())
    if n_results == 0:
        return []
    results = collection.query(query_texts=[query], n_results=n_results, include=["documents", "metadatas"])
    return [
        (int(metadata["chunk"]), document)
        for document, metadata in zip(results["documents"][0], results["metadatas"][0])
    ]


def build_document_context(job_id: str, full_text: str, max_chars: int) -> str:
    """The text the analyst reads: the whole document if it fits, otherwise the best-matching chunks."""
    if len(full_text) <= max_chars:
        return full_text

    ranked_per_query = [search(job_id, query, top_k=8) for query in ANALYSIS_QUERIES]

    # Take results round-robin across queries so every topic is represented within the budget.
    selected = {}
    used = 0
    for tier in zip_longest(*ranked_per_query):
        for hit in tier:
            if hit is None or hit[0] in selected:
                continue
            index, text = hit
            if used + len(text) > max_chars:
                continue
            selected[index] = text
            used += len(text)

    # Present the chunks in document order so the analyst reads a coherent narrative.
    return "\n[...]\n".join(selected[index] for index in sorted(selected))
