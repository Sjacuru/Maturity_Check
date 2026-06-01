import pytest
from pydantic import ValidationError

from evaluation import EvaluationResult
from retrieval import RetrievedChunk

_CHUNK = dict(
    process_number="0023.001234/2024-01",
    filename="EVTEA.pdf",
    page_number=1,
    chunk_index=0,
    char_offset=0,
    page_total=10,
    ocr_used=False,
    source_type="text",
    text="Texto de exemplo.",
    cascade_step="bm25",
    expected_product_id="1a",
    bm25_score=3.5,
    rank=1,
)

_BASE = dict(
    acao_id=1,
    process_number="0023.001234/2024-01",
    provider="ollama",
    model="mistral",
    retrieved_chunks=[RetrievedChunk(**_CHUNK)],
    evidence_char_count=17,
    system_prompt="system",
    user_prompt="user",
    raw_llm_response="reasoning\nSCORE: 3\nUNCERTAINTY: no",
    reasoning="reasoning",
    proposed_score=3,
    uncertainty_flag=False,
    parse_failed=False,
    no_evidence_found=False,
)


# --- Valid construction ---

def test_valid_normal_evaluation():
    result = EvaluationResult(**_BASE)
    assert result.proposed_score == 3
    assert result.uncertainty_flag is False
    assert result.parse_failed is False
    assert result.no_evidence_found is False


def test_valid_score_zero():
    result = EvaluationResult(**{**_BASE, "proposed_score": 0})
    assert result.proposed_score == 0


def test_valid_score_one():
    result = EvaluationResult(**{**_BASE, "proposed_score": 1})
    assert result.proposed_score == 1


def test_valid_uncertainty_flag():
    result = EvaluationResult(**{**_BASE, "uncertainty_flag": True})
    assert result.uncertainty_flag is True
    assert result.proposed_score == 3  # uncertainty compatible with valid score


def test_valid_parse_failed():
    result = EvaluationResult(**{
        **_BASE,
        "raw_llm_response": "bad response",
        "reasoning": None,
        "proposed_score": None,
        "parse_failed": True,
        "uncertainty_flag": False,
    })
    assert result.parse_failed is True
    assert result.proposed_score is None
    assert result.reasoning is None


def test_valid_no_evidence_found():
    result = EvaluationResult(**{
        **_BASE,
        "retrieved_chunks": [],
        "evidence_char_count": 0,
        "system_prompt": None,
        "user_prompt": None,
        "raw_llm_response": None,
        "reasoning": None,
        "proposed_score": None,
        "uncertainty_flag": False,
        "parse_failed": False,
        "no_evidence_found": True,
    })
    assert result.no_evidence_found is True


def test_valid_proposed_score_none():
    result = EvaluationResult(**{**_BASE, "proposed_score": None, "reasoning": None, "parse_failed": True})
    assert result.proposed_score is None


# --- proposed_score validation ---

def test_invalid_score_2():
    with pytest.raises(ValidationError):
        EvaluationResult(**{**_BASE, "proposed_score": 2})


def test_invalid_score_negative():
    with pytest.raises(ValidationError):
        EvaluationResult(**{**_BASE, "proposed_score": -1})


def test_invalid_score_4():
    with pytest.raises(ValidationError):
        EvaluationResult(**{**_BASE, "proposed_score": 4})


# --- no_evidence_found invariants ---

def test_no_evidence_found_with_proposed_score():
    with pytest.raises(ValidationError):
        EvaluationResult(**{
            **_BASE,
            "retrieved_chunks": [],
            "evidence_char_count": 0,
            "system_prompt": None,
            "user_prompt": None,
            "raw_llm_response": None,
            "reasoning": None,
            "proposed_score": 1,  # must be None
            "uncertainty_flag": False,
            "parse_failed": False,
            "no_evidence_found": True,
        })


def test_no_evidence_found_with_uncertainty_flag():
    with pytest.raises(ValidationError):
        EvaluationResult(**{
            **_BASE,
            "retrieved_chunks": [],
            "evidence_char_count": 0,
            "system_prompt": None,
            "user_prompt": None,
            "raw_llm_response": None,
            "reasoning": None,
            "proposed_score": None,
            "uncertainty_flag": True,  # must be False
            "parse_failed": False,
            "no_evidence_found": True,
        })


def test_no_evidence_found_with_parse_failed():
    with pytest.raises(ValidationError):
        EvaluationResult(**{
            **_BASE,
            "retrieved_chunks": [],
            "evidence_char_count": 0,
            "system_prompt": None,
            "user_prompt": None,
            "raw_llm_response": None,
            "reasoning": None,
            "proposed_score": None,
            "uncertainty_flag": False,
            "parse_failed": True,  # must be False
            "no_evidence_found": True,
        })


def test_no_evidence_found_with_system_prompt():
    with pytest.raises(ValidationError):
        EvaluationResult(**{
            **_BASE,
            "evidence_char_count": 0,
            "system_prompt": "should be None",  # must be None
            "user_prompt": None,
            "raw_llm_response": None,
            "reasoning": None,
            "proposed_score": None,
            "uncertainty_flag": False,
            "parse_failed": False,
            "no_evidence_found": True,
        })


# --- parse_failed invariants ---

def test_parse_failed_with_reasoning():
    with pytest.raises(ValidationError):
        EvaluationResult(**{
            **_BASE,
            "reasoning": "some text",  # must be None when parse_failed
            "proposed_score": None,
            "parse_failed": True,
        })


def test_parse_failed_with_proposed_score():
    with pytest.raises(ValidationError):
        EvaluationResult(**{
            **_BASE,
            "reasoning": None,
            "proposed_score": 1,  # must be None when parse_failed
            "parse_failed": True,
        })
