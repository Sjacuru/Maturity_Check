from __future__ import annotations

import difflib
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from ingestion import get_retrieval_profile_store
from ingestion.retrieval_profile import ExpectedProductProfile
from retrieval import fetch_neighbor_chunks
from retrieval.interfaces.contracts import RetrievedChunk

from evaluation._config import get_gate_llm_client
from evaluation.interfaces.contracts import RejectedChunk
from evaluation.parsing.relevance_response import RelevanceVerdict, parse_relevance_response
from evaluation.prompt.relevance_builder import build_relevance_system_prompt, build_relevance_user_prompt

logger = logging.getLogger(__name__)

_ANCHOR_TARGET = 5
_EXPANSION_TARGET = 5

# Worst-case bound on candidates examined per product before giving up, even
# if fewer than _ANCHOR_TARGET were accepted. Without this, a strict gate
# model traverses the full fused BM25+vector candidate pool (up to ~40, since
# BM25's and vector's top-20 rarely overlap) — observed: 40+ gate calls for a
# single product (2026-06-28 live run). Trades thoroughness for a predictable
# latency ceiling: 46 actions in one interactive sitting cannot tolerate an
# unbounded per-product call count (ADR-0050 latency redesign, 2026-06-29).
_MAX_EXAMINED = 8

# Mirrors evaluator._MAX_EVIDENCE_CHARS — evidence_selection trims expansion
# chunks against the same ceiling _cap_evidence() enforces downstream as a
# final safety net for any residual overflow (ADR-0050).
_EVIDENCE_BUDGET_CHARS = 21_000

# Deterministic stripping of mechanical PDF-extraction noise (repeated
# header/address block, digital-signature block, version tag, vertically-
# rotated watermark) — applied before the chunk text ever reaches the LLM
# gate. The gate itself no longer attempts any further cleaning (dropped
# 2026-06-29): regenerating a cleaned copy of the chunk cost 50-86s per accept
# vs. ~4s for a bare yes/no, and the cleaning was unreliable enough (silent
# early-stop, few-shot regurgitation — see ADR-0050 amendments) that its
# output was rarely usable anyway. This deterministic pass is the only
# cleaning that happens now.
_HEADER_RE = re.compile(
    r"PREFEITURA DA CIDADE DO RIO DE JANEIRO\s*\n"
    r"Secretaria Municipal de Coordena[cç][aã]o Governamental\s*\n"
    # "Cavalcanti" — PDF ligature extraction sometimes mangles "ti" into a
    # single substitute glyph (observed: "Ɵ") or a 2-char CJK look-alike
    # (observed: "琀椀"); match either the clean spelling or 1-2 stand-in chars.
    r"R\. Afonso Cavalcan(?:ti|\S{1,2}), 455 [–-] Cidade Nova\s*\n"
    r"Rio de Janeiro - RJ - CEP 20211-110\s*\n?",
    re.IGNORECASE,
)

_SIGNATURE_BLOCK_RE = re.compile(
    r"(SMGPRO\d+V\d+\s*\n(MINUTA\s*\n)?)?"
    r"Autenticado digitalmente por .+? [aà]s \d{2}:\d{2}:\d{2}\.\s+"
    r"Documento N[ºo°]:.+?consulta [aà] autenticidade em\s+"
    r"https?://\S+\s*",
    re.IGNORECASE | re.DOTALL,
)

_BARE_VERSION_TAG_RE = re.compile(r"^SMGPRO\d+V\d+\s*\n(MINUTA\s*\n)?", re.MULTILINE)

# Vertically-rotated margin watermark, extracted one glyph per line by the PDF
# layout parser ("processo.rio Secretaria Municipal de... / SMG###"). Any run
# of 10+ consecutive single-character (or blank) lines is this artifact, never
# real prose; the trailing short alphanumeric line is the page-number tail,
# which doesn't get split the same way as the rest of the stamp.
_WATERMARK_RUN_RE = re.compile(r"(?:^[^\n]?\n){10,}(?:^[A-Za-z0-9]{1,6}\n?)?", re.MULTILINE)

# Similarity threshold for near-duplicate removal at the end of select_evidence().
# Two accepted chunks with SequenceMatcher.ratio() >= this are considered
# semantic duplicates — the later one (lower-priority) is discarded. 0.7 catches
# virtually-identical text that differs only in minor formatting/boilerplate prefix
# (e.g. the same "13 CONCLUSÃO: há viabilidade..." paragraph repeated verbatim
# across multiple contract lots), while staying well above the similarity of
# genuinely different legal clauses that share common terminology.
_SEMANTIC_DEDUP_THRESHOLD = 0.7
# Chunks shorter than this are skipped in semantic comparison — very short texts
# produce unreliable SequenceMatcher ratios (a 5-char "texto" vs "texto" hits 1.0,
# but "anchor0" vs "anchor1" hits 0.86 even though they're different identifiers).
# Real corpus chunks are always much longer than this (typical: 200-3000 chars).
_SEMANTIC_DEDUP_MIN_CHARS = 100
_SEMANTIC_DEDUP_WS_RE = re.compile(r"\s+")

# Pre-gate dedup threshold: higher than post-gate (0.92 vs 0.70) because it must
# be conservative enough that the gate would give identical verdicts to both copies.
# At 0.92+, texts are so similar (same clause on different pages, same lot
# repeating the same conclusion) that gating one is equivalent to gating all.
_PREGATE_DEDUP_THRESHOLD = 0.92


def strip_extraction_noise(text: str) -> str:
    text = _HEADER_RE.sub("", text)
    text = _SIGNATURE_BLOCK_RE.sub("", text)
    text = _BARE_VERSION_TAG_RE.sub("", text)
    text = _WATERMARK_RUN_RE.sub("", text)
    return text.strip()


@dataclass
class EvidenceSelectionResult:
    accepted: list[RetrievedChunk] = field(default_factory=list)
    rejected: list[RejectedChunk] = field(default_factory=list)


@dataclass
class _ProductSelection:
    anchors: list[tuple[float, RetrievedChunk]]
    expansions: list[tuple[float, RetrievedChunk]]
    rejected: list[RejectedChunk]


def _attribute_concepts(
    text: str,
    profile_product: ExpectedProductProfile,
) -> list[str]:
    """Return sorted concept keys whose query terms appear in text.

    Deterministic post-gate attribution: for each active query term, check
    whether a phrase term appears as a substring or all NEAR tokens appear
    individually. A concept is matched if at least one of its associated terms
    fires. Uses the same terms that drove BM25 retrieval, making attribution
    consistent with what the retrieval step was searching for.
    """
    text_lower = text.lower()
    matched: set[str] = set()
    for term in profile_product.query_terms:
        if term.status == "deprecated":
            continue  # experimental terms still contribute to attribution
        if term.concept_ref is None:
            continue
        if term.encoding == "phrase":
            if term.text.lower() in text_lower:
                matched.add(term.concept_ref)
        else:  # near — check all tokens present (proximity not enforced; presence sufficient for attribution)
            if all(tok.lower() in text_lower for tok in term.tokens):
                matched.add(term.concept_ref)
    return sorted(matched)


def _prefilter_near_duplicates(
    ranked: list[tuple[float, RetrievedChunk]],
    threshold: float = _PREGATE_DEDUP_THRESHOLD,
) -> list[tuple[float, RetrievedChunk]]:
    """Remove near-identical RRF candidates before gate evaluation.

    Candidates are processed in RRF priority order (highest score first). When
    two candidates have noise-stripped SequenceMatcher ratio >= threshold, the
    lower-ranked copy is dropped — the gate would give it the same verdict as
    the higher-ranked copy, so gating it is wasted computation. Using a higher
    threshold than post-gate dedup (0.92 vs 0.70) ensures conservatism: only
    drop when texts are so similar that gate verdict divergence is implausible.
    Short texts (< _SEMANTIC_DEDUP_MIN_CHARS) skip comparison and always pass.
    """
    kept: list[tuple[float, RetrievedChunk]] = []
    kept_norms: list[str] = []

    for score, chunk in ranked:
        stripped = strip_extraction_noise(chunk.text)
        norm = _SEMANTIC_DEDUP_WS_RE.sub(" ", stripped).strip().lower()
        if len(norm) < _SEMANTIC_DEDUP_MIN_CHARS:
            kept.append((score, chunk))
            kept_norms.append(norm)
            continue
        duplicate = False
        for existing_norm in kept_norms:
            if len(existing_norm) < _SEMANTIC_DEDUP_MIN_CHARS:
                continue
            if difflib.SequenceMatcher(None, norm, existing_norm, autojunk=False).ratio() >= threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append((score, chunk))
            kept_norms.append(norm)

    return kept


def select_evidence(
    acao_id: int,
    process_number: str,
    candidates: dict[str, list[tuple[float, RetrievedChunk]]],
) -> EvidenceSelectionResult:
    """LLM relevance gate + neighbor expansion (ADR-0050).

    Every candidate's text is first run through strip_extraction_noise()
    (deterministic — header/address block, signature block, version tag,
    vertically-rotated watermark) before anything else sees it. The gate
    itself only returns a binary relevant/not-relevant verdict — no cleaning.

    For each product: classifies up to _MAX_EXAMINED RRF-ranked candidates
    against the product's evidence_intent PLUS its retrieval_signal_concepts
    (in original RRF order) — the same curated concepts hybrid.py's vector
    query already uses (_vector_query_text()). Keeps the top _ANCHOR_TARGET
    relevant ones as anchors, fetches each anchor's immediate document
    neighbors and gates them too, keeping up to _EXPANSION_TARGET relevant
    neighbors per product. When the combined result exceeds the evidence
    character budget, expansion chunks are trimmed first — weakest
    anchor-score products first; anchors are never trimmed here
    (evaluator._cap_evidence() remains the final safety net for any residual
    overflow).

    Products with no evidence_intent in the retrieval profile pass through
    ungated (top _ANCHOR_TARGET candidates by score, noise-stripped, no
    expansion) — a safe degrade for Ações without a populated profile yet.

    The 4+ products are independent of each other and gated concurrently —
    each is I/O-bound (waiting on the local Ollama HTTP call), so threads
    give real wall-clock parallelism despite Python's GIL. Measured 2.4x
    speedup on 6-core/12-thread CPU-only hardware (2026-06-29); necessary to
    keep a 46-action interactive assessment within an acceptable total time.
    """
    profile_acao = get_retrieval_profile_store().acoes.get(acao_id)

    def _run(item: tuple[str, list[tuple[float, RetrievedChunk]]]) -> _ProductSelection:
        product_id, ranked = item
        profile_product = (
            profile_acao.expected_products.get(product_id) if profile_acao else None
        )
        return _select_for_product(
            product_id, _prefilter_near_duplicates(ranked), profile_product, process_number
        )

    with ThreadPoolExecutor(max_workers=max(len(candidates), 1)) as pool:
        results = list(pool.map(_run, candidates.items()))

    scored_anchors = [a for r in results for a in r.anchors]
    scored_expansions = [e for r in results for e in r.expansions]
    rejected = [rc for r in results for rc in r.rejected]

    deduped_anchors, deduped_expansions = _deduplicate_across_products(
        scored_anchors, scored_expansions
    )
    accepted_anchors = [chunk for _, chunk in deduped_anchors]
    accepted_expansions = _trim_expansions_to_budget(deduped_anchors, deduped_expansions)
    accepted = _dedup_semantic(accepted_anchors + accepted_expansions)

    return EvidenceSelectionResult(
        accepted=accepted,
        rejected=rejected,
    )


def _select_for_product(
    product_id: str,
    ranked: list[tuple[float, RetrievedChunk]],
    profile_product: ExpectedProductProfile | None,
    process_number: str,
) -> _ProductSelection:
    if profile_product is None or not profile_product.evidence_intent:
        anchors = [
            (score, chunk.model_copy(update={"text": strip_extraction_noise(chunk.text)}))
            for score, chunk in ranked[:_ANCHOR_TARGET]
        ]
        return _ProductSelection(anchors=anchors, expansions=[], rejected=[])

    evidence_intent = profile_product.evidence_intent
    concepts = [c.text for c in profile_product.retrieval_signal_concepts]
    rejected: list[RejectedChunk] = []
    product_anchors: list[tuple[float, RetrievedChunk]] = []

    for score, chunk in ranked[:_MAX_EXAMINED]:
        if len(product_anchors) >= _ANCHOR_TARGET:
            break
        stripped_text = strip_extraction_noise(chunk.text)
        verdict = _gate_chunk(stripped_text, evidence_intent, concepts)
        matched = _attribute_concepts(stripped_text, profile_product)
        if not verdict.relevant:
            rejected.append(_to_rejected(chunk, product_id, matched))
            continue
        product_anchors.append((score, chunk.model_copy(update={
            "text": stripped_text,
            "matched_concepts": matched,
        })))

    expansions = _expand_anchors(
        product_anchors, product_id, process_number, evidence_intent, concepts, rejected,
        profile_product=profile_product,
    )
    return _ProductSelection(anchors=product_anchors, expansions=expansions, rejected=rejected)


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
    concepts: list[str],
    rejected: list[RejectedChunk],
    profile_product: ExpectedProductProfile | None = None,
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
            stripped_text = strip_extraction_noise(neighbor.text)
            verdict = _gate_chunk(stripped_text, evidence_intent, concepts)
            matched = (
                _attribute_concepts(stripped_text, profile_product)
                if profile_product else []
            )
            if not verdict.relevant:
                rejected.append(_to_rejected(neighbor, product_id, matched))
                continue
            expanded = neighbor.model_copy(update={
                "text": stripped_text,
                "expected_product_id": product_id,
                "matched_concepts": matched,
            })
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


def _dedup_semantic(
    chunks: list[RetrievedChunk],
    threshold: float = _SEMANTIC_DEDUP_THRESHOLD,
) -> list[RetrievedChunk]:
    """Drop near-duplicate accepted chunks whose text is ≥ threshold similar.

    Physical-key dedup (_deduplicate_across_products) cannot catch same-content
    text appearing on different pages or in different lots of the same document —
    e.g. the identical '13 CONCLUSÃO: há viabilidade econômico-financeira...'
    paragraph repeated verbatim in three pages across three contract versions.
    Sending duplicates wastes the evidence budget and gives the scorer
    repetition where it expects diversity. The earlier/higher-priority chunk
    always wins; order is preserved. Uses difflib.SequenceMatcher for
    determinism — no LLM call. Threshold configurable so callers/tests can
    override without patching a module constant.
    """
    def _norm(text: str) -> str:
        return _SEMANTIC_DEDUP_WS_RE.sub(" ", text).strip().lower()

    kept: list[RetrievedChunk] = []
    kept_norms: list[str] = []

    for chunk in chunks:
        norm = _norm(chunk.text)
        # Skip similarity check for very short texts — they produce unreliable
        # ratios and real corpus chunks are always much longer than this floor.
        if len(norm) < _SEMANTIC_DEDUP_MIN_CHARS:
            kept.append(chunk)
            kept_norms.append(norm)
            continue
        duplicate = False
        for existing_norm in kept_norms:
            if len(existing_norm) < _SEMANTIC_DEDUP_MIN_CHARS:
                continue
            if difflib.SequenceMatcher(None, norm, existing_norm, autojunk=False).ratio() >= threshold:
                duplicate = True
                break
        if duplicate:
            logger.info(
                "Semantic dedup dropped near-duplicate: %s pg=%d idx=%d",
                chunk.filename, chunk.page_number, chunk.chunk_index,
            )
        else:
            kept.append(chunk)
            kept_norms.append(norm)

    return kept


def _gate_chunk(text: str, evidence_intent: str, concepts: list[str]) -> RelevanceVerdict:
    client = get_gate_llm_client()
    system = build_relevance_system_prompt(evidence_intent, concepts)
    user = build_relevance_user_prompt(text)
    raw = client.complete(system, user)
    return parse_relevance_response(raw)


def _to_rejected(
    chunk: RetrievedChunk,
    product_id: str,
    matched_concepts: list[str] | None = None,
) -> RejectedChunk:
    return RejectedChunk(
        filename=chunk.filename,
        page_number=chunk.page_number,
        chunk_index=chunk.chunk_index,
        expected_product_id=product_id,
        matched_concepts=matched_concepts or [],
    )
