from __future__ import annotations

from ingestion import get_acronym_store, get_ipmp_store, get_retrieval_profile_store, get_rio_manual_store
from retrieval.interfaces.contracts import RetrievedChunk
from retrieval.query.bm25 import search_bm25
from retrieval.query.query_builder import build_bm25_query, build_query_from_terms


def retrieve_bm25_for_acao(
    acao_id: int,
    process_number: str,
) -> list[RetrievedChunk]:
    """Retrieve chunks using the BM25 corpus-wide path only.

    Builds one FTS5 OR query per letter-suffixed Expected Product (1a, 1b …).
    When a retrieval profile exists for the Ação, uses its curated Layer C query
    terms (phrase and NEAR encodings) for the relevant Expected Product.
    Falls back to build_bm25_query() for any product without a profile entry.
    Merges and deduplicates results, returns at most MAX_CHUNKS_PER_ACAO chunks.
    Returns [] when acao_id is not found in the IPMP store.
    """
    acao = get_ipmp_store().acoes.get(acao_id)
    if acao is None:
        return []

    profile_acao = get_retrieval_profile_store().acoes.get(acao_id)
    acronym_map = get_acronym_store()

    queries: dict[str, str] = {}
    for product in acao.produtos_esperados:
        if product.id[-1:].isalpha():
            profile_product = (
                profile_acao.expected_products.get(product.id)
                if profile_acao else None
            )
            if profile_product and profile_product.query_terms:
                q = build_query_from_terms(profile_product.query_terms)
            else:
                q = build_bm25_query(product.texto, acronym_map)
            if q:
                queries[product.id] = q

    rio_acao = get_rio_manual_store().acoes.get(acao_id)
    if rio_acao:
        hints = rio_acao.bm25_search_hints
        all_hints = hints.primary_terms + hints.secondary_terms
        if all_hints:
            queries["rio_hints"] = " OR ".join(f'"{t}"' for t in all_hints)

    return search_bm25(queries, process_number)


def retrieve_for_acao(
    acao_id: int,
    process_number: str,
) -> list[RetrievedChunk]:
    """Execute the full retrieval cascade.

    Step A — filename match: compare indexed filenames against Rio Manual document names.
    Step B — variant match: search first chunks for Rio Manual document name patterns.
    If A or B identifies a document, return all its chunks (regex naturally scoped).
    Step C — corpus-wide BM25.
    Step D — corpus-wide regex (ADR-0007), additive to BM25; not counted against MAX_CHUNKS_PER_ACAO.
    Step E — vector fallback (ADR-0033): runs only when A–D return zero chunks.
    """
    from retrieval.query.document import retrieve_document_focused
    from retrieval.query.regex_search import search_regex
    from retrieval.query.vector import search_vector

    doc_result = retrieve_document_focused(acao_id, process_number)
    if doc_result is not None:
        return doc_result

    bm25_results = retrieve_bm25_for_acao(acao_id, process_number)

    bm25_keys = {(r.filename, r.page_number, r.chunk_index) for r in bm25_results}
    regex_results = search_regex(acao_id, process_number)
    new_hits = [
        r for r in regex_results
        if (r.filename, r.page_number, r.chunk_index) not in bm25_keys
    ]

    lexical = bm25_results + new_hits
    if lexical:
        return lexical

    query_text = _build_vector_query(acao_id)
    if not query_text:
        return []
    return search_vector(process_number, query_text)


def _build_vector_query(acao_id: int) -> str:
    """Concatenate letter-suffixed Expected Product texts for the Ação as the vector query."""
    acao = get_ipmp_store().acoes.get(acao_id)
    if acao is None:
        return ""
    parts = [
        p.texto for p in acao.produtos_esperados
        if p.id[-1:].isalpha()
    ]
    return " ".join(parts)
