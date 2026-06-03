from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from assessment import ReviewOutcome

_NOW = datetime.now(timezone.utc)

_BASE = dict(
    acao_id=1,
    process_number="0023.001234/2024-01",
    final_score=3,
    is_override=False,
    justification=None,
    evidence_references=None,
    created_at=_NOW,
)


# --- Valid construction ---

def test_valid_accept():
    ro = ReviewOutcome(**_BASE)
    assert ro.final_score == 3
    assert ro.is_override is False
    assert ro.justification is None


def test_valid_score_zero():
    ro = ReviewOutcome(**{**_BASE, "final_score": 0})
    assert ro.final_score == 0


def test_valid_score_one():
    ro = ReviewOutcome(**{**_BASE, "final_score": 1})
    assert ro.final_score == 1


def test_valid_override_with_justification():
    ro = ReviewOutcome(**{
        **_BASE,
        "is_override": True,
        "justification": "Texto claramente presente na página 12.",
    })
    assert ro.is_override is True
    assert ro.justification == "Texto claramente presente na página 12."


def test_valid_evidence_references_none():
    ro = ReviewOutcome(**{**_BASE, "evidence_references": None})
    assert ro.evidence_references is None


def test_valid_evidence_references_empty_list():
    ro = ReviewOutcome(**{**_BASE, "evidence_references": []})
    assert ro.evidence_references == []


def test_valid_evidence_references_list():
    ro = ReviewOutcome(**{**_BASE, "evidence_references": [0, 2, 5]})
    assert ro.evidence_references == [0, 2, 5]


# --- final_score validation ---

def test_invalid_score_2():
    with pytest.raises(ValidationError):
        ReviewOutcome(**{**_BASE, "final_score": 2})


def test_invalid_score_negative():
    with pytest.raises(ValidationError):
        ReviewOutcome(**{**_BASE, "final_score": -1})


def test_invalid_score_4():
    with pytest.raises(ValidationError):
        ReviewOutcome(**{**_BASE, "final_score": 4})


# --- override invariants ---

def test_override_true_requires_justification():
    with pytest.raises(ValidationError):
        ReviewOutcome(**{**_BASE, "is_override": True, "justification": None})


def test_override_true_empty_justification_raises():
    with pytest.raises(ValidationError):
        ReviewOutcome(**{**_BASE, "is_override": True, "justification": ""})


def test_override_false_justification_must_be_none():
    with pytest.raises(ValidationError):
        ReviewOutcome(**{**_BASE, "is_override": False, "justification": "some text"})


# --- evidence_references serialisation ---

def test_evidence_references_none_serialises_to_null():
    ro = ReviewOutcome(**{**_BASE, "evidence_references": None})
    d = ro.model_dump()
    assert d["evidence_references"] is None


def test_evidence_references_empty_list_serialises_to_empty():
    ro = ReviewOutcome(**{**_BASE, "evidence_references": []})
    d = ro.model_dump()
    assert d["evidence_references"] == []
