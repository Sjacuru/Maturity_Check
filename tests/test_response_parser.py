import json

from evaluation.parsing.response import parse_llm_response


def _make_response(score, uncertainty: bool, reasoning: str = "Some reasoning text.") -> str:
    return json.dumps({"reasoning": reasoning, "score": score, "uncertainty": uncertainty})


# --- Well-formed responses ---

def test_score_0_uncertainty_false():
    r = parse_llm_response(_make_response(0, False))
    assert r.proposed_score == 0
    assert r.uncertainty_flag is False
    assert r.parse_failed is False
    assert r.reasoning == "Some reasoning text."


def test_score_1_uncertainty_true():
    r = parse_llm_response(_make_response(1, True))
    assert r.proposed_score == 1
    assert r.uncertainty_flag is True
    assert r.parse_failed is False


def test_score_3_uncertainty_false():
    r = parse_llm_response(_make_response(3, False))
    assert r.proposed_score == 3
    assert r.uncertainty_flag is False
    assert r.parse_failed is False


def test_reasoning_stripped():
    raw = json.dumps({"reasoning": "  Line one.\n\nLine two.  ", "score": 3, "uncertainty": False})
    r = parse_llm_response(raw)
    assert r.reasoning == "Line one.\n\nLine two."
    assert r.parse_failed is False


def test_reasoning_none_when_empty_string():
    raw = json.dumps({"reasoning": "", "score": 1, "uncertainty": False})
    r = parse_llm_response(raw)
    assert r.reasoning is None
    assert r.proposed_score == 1


def test_extra_unknown_fields_tolerated():
    raw = json.dumps(
        {"reasoning": "ok", "score": 3, "uncertainty": False, "extra_field": "ignored"}
    )
    r = parse_llm_response(raw)
    assert r.proposed_score == 3
    assert r.parse_failed is False


# --- raw_llm_response always preserved ---

def test_raw_response_preserved_on_success():
    raw = _make_response(3, False)
    r = parse_llm_response(raw)
    assert r.raw_llm_response == raw


def test_raw_response_preserved_on_failure():
    raw = "not json at all"
    r = parse_llm_response(raw)
    assert r.raw_llm_response == raw


# --- Parse failures ---

def test_missing_score_field():
    raw = json.dumps({"reasoning": "ok", "uncertainty": False})
    r = parse_llm_response(raw)
    assert r.parse_failed is True
    assert r.proposed_score is None
    assert r.reasoning is None
    assert r.uncertainty_flag is False


def test_missing_uncertainty_field():
    raw = json.dumps({"reasoning": "ok", "score": 3})
    r = parse_llm_response(raw)
    assert r.parse_failed is True


def test_missing_reasoning_field():
    raw = json.dumps({"score": 3, "uncertainty": False})
    r = parse_llm_response(raw)
    assert r.parse_failed is True


def test_invalid_score_2():
    r = parse_llm_response(_make_response(2, False))
    assert r.parse_failed is True
    assert r.proposed_score is None


def test_invalid_score_string():
    r = parse_llm_response(_make_response("Atendido", False))
    assert r.parse_failed is True


def test_score_as_boolean_is_rejected():
    """bool is a subclass of int in Python — a boolean score must not be
    silently accepted as score=1 (True == 1)."""
    raw = json.dumps({"reasoning": "ok", "score": True, "uncertainty": False})
    r = parse_llm_response(raw)
    assert r.parse_failed is True
    assert r.proposed_score is None


def test_uncertainty_as_string_is_rejected():
    raw = json.dumps({"reasoning": "ok", "score": 1, "uncertainty": "yes"})
    r = parse_llm_response(raw)
    assert r.parse_failed is True


def test_empty_string():
    r = parse_llm_response("")
    assert r.parse_failed is True
    assert r.proposed_score is None
    assert r.reasoning is None


def test_malformed_json():
    r = parse_llm_response('{"reasoning": "ok", "score": 3, "uncertainty":')
    assert r.parse_failed is True


def test_json_array_instead_of_object():
    r = parse_llm_response('["reasoning", 3, false]')
    assert r.parse_failed is True


def test_json_scalar_instead_of_object():
    r = parse_llm_response("3")
    assert r.parse_failed is True
