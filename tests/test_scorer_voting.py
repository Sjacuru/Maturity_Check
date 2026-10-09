"""combine_votes(): repeated scorer calls on one prompt collapsed per product.

The scorer was measured non-deterministic on 2026-09-29 — one byte-identical
Ação 3 prompt returned score=3 six times and score=0 once — so evaluate() now
calls it _SCORER_VOTES times and combines per Expected Product. These pin the
combination rules, which the orchestration tests cannot: their stub returns the
same response every call, so voting collapses there and the logic never runs.
"""

import json

from evaluation.parsing.response import combine_votes, parse_llm_response

_PRODUCTS = ["1a", "1b", "1c", "1d"]


def _response(score, uncertainty=False, reasoning="Razão.", evidenced=None) -> str:
    body = {"reasoning": reasoning, "score": score, "uncertainty": uncertainty}
    if evidenced is not None:
        body["products"] = [
            {"product_id": pid, "evidenced": e, "justificativa": f"just-{pid}"}
            for pid, e in zip(_PRODUCTS, evidenced)
        ]
    return json.dumps(body)


def _parse(*raws):
    return [parse_llm_response(r, expected_product_ids=_PRODUCTS) for r in raws]


# ── unanimous ────────────────────────────────────────────────────────────────

def test_unanimous_votes_match_a_single_call():
    raw = _response(1, evidenced=[True, False, False, False])
    combined, splits = combine_votes(_parse(raw, raw, raw), _PRODUCTS)
    assert splits == 0
    assert combined.proposed_score == 1
    assert combined.score_source == "computed"
    assert combined.uncertainty_flag is False
    assert [v.evidenced for v in combined.product_verdicts] == [True, False, False, False]


def test_unanimous_all_evidenced_scores_3():
    raw = _response(3, evidenced=[True] * 4)
    combined, splits = combine_votes(_parse(raw, raw, raw), _PRODUCTS)
    assert (combined.proposed_score, splits) == (3, 0)


# ── split ────────────────────────────────────────────────────────────────────

def test_majority_wins_per_product_and_forces_uncertainty():
    # 1b: True, True, False -> majority True. Score stays 1 (not all evidenced).
    combined, splits = combine_votes(
        _parse(
            _response(1, evidenced=[True, True, False, False]),
            _response(1, evidenced=[True, True, False, False]),
            _response(0, evidenced=[True, False, False, False]),
        ),
        _PRODUCTS,
    )
    assert splits == 1
    assert [v.evidenced for v in combined.product_verdicts] == [True, True, False, False]
    assert combined.proposed_score == 1
    assert combined.uncertainty_flag is True, "a split must reach the auditor"


def test_minority_vote_cannot_change_the_score():
    """The 2026-09-29 Ação 3 signature: one call in three disagreeing.

    Single-call behaviour would surface that call's score=0 one run in seven;
    the vote keeps the majority verdict and marks the disagreement instead.
    """
    combined, splits = combine_votes(
        _parse(
            _response(3, evidenced=[True] * 4),
            _response(0, evidenced=[False] * 4),
            _response(3, evidenced=[True] * 4),
        ),
        _PRODUCTS,
    )
    assert combined.proposed_score == 3
    assert splits == 4
    assert combined.uncertainty_flag is True


def test_split_on_every_product_is_counted_per_product():
    combined, splits = combine_votes(
        _parse(
            _response(3, evidenced=[True, True, False, False]),
            _response(0, evidenced=[False, False, True, True]),
            _response(1, evidenced=[True, False, True, False]),
        ),
        _PRODUCTS,
    )
    assert splits == 4
    assert [v.evidenced for v in combined.product_verdicts] == [True, False, True, False]


def test_justificativa_comes_from_a_call_holding_the_winning_verdict():
    winner = json.dumps({
        "reasoning": "ganhou",
        "score": 1,
        "uncertainty": False,
        "products": [
            {"product_id": "1a", "evidenced": True, "justificativa": "achei"},
            {"product_id": "1b", "evidenced": False, "justificativa": "nada"},
            {"product_id": "1c", "evidenced": False, "justificativa": "nada"},
            {"product_id": "1d", "evidenced": False, "justificativa": "nada"},
        ],
    })
    loser = json.dumps({
        "reasoning": "perdeu",
        "score": 0,
        "uncertainty": False,
        "products": [
            {"product_id": "1a", "evidenced": False, "justificativa": "NAO achei"},
            {"product_id": "1b", "evidenced": False, "justificativa": "nada"},
            {"product_id": "1c", "evidenced": False, "justificativa": "nada"},
            {"product_id": "1d", "evidenced": False, "justificativa": "nada"},
        ],
    })
    combined, _ = combine_votes(_parse(winner, winner, loser), _PRODUCTS)
    assert combined.product_verdicts[0].justificativa == "achei"
    assert combined.reasoning == "ganhou", "reasoning must match the stored verdicts"


# ── degraded inputs ──────────────────────────────────────────────────────────

def test_all_parse_failures_stay_a_parse_failure():
    combined, splits = combine_votes(_parse("nao e json", "{", "[]"), _PRODUCTS)
    assert combined.parse_failed is True
    assert splits == 0


def test_parse_failures_are_ignored_when_others_are_usable():
    good = _response(3, evidenced=[True] * 4)
    combined, splits = combine_votes(_parse(good, "nao e json", good), _PRODUCTS)
    assert combined.parse_failed is False
    assert (combined.proposed_score, splits) == (3, 0)


def test_no_usable_verdicts_falls_back_to_the_modal_model_score():
    # No "products" at all -> parse_llm_response keeps score_source="model"
    # and has already forced uncertainty; there is nothing to vote per product.
    combined, splits = combine_votes(
        _parse(_response(1), _response(1), _response(3)), _PRODUCTS
    )
    assert combined.score_source == "model"
    assert combined.proposed_score == 1
    assert combined.uncertainty_flag is True
    assert splits == 0


def test_single_vote_is_a_passthrough():
    """_SCORER_VOTES = 1 is the documented one-line revert; it must not alter anything."""
    raw = _response(1, evidenced=[True, False, False, False])
    one = _parse(raw)
    combined, splits = combine_votes(one, _PRODUCTS)
    assert splits == 0
    assert combined.proposed_score == one[0].proposed_score
    assert combined.uncertainty_flag == one[0].uncertainty_flag
    assert combined.score_source == one[0].score_source


def test_empty_candidate_list_is_a_parse_failure_not_a_crash():
    combined, splits = combine_votes([], _PRODUCTS)
    assert combined.parse_failed is True
    assert splits == 0
