"""Unit tests for Reciprocal Rank Fusion (ADR-0049)."""

from retrieval.query.rrf import RRF_K, fuse_rankings


def test_fuse_single_ranking_matches_plain_rrf_formula():
    scores = fuse_rankings([["a", "b", "c"]])
    assert scores["a"] == 1 / (RRF_K + 1)
    assert scores["b"] == 1 / (RRF_K + 2)
    assert scores["c"] == 1 / (RRF_K + 3)


def test_item_in_both_rankings_accumulates_contributions():
    scores = fuse_rankings([["a", "b"], ["b", "a"]])
    assert scores["a"] == 1 / (RRF_K + 1) + 1 / (RRF_K + 2)
    assert scores["b"] == 1 / (RRF_K + 2) + 1 / (RRF_K + 1)
    assert scores["a"] == scores["b"]


def test_item_found_by_both_rankings_outranks_item_found_by_one_even_at_rank_1():
    # "weak" is rank 2 in ranking A but rank 1 in ranking B; "strong" is rank 1
    # in ranking A only. Two weak signals should beat one strong signal.
    scores = fuse_rankings([["strong", "weak"], ["weak"]])
    assert scores["weak"] > scores["strong"]


def test_item_absent_from_a_ranking_contributes_nothing_from_it():
    scores = fuse_rankings([["a"], []])
    assert scores["a"] == 1 / (RRF_K + 1)


def test_custom_k_changes_score_magnitude_not_ordering():
    default_scores = fuse_rankings([["a", "b"]])
    custom_scores = fuse_rankings([["a", "b"]], k=10)
    assert default_scores["a"] > default_scores["b"]
    assert custom_scores["a"] > custom_scores["b"]
    assert custom_scores["a"] != default_scores["a"]


def test_empty_rankings_returns_empty_dict():
    assert fuse_rankings([]) == {}
    assert fuse_rankings([[], []]) == {}
