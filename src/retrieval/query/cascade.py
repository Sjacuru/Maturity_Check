from __future__ import annotations

from retrieval.interfaces.contracts import RetrievedChunk
from retrieval.query.hybrid import retrieve_hybrid_for_acao


def retrieve_for_acao(
    acao_id: int,
    process_number: str,
) -> list[RetrievedChunk]:
    """Execute the full retrieval cascade.

    Step A — filename match: compare indexed filenames against Rio Manual document names.
    Step B — variant match: search first chunks for Rio Manual document name patterns.
    If A or B identifies a document, return all its chunks (regex naturally scoped).
    Step C — corpus-wide hybrid retrieval: per-product BM25 + vector fusion via RRF (ADR-0049).
    Step D — corpus-wide regex (ADR-0007), additive to Step C; not counted against MAX_CHUNKS_PER_ACAO.
    """
    from retrieval.query.document import retrieve_document_focused
    from retrieval.query.regex_search import search_regex

    doc_result = retrieve_document_focused(acao_id, process_number)
    if doc_result is not None:
        return doc_result

    hybrid_results = retrieve_hybrid_for_acao(acao_id, process_number)

    hybrid_keys = {(r.filename, r.page_number, r.chunk_index) for r in hybrid_results}
    regex_results = search_regex(acao_id, process_number)
    new_hits = [
        r for r in regex_results
        if (r.filename, r.page_number, r.chunk_index) not in hybrid_keys
    ]

    return hybrid_results + new_hits
