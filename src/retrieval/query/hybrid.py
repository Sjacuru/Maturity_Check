from __future__ import annotations

from ingestion import get_acronym_store, get_ipmp_store, get_retrieval_profile_store, get_rio_manual_store
from retrieval.interfaces.contracts import RetrievedChunk
from retrieval.query import vector as vector_mod
from retrieval.query.bm25 import MAX_CHUNKS_PER_ACAO, fetch_bm25_candidates
from retrieval.query.query_builder import build_bm25_query, build_query_from_terms
from retrieval.query.rrf import fuse_rankings

# Candidate pool size fed into RRF — both BM25 and vector are truncated to this
# size before fusion, so neither side's raw pool size biases the fused ranking.
_CANDIDATE_POOL_SIZE = 20

# Each product (and rio_hints) keeps at most this many best-scoring chunks
# after fusion/ranking. 4 IPMP products + rio_hints x 5 = 25 candidates, minus
# physical duplicates -> capped at MAX_CHUNKS_PER_ACAO.
_PER_PRODUCT_TARGET = 5

_Key = tuple  # (filename, page_number, chunk_index)


def _natural_key(chunk: RetrievedChunk) -> _Key:
    return (chunk.filename, chunk.page_number, chunk.chunk_index)


def _vector_query_text(profile_product, ipmp_texto: str) -> str:
    """evidence_intent + retrieval_signal_concepts when a profile exists, else IPMP text."""
    if profile_product is not None:
        concept_text = " ".join(c.text for c in profile_product.retrieval_signal_concepts)
        combined = f"{profile_product.evidence_intent} {concept_text}".strip()
        if combined:
            return combined
    return ipmp_texto


def _fused_candidates_for_product(
    product,
    profile_product,
    acronym_map: dict[str, str],
    process_number: str,
) -> list[tuple[float, RetrievedChunk]]:
    """BM25 + vector candidates for one product, fused via RRF, sorted best-first.

    Returns up to _CANDIDATE_POOL_SIZE (score, chunk) pairs, NOT capped to
    _PER_PRODUCT_TARGET — callers decide how many to keep.
    """
    if profile_product and profile_product.query_terms:
        bm25_query = build_query_from_terms(profile_product.query_terms)
    else:
        bm25_query = build_bm25_query(product.texto, acronym_map)

    vector_query = _vector_query_text(profile_product, product.texto)

    bm25_hits = (
        fetch_bm25_candidates(bm25_query, process_number, product.id, limit=_CANDIDATE_POOL_SIZE)
        if bm25_query
        else []
    )
    vector_hits = (
        vector_mod.search_vector(process_number, vector_query, k=_CANDIDATE_POOL_SIZE)
        if vector_query
        else []
    )
    if not bm25_hits and not vector_hits:
        return []

    by_key: dict[_Key, RetrievedChunk] = {}
    for c in bm25_hits:
        by_key[_natural_key(c)] = c
    for c in vector_hits:
        by_key.setdefault(_natural_key(c), c)

    fused_scores = fuse_rankings(
        [
            [_natural_key(c) for c in bm25_hits],
            [_natural_key(c) for c in vector_hits],
        ]
    )
    ranked_keys = sorted(fused_scores, key=lambda key: fused_scores[key], reverse=True)

    return [
        (fused_scores[key], by_key[key].model_copy(update={"expected_product_id": product.id}))
        for key in ranked_keys
    ]


def retrieve_hybrid_candidates_for_acao(
    acao_id: int,
    process_number: str,
) -> dict[str, list[tuple[float, RetrievedChunk]]]:
    """Per-Expected-Product RRF-fused candidates, wider than the per-product cap (ADR-0050).

    For each letter-suffixed Expected Product, returns up to _CANDIDATE_POOL_SIZE
    (fused_score, chunk) pairs sorted best-first — BEFORE the _PER_PRODUCT_TARGET
    narrowing that retrieve_hybrid_for_acao() applies. This is the wider pool the
    relevance gate (evidence_selection.select_evidence) classifies against, so a
    genuinely relevant chunk ranked below 5 by RRF still gets a chance.

    Returns {} when acao_id is not found in the IPMP store.
    """
    acao = get_ipmp_store().acoes.get(acao_id)
    if acao is None:
        return {}

    profile_acao = get_retrieval_profile_store().acoes.get(acao_id)
    acronym_map = get_acronym_store()

    candidates: dict[str, list[tuple[float, RetrievedChunk]]] = {}
    for product in acao.produtos_esperados:
        if not product.id[-1:].isalpha():
            continue
        profile_product = (
            profile_acao.expected_products.get(product.id) if profile_acao else None
        )
        ranked = _fused_candidates_for_product(product, profile_product, acronym_map, process_number)
        if ranked:
            candidates[product.id] = ranked
    return candidates


def retrieve_hybrid_for_acao(
    acao_id: int,
    process_number: str,
) -> list[RetrievedChunk]:
    """Per-Expected-Product hybrid retrieval: BM25 + vector fused via RRF (ADR-0049).

    For each letter-suffixed Expected Product (1a, 1b, ...): builds a BM25 query
    (curated profile terms, falling back to build_bm25_query()) and a vector
    query (evidence_intent + retrieval_signal_concepts, falling back to the raw
    IPMP product text), retrieves up to _CANDIDATE_POOL_SIZE candidates from
    each, fuses them via Reciprocal Rank Fusion (k=60), and keeps the top
    _PER_PRODUCT_TARGET fused chunks per product.

    rio_hints stays BM25-only (no vector counterpart, no RRF): its own top
    _PER_PRODUCT_TARGET candidates by raw BM25 score.

    Cross-lane conflicts (same physical chunk claimed by more than one IPMP
    product) resolve in favor of the higher RRF score. Conflicts between an
    IPMP product lane and rio_hints always resolve in favor of the IPMP
    product lane, regardless of score — RRF and raw BM25 scores are not on a
    comparable scale.

    Returns at most MAX_CHUNKS_PER_ACAO chunks total, IPMP-lane chunks
    prioritised over rio_hints when the combined pool exceeds the cap.
    Returns [] when acao_id is not found in the IPMP store.
    """
    acao = get_ipmp_store().acoes.get(acao_id)
    if acao is None:
        return []

    candidates = retrieve_hybrid_candidates_for_acao(acao_id, process_number)

    # key -> (fused_score, chunk) for the best-scoring IPMP product lane that claimed it.
    product_selected: dict[_Key, tuple[float, RetrievedChunk]] = {}
    for product_id, ranked in candidates.items():
        for score, chunk in ranked[:_PER_PRODUCT_TARGET]:
            key = _natural_key(chunk)
            if key not in product_selected or score > product_selected[key][0]:
                product_selected[key] = (score, chunk)

    rio_selected: dict[_Key, RetrievedChunk] = {}
    rio_acao = get_rio_manual_store().acoes.get(acao_id)
    if rio_acao:
        hints = rio_acao.bm25_search_hints
        all_hints = hints.primary_terms + hints.secondary_terms
        if all_hints:
            rio_query = " OR ".join(f'"{t}"' for t in all_hints)
            rio_hits = fetch_bm25_candidates(
                rio_query, process_number, "rio_hints", limit=_CANDIDATE_POOL_SIZE
            )
            rio_hits.sort(key=lambda c: c.bm25_score)  # most negative (best) first
            for c in rio_hits[:_PER_PRODUCT_TARGET]:
                rio_selected[_natural_key(c)] = c

    # IPMP product lanes always win conflicts with rio_hints (ADR-0049).
    for key in product_selected:
        rio_selected.pop(key, None)

    ordered_product_chunks = [
        chunk
        for _, chunk in sorted(
            product_selected.values(), key=lambda pair: pair[0], reverse=True
        )
    ]
    combined = ordered_product_chunks + list(rio_selected.values())
    return combined[:MAX_CHUNKS_PER_ACAO]
