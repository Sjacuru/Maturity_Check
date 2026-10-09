"""The deterministic score margin and interval (2026-10-05).

The measurement that motivates these tests: across two independent cold runs of
the same frozen configuration, the gate's ACCEPTS flipped 38.5 % of the time
against 1.7 % for its rejections, and 8 of the 13 product-bit flips came from
products held by a single accepted chunk. So "this bit rests on one accept" is
the structural property worth computing, and "how far is this score from a
different band" is the number the auditor needs beside it.
"""

from __future__ import annotations

import pytest

from evaluation.interfaces.contracts import (
    EvaluationResult,
    ProductVerdict,
    ScoreMargin,
)
from evaluation.margin import band_margin, compute_score_margin
from evaluation.parsing.response import score_for_counts
from retrieval import RetrievedChunk


def _chunk(page_number: int, product_ids: list[str], **kwargs) -> RetrievedChunk:
    defaults = dict(
        process_number="0023.001234/2024-01",
        filename="EVTEA.pdf",
        page_number=page_number,
        chunk_index=0,
        char_offset=0,
        page_total=10,
        ocr_used=False,
        source_type="text",
        text="Trecho de evidência.",
        cascade_step="bm25",
        expected_product_ids=product_ids,
        bm25_score=3.5,
        rank=1,
    )
    return RetrievedChunk(**{**defaults, **kwargs})


def _verdicts(mapping: dict[str, bool]) -> list[ProductVerdict]:
    return [
        ProductVerdict(product_id=pid, evidenced=ev, justificativa="")
        for pid, ev in mapping.items()
    ]


# --------------------------------------------------------------------------
# band_margin — distance to a band change, read off the rubric itself
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "n_evidenced,n_products,expected",
    [
        (0, 3, 1),   # score 0; one bit on -> 1
        (1, 3, 1),   # score 1; one bit off -> 0
        (2, 3, 1),   # score 1; one bit on -> 3
        (3, 3, 1),   # score 3; one bit off -> 1
        (3, 5, 2),   # score 1; 2 bits on -> 3 is nearer than 3 bits off -> 0
        (1, 5, 1),   # score 1; one bit off -> 0
        (0, 1, 1),   # single-product Ação: one bit swings 0 <-> 3
        (1, 1, 1),
    ],
)
def test_band_margin_counts_bit_flips_to_the_nearest_band(n_evidenced, n_products, expected):
    assert band_margin(n_evidenced, n_products) == expected


def test_band_margin_is_none_without_scored_products():
    assert band_margin(0, 0) is None


def test_band_margin_never_contradicts_the_rubric():
    """Whatever distance it reports must really land in a different band."""
    for n_products in range(1, 10):
        for n_evidenced in range(0, n_products + 1):
            distance = band_margin(n_evidenced, n_products)
            assert distance is not None
            here = score_for_counts(n_evidenced, n_products)
            reachable = {
                score_for_counts(candidate, n_products)
                for candidate in (n_evidenced - distance, n_evidenced + distance)
                if 0 <= candidate <= n_products
            }
            assert here not in reachable or len(reachable) > 1
            # and nothing nearer changes the band
            for nearer in range(1, distance):
                for candidate in (n_evidenced - nearer, n_evidenced + nearer):
                    if 0 <= candidate <= n_products:
                        assert score_for_counts(candidate, n_products) == here


# --------------------------------------------------------------------------
# per-product margin
# --------------------------------------------------------------------------


def test_margin_counts_the_accepts_the_scorer_actually_saw():
    chunks = [
        _chunk(1, ["1a"]),
        _chunk(2, ["1a"]),
        _chunk(3, ["1b"]),
    ]
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": True, "1c": False}),
        chunks=chunks,
        expected_product_ids=["1a", "1b", "1c"],
        proposed_score=1,
    )
    by_id = {p.product_id: p for p in margin.products}
    assert by_id["1a"].n_accepted == 2
    assert by_id["1b"].n_accepted == 1
    assert by_id["1c"].n_accepted == 0
    assert margin.n_evidenced == 2
    assert margin.n_products == 3


def test_a_bit_held_by_one_accept_is_fragile_and_two_accepts_is_not():
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": True}),
        chunks=[_chunk(1, ["1a"]), _chunk(2, ["1a"]), _chunk(3, ["1b"])],
        expected_product_ids=["1a", "1b"],
        proposed_score=3,
    )
    by_id = {p.product_id: p for p in margin.products}
    assert by_id["1a"].fragile is False
    assert by_id["1b"].fragile is True
    assert margin.n_fragile == 1


def test_an_unevidenced_product_has_no_fragile_bit_to_lose():
    """A single accept the scorer judged insufficient is not a fragile bit.

    There is no `evidenced` bit resting on it, so losing the chunk changes
    nothing about the score.
    """
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": False}),
        chunks=[_chunk(1, ["1a"]), _chunk(2, ["1b"])],
        expected_product_ids=["1a", "1b"],
        proposed_score=1,
    )
    by_id = {p.product_id: p for p in margin.products}
    assert by_id["1b"].n_accepted == 1
    assert by_id["1b"].fragile is False
    assert margin.n_fragile == 1  # only 1a


# --------------------------------------------------------------------------
# the interval
# --------------------------------------------------------------------------


def test_floor_equals_the_score_when_nothing_is_fragile():
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": True}),
        chunks=[
            _chunk(1, ["1a"]),
            _chunk(2, ["1a"]),
            _chunk(3, ["1b"]),
            _chunk(4, ["1b"]),
        ],
        expected_product_ids=["1a", "1b"],
        proposed_score=3,
    )
    assert margin.n_fragile == 0
    assert margin.score_floor == 3
    assert margin.score_ceiling == 3
    assert margin.review_recommended is False


def test_floor_drops_a_band_when_a_fragile_bit_falls():
    """3 -> 1: all products evidenced, one of them on a single accept."""
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": True}),
        chunks=[_chunk(1, ["1a"]), _chunk(2, ["1a"]), _chunk(3, ["1b"])],
        expected_product_ids=["1a", "1b"],
        proposed_score=3,
    )
    assert margin.score_floor == 1
    assert margin.score_ceiling == 3
    assert margin.review_recommended is True


def test_floor_is_sem_evidencia_not_zero_when_no_accept_would_remain():
    """The Ação 28 shape the user named: two products, one accept each.

    Losing both leaves the gate having accepted nothing, which is
    no_evidence_found — a different outcome from score 0, so the floor is None
    rather than 0.
    """
    margin = compute_score_margin(
        verdicts=_verdicts({"28.1": False, "28.2": True, "28.3": True}),
        chunks=[_chunk(193, ["28.2"]), _chunk(136, ["28.3"])],
        expected_product_ids=["28.1", "28.2", "28.3"],
        proposed_score=1,
    )
    assert margin.n_fragile == 2
    assert margin.score_floor is None
    assert margin.score_ceiling == 1
    assert margin.review_recommended is True
    assert "sem evidência" in margin.explanation
    assert "28.2" in margin.explanation and "28.3" in margin.explanation


def test_one_chunk_supporting_two_fragile_products_takes_both_bits():
    """_deduplicate_across_products merges attributions onto a single chunk.

    The floor must be simulated by removing chunks, not by subtracting a count:
    one chunk can be the sole support of more than one product.
    """
    shared = _chunk(500, ["1a", "1b"])
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": True, "1c": True}),
        chunks=[shared, _chunk(501, ["1c"]), _chunk(502, ["1c"])],
        expected_product_ids=["1a", "1b", "1c"],
        proposed_score=3,
    )
    assert margin.n_fragile == 2
    # 1c keeps two accepts, so it survives: 3 -> 1, not -> 0.
    assert margin.score_floor == 1


def test_a_product_that_keeps_an_accept_keeps_its_verdict():
    """No downward claim on a bit that still has evidence in its block."""
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": True}),
        chunks=[_chunk(1, ["1a"]), _chunk(2, ["1a", "1b"]), _chunk(3, ["1b"])],
        expected_product_ids=["1a", "1b"],
        proposed_score=3,
    )
    # Neither product is fragile — each has two accepts.
    assert margin.n_fragile == 0
    assert margin.score_floor == 3


def test_no_upward_claim_is_made_from_a_single_pass():
    """score_ceiling is the current score, never a speculative better one."""
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": False}),
        chunks=[_chunk(1, ["1a"]), _chunk(2, ["1a"])],
        expected_product_ids=["1a", "1b"],
        proposed_score=1,
    )
    assert margin.score_ceiling == 1


# --------------------------------------------------------------------------
# honesty about what cannot be measured
# --------------------------------------------------------------------------


def test_document_focused_evidence_is_reported_as_unattributed():
    """Step A/B bypasses the gate, so there are no per-product accepts to count.

    Reported as attribution_complete=False rather than as every product having
    zero accepts, which would read as a fragile bit everywhere.
    """
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True, "1b": True}),
        chunks=[
            _chunk(1, [], cascade_step="filename_match", bm25_score=None, rank=None),
            _chunk(2, [], cascade_step="filename_match", bm25_score=None, rank=None),
        ],
        expected_product_ids=["1a", "1b"],
        proposed_score=3,
    )
    assert margin.attribution_complete is False
    assert margin.n_fragile == 0
    assert margin.score_floor == 3
    assert margin.review_recommended is False
    assert "documento focal" in margin.explanation


def test_no_evidence_at_all_reports_the_product_count_and_no_review():
    margin = compute_score_margin(
        verdicts=[],
        chunks=[],
        expected_product_ids=["1a", "1b", "1c", "1d"],
        proposed_score=None,
    )
    assert margin.n_products == 4
    assert margin.n_evidenced == 0
    assert margin.n_fragile == 0
    assert margin.review_recommended is False
    assert "Nenhum trecho foi aceito" in margin.explanation


def test_parse_failure_does_not_recommend_review():
    """No verdicts means no bit rests on anything — nothing to flag."""
    margin = compute_score_margin(
        verdicts=[],
        chunks=[_chunk(1, ["1a"])],
        expected_product_ids=["1a", "1b"],
        proposed_score=None,
    )
    assert margin.n_fragile == 0
    assert margin.review_recommended is False


# --------------------------------------------------------------------------
# reproducibility and persistence
# --------------------------------------------------------------------------


def test_same_input_gives_the_same_margin():
    """The reproducibility constraint covers the interval, not only the score."""
    args = dict(
        verdicts=_verdicts({"1a": True, "1b": True, "1c": False}),
        chunks=[_chunk(1, ["1a"]), _chunk(2, ["1b"]), _chunk(3, ["1c"])],
        expected_product_ids=["1a", "1b", "1c"],
        proposed_score=1,
    )
    first = compute_score_margin(**args)
    second = compute_score_margin(**args)
    assert first.model_dump() == second.model_dump()


def test_rows_persisted_without_a_margin_still_validate():
    """ADR-0031: the read path is json.loads(raw_json) and does not revalidate,
    but a stored row must still round-trip through the model."""
    result = EvaluationResult(
        acao_id=1,
        process_number="0023.001234/2024-01",
        provider="llamacpp",
        model="gpt-oss-20b-F16.gguf",
        retrieved_chunks=[],
        evidence_char_count=0,
        system_prompt=None,
        user_prompt=None,
        raw_llm_response=None,
        reasoning=None,
        proposed_score=None,
        uncertainty_flag=False,
        parse_failed=False,
        no_evidence_found=True,
    )
    assert result.score_margin is None
    stored = result.model_dump()
    del stored["score_margin"]
    assert EvaluationResult.model_validate(stored).score_margin is None


def test_margin_serializes_inside_the_evaluation_result():
    margin = compute_score_margin(
        verdicts=_verdicts({"1a": True}),
        chunks=[_chunk(1, ["1a"])],
        expected_product_ids=["1a"],
        proposed_score=3,
    )
    assert isinstance(margin, ScoreMargin)
    payload = margin.model_dump()
    assert payload["n_fragile"] == 1
    assert payload["score_floor"] is None  # single-product Ação, sole accept
    assert payload["products"][0]["fragile"] is True
