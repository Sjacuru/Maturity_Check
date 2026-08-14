import json

import pytest

from evaluation import configure_llm, evaluate, EvaluationResult
from evaluation._config import _reset
from retrieval import RetrievedChunk


class StubLLMClient:
    def __init__(self, response: str) -> None:
        self._response = response
        self.call_count = 0

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.call_count += 1
        return self._response


def _json_response(reasoning: str, score, uncertainty: bool) -> str:
    return json.dumps({"reasoning": reasoning, "score": score, "uncertainty": uncertainty})


def _chunk(**kwargs) -> RetrievedChunk:
    defaults = dict(
        process_number="0023.001234/2024-01",
        filename="EVTEA.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        page_total=10,
        ocr_used=False,
        source_type="text",
        text="O projeto visa construção de contorno rodoviário.",
        cascade_step="bm25",
        expected_product_ids=["1a"],
        bm25_score=3.5,
        rank=1,
    )
    return RetrievedChunk(**{**defaults, **kwargs})


@pytest.fixture(autouse=True)
def reset_config():
    _reset()
    yield
    _reset()


def _wire(stub: StubLLMClient) -> None:
    """Inject stub directly — bypasses OllamaClient/GroqClient instantiation."""
    import evaluation._config as cfg
    cfg._client = stub
    cfg._provider = "ollama"
    cfg._model = "mistral"


# --- configure_llm guards ---

def test_evaluate_raises_before_configure():
    with pytest.raises(RuntimeError, match="configure_llm"):
        evaluate(1, "0023.001234/2024-01", [])


def test_configure_unknown_provider_raises():
    with pytest.raises(ValueError, match="unknown"):
        configure_llm("unknown", "model")


# --- no_evidence_found short-circuit ---

def test_no_evidence_found_empty_chunks():
    stub = StubLLMClient("should not be called")
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [])
    assert result.no_evidence_found is True
    assert stub.call_count == 0
    assert result.proposed_score is None
    assert result.reasoning is None
    assert result.system_prompt is None
    assert result.user_prompt is None
    assert result.raw_llm_response is None
    assert result.uncertainty_flag is False
    assert result.parse_failed is False


# --- Invalid acao_id ---

def test_evaluate_unknown_acao_id_raises():
    stub = StubLLMClient("irrelevant")
    _wire(stub)
    with pytest.raises(ValueError, match="acao_id"):
        evaluate(999, "0023.001234/2024-01", [_chunk()])


# --- Normal evaluation ---

def test_normal_evaluation_score_3():
    stub = StubLLMClient(_json_response("Todos os produtos foram evidenciados.", 3, False))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.proposed_score == 3
    assert result.uncertainty_flag is False
    assert result.parse_failed is False
    assert result.no_evidence_found is False
    assert result.reasoning == "Todos os produtos foram evidenciados."


def test_normal_evaluation_score_0():
    stub = StubLLMClient(_json_response("Nenhuma evidência encontrada.", 0, False))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.proposed_score == 0


def test_normal_evaluation_uncertainty_flag():
    stub = StubLLMClient(_json_response("Evidência insuficiente.", 1, True))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.uncertainty_flag is True
    assert result.proposed_score == 1
    assert result.parse_failed is False


# --- Parse failure ---

def test_parse_failed_response():
    stub = StubLLMClient("Resposta malformada, não é JSON.")
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.parse_failed is True
    assert result.proposed_score is None
    assert result.reasoning is None
    assert result.raw_llm_response == "Resposta malformada, não é JSON."
    assert result.no_evidence_found is False


# --- Metadata ---

def test_provider_and_model_in_result():
    stub = StubLLMClient(_json_response("ok", 3, False))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.provider == "ollama"
    assert result.model == "mistral"


def test_evidence_char_count_populated():
    text = "A" * 200
    stub = StubLLMClient(_json_response("ok", 1, False))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk(text=text)])
    assert result.evidence_char_count == 200


def test_retrieved_chunks_preserved_in_result():
    chunks = [_chunk(text="chunk one"), _chunk(text="chunk two", chunk_index=1)]
    stub = StubLLMClient(_json_response("ok", 3, False))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", chunks)
    assert len(result.retrieved_chunks) == 2


def test_prompts_populated_in_result():
    stub = StubLLMClient(_json_response("ok", 3, False))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.system_prompt is not None
    assert len(result.system_prompt) > 0
    assert result.user_prompt is not None
    assert len(result.user_prompt) > 0
