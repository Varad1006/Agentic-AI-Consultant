import uuid

from app import vector_store

PARAGRAPHS = [
    "Brightline Fulfillment stores and ships products for 180 online retailers.",
    "The operations team relies on Microsoft Excel, WhatsApp and a legacy on-premise ERP.",
    "Dispatchers spend three hours every morning building delivery routes by hand.",
    "Procurement types purchase orders manually, which takes about twelve hours a week.",
]


def test_ingest_and_search_round_trip():
    job_id = str(uuid.uuid4())
    text = "\n\n".join(p + " " + "Filler sentence about the warehouse. " * 25 for p in PARAGRAPHS)
    chunks = vector_store.ingest_document(job_id, text)
    assert chunks > 1

    hits = vector_store.search(job_id, "How long does route planning take?", top_k=1)
    assert "delivery routes" in hits[0][1]


def test_short_documents_are_used_whole():
    text = "A short document that fits in the context budget."
    assert vector_store.build_document_context("unused", text, max_chars=1000) == text


def test_long_documents_use_round_robin_retrieval(monkeypatch):
    results = {
        query: [(i * 10 + rank, f"q{i}-r{rank} " + "x" * 90) for rank in range(3)]
        for i, query in enumerate(vector_store.ANALYSIS_QUERIES)
    }
    monkeypatch.setattr(vector_store, "search", lambda job_id, query, top_k: results[query])

    context = vector_store.build_document_context("job", "y" * 10_000, max_chars=450)
    # The budget fits four chunks: the best hit from each query, in document order.
    assert [part.split()[0] for part in context.split("\n[...]\n")] == ["q0-r0", "q1-r0", "q2-r0", "q3-r0"]
