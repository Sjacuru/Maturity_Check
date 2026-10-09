from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, replace

logger = logging.getLogger(__name__)

_VALID_SCORES = {0, 1, 3}


@dataclass
class ProductVerdict:
    """The scorer's judgement on one Expected Product."""

    product_id: str
    evidenced: bool
    justificativa: str


@dataclass
class ParsedResponse:
    raw_llm_response: str
    reasoning: str | None
    proposed_score: int | None
    uncertainty_flag: bool
    parse_failed: bool
    product_verdicts: list[ProductVerdict] = field(default_factory=list)
    score_source: str = "model"
    """Where proposed_score came from.

    'computed' — derived in code from a complete set of per-product verdicts.
    'model'    — taken from the model's own "score" field, because the verdicts
                 were absent, incomplete, or inconsistent with the expected
                 product ids.
    """


def _failed(raw: str) -> ParsedResponse:
    return ParsedResponse(
        raw_llm_response=raw,
        reasoning=None,
        proposed_score=None,
        uncertainty_flag=False,
        parse_failed=True,
    )


def score_for_counts(n_evidenced: int, n_products: int) -> int:
    """The IPMP rubric as arithmetic: none -> 0, all -> 3, some -> 1.

    The single source of truth for the band boundaries. evaluation.margin reads
    it to work out how far a score sits from a band change, so the margin can
    never disagree with the score it qualifies.
    """
    if n_evidenced <= 0:
        return 0
    if n_products > 0 and n_evidenced >= n_products:
        return 3
    return 1


def _score_from_verdicts(verdicts: list[ProductVerdict]) -> int:
    """all evidenced -> 3, some -> 1, none -> 0.

    The IPMP rubric is a count over Expected Products, so counting it in code
    makes the score a reproducible function of the per-product verdicts. Asking
    the model for a single 0/1/3 instead let it apply the rubric to whatever
    subset it happened to receive: in the 2026-09-07 run Ação 31 returned a full
    3 having judged 2 of 9 products, and Ação 2 returned 0 having judged 1 of 4.
    """
    return score_for_counts(
        sum(1 for v in verdicts if v.evidenced), len(verdicts)
    )


def _parse_verdicts(data: dict) -> list[ProductVerdict] | None:
    """Return the per-product verdicts, or None if the field is unusable."""
    raw_products = data.get("products")
    if not isinstance(raw_products, list) or not raw_products:
        return None
    verdicts: list[ProductVerdict] = []
    for item in raw_products:
        if not isinstance(item, dict):
            return None
        product_id = item.get("product_id")
        evidenced = item.get("evidenced")
        justificativa = item.get("justificativa", "")
        if not isinstance(product_id, str) or not product_id:
            return None
        if not isinstance(evidenced, bool):
            return None
        if not isinstance(justificativa, str):
            justificativa = ""
        verdicts.append(
            ProductVerdict(
                product_id=product_id,
                evidenced=evidenced,
                justificativa=justificativa.strip(),
            )
        )
    return verdicts


def parse_llm_response(
    raw: str,
    expected_product_ids: list[str] | None = None,
) -> ParsedResponse:
    """Parse the scorer's structured JSON response (ADR-0053).

    Expects "reasoning" (string), "score" (integer in 0/1/3) and "uncertainty"
    (boolean) — the shape enforced by evaluation.schemas.SCORER_SCHEMA when the
    provider supports grammar-constrained output. Still validated defensively:
    a provider without structured-output support, or one that degrades to a
    looser JSON mode, is not guaranteed to honour the schema.

    Since 2026-09-27 the schema also carries "products": one {product_id,
    evidenced, justificativa} entry per scored Expected Product. When
    expected_product_ids is supplied and the verdicts cover exactly that set,
    proposed_score is COMPUTED from them (score_source="computed") and the
    model's own "score" is ignored. Anything less — field absent, malformed,
    or not matching the expected ids — falls back to the model's "score"
    (score_source="model"), which is exactly the pre-2026-09-27 behaviour. That
    fallback is deliberate: a model that does not cooperate with the richer
    schema must degrade to the old result, never to parse_failed.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _failed(raw)

    if not isinstance(data, dict):
        return _failed(raw)

    score = data.get("score")
    uncertainty = data.get("uncertainty")
    reasoning = data.get("reasoning")

    # bool is a subclass of int in Python — isinstance(True, int) is True and
    # True == 1, so an accidental boolean in the score field must be rejected
    # explicitly rather than silently accepted as score=1.
    if isinstance(score, bool) or not isinstance(score, int) or score not in _VALID_SCORES:
        return _failed(raw)
    if not isinstance(uncertainty, bool):
        return _failed(raw)
    if not isinstance(reasoning, str):
        return _failed(raw)

    verdicts = _parse_verdicts(data) or []
    proposed_score = score
    score_source = "model"
    uncertainty_flag = uncertainty

    if expected_product_ids:
        expected = list(expected_product_ids)
        got = [v.product_id for v in verdicts]
        if verdicts and sorted(got) == sorted(expected) and len(got) == len(set(got)):
            proposed_score = _score_from_verdicts(verdicts)
            score_source = "computed"
            if proposed_score != score:
                logger.info(
                    "Score computed from per-product verdicts (%d) differs from the "
                    "model's own score (%d) — using the computed value. Evidenced: "
                    "%d of %d products.",
                    proposed_score, score,
                    sum(1 for v in verdicts if v.evidenced), len(verdicts),
                )
        else:
            # Incomplete verdicts mean we could not confirm every Expected
            # Product was considered, so the result is flagged for the auditor
            # regardless of what the model claimed.
            uncertainty_flag = True
            logger.warning(
                "Per-product verdicts unusable (expected %s, got %s) — falling back "
                "to the model's own score and forcing uncertainty=True.",
                expected, got or "none",
            )

    return ParsedResponse(
        raw_llm_response=raw,
        reasoning=reasoning.strip() or None,
        proposed_score=proposed_score,
        uncertainty_flag=uncertainty_flag,
        parse_failed=False,
        product_verdicts=verdicts,
        score_source=score_source,
    )


def combine_votes(
    candidates: list[ParsedResponse], expected_product_ids: list[str]
) -> tuple[ParsedResponse, int]:
    """Collapse repeated scorer calls on the SAME prompt into one result.

    The scorer was shown to be non-deterministic on 2026-09-29: with the prompt
    digest captured at the client, one byte-identical Ação 3 prompt returned
    score=3 six times and score=0 once, and two Ação 14 prompts each returned
    both 0 and 1. That is the same engine-level behaviour already documented for
    the gate (2026-08-27) — stable when a prompt is repeated back-to-back,
    unstable when the same prompt is interleaved with other traffic.

    Voting over those calls was implemented, measured and REVERTED (ADR-0063);
    _SCORER_VOTES is 1 and this function is a passthrough at that setting. The
    reason it fails is worth keeping next to the code: the votes are issued
    back-to-back on a byte-identical prompt, and repeating an identical prompt
    immediately is precisely the condition under which this engine reproduces
    itself (8 of 8 identical in an earlier probe). The votes therefore arrive as
    near-copies — verdicts split in 2 of 10 passes on Ação 3 and 0 of 10 on
    Ação 14 — and a majority over near-copies cannot reduce variance. Making
    them independent would mean interleaving other traffic between them, which
    is the condition that CAUSES the divergence, so no configuration yields
    samples that are both independent and individually stable.

    The vote is per Expected Product, not on the final 0/1/3. Since ADR-0058 the
    score is a count over the verdicts, so voting before the count is strictly
    more informative than voting after it — a 3/1/0 majority can hide two
    different disagreements.

    Returns the combined response and the number of products whose verdict was
    not unanimous. A split forces uncertainty_flag: the auditor should see that
    the model did not agree with itself, which is exactly the signal a single
    call throws away.
    """
    usable = [c for c in candidates if not c.parse_failed]
    if not usable:
        return (candidates[0] if candidates else _failed("")), 0

    computed = [c for c in usable if c.score_source == "computed"]
    if not computed:
        # No call produced a verdict set covering the expected products, so
        # there is nothing to vote on per product. Fall back to the modal score
        # the model reported; parse_llm_response has already forced uncertainty.
        scores = [c.proposed_score for c in usable]
        return max(usable, key=lambda c: scores.count(c.proposed_score)), 0

    verdicts: list[ProductVerdict] = []
    splits = 0
    for product_id in expected_product_ids:
        votes = [
            v for c in computed for v in c.product_verdicts if v.product_id == product_id
        ]
        if not votes:
            continue
        yes = sum(1 for v in votes if v.evidenced)
        evidenced = yes * 2 > len(votes)
        if 0 < yes < len(votes):
            splits += 1
        # Keep a justificativa written by a call that actually held the winning
        # verdict, so the stored rationale matches the stored verdict.
        justificativa = next(
            (v.justificativa for v in votes if v.evidenced == evidenced), ""
        )
        verdicts.append(
            ProductVerdict(
                product_id=product_id, evidenced=evidenced, justificativa=justificativa
            )
        )

    majority = {v.product_id: v.evidenced for v in verdicts}

    def agreement(candidate: ParsedResponse) -> int:
        return sum(
            1
            for v in candidate.product_verdicts
            if majority.get(v.product_id) == v.evidenced
        )

    # reasoning comes from whichever call agreed most with the majority, so the
    # narrative the auditor reads is the one that argued for the stored verdicts.
    representative = max(computed, key=agreement)
    score = _score_from_verdicts(verdicts)
    if splits:
        logger.info(
            "Scorer votes split on %d of %d products; combined score %d, "
            "uncertainty forced.",
            splits, len(verdicts), score,
        )
    return (
        replace(
            representative,
            proposed_score=score,
            product_verdicts=verdicts,
            score_source="computed",
            uncertainty_flag=representative.uncertainty_flag or splits > 0,
        ),
        splits,
    )
