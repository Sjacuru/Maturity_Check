from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from extraction.noise import strip_extraction_noise
from ingestion import get_genre_exemption_store, get_ipmp_store, get_retrieval_profile_store
from ingestion.retrieval_profile import ExpectedProductProfile
from retrieval import fetch_neighbor_chunks, get_chunk_genres
from retrieval.genre import INSTRUMENT
from retrieval.interfaces.contracts import RetrievedChunk

from evaluation._config import get_gate_ledger, get_gate_llm_client
from evaluation.interfaces.contracts import ProductGateReport, RejectedChunk
from evaluation.llm.llamacpp import LlamaCppTruncated
from evaluation.parsing.relevance_response import RelevanceVerdict, parse_relevance_response
from evaluation.progress import report
from evaluation.prompt.relevance_builder import build_relevance_system_prompt, build_relevance_user_prompt
from evaluation.schemas import GATE_SCHEMA

logger = logging.getLogger(__name__)

# How many accepted candidates are KEPT per product. Not how many are
# examined: since 2026-10-05 the gate walks the whole examined pool whatever
# the verdicts are. It used to stop at the 5th accept, which made the list of
# questions depend on the answers -- measured consequence: of the differences
# between two clean passes over the same documents, part came from chunks that
# were never even asked in one of them, not from a verdict that changed.
_ANCHOR_TARGET = 5
_EXPANSION_TARGET = 5

# Neighbour expansion: gate the previous/next chunk of each ACCEPTED chunk.
# Off from 2026-10-06 to 2026-10-13, because the question it asks depends on
# an answer: a flip on an accept changes WHICH chunks are gated, not just how
# one is judged (ADR-0069: with it on, the per-product n_examined vector
# repeated in 26/46 Ações over clean passes; without it, 46/46).
# Back on since 2026-10-13 by the user's decision, behind the genre filter
# (ADR-0074): a neighbour is gated only when its document is NOT instrument
# text -- the rule the candidates pass through, applied to every product,
# exempt ones included. The neighbours of an accepted passage are mostly pages
# of the same document; with instrument text gone, what is left to expand is
# the passages of studies, opinions and acts. A neighbour already judged for
# the product in this pass is not asked again. Test cycle 3 measures what this
# costs in constancy; reproducibility.py --no-expansion turns it off.
EXPANSION_ENABLED = True

# Genre filter (ADR-0074). For every Expected Product whose IPMP criterion is
# not the instrument itself (data/ipmp/isencoes_genero.json lists the ones
# that are), candidates from documents of genre INSTRUMENTO -- contract or
# minuta, edital, termo de referência and their normative annexes -- are
# removed BEFORE the near-duplicate prefilter and the _MAX_EXAMINED cut, so the
# examined pool is filled by the best-ranked candidates that are not
# instrument text. Over the ten processes of test cycle 2, 90 of the 101
# confound pairs that the gate accepted at random were contract, edital or TR
# text. The genre is the DOCUMENT's, read from the canonical document index
# (retrieval.genre), not a vote of the chunk alone. Switchable for
# diagnostics: reproducibility.py --no-genre-filter.
GENRE_FILTER_ENABLED = True

# Narrative sections (ADR-0077). Inside an instrument document, the passages
# of a section titled as narrative (introduction, context, history,
# justification, conclusion...) are not the normative text the filter exists
# to remove: the index marks them and the filter lets them through, for every
# product. Test cycle 11 (10 full processes): constancy 40/46 as in cycle 8,
# no confusion accepted in 5+ of 10, the TR's statement of the concession's
# objectives accepted for 1c in 10/10. Switchable for diagnostics:
# reproducibility.py --no-narrative-sections.
NARRATIVE_SECTIONS_ENABLED = True

# Worst-case bound on candidates examined per product before giving up, even
# if fewer than _ANCHOR_TARGET were accepted. Without this, a strict gate
# model traverses the full fused BM25+vector candidate pool (up to ~40, since
# BM25's and vector's top-20 rarely overlap) — observed: 40+ gate calls for a
# single product (2026-06-28 live run). Trades thoroughness for a predictable
# latency ceiling: 46 actions in one interactive sitting cannot tolerate an
# unbounded per-product call count (ADR-0050 latency redesign, 2026-06-29).
#
# 8 -> 16 on 2026-10-03: at 8, 161 of the 164 products hit the cap and 49.8 %
# of the distinct fused candidates never reached the gate; Ação 3's validated
# evidence (p.158) sat at rank 10 and could never be examined. With one call in
# flight at reasoning_effort=low (ADR-0065) a gate call costs ~0.7-1.0 s, so the
# doubled cap is affordable. _ANCHOR_TARGET is unchanged, so the evidence volume
# sent to the scorer is bounded exactly as before.
_MAX_EXAMINED = 16

# How many gate calls may be in flight to the server at once. 1 = the products
# are gated one after the other, in scored-product order, each product's
# candidates in RRF rank order - the same fixed call sequence the 2026-10-02
# measurements used. Under 4 concurrent calls the same prompt reached up to 8
# distinct verdict trajectories in 8 passes; with one call in flight and the
# gate model at reasoning_effort=low, 0/80 chunks were unstable across Acoes
# 14, 22 and 3 (ADR-0065). main.py gives the gate client the same number as its
# request semaphore, so this constant is the single knob.
GATE_MAX_IN_FLIGHT = 1

# Mirrors evaluator._MAX_EVIDENCE_CHARS — evidence_selection trims expansion
# chunks against the same ceiling _cap_evidence() enforces downstream as a
# final safety net for any residual overflow (ADR-0050). Raised 21,000 ->
# 40,000 on 2026-09-28 in lockstep with it; see the derivation in evaluator.py.
# These two must move together — whichever is lower is the one that actually
# binds, so raising only one changes nothing. evaluator moved to 70,000 on
# 2026-10-06 while expansion was off, so this one was never reached; it
# follows now that expansion is back (ADR-0074).
_EVIDENCE_BUDGET_CHARS = 70_000

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


@dataclass
class EvidenceSelectionResult:
    accepted: list[RetrievedChunk] = field(default_factory=list)
    rejected: list[RejectedChunk] = field(default_factory=list)
    # Per-product gate telemetry (one entry per product examined). Lets the
    # caller distinguish "the gate judged everything irrelevant" from "the gate
    # never managed to judge", and record which provider decided — neither was
    # observable before 2026-09-27.
    product_reports: list[ProductGateReport] = field(default_factory=list)


@dataclass
class _GateCall:
    """One gate verdict plus who produced it and the reasoning behind it."""

    verdict: RelevanceVerdict
    provider: str | None
    model: str | None
    reasoning: str | None = None
    source: str = "model"          # "model" | "ledger" | "auditor" (ADR-0067)
    prompt_hash: str | None = None


@dataclass
class _GateStats:
    """Mutable accumulator threaded through anchor selection and expansion, so
    both phases' calls land in the same ProductGateReport."""

    n_candidates: int = 0
    n_examined: int = 0
    n_accepted: int = 0
    n_rejected: int = 0
    n_failures: int = 0
    n_ledger_hits: int = 0
    n_genre_excluded: int = 0
    n_neighbors_genre_excluded: int = 0
    providers: set[str] = field(default_factory=set)
    models: set[str] = field(default_factory=set)

    def record(self, call: _GateCall) -> None:
        self.n_examined += 1
        if call.source != "model":
            self.n_ledger_hits += 1
        if call.provider:
            self.providers.add(call.provider)
        if call.model:
            self.models.add(call.model)
        if call.verdict.parse_failed:
            self.n_failures += 1
        elif call.verdict.relevant:
            self.n_accepted += 1
        else:
            self.n_rejected += 1

    def to_report(self, product_id: str) -> ProductGateReport:
        return ProductGateReport(
            expected_product_id=product_id,
            n_candidates=self.n_candidates,
            n_examined=self.n_examined,
            n_accepted=self.n_accepted,
            n_rejected=self.n_rejected,
            n_gate_failures=self.n_failures,
            providers=sorted(self.providers),
            models=sorted(self.models),
            n_ledger_hits=self.n_ledger_hits,
            n_genre_excluded=self.n_genre_excluded,
            n_neighbors_genre_excluded=self.n_neighbors_genre_excluded,
        )


@dataclass
class _ProductSelection:
    anchors: list[tuple[float, RetrievedChunk]]
    expansions: list[tuple[float, RetrievedChunk]]
    rejected: list[RejectedChunk]
    report: ProductGateReport | None = None


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
    two candidates have noise-stripped rapidfuzz ratio >= threshold, the
    lower-ranked copy is dropped — the gate would give it the same verdict as
    the higher-ranked copy, so gating it is wasted computation. Using a higher
    threshold than post-gate dedup (0.92 vs 0.70) ensures conservatism: only
    drop when texts are so similar that gate verdict divergence is implausible.
    Short texts (< _SEMANTIC_DEDUP_MIN_CHARS) skip comparison and always pass.

    rapidfuzz.fuzz.ratio (C-accelerated) replaced difflib.SequenceMatcher here
    2026-08-14: measured 547x faster on realistic candidate volumes (~40
    candidates/product), and this step — pure string comparison, no LLM
    involved — was consuming 100-180s per product, the single largest time
    sink in a full run (more than all gate LLM calls combined). Both are
    0-100/0-1 normalized edit-distance-based similarity measures; the 0.92/0.70
    thresholds carry over unchanged (divide rapidfuzz's 0-100 by 100 below).
    """
    threshold_pct = threshold * 100
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
            if fuzz.ratio(norm, existing_norm) >= threshold_pct:
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

    For each product: classifies the _MAX_EXAMINED top RRF-ranked candidates
    against the product's evidence_intent PLUS its retrieval_signal_concepts
    (in original RRF order) — the same curated concepts hybrid.py's vector
    query already uses (_vector_query_text()). All of them are classified, in
    every pass, whatever the verdicts are: retrieval is deterministic, so the
    set of questions asked is too. Keeps the top _ANCHOR_TARGET
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

    The products are independent of each other. They USED to be gated
    concurrently (measured 2.4x speedup on CPU-only Ollama, 2026-06-29); since
    ADR-0065 the default is one gate call in flight, in a fixed order (see
    GATE_MAX_IN_FLIGHT) — concurrency on the GPU server was the largest single
    source of verdict non-determinism, and reasoning_effort=low makes the
    serial gate cost about what the concurrent one did.
    """
    profile_acao = get_retrieval_profile_store().acoes.get(acao_id)
    # Identity for the gate prompt: which Acao and which Expected Product this
    # judgement belongs to. Resolved once here rather than per call.
    acao = get_ipmp_store().acoes.get(acao_id)
    # ADR-0074: the genre of every chunk, by its document, resolved once per
    # Ação before any product is gated -- the index is built or found current
    # here, never in the middle of a pass.
    genres = _chunk_genres(process_number) if GENRE_FILTER_ENABLED else {}
    exempt = get_genre_exemption_store().produtos(acao_id)

    gate_client = get_gate_llm_client()
    describe_route = getattr(gate_client, "describe_route", None)
    if describe_route is not None:
        report("selecionando_llm", f"Gate de relevância: {describe_route()}.")

    mode = (
        "em sequência, 1 chamada em voo (ADR-0065)"
        if GATE_MAX_IN_FLIGHT <= 1
        else f"até {GATE_MAX_IN_FLIGHT} chamadas em voo"
    )
    report(
        "avaliando_relevancia",
        f"Iniciando gate de relevância — {len(candidates)} produto(s), {mode}.",
    )

    # One memo per select_evidence call -- one Acao, one pass. No lock: each
    # product is handled by exactly one worker and its prompts carry its own
    # product block, so two workers never write the same key.
    gate_memo: dict[str, _GateCall] = {}

    def _run(item: tuple[str, list[tuple[float, RetrievedChunk]]]) -> _ProductSelection:
        product_id, ranked = item
        profile_product = (
            profile_acao.expected_products.get(product_id) if profile_acao else None
        )
        n_excluded = 0
        if genres and product_id not in exempt:
            ranked, n_excluded = _drop_instrument_text(ranked, genres)
        ranked = _drop_empty_text(ranked)
        deduped = _prefilter_near_duplicates(ranked)
        return _select_for_product(
            product_id, deduped, profile_product, process_number, acao, memo=gate_memo,
            genres=genres, n_genre_excluded=n_excluded,
        )

    if GATE_MAX_IN_FLIGHT <= 1:
        # Fixed order: dict insertion order is hybrid.py's scored-product order,
        # and _select_for_product walks each product's candidates by RRF rank.
        results = [_run(item) for item in candidates.items()]
    else:
        with ThreadPoolExecutor(
            max_workers=max(1, min(len(candidates), GATE_MAX_IN_FLIGHT))
        ) as pool:
            results = list(pool.map(_run, candidates.items()))

    scored_anchors = [a for r in results for a in r.anchors]
    scored_expansions = [e for r in results for e in r.expansions]
    rejected = [rc for r in results for rc in r.rejected]
    product_reports = [r.report for r in results if r.report is not None]

    total_failures = sum(rep.n_gate_failures for rep in product_reports)
    if total_failures:
        report(
            "avaliando_relevancia",
            f"Atenção: {total_failures} chamada(s) do gate falharam nesta Ação - "
            "os trechos correspondentes foram descartados sem julgamento.",
            "warning",
        )

    deduped_anchors, deduped_expansions = _deduplicate_across_products(
        scored_anchors, scored_expansions
    )
    accepted_anchors = [chunk for _, chunk in deduped_anchors]
    accepted_expansions = _trim_expansions_to_budget(deduped_anchors, deduped_expansions)
    accepted = _dedup_semantic_per_product(accepted_anchors + accepted_expansions)

    return EvidenceSelectionResult(
        accepted=accepted,
        rejected=rejected,
        product_reports=sorted(product_reports, key=lambda r: r.expected_product_id),
    )


def _select_for_product(
    product_id: str,
    ranked: list[tuple[float, RetrievedChunk]],
    profile_product: ExpectedProductProfile | None,
    process_number: str,
    acao=None,
    memo: dict[str, _GateCall] | None = None,
    genres: dict[tuple[str, int, int], str] | None = None,
    n_genre_excluded: int = 0,
) -> _ProductSelection:
    if profile_product is None or not profile_product.evidence_intent:
        anchors = [
            (score, chunk.model_copy(update={"text": strip_extraction_noise(chunk.text)}))
            for score, chunk in ranked[:_ANCHOR_TARGET]
        ]
        # Ungated degrade path: no gate call was made, so there is nothing to
        # report beyond how many candidates went straight through.
        stats = _GateStats(
            n_candidates=len(ranked), n_accepted=len(anchors), n_genre_excluded=n_genre_excluded
        )
        return _ProductSelection(
            anchors=anchors, expansions=[], rejected=[], report=stats.to_report(product_id)
        )

    evidence_intent = profile_product.evidence_intent
    concepts = [c.text for c in profile_product.retrieval_signal_concepts]
    rejected: list[RejectedChunk] = []
    product_anchors: list[tuple[float, RetrievedChunk]] = []
    stats = _GateStats(n_candidates=len(ranked), n_genre_excluded=n_genre_excluded)

    examined_pool = ranked[:_MAX_EXAMINED]
    excluded = (
        f" ({n_genre_excluded} de texto de instrumento retirado(s) antes do gate)"
        if n_genre_excluded else ""
    )
    report(
        "avaliando_relevancia",
        f"Produto {product_id}: avaliando até {len(examined_pool)} candidato(s){excluded}...",
    )
    negative_patterns = profile_product.negative_evidence_patterns
    for score, chunk in examined_pool:
        stripped_text = strip_extraction_noise(chunk.text)
        call = _gate_chunk(
            stripped_text, evidence_intent, concepts, negative_patterns,
            acao=acao, product_id=product_id,
            chunk=chunk, process_number=process_number, memo=memo,
        )
        stats.record(call)
        matched = _attribute_concepts(stripped_text, profile_product)
        if not call.verdict.relevant:
            rejected.append(_to_rejected(chunk, product_id, matched, call))
            continue
        if len(product_anchors) >= _ANCHOR_TARGET:
            # Accepted, but the anchor cap is full. Not kept -- the evidence
            # delivered is the same first _ANCHOR_TARGET accepts in rank order
            # as before. What changed is that it was still ASKED: the examined
            # pool must be a function of retrieval alone.
            continue
        product_anchors.append((score, chunk.model_copy(update={
            "text": stripped_text,
            "expected_product_ids": [product_id],
            "matched_concepts": matched,
            "gate_reasoning": _reasoning_entry(product_id, call),
            "gate_source": {product_id: call.source},
            "gate_prompt_hash": _hash_entry(product_id, call),
        })))

    expansions = (
        _expand_anchors(
            product_anchors, product_id, process_number, evidence_intent, concepts, rejected,
            profile_product=profile_product, stats=stats, acao=acao, memo=memo,
            genres=genres, skip_keys={_natural_key(chunk) for _, chunk in examined_pool},
        )
        if EXPANSION_ENABLED
        else []
    )
    failures = f", {stats.n_failures} falha(s) de gate" if stats.n_failures else ""
    report(
        "avaliando_relevancia",
        f"Produto {product_id}: {len(product_anchors)} aceito(s), "
        f"{len(rejected)} descartado(s){failures}.",
        "warning" if stats.n_failures else "info",
    )
    if stats.n_failures:
        logger.warning(
            "Product %s: %d of %d gate calls failed - those chunks were dropped "
            "unjudged, so this product's evidence set is incomplete for reasons "
            "unrelated to relevance.",
            product_id, stats.n_failures, stats.n_examined,
        )
    return _ProductSelection(
        anchors=product_anchors,
        expansions=expansions,
        rejected=rejected,
        report=stats.to_report(product_id),
    )


def _natural_key(chunk: RetrievedChunk) -> tuple[str, int, int]:
    return (chunk.filename, chunk.page_number, chunk.chunk_index)


def _chunk_genres(process_number: str) -> dict[tuple[str, int, int], str]:
    """Genre of every chunk of the process, by its document (ADR-0074), with
    the narrative sections of instrument documents read as OUTRO (ADR-0077).

    The one seam to the canonical document index: tests replace it, production
    reads (and, when stale, rebuilds) the index next to the chunks.
    """
    return get_chunk_genres(process_number, release_narrative_sections=NARRATIVE_SECTIONS_ENABLED)


def _drop_instrument_text(
    ranked: list[tuple[float, RetrievedChunk]],
    genres: dict[tuple[str, int, int], str],
) -> tuple[list[tuple[float, RetrievedChunk]], int]:
    """The candidates whose document is not instrument text, in rank order,
    and how many were removed. A chunk the index does not know is kept: in
    doubt, the classifier's rule is OUTRO."""
    kept = [(score, chunk) for score, chunk in ranked
            if genres.get(_natural_key(chunk)) != INSTRUMENT]
    return kept, len(ranked) - len(kept)


def _drop_empty_text(
    ranked: list[tuple[float, RetrievedChunk]],
) -> list[tuple[float, RetrievedChunk]]:
    """The candidates that still have text once the extraction noise is
    stripped. A chunk that is nothing but noise -- the rest of a signature
    stamp the chunker cut off its page, "em https://..." -- has no passage
    to judge, so it never takes a place in the examined pool."""
    return [(score, chunk) for score, chunk in ranked if strip_extraction_noise(chunk.text)]


def filter_focal_document(
    acao_id: int,
    process_number: str,
    chunks: list[RetrievedChunk],
) -> list[RetrievedChunk] | None:
    """The Step A/B route (one focal document, ungated) under the genre filter.

    A focal document reaches the scorer unattributed, with no product block of
    its own, so its instrument text cannot be kept for one product and removed
    for another. Returns the chunks to use, or None to fall through to the
    per-product hybrid route:
      * the filter is off, or the document has no instrument chunk -> as it is
      * every scored product of the Ação is exempt -> as it is
      * some products exempt and some not -> None (only the per-product route
        can keep instrument text for the exempt products alone)
      * no product exempt -> the document without its instrument chunks, or
        None when nothing is left
    """
    if not GENRE_FILTER_ENABLED or not chunks:
        return chunks
    genres = _chunk_genres(process_number)
    if not any(genres.get(_natural_key(c)) == INSTRUMENT for c in chunks):
        return chunks
    acao = get_ipmp_store().acoes.get(acao_id)
    scored = {p.id for p in acao.produtos_esperados if p.scored} if acao else set()
    exempt = get_genre_exemption_store().produtos(acao_id) & scored
    if scored and exempt == scored:
        return chunks
    if exempt:
        return None
    kept = [c for c in chunks if genres.get(_natural_key(c)) != INSTRUMENT]
    return kept or None


def _deduplicate_across_products(
    scored_anchors: list[tuple[float, RetrievedChunk]],
    scored_expansions: list[tuple[float, RetrievedChunk]],
) -> tuple[list[tuple[float, RetrievedChunk]], list[tuple[float, RetrievedChunk]]]:
    """Collapse the same physical chunk accepted by multiple products to one copy.

    Final scoring is a single combined LLM call across all products (ADR-0009).
    A chunk accepted by multiple products' gates reaches evaluate() only once,
    but carries ALL product attributions merged into expected_product_ids — so
    build_user_prompt() can place it in every relevant product block.
    Anchors win over expansions for the same physical chunk (higher-confidence
    inclusion); within each tier, the highest-scoring copy wins for tie-breaking
    while ALL product IDs are merged. Mirrors ADR-0049's tie-break rule.
    """
    best_anchor: dict[tuple[str, int, int], tuple[float, RetrievedChunk]] = {}
    for score, chunk in scored_anchors:
        key = _natural_key(chunk)
        if key not in best_anchor:
            best_anchor[key] = (score, chunk)
        else:
            existing_score, existing = best_anchor[key]
            winner = existing if existing_score >= score else chunk
            best_anchor[key] = (max(existing_score, score), _merge_attribution(winner, existing, chunk))
    anchor_keys = set(best_anchor.keys())

    best_expansion: dict[tuple[str, int, int], tuple[float, RetrievedChunk]] = {}
    for score, chunk in scored_expansions:
        key = _natural_key(chunk)
        if key in anchor_keys:
            # Anchor already includes this chunk — merge the expansion's product IDs in.
            existing_score, existing = best_anchor[key]
            best_anchor[key] = (existing_score, _merge_attribution(existing, existing, chunk))
            continue
        if key not in best_expansion:
            best_expansion[key] = (score, chunk)
        else:
            existing_score, existing = best_expansion[key]
            winner = existing if existing_score >= score else chunk
            best_expansion[key] = (max(existing_score, score), _merge_attribution(winner, existing, chunk))

    return list(best_anchor.values()), list(best_expansion.values())


def _merge_attribution(
    winner: RetrievedChunk, a: RetrievedChunk, b: RetrievedChunk
) -> RetrievedChunk:
    """The winner's copy with both chunks' product ids and per-product gate
    reasoning merged in — one physical chunk, every product that accepted it."""
    merged_ids = sorted(set(a.expected_product_ids + b.expected_product_ids))
    return winner.model_copy(update={
        "expected_product_ids": merged_ids,
        "gate_reasoning": {**a.gate_reasoning, **b.gate_reasoning},
        "gate_source": {**a.gate_source, **b.gate_source},
        "gate_prompt_hash": {**a.gate_prompt_hash, **b.gate_prompt_hash},
    })


def _reasoning_entry(product_id: str, call: _GateCall) -> dict[str, str]:
    return {product_id: call.reasoning} if call.reasoning else {}


def _hash_entry(product_id: str, call: _GateCall) -> dict[str, str]:
    return {product_id: call.prompt_hash} if call.prompt_hash else {}


def _expand_anchors(
    product_anchors: list[tuple[float, RetrievedChunk]],
    product_id: str,
    process_number: str,
    evidence_intent: str,
    concepts: list[str],
    rejected: list[RejectedChunk],
    profile_product: ExpectedProductProfile | None = None,
    stats: _GateStats | None = None,
    acao=None,
    memo: dict[str, _GateCall] | None = None,
    genres: dict[tuple[str, int, int], str] | None = None,
    skip_keys: set[tuple[str, int, int]] | None = None,
) -> list[tuple[float, RetrievedChunk]]:
    """Gate the previous/next chunk of each anchor, up to _EXPANSION_TARGET
    accepted neighbours per product.

    A neighbour whose document is instrument text (genres, ADR-0074) is not
    gated, for any product. A neighbour already judged for this product in
    this pass -- a member of the examined pool (skip_keys) or the neighbour of
    an earlier anchor -- is not asked again: its answer is already known, and
    re-asking only duplicated the rejected rows and spent expansion slots on
    chunks that were already anchors. A neighbour left with no text once the
    extraction noise is stripped is not gated either.
    """
    negative_patterns = profile_product.negative_evidence_patterns if profile_product else []
    product_expansions: list[tuple[float, RetrievedChunk]] = []
    seen: set[tuple[str, int, int]] = set(skip_keys or ())
    for anchor_score, anchor in product_anchors:
        if len(product_expansions) >= _EXPANSION_TARGET:
            break
        prev_chunk, next_chunk = fetch_neighbor_chunks(
            process_number, anchor.filename, anchor.page_number, anchor.chunk_index
        )
        for neighbor in (c for c in (prev_chunk, next_chunk) if c is not None):
            if len(product_expansions) >= _EXPANSION_TARGET:
                break
            key = _natural_key(neighbor)
            if key in seen:
                continue
            seen.add(key)
            if genres and genres.get(key) == INSTRUMENT:
                if stats is not None:
                    stats.n_neighbors_genre_excluded += 1
                continue
            stripped_text = strip_extraction_noise(neighbor.text)
            if not stripped_text:
                # Nothing but extraction noise (the rest of a signature stamp
                # the chunker cut): there is no passage to judge.
                continue
            call = _gate_chunk(
                stripped_text, evidence_intent, concepts, negative_patterns,
                acao=acao, product_id=product_id,
                chunk=neighbor, process_number=process_number, memo=memo,
            )
            if stats is not None:
                stats.record(call)
            matched = (
                _attribute_concepts(stripped_text, profile_product)
                if profile_product else []
            )
            if not call.verdict.relevant:
                rejected.append(_to_rejected(neighbor, product_id, matched, call))
                continue
            expanded = neighbor.model_copy(update={
                "text": stripped_text,
                "expected_product_ids": [product_id],
                "matched_concepts": matched,
                "gate_reasoning": _reasoning_entry(product_id, call),
                "gate_source": {product_id: call.source},
                "gate_prompt_hash": _hash_entry(product_id, call),
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
    always wins; order is preserved. Uses rapidfuzz (C-accelerated, replaced
    difflib.SequenceMatcher 2026-08-14 — see _prefilter_near_duplicates) for
    determinism — no LLM call. Threshold configurable so callers/tests can
    override without patching a module constant.
    """
    threshold_pct = threshold * 100

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
            if fuzz.ratio(norm, existing_norm) >= threshold_pct:
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


def _dedup_semantic_per_product(
    chunks: list[RetrievedChunk],
    threshold: float = _SEMANTIC_DEDUP_THRESHOLD,
) -> list[RetrievedChunk]:
    """Near-duplicate dedup WITHIN each Expected Product, never across them.

    _dedup_semantic() ran over the whole Ação's accepted list and dropped the
    later chunk without transferring its attribution, so a product could lose
    its only evidence to a >= threshold-similar chunk accepted by a different
    product — and since the score counts evidenced products (ADR-0058), that
    silently turned a bit off. Each product now compares only against its own
    chunks: a chunk leaves the batch only when it is a duplicate for every
    product that attributed it, and otherwise stays with its attribution
    narrowed to the products that kept it.

    Deliberate consequence: the same text may now appear in two different
    product blocks of the scorer prompt. That is what the criterion asks for —
    each product is judged on its own evidence — and it costs evidence budget,
    which _cap_evidence bounds.
    """
    def _norm(text: str) -> str:
        return _SEMANTIC_DEDUP_WS_RE.sub(" ", text).strip().lower()

    threshold_pct = threshold * 100
    by_product: dict[str, list[RetrievedChunk]] = {}
    unattributed: list[RetrievedChunk] = []
    for chunk in chunks:
        if not chunk.expected_product_ids:
            unattributed.append(chunk)
            continue
        for product_id in chunk.expected_product_ids:
            by_product.setdefault(product_id, []).append(chunk)

    keep: dict[tuple[str, int, int], set[str]] = {}
    for product_id in sorted(by_product):
        kept_norms: list[str] = []
        for chunk in by_product[product_id]:
            norm = _norm(chunk.text)
            if len(norm) >= _SEMANTIC_DEDUP_MIN_CHARS and any(
                len(existing) >= _SEMANTIC_DEDUP_MIN_CHARS
                and fuzz.ratio(norm, existing) >= threshold_pct
                for existing in kept_norms
            ):
                logger.info(
                    "Semantic dedup dropped near-duplicate for %s: %s pg=%d idx=%d",
                    product_id, chunk.filename, chunk.page_number, chunk.chunk_index,
                )
                continue
            kept_norms.append(norm)
            keep.setdefault(_natural_key(chunk), set()).add(product_id)

    # Original order preserved: only membership and attribution change here.
    out = _dedup_semantic(unattributed, threshold)
    for chunk in chunks:
        if not chunk.expected_product_ids:
            continue
        kept_for = keep.get(_natural_key(chunk))
        if not kept_for:
            continue
        out.append(
            chunk if set(chunk.expected_product_ids) == kept_for
            else chunk.model_copy(update={"expected_product_ids": sorted(kept_for)})
        )
    return out


def _gate_chunk(
    text: str,
    evidence_intent: str,
    concepts: list[str],
    negative_patterns: list[str] | None = None,
    acao=None,
    product_id: str | None = None,
    chunk: RetrievedChunk | None = None,
    process_number: str | None = None,
    memo: dict[str, _GateCall] | None = None,
) -> _GateCall:
    """One gate call, returning the verdict plus which provider/model served it.

    memo, when given, holds the verdicts already produced in THIS pass, keyed
    by the same prompt hash. A chunk can reach the gate twice for one product
    in a single pass -- once from ranked[:_MAX_EXAMINED], once as the neighbour
    of an accepted chunk -- and answering the identical question twice with two
    different verdicts is incoherent. The memo makes the second occurrence
    deterministic without a ledger; it is created per select_evidence call, so
    nothing survives into the next pass.

    With a gate ledger configured (ADR-0067) the call is first looked up by
    the hash of (model, reasoning effort, system prompt, user prompt); a hit
    is returned without asking the model, and a fresh successful verdict is
    recorded so the next identical call is answered the same way. chunk and
    process_number only annotate the ledger row for the auditor.

    A LlamaCppTruncated (the server hit its token cap mid-answer) is converted
    into a FAILED verdict rather than being allowed to look like "not
    relevant" — gpt-oss emits the schema-constrained JSON after an
    unconstrained reasoning channel, so a cap firing mid-reasoning yields empty
    content that json.loads() rejects. The chunk is then dropped without
    judgement, which is materially different from being judged irrelevant, and
    _GateStats counts it separately.

    Transport failures (LlamaCppUnavailable/Timeout/Busy) are deliberately NOT
    caught: with the GPU-only wiring there is no fallback, so a server outage
    must abort the run loudly instead of quietly producing an assessment in
    which every product looks unevidenced.

    Deliberately ONE call, not a best-of-N vote: voting was implemented,
    measured over a full sweep and reverted — see ADR-0061 for why majority
    voting cannot stabilise this gate.
    """
    client = get_gate_llm_client()
    system = build_relevance_system_prompt(
        evidence_intent, concepts, negative_patterns,
        acao=acao, product_id=product_id,
    )
    user = build_relevance_user_prompt(text, product_id=product_id)
    from evaluation.gate_ledger import prompt_hash

    # Computed whether or not a ledger is configured: the in-pass memo is keyed
    # on the same hash, so the two mechanisms cannot disagree about what counts
    # as "the same question".
    key = prompt_hash(
        _ledger_model(client), getattr(client, "reasoning_effort", None), system, user
    )
    if memo is not None and key in memo:
        return memo[key]
    ledger = get_gate_ledger()
    if ledger is not None:
        hit = ledger.lookup(key)
        if hit is not None:
            call = _GateCall(
                RelevanceVerdict(relevant=hit.relevant, parse_failed=False),
                provider="ledger",
                model=hit.model,
                reasoning=hit.reasoning,
                source=hit.source if hit.source == "auditor" else "ledger",
                prompt_hash=key,
            )
            if memo is not None:
                memo[key] = call
            return call
    reasoning: str | None = None
    try:
        detailed = getattr(client, "complete_detailed", None)
        if detailed is not None:
            completion = detailed(system, user, schema=GATE_SCHEMA)
            raw = completion.content
            reasoning = completion.reasoning
        else:
            raw = client.complete(system, user, schema=GATE_SCHEMA)
    except LlamaCppTruncated as exc:
        logger.warning("Gate call truncated at the token cap — chunk dropped unjudged: %s", exc)
        verdict = RelevanceVerdict(relevant=False, parse_failed=True, failure_reason="truncated")
        return _GateCall(verdict, _gate_provider(client), _gate_model(client), prompt_hash=key)
    verdict = parse_relevance_response(raw)
    if verdict.parse_failed:
        logger.warning(
            "Gate response could not be parsed (%s) — chunk dropped unjudged, "
            "NOT counted as a rejection. Raw: %.200r",
            verdict.failure_reason, raw,
        )
    elif ledger is not None:
        ledger.record(
            key,
            relevant=verdict.relevant,
            reasoning=reasoning,
            model=_ledger_model(client),  # the same string the key was hashed with
            reasoning_effort=getattr(client, "reasoning_effort", None),
            acao_id=getattr(acao, "acao_id", None),
            product_id=product_id,
            process_number=process_number,
            filename=chunk.filename if chunk else None,
            page_number=chunk.page_number if chunk else None,
            chunk_index=chunk.chunk_index if chunk else None,
        )
    call = _GateCall(
        verdict, _gate_provider(client), _gate_model(client), reasoning, prompt_hash=key
    )
    # A failed call is not an answer, so it is not frozen for the rest of the
    # pass either -- the same rule the ledger follows (ADR-0060).
    if memo is not None and not verdict.parse_failed:
        memo[key] = call
    return call


def _gate_provider(client) -> str | None:
    """Provider label for whichever client served the call. last_provider_used
    covers a FallbackLLMClient that may have switched; provider_label covers a
    bare client. Stubs in tests have neither, hence the None."""
    return getattr(client, "last_provider_used", None) or getattr(client, "provider_label", None)


def _gate_model(client) -> str | None:
    return getattr(client, "last_model_used", None) or getattr(client, "model_label", None)


def _ledger_model(client) -> str | None:
    """Model component of the ledger key (ADR-0067): the label the client was
    CONFIGURED with, not the name the server reports back. last_model_used is
    None until the process's first response and then the served name
    ("Meme-GPT" for the gpt-oss GGUF), so a key built from it changes after
    the first call — the first prompt of every process would miss once and be
    re-asked. The configured label is known before any call and stable."""
    return getattr(client, "model_label", None) or _gate_model(client)


def _to_rejected(
    chunk: RetrievedChunk,
    product_id: str,
    matched_concepts: list[str] | None = None,
    call: _GateCall | None = None,
) -> RejectedChunk:
    verdict = call.verdict if call else None
    return RejectedChunk(
        filename=chunk.filename,
        page_number=chunk.page_number,
        chunk_index=chunk.chunk_index,
        expected_product_id=product_id,
        matched_concepts=matched_concepts or [],
        gate_failed=bool(verdict and verdict.parse_failed),
        gate_failure_reason=verdict.failure_reason if verdict else None,
        gate_provider=call.provider if call else None,
        gate_model=call.model if call else None,
        gate_reasoning=call.reasoning if call else None,
        gate_source=call.source if (call and not call.verdict.parse_failed) else None,
        gate_prompt_hash=call.prompt_hash if call else None,
    )
