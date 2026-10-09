import json

import pytest

from evaluation import evaluator
from evaluation.evaluator import _SCORER_VOTES
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


# Ação 1's scored Expected Products, in IPMP order.
_ACAO1_PRODUCTS = ["1a", "1b", "1c", "1d"]


def _json_response(reasoning: str, score, uncertainty: bool, products=None) -> str:
    """Build a scorer response.

    products=None omits the field entirely — the pre-2026-09-27 shape, which
    parse_llm_response() must still accept (falling back to the model's own
    score) rather than failing. Pass a dict {product_id: evidenced} to exercise
    the per-product path that the score is computed from.
    """
    body = {"reasoning": reasoning, "score": score, "uncertainty": uncertainty}
    if products is not None:
        body["products"] = [
            {"product_id": pid, "evidenced": ev, "justificativa": f"veredito de {pid}"}
            for pid, ev in products.items()
        ]
    return json.dumps(body)


def _all_evidenced(value: bool = True) -> dict:
    return {pid: value for pid in _ACAO1_PRODUCTS}


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
    stub = StubLLMClient(
        _json_response(
            "Todos os produtos foram evidenciados.", 3, False, products=_all_evidenced()
        )
    )
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


# --- per-product verdicts drive the score (2026-09-27) ---

def test_score_is_computed_from_verdicts_not_taken_from_the_model():
    """The model claims 3 while reporting only 2 of 4 products evidenced.

    This is the Ação 31 failure mode from the 2026-09-07 run, where a full
    unhedged 3 rested on 2 of 9 products. The count in code must win.
    """
    verdicts = {"1a": True, "1b": True, "1c": False, "1d": False}
    stub = StubLLMClient(_json_response("2 de 4", 3, False, products=verdicts))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.proposed_score == 1, "some-but-not-all must be 1, whatever the model said"
    assert result.score_source == "computed"


def test_all_products_evidenced_computes_3():
    stub = StubLLMClient(_json_response("todos", 1, False, products=_all_evidenced(True)))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.proposed_score == 3
    assert result.score_source == "computed"


def test_no_products_evidenced_computes_0():
    stub = StubLLMClient(_json_response("nenhum", 3, False, products=_all_evidenced(False)))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.proposed_score == 0
    assert result.score_source == "computed"


def test_verdicts_are_persisted_on_the_result():
    verdicts = {"1a": True, "1b": False, "1c": True, "1d": False}
    stub = StubLLMClient(_json_response("misto", 1, False, products=verdicts))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert {v.product_id: v.evidenced for v in result.product_verdicts} == verdicts
    assert all(v.justificativa for v in result.product_verdicts)


# --- degradation: a non-cooperating model must fall back, never fail ---

def test_missing_products_field_falls_back_to_the_model_score():
    """The pre-2026-09-27 response shape must still produce a usable result."""
    stub = StubLLMClient(_json_response("sem vereditos", 1, False))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.parse_failed is False
    assert result.proposed_score == 1
    assert result.score_source == "model"


def test_missing_products_field_forces_uncertainty():
    """Without per-product verdicts we cannot confirm every Expected Product was
    considered, so the auditor must be flagged even if the model said otherwise."""
    stub = StubLLMClient(_json_response("sem vereditos", 3, False))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.uncertainty_flag is True
    assert result.score_source == "model"


def test_verdicts_for_the_wrong_products_fall_back():
    stub = StubLLMClient(
        _json_response("ids errados", 3, False, products={"9z": True, "9y": True})
    )
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.parse_failed is False
    assert result.proposed_score == 3
    assert result.score_source == "model"
    assert result.uncertainty_flag is True


def test_incomplete_verdicts_fall_back():
    """Verdicts for a subset of the products cannot support the count."""
    stub = StubLLMClient(_json_response("parcial", 3, False, products={"1a": True}))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.score_source == "model"
    assert result.uncertainty_flag is True


def test_duplicated_product_verdicts_fall_back():
    raw = json.dumps({
        "reasoning": "duplicado",
        "score": 3,
        "uncertainty": False,
        "products": [
            {"product_id": "1a", "evidenced": True, "justificativa": "x"},
            {"product_id": "1a", "evidenced": True, "justificativa": "y"},
            {"product_id": "1b", "evidenced": True, "justificativa": "z"},
            {"product_id": "1c", "evidenced": True, "justificativa": "w"},
        ],
    })
    _wire(StubLLMClient(raw))
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.score_source == "model"


def test_malformed_verdict_entry_falls_back_without_failing():
    raw = json.dumps({
        "reasoning": "malformado",
        "score": 1,
        "uncertainty": False,
        "products": [{"product_id": "1a", "evidenced": "sim", "justificativa": "x"}],
    })
    _wire(StubLLMClient(raw))
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.parse_failed is False
    assert result.proposed_score == 1
    assert result.score_source == "model"


# ── scorer voting wiring (2026-09-29) ─────────────────────────────────────────

class SequenceLLMClient:
    """Returns a different response per call, so a vote can actually split."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.call_count = 0

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        response = self._responses[min(self.call_count, len(self._responses) - 1)]
        self.call_count += 1
        return response


def test_evaluate_calls_the_scorer_once_per_vote():
    stub = StubLLMClient(_json_response("ok", 1, False, products={
        "1a": True, "1b": False, "1c": False, "1d": False}))
    _wire(stub)
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert stub.call_count == _SCORER_VOTES
    assert result.n_scorer_votes == _SCORER_VOTES


def test_scorer_voting_is_off_by_default_adr0063():
    """One call per Ação. Voting was measured and reverted — see ADR-0063."""
    assert _SCORER_VOTES == 1


def test_a_split_is_recorded_and_forces_uncertainty_when_voting_is_enabled(monkeypatch):
    """Covers combine_votes' wiring while _SCORER_VOTES is 1.

    Raising the constant is the whole of re-enabling the experiment, so the
    path stays tested rather than rotting in the tree (same treatment the
    unwired provider fallback gets under ADR-0059).
    """
    monkeypatch.setattr(evaluator, "_SCORER_VOTES", 3)
    all_yes = _json_response("tudo", 3, False, products=_all_evidenced(True))
    one_no = _json_response("quase", 1, False, products={
        "1a": True, "1b": True, "1c": True, "1d": False})
    _wire(SequenceLLMClient([all_yes, one_no, all_yes]))
    result = evaluate(1, "0023.001234/2024-01", [_chunk()])
    assert result.n_scorer_votes == 3
    assert result.proposed_score == 3, "majority on 1d is evidenced"
    assert result.n_verdict_splits == 1
    assert result.uncertainty_flag is True


# --- orcamento de evidencia e ordem de corte (2026-10-06) ---

def test_cap_evidence_passes_everything_through_under_the_budget():
    """The cap is a safety net against the 32,000-token slot, not a working
    limit: the largest real evidence set measured over five full passes is
    33,891 chars against a 70,000 cap."""
    chunks = [_chunk(page_number=i, text="x" * 1000) for i in range(10)]
    assert evaluator._cap_evidence(chunks, 1, "P001") == chunks


def test_truncation_keeps_one_chunk_per_product_before_a_second(monkeypatch):
    """The score is a count over Expected Products (ADR-0058), so dropping a
    product's ONLY chunk changes the score while dropping its third usually
    does not. The old rule sorted by cascade step and could spend the whole
    budget on one product."""
    monkeypatch.setattr(evaluator, "_MAX_EVIDENCE_CHARS", 3_500)
    chunks = [
        _chunk(page_number=i, chunk_index=j, text=f"{pid}-{j}: " + "x" * 1000,
               expected_product_ids=[pid])
        for i, pid in enumerate(["1a", "1b", "1c"])
        for j in range(3)
    ]
    kept = evaluator._cap_evidence(chunks, 1, "P001")

    assert {c.expected_product_ids[0] for c in kept} == {"1a", "1b", "1c"}
    assert [c.chunk_index for c in kept] == [0, 0, 0]
    # a ordem de leitura e preservada: o corte decide quem fica, nao a ordem
    assert kept == [c for c in chunks if c in kept]


def test_truncation_does_not_penalise_the_vector_lane(monkeypatch):
    """_CASCADE_PRIORITY put "vector" last, from when vector was a fallback;
    ADR-0049 made it co-equal to BM25 and the RRF order is already encoded in
    the list, so the lane is no longer a priority signal."""
    monkeypatch.setattr(evaluator, "_MAX_EVIDENCE_CHARS", 2_200)
    vetorial = _chunk(page_number=1, text="v" * 1000, cascade_step="vector",
                      bm25_score=None, rank=None, expected_product_ids=["1a"])
    lexical = _chunk(page_number=2, text="b" * 1000, cascade_step="bm25",
                     expected_product_ids=["1b"])
    extra = _chunk(page_number=3, text="b" * 1000, cascade_step="bm25",
                   expected_product_ids=["1b"])

    kept = evaluator._cap_evidence([vetorial, lexical, extra], 1, "P001")

    assert [c.page_number for c in kept] == [1, 2]
