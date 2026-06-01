from evaluation.parsing.response import parse_llm_response


def _make_response(score: int | str, uncertainty: str, reasoning: str = "Some reasoning text.") -> str:
    return f"{reasoning}\nSCORE: {score}\nUNCERTAINTY: {uncertainty}"


# --- Well-formed responses ---

def test_score_0_uncertainty_no():
    r = parse_llm_response(_make_response(0, "no"))
    assert r.proposed_score == 0
    assert r.uncertainty_flag is False
    assert r.parse_failed is False
    assert r.reasoning == "Some reasoning text."


def test_score_1_uncertainty_yes():
    r = parse_llm_response(_make_response(1, "yes"))
    assert r.proposed_score == 1
    assert r.uncertainty_flag is True
    assert r.parse_failed is False


def test_score_3_uncertainty_no():
    r = parse_llm_response(_make_response(3, "no"))
    assert r.proposed_score == 3
    assert r.uncertainty_flag is False
    assert r.parse_failed is False


def test_uncertainty_case_insensitive():
    r = parse_llm_response(_make_response(1, "YES"))
    assert r.uncertainty_flag is True
    assert r.parse_failed is False


def test_reasoning_stripped():
    raw = "  Line one.\n\nLine two.  \nSCORE: 3\nUNCERTAINTY: no"
    r = parse_llm_response(raw)
    assert r.reasoning == "  Line one.\n\nLine two."
    assert r.parse_failed is False


def test_reasoning_none_when_only_sentinel():
    raw = "SCORE: 1\nUNCERTAINTY: no"
    r = parse_llm_response(raw)
    assert r.reasoning is None
    assert r.proposed_score == 1


def test_trailing_newline_accepted():
    raw = "Raciocínio.\nSCORE: 3\nUNCERTAINTY: no\n"
    r = parse_llm_response(raw)
    assert r.proposed_score == 3
    assert r.parse_failed is False


# --- raw_llm_response always preserved ---

def test_raw_response_preserved_on_success():
    raw = _make_response(3, "no")
    r = parse_llm_response(raw)
    assert r.raw_llm_response == raw


def test_raw_response_preserved_on_failure():
    raw = "No sentinel here."
    r = parse_llm_response(raw)
    assert r.raw_llm_response == raw


# --- Parse failures ---

def test_missing_score_line():
    r = parse_llm_response("Some reasoning.\nUNCERTAINTY: no")
    assert r.parse_failed is True
    assert r.proposed_score is None
    assert r.reasoning is None
    assert r.uncertainty_flag is False


def test_missing_uncertainty_line():
    r = parse_llm_response("Some reasoning.\nSCORE: 3")
    assert r.parse_failed is True


def test_invalid_score_2():
    r = parse_llm_response(_make_response(2, "no"))
    assert r.parse_failed is True
    assert r.proposed_score is None


def test_invalid_score_string():
    r = parse_llm_response(_make_response("Atendido", "no"))
    assert r.parse_failed is True


def test_empty_string():
    r = parse_llm_response("")
    assert r.parse_failed is True
    assert r.proposed_score is None
    assert r.reasoning is None


def test_extra_text_after_sentinel():
    raw = "Reasoning.\nSCORE: 3\nUNCERTAINTY: no\nExtra line."
    r = parse_llm_response(raw)
    assert r.parse_failed is True


def test_sentinel_in_middle_only():
    raw = "SCORE: 3\nUNCERTAINTY: no\nMore text after sentinel."
    r = parse_llm_response(raw)
    assert r.parse_failed is True
