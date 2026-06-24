from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from ingestion import get_retrieval_profile_store
from retrieval import fetch_neighbor_chunks
from retrieval.interfaces.contracts import RetrievedChunk

from evaluation._config import get_gate_llm_client
from evaluation.interfaces.contracts import RejectedChunk
from evaluation.parsing.relevance_response import RelevanceVerdict, parse_relevance_response
from evaluation.prompt.relevance_builder import build_relevance_system_prompt, build_relevance_user_prompt

logger = logging.getLogger(__name__)

_ANCHOR_TARGET = 5
_EXPANSION_TARGET = 5

# Mirrors evaluator._MAX_EVIDENCE_CHARS — evidence_selection trims expansion
# chunks against the same ceiling _cap_evidence() enforces downstream as a
# final safety net for any residual overflow (ADR-0050).
_EVIDENCE_BUDGET_CHARS = 21_000

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class EvidenceSelectionResult:
    accepted: list[RetrievedChunk] = field(default_factory=list)
    rejected: list[RejectedChunk] = field(default_factory=list)


def select_evidence(
    acao_id: int,
    process_number: str,
    candidates: dict[str, list[tuple[float, RetrievedChunk]]],
) -> EvidenceSelectionResult:
    """LLM relevance gate + neighbor expansion + verbatim cleaning (ADR-0050).

    For each product: classifies up to 20 RRF-ranked candidates against the
    product's evidence_intent (in original RRF order), keeps the top
    _ANCHOR_TARGET relevant ones as anchors, fetches each anchor's immediate
    document neighbors and gates them too, keeping up to _EXPANSION_TARGET
    relevant neighbors per product. When the combined result exceeds the
    evidence character budget, expansion chunks are trimmed first — weakest
    anchor-score products first; anchors are never trimmed here
    (evaluator._cap_evidence() remains the final safety net for any residual
    overflow).

    Products with no evidence_intent in the retrieval profile pass through
    ungated (top _ANCHOR_TARGET candidates by score, no cleaning, no
    expansion) — a safe degrade for Ações without a populated profile yet.
    """
    profile_acao = get_retrieval_profile_store().acoes.get(acao_id)

    rejected: list[RejectedChunk] = []
    # Expansions carry their anchor's fused score as a trim-priority proxy —
    # they have no RRF score of their own (they're fetched, not retrieved).
    scored_anchors: list[tuple[float, RetrievedChunk]] = []
    scored_expansions: list[tuple[float, RetrievedChunk]] = []

    for product_id, ranked in candidates.items():
        profile_product = (
            profile_acao.expected_products.get(product_id) if profile_acao else None
        )
        if profile_product is None or not profile_product.evidence_intent:
            scored_anchors.extend(ranked[:_ANCHOR_TARGET])
            continue

        evidence_intent = profile_product.evidence_intent
        product_anchors: list[tuple[float, RetrievedChunk]] = []

        for score, chunk in ranked:
            if len(product_anchors) >= _ANCHOR_TARGET:
                break
            verdict = _gate_chunk(chunk.text, evidence_intent)
            if not verdict.relevant:
                rejected.append(_to_rejected(chunk, product_id))
                continue
            cleaned_text = _resolve_cleaned_text(chunk.text, verdict)
            product_anchors.append((score, chunk.model_copy(update={"text": cleaned_text})))

        scored_anchors.extend(product_anchors)
        scored_expansions.extend(
            _expand_anchors(product_anchors, product_id, process_number, evidence_intent, rejected)
        )

    deduped_anchors, deduped_expansions = _deduplicate_across_products(
        scored_anchors, scored_expansions
    )
    accepted_anchors = [chunk for _, chunk in deduped_anchors]
    accepted_expansions = _trim_expansions_to_budget(deduped_anchors, deduped_expansions)

    return EvidenceSelectionResult(
        accepted=accepted_anchors + accepted_expansions,
        rejected=rejected,
    )


def _natural_key(chunk: RetrievedChunk) -> tuple[str, int, int]:
    return (chunk.filename, chunk.page_number, chunk.chunk_index)


def _deduplicate_across_products(
    scored_anchors: list[tuple[float, RetrievedChunk]],
    scored_expansions: list[tuple[float, RetrievedChunk]],
) -> tuple[list[tuple[float, RetrievedChunk]], list[tuple[float, RetrievedChunk]]]:
    """Collapse the same physical chunk accepted by multiple products to one copy.

    Final scoring is a single combined LLM call across all products (ADR-0009),
    and build_user_prompt() doesn't even include expected_product_id — the LLM
    cannot tell two copies of the same chunk's text apart, so a chunk accepted
    by multiple products' gates must still reach evaluate() only once. This is
    ADR-0049's "one physical chunk, one attribution" invariant, extended to
    the gated path (ADR-0050 amendment, 2026-06-24): anchors win over
    expansions for the same physical chunk (a higher-confidence inclusion
    than a fetched neighbor); within each tier, the highest-scoring copy
    wins, mirroring ADR-0049's tie-break rule.
    """
    best_anchor: dict[tuple[str, int, int], tuple[float, RetrievedChunk]] = {}
    for score, chunk in scored_anchors:
        key = _natural_key(chunk)
        if key not in best_anchor or score > best_anchor[key][0]:
            best_anchor[key] = (score, chunk)
    anchor_keys = set(best_anchor.keys())

    best_expansion: dict[tuple[str, int, int], tuple[float, RetrievedChunk]] = {}
    for score, chunk in scored_expansions:
        key = _natural_key(chunk)
        if key in anchor_keys:
            continue  # already included as an anchor — anchors win
        if key not in best_expansion or score > best_expansion[key][0]:
            best_expansion[key] = (score, chunk)

    return list(best_anchor.values()), list(best_expansion.values())


def _expand_anchors(
    product_anchors: list[tuple[float, RetrievedChunk]],
    product_id: str,
    process_number: str,
    evidence_intent: str,
    rejected: list[RejectedChunk],
) -> list[tuple[float, RetrievedChunk]]:
    product_expansions: list[tuple[float, RetrievedChunk]] = []
    for anchor_score, anchor in product_anchors:
        if len(product_expansions) >= _EXPANSION_TARGET:
            break
        prev_chunk, next_chunk = fetch_neighbor_chunks(
            process_number, anchor.filename, anchor.page_number, anchor.chunk_index
        )
        for neighbor in (c for c in (prev_chunk, next_chunk) if c is not None):
            if len(product_expansions) >= _EXPANSION_TARGET:
                break
            verdict = _gate_chunk(neighbor.text, evidence_intent)
            if not verdict.relevant:
                rejected.append(_to_rejected(neighbor, product_id))
                continue
            cleaned_text = _resolve_cleaned_text(neighbor.text, verdict)
            expanded = neighbor.model_copy(
                update={"text": cleaned_text, "expected_product_id": product_id}
            )
            product_expansions.append((anchor_score, expanded))
    return product_expansions


def _trim_expansions_to_budget(
    scored_anchors: list[tuple[float, RetrievedChunk]],
    scored_expansions: list[tuple[float, RetrievedChunk]],
) -> list[RetrievedChunk]:
    anchors_chars = sum(len(c.text) for _, c in scored_anchors)
    kept = [c for _, c in sorted(scored_expansions, key=lambda pair: pair[0])]  # weakest first

    total = anchors_chars + sum(len(c.text) for c in kept)
    while total > _EVIDENCE_BUDGET_CHARS and kept:
        dropped = kept.pop(0)
        total -= len(dropped.text)
        logger.info(
            "Trimmed expansion chunk to respect evidence budget: %s pg=%d idx=%d",
            dropped.filename, dropped.page_number, dropped.chunk_index,
        )
    return kept


def _gate_chunk(text: str, evidence_intent: str) -> RelevanceVerdict:
    client = get_gate_llm_client()
    system = build_relevance_system_prompt(evidence_intent)
    user = build_relevance_user_prompt(text)
    raw = client.complete(system, user)
    return parse_relevance_response(raw)


def _resolve_cleaned_text(original: str, verdict: RelevanceVerdict) -> str:
    if verdict.cleaned_text is None:
        return original
    if not _is_verbatim_subsequence(verdict.cleaned_text, original):
        logger.warning("Gate cleaning violated deletion-only constraint; using original text.")
        return original
    return verdict.cleaned_text


def _is_verbatim_subsequence(cleaned: str, original: str) -> bool:
    """True if `cleaned` only deletes content from `original` (whitespace-insensitive).

    Every non-whitespace character of `cleaned` must appear in `original` in
    the same relative order, proving the model only deleted spans rather than
    inserting, reordering, or altering text (ADR-0050).
    """
    candidate = _WHITESPACE_RE.sub("", cleaned)
    source = iter(_WHITESPACE_RE.sub("", original))
    return all(ch in source for ch in candidate)


def _to_rejected(chunk: RetrievedChunk, product_id: str) -> RejectedChunk:
    return RejectedChunk(
        filename=chunk.filename,
        page_number=chunk.page_number,
        chunk_index=chunk.chunk_index,
        expected_product_id=product_id,
    )
