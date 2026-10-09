"""The deterministic margin around a counted score.

Decided 2026-10-05. The score has been counted in code since ADR-0058, which
made it a reproducible function of the per-product verdicts — but it said
nothing about how FAR that score sits from a different one. Two independent cold
runs of the same frozen configuration showed why that distance is the number
that matters:

  * verdict stability 96.3 %, but concentrated entirely in the rejections:
    `P(unstable | REJECTED)` = 1.7 % against `P(unstable | ACCEPTED)` = 38.5 %,
    a 23x risk ratio; of 173 chunks ever accepted only 83 (48 %) were accepted
    by both runs;
  * that propagated to the product `evidenced` bit in 151/164 products (92.1 %),
    and **8 of the 13 bit flips came from products held by a single accept**;
  * the 0/1/3 band then absorbed 5 of the 11 Ações whose evidenced-product set
    differed, so flip COUNT is the wrong metric and DISTANCE TO A BAND CHANGE is
    the right one.

Everything here is arithmetic over data the pipeline already has: no model call,
no extra latency, and the same input yields the same margin as well as the same
score, so the reproducibility constraint is untouched. Nothing computed here is
fed back to the scorer — ADR-0058 deliberately removed the count from the
model's judgement, and a margin field in the scorer prompt would put a form of
it back while changing every prompt byte.
"""

from __future__ import annotations

import logging

from retrieval.interfaces.contracts import RetrievedChunk

from evaluation.interfaces.contracts import (
    ProductMargin,
    ProductVerdict,
    ScoreMargin,
)
from evaluation.parsing.response import score_for_counts

logger = logging.getLogger(__name__)

_ChunkKey = tuple[str, int, int]

# An evidenced product supported by this many accepted chunks (or fewer) has a
# deterministically fragile bit: remove its support and build_user_prompt emits
# an empty block, which the header instruction defines as NOT evidenced. One is
# the only value for which that implication holds without a judgement.
_FRAGILE_AT = 1


def _key(chunk: RetrievedChunk) -> _ChunkKey:
    return (chunk.filename, chunk.page_number, chunk.chunk_index)


def _accepts_per_product(
    chunks: list[RetrievedChunk], product_ids: list[str]
) -> dict[str, set[_ChunkKey]]:
    """Which accepted chunks support each product, as the scorer saw them."""
    support: dict[str, set[_ChunkKey]] = {pid: set() for pid in product_ids}
    for chunk in chunks:
        for pid in chunk.expected_product_ids:
            if pid in support:
                support[pid].add(_key(chunk))
    return support


def band_margin(n_evidenced: int, n_products: int) -> int | None:
    """How many `evidenced` bits must flip to land in a different 0/1/3 band.

    Counted in both directions over the rubric itself (score_for_counts), so it
    cannot drift from the score it qualifies. None when there is nothing to
    count over.

    A single-product Ação always returns 1: its one bit swings the score between
    0 and 3 outright, which is why Ação 45's whole result moved on one verdict
    across the 10-run acceptance test (score 3 in 8 runs, sem evidência in 2).
    """
    if n_products <= 0:
        return None
    here = score_for_counts(n_evidenced, n_products)
    for distance in range(1, n_products + 1):
        for candidate in (n_evidenced - distance, n_evidenced + distance):
            if 0 <= candidate <= n_products and score_for_counts(candidate, n_products) != here:
                return distance
    return None


def compute_score_margin(
    verdicts: list[ProductVerdict],
    chunks: list[RetrievedChunk],
    expected_product_ids: list[str],
    proposed_score: int | None,
) -> ScoreMargin:
    """Build the margin and the score interval for one evaluation.

    `chunks` must be the accepted evidence the scorer was actually shown — the
    post-dedup, post-_cap_evidence list — because that is what holds the bits.
    """
    n_products = len(expected_product_ids)
    verdict_by_id = {v.product_id: v.evidenced for v in verdicts}
    attribution_complete = not chunks or any(c.expected_product_ids for c in chunks)
    support = _accepts_per_product(chunks, expected_product_ids)

    products: list[ProductMargin] = []
    for pid in expected_product_ids:
        evidenced = verdict_by_id.get(pid, False)
        n_accepted = len(support[pid])
        products.append(
            ProductMargin(
                product_id=pid,
                evidenced=evidenced,
                n_accepted=n_accepted,
                # Without per-product attribution there is no support to count,
                # so no bit can be called fragile on this evidence.
                fragile=bool(
                    attribution_complete and evidenced and 0 < n_accepted <= _FRAGILE_AT
                ),
            )
        )

    n_evidenced = sum(1 for p in products if p.evidenced)
    fragile = [p for p in products if p.fragile]
    margin = band_margin(n_evidenced, n_products)

    floor = _score_floor(products, fragile, support, chunks, n_products, attribution_complete)
    ceiling = proposed_score
    review = floor != ceiling and bool(fragile)

    return ScoreMargin(
        products=products,
        n_products=n_products,
        n_evidenced=n_evidenced,
        n_fragile=len(fragile),
        band_margin=margin,
        score_floor=floor,
        score_ceiling=ceiling,
        attribution_complete=attribution_complete,
        review_recommended=review,
        explanation=_explain(
            proposed_score=proposed_score,
            floor=floor,
            n_evidenced=n_evidenced,
            n_products=n_products,
            fragile=fragile,
            margin=margin,
            attribution_complete=attribution_complete,
            has_chunks=bool(chunks),
        ),
    )


def _score_floor(
    products: list[ProductMargin],
    fragile: list[ProductMargin],
    support: dict[str, set[_ChunkKey]],
    chunks: list[RetrievedChunk],
    n_products: int,
    attribution_complete: bool,
) -> int | None:
    """The score if every fragile bit turned off at once.

    Simulated by removing the chunks that are the SOLE support of some fragile
    product and recounting, rather than by subtracting a number — one chunk can
    be attributed to several products (_deduplicate_across_products merges the
    attributions), so dropping it may take more than one bit with it.

    A product that keeps at least one accept keeps its verdict: with evidence
    still in its block the bit is the scorer's call, and claiming otherwise
    would not be deterministic.

    Returns None when nothing accepted would remain — the Ação would then come
    out `sem evidência` (no_evidence_found), which is a different outcome from
    score 0 and must not be reported as one.
    """
    if not products:
        return None
    if not attribution_complete or not fragile:
        # No deterministic downward lever: the floor is the score itself.
        return score_for_counts(sum(1 for p in products if p.evidenced), n_products)

    doomed: set[_ChunkKey] = set()
    for p in fragile:
        doomed |= support[p.product_id]

    remaining = [c for c in chunks if _key(c) not in doomed]
    if not remaining:
        return None

    surviving_support = _accepts_per_product(remaining, [p.product_id for p in products])
    still_evidenced = sum(
        1 for p in products if p.evidenced and surviving_support[p.product_id]
    )
    return score_for_counts(still_evidenced, n_products)


def _label(score: int | None) -> str:
    return "sem evidência" if score is None else f"score {score}"


def _explain(
    *,
    proposed_score: int | None,
    floor: int | None,
    n_evidenced: int,
    n_products: int,
    fragile: list[ProductMargin],
    margin: int | None,
    attribution_complete: bool,
    has_chunks: bool,
) -> str:
    """One deterministic sentence for the auditor, in the interface's language."""
    if not has_chunks:
        return (
            f"Nenhum trecho foi aceito pelo gate para nenhum dos {n_products} "
            "produtos esperados — a Ação sai sem evidência."
        )
    if not attribution_complete:
        return (
            "Evidência recuperada por documento focal, sem atribuição por produto "
            "(a rota não passa pelo gate), portanto a margem por produto não se "
            "aplica a esta avaliação."
        )

    head = (
        f"{_label(proposed_score).capitalize()} com {n_evidenced} de {n_products} "
        "produtos evidenciados"
    )
    if not fragile:
        tail = (
            f"; nenhum produto evidenciado depende de um único trecho aceito e a "
            f"mudança de faixa exigiria {margin} veredito(s)."
            if margin is not None
            else "; não há produtos pontuados para medir a margem."
        )
        return head + tail

    ids = ", ".join(p.product_id for p in fragile)
    plural = "produtos" if len(fragile) > 1 else "produto"
    verb = "dependem" if len(fragile) > 1 else "depende"
    if floor == proposed_score:
        return (
            f"{head}. O {plural} {ids} {verb} de um único trecho aceito, mas sua "
            f"queda não mudaria a faixa (seguiria {_label(floor)})."
        )
    return (
        f"{head}. O {plural} {ids} {verb} de um único trecho aceito; se não "
        f"tivessem se sustentado, o resultado seria {_label(floor)}."
    )
