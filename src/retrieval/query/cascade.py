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

    Step D (corpus-wide regex) was removed in ADR-0052. Law-reference pages it found
    were structurally boilerplate (preambles, glossaries) with no product attribution;
    the ungated path allowed them to displace gate-approved evidence via the character
    budget cap; and the pattern scales destructively across 46 Ações because the same
    foundational PPP laws appear on hundreds of procedural pages.
    """
    from retrieval.query.document import retrieve_document_focused

    doc_result = retrieve_document_focused(acao_id, process_number)
    if doc_result is not None:
        return doc_result

    return retrieve_hybrid_for_acao(acao_id, process_number)
