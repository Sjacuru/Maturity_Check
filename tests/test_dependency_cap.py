"""Teto por dependência (ADR-0070).

Regra do usuário (2026-10-09): uma Ação que cita outra que ficou em 0 ou sem
evidência não pode receber 3 — "não há revisão ou confirmação do que não foi
feito". Só as arestas `pre` limitam; `artefato` vira sinal de revisão; os demais
tipos não fazem nada. O teto é aritmética sobre scores já produzidos na mesma
corrida e nunca toca o prompt do scorer.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation import evaluate
from evaluation._config import _reset
from evaluation.dependency_cap import apply_dependency_cap, compute_dependency_cap
from evaluation.interfaces.contracts import (
    DependencyCap,
    EvaluationResult,
    ScoreMargin,
)
from ingestion import get_dependency_store, get_ipmp_store
from ingestion.dependencias import DependencyStore, load_dependencies
from retrieval import RetrievedChunk


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _store(*arestas: tuple[int, int, str]) -> DependencyStore:
    return DependencyStore(dependencias=[
        {"citante": a, "citada": b, "tipo": t} for a, b, t in arestas
    ])


def _result(acao_id: int, score: int | None, *, no_evidence: bool = False,
            parse_failed: bool = False) -> EvaluationResult:
    """A minimal persisted-shape result for the cited Ação."""
    if no_evidence:
        return EvaluationResult(
            acao_id=acao_id, process_number="P", provider="llamacpp", model="m",
            retrieved_chunks=[], evidence_char_count=0, system_prompt=None,
            user_prompt=None, raw_llm_response=None, reasoning=None,
            proposed_score=None, uncertainty_flag=False, parse_failed=False,
            no_evidence_found=True,
        )
    if parse_failed:
        return EvaluationResult(
            acao_id=acao_id, process_number="P", provider="llamacpp", model="m",
            retrieved_chunks=[], evidence_char_count=10, system_prompt="s",
            user_prompt="u", raw_llm_response="??", reasoning=None,
            proposed_score=None, uncertainty_flag=True, parse_failed=True,
            no_evidence_found=False,
        )
    return EvaluationResult(
        acao_id=acao_id, process_number="P", provider="llamacpp", model="m",
        retrieved_chunks=[], evidence_char_count=10, system_prompt="s",
        user_prompt="u", raw_llm_response="{}", reasoning="r",
        proposed_score=score, uncertainty_flag=False, parse_failed=False,
        no_evidence_found=False,
    )


def _write(tmp_path: Path, arestas: list[dict]) -> Path:
    p = tmp_path / "dependencias.json"
    p.write_text(json.dumps({"dependencias": arestas}), encoding="utf-8")
    return p


# --------------------------------------------------------------------------
# the data file and its loader
# --------------------------------------------------------------------------


def test_the_shipped_file_loads_and_every_effective_edge_points_backwards():
    store = get_dependency_store()
    assert store.dependencias, "data/ipmp/dependencias.json must not be empty"
    for d in store.dependencias:
        if d.tipo in ("pre", "artefato"):
            assert d.citada < d.citante, (d.citante, d.citada, d.tipo)


def test_the_ipmp_store_walks_the_acoes_in_ascending_order():
    """The cap reads the cited Ação's score from the SAME run, which only
    works because the run visits the Ações in order 1..46 — pinned here."""
    ids = list(get_ipmp_store().acoes)
    assert ids == sorted(ids)
    assert ids[0] == 1 and ids[-1] == 46


def test_the_shipped_file_records_the_user_rule_decisions():
    """3->2 caps (prerequisite); 43->28 does not (the IPMP's own Atendido example
    for 43 has 28 undone and 43 doing it); 29->11 is the same artefact."""
    store = get_dependency_store()
    tipos = {(d.citante, d.citada): d.tipo for d in store.dependencias}
    assert tipos[(3, 2)] == "pre"
    assert tipos[(43, 28)] == "lacuna"
    assert tipos[(29, 11)] == "artefato"
    assert store.com_efeito(43) == []


def test_loader_refuses_an_acao_outside_1_46(tmp_path):
    with pytest.raises(Exception, match="1..46|fora"):
        load_dependencies(_write(tmp_path, [{"citante": 47, "citada": 2, "tipo": "pre"}]))


def test_loader_refuses_a_self_edge(tmp_path):
    with pytest.raises(RuntimeError, match="si mesma"):
        load_dependencies(_write(tmp_path, [{"citante": 3, "citada": 3, "tipo": "pre"}]))


def test_loader_refuses_a_duplicate_edge(tmp_path):
    with pytest.raises(RuntimeError, match="duplicada"):
        load_dependencies(_write(tmp_path, [
            {"citante": 3, "citada": 2, "tipo": "pre"},
            {"citante": 3, "citada": 2, "tipo": "fraco"},
        ]))


def test_loader_refuses_a_forward_pre_or_artefato_edge(tmp_path):
    """A forward 'pre' edge would be silently inert (the cited Ação is scored
    later); the loader refuses the file instead of letting the rule sleep."""
    with pytest.raises(RuntimeError, match="frente"):
        load_dependencies(_write(tmp_path, [{"citante": 3, "citada": 6, "tipo": "pre"}]))
    with pytest.raises(RuntimeError, match="frente"):
        load_dependencies(_write(tmp_path, [{"citante": 3, "citada": 6, "tipo": "artefato"}]))
    # a forward edge of a type WITHOUT effect is fine — it only documents a reading
    load_dependencies(_write(tmp_path, [{"citante": 3, "citada": 6, "tipo": "sucessora"}]))


def test_loader_refuses_an_unknown_type(tmp_path):
    with pytest.raises(Exception):
        load_dependencies(_write(tmp_path, [{"citante": 3, "citada": 2, "tipo": "forte"}]))


# --------------------------------------------------------------------------
# compute_dependency_cap — the rule
# --------------------------------------------------------------------------


def test_no_effective_dependency_means_no_cap_object():
    assert compute_dependency_cap(1, 3, {}, _store()) is None
    assert compute_dependency_cap(14, 3, {4: _result(4, 0)}, _store((14, 4, "fraco"))) is None


@pytest.mark.parametrize("cited", [
    _result(2, 0),
    _result(2, None, no_evidence=True),
])
def test_pre_cited_low_and_counted_3_applies_the_cap(cited):
    cap = compute_dependency_cap(3, 3, {2: cited}, _store((3, 2, "pre")))
    assert cap is not None and cap.applied
    assert cap.score_before_cap == 3
    assert [o.estado for o in cap.dependencies] == ["baixa"]
    assert "Ação 2" in cap.explanation and "limitado a 1" in cap.explanation


@pytest.mark.parametrize("counted", [0, 1])
def test_pre_cited_low_but_counted_below_3_does_not_apply(counted):
    cap = compute_dependency_cap(3, counted, {2: _result(2, 0)}, _store((3, 2, "pre")))
    assert cap is not None and not cap.applied
    assert cap.score_before_cap is None
    assert "não aplicado" in cap.explanation


@pytest.mark.parametrize("cited_score", [1, 3])
def test_pre_cited_ok_never_caps(cited_score):
    cap = compute_dependency_cap(3, 3, {2: _result(2, cited_score)}, _store((3, 2, "pre")))
    assert cap is not None and not cap.applied
    assert [o.estado for o in cap.dependencies] == ["ok"]


@pytest.mark.parametrize(
    "tipo", ["fraco", "sucessora", "contraste", "delega", "sequencia", "lacuna"]
)
def test_types_without_effect_are_ignored_even_when_the_cited_is_low(tipo):
    assert compute_dependency_cap(3, 3, {2: _result(2, 0)}, _store((3, 2, tipo))) is None


def test_unknown_cited_state_does_not_cap():
    """Not evaluated, parse failure, or absent from the run: the cap never
    engages over the unknown — it only speaks of a cited Ação known to be low."""
    store = _store((3, 2, "pre"))
    for prior in ({}, {2: _result(2, None, parse_failed=True)}):
        cap = compute_dependency_cap(3, 3, prior, store)
        assert cap is not None and not cap.applied
        assert [o.estado for o in cap.dependencies] == ["desconhecida"]
        assert "não avaliada" in cap.explanation


def test_one_low_pre_among_several_is_enough_and_is_the_one_named():
    store = _store((17, 1, "pre"), (17, 2, "pre"), (17, 3, "pre"), (17, 4, "pre"))
    prior = {1: _result(1, 3), 2: _result(2, 1), 3: _result(3, 0), 4: _result(4, 3)}
    cap = compute_dependency_cap(17, 3, prior, store)
    assert cap.applied
    assert "pré-requisito: Ação 3 (score 0)" in cap.explanation
    assert "Ação 1 " not in cap.explanation and "Ação 4" not in cap.explanation


def test_artefato_cited_low_recommends_review_and_never_caps():
    store = _store((29, 11, "artefato"))
    cap = compute_dependency_cap(29, 3, {11: _result(11, None, no_evidence=True)}, store)
    assert not cap.applied
    assert cap.review_recommended
    assert "Revisão sugerida" in cap.explanation and "Ação 11" in cap.explanation


@pytest.mark.parametrize("counted", [0, None])
def test_artefato_review_is_silent_when_this_acao_found_nothing(counted):
    """'cited empty + citing empty' is consistent — nothing to review."""
    store = _store((29, 11, "artefato"))
    cap = compute_dependency_cap(29, counted, {11: _result(11, 0)}, store)
    assert not cap.review_recommended


def test_scoped_artefato_review_reads_the_scoped_products_not_the_score():
    """35 -> 14 is scoped to 35.1 (the benefits plan). Measured 2026-10-09: with
    an Ação-level test the signal fired in 13/13 runs while 35.1 was never
    evidenced — the accepts were 35.2e/35.2f, the later version of Ação 15."""
    from evaluation.interfaces.contracts import ProductVerdict

    store = DependencyStore(dependencias=[{
        "citante": 35, "citada": 14, "tipo": "artefato", "produtos_citante": ["35.1"],
    }])
    prior = {14: _result(14, None, no_evidence=True)}
    verdicts = lambda on: [  # noqa: E731
        ProductVerdict(product_id=p, evidenced=(p in on)) for p in ("35.1", "35.2e", "35.2f")
    ]
    assert not compute_dependency_cap(35, 1, prior, store, verdicts({"35.2e", "35.2f"})).review_recommended
    assert compute_dependency_cap(35, 1, prior, store, verdicts({"35.1"})).review_recommended
    # without verdicts a scoped edge cannot claim anything
    assert not compute_dependency_cap(35, 1, prior, store).review_recommended


def test_the_shipped_file_scopes_acao_35_by_plan():
    store = get_dependency_store()
    escopos = {d.citada: d.produtos_citante for d in store.artefato(35)}
    assert escopos[14] == ["35.1"]
    assert escopos[15] == ["35.2a", "35.2b", "35.2c", "35.2d", "35.2e", "35.2f", "35.2g"]


def test_loader_refuses_a_scope_outside_the_citing_acao(tmp_path):
    with pytest.raises(RuntimeError, match="não pertence"):
        load_dependencies(_write(tmp_path, [{
            "citante": 35, "citada": 14, "tipo": "artefato", "produtos_citante": ["14a"],
        }]))


def test_artefato_cited_ok_is_silent():
    store = _store((29, 11, "artefato"))
    cap = compute_dependency_cap(29, 3, {11: _result(11, 1)}, store)
    assert not cap.applied and not cap.review_recommended


def test_the_shipped_graph_never_caps_43():
    """The IPMP's own Atendido example for 43 contradicts the cap, so the file
    types both 43 edges as `lacuna` and the rule has nothing to say."""
    prior = {27: _result(27, 0), 28: _result(28, None, no_evidence=True)}
    assert compute_dependency_cap(43, 3, prior, get_dependency_store()) is None


# --------------------------------------------------------------------------
# apply_dependency_cap — the score and the interval
# --------------------------------------------------------------------------


def _margin(floor: int | None, ceiling: int | None) -> ScoreMargin:
    return ScoreMargin(n_products=4, n_evidenced=4, band_margin=1,
                       score_floor=floor, score_ceiling=ceiling)


def test_apply_without_cap_changes_nothing():
    m = _margin(1, 3)
    assert apply_dependency_cap(3, m, None) == (3, m)
    assert apply_dependency_cap(3, m, DependencyCap(applied=False)) == (3, m)


def test_apply_caps_3_to_1_and_clips_the_interval():
    cap = DependencyCap(applied=True, score_before_cap=3)
    score, m = apply_dependency_cap(3, _margin(1, 3), cap)
    assert score == 1
    assert (m.score_floor, m.score_ceiling) == (1, 1)


def test_apply_never_raises_a_score_and_keeps_a_none_floor():
    cap = DependencyCap(applied=True, score_before_cap=3)
    assert apply_dependency_cap(1, _margin(0, 1), cap) == (1, _margin(0, 1))
    assert apply_dependency_cap(0, _margin(None, 0), cap)[0] == 0
    score, m = apply_dependency_cap(3, _margin(None, 3), cap)
    assert score == 1 and m.score_floor is None and m.score_ceiling == 1


def test_apply_keeps_the_rest_of_the_margin_untouched():
    """The fragile bits and the band margin are facts about the evidence; the
    cap only bounds the reported interval."""
    m = ScoreMargin(n_products=4, n_evidenced=4, n_fragile=2, band_margin=1,
                    score_floor=1, score_ceiling=3, review_recommended=True,
                    explanation="x")
    _, capped = apply_dependency_cap(3, m, DependencyCap(applied=True, score_before_cap=3))
    assert capped.n_fragile == 2 and capped.band_margin == 1
    assert capped.review_recommended and capped.explanation == "x"


# --------------------------------------------------------------------------
# evaluate() integration — the real graph, a stub scorer
# --------------------------------------------------------------------------


class _Stub:
    def __init__(self, products: dict[str, bool]) -> None:
        self._products = products
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.calls.append((system, user))
        return json.dumps({
            "reasoning": "ok", "score": 3, "uncertainty": False,
            "products": [{"product_id": p, "evidenced": e, "justificativa": "j"}
                         for p, e in self._products.items()],
        })


def _chunk(product_ids: list[str]) -> RetrievedChunk:
    return RetrievedChunk(
        process_number="P", filename="ETP.pdf", page_number=158, chunk_index=0,
        char_offset=0, page_total=10, ocr_used=False, source_type="text",
        text="Divisão do objeto em quatro lotes com quantitativos.",
        cascade_step="bm25", expected_product_ids=product_ids, bm25_score=3.5, rank=1,
    )


@pytest.fixture(autouse=True)
def _reset_llm():
    _reset()
    yield
    _reset()


def _wire(stub: _Stub) -> None:
    import evaluation._config as cfg
    cfg._client = stub
    cfg._provider = "llamacpp"
    cfg._model = "stub"


def test_evaluate_caps_acao_3_when_acao_2_scored_0_in_the_run():
    """Ação 3 counts 3 (its single product 3a evidenced); Ação 2 came out 0."""
    stub = _Stub({"3a": True})
    _wire(stub)
    result = evaluate(3, "P", [_chunk(["3a"])], prior_results={2: _result(2, 0)})
    assert result.proposed_score == 1
    assert result.dependency_cap is not None and result.dependency_cap.applied
    assert result.dependency_cap.score_before_cap == 3
    assert result.score_margin.score_ceiling == 1
    # the counted verdicts are kept intact — the auditor sees what the scorer said
    assert [v.evidenced for v in result.product_verdicts] == [True]
    assert result.score_source == "computed"


def test_evaluate_does_not_cap_when_acao_2_scored_at_least_1():
    _wire(_Stub({"3a": True}))
    result = evaluate(3, "P", [_chunk(["3a"])], prior_results={2: _result(2, 1)})
    assert result.proposed_score == 3
    assert result.dependency_cap is not None and not result.dependency_cap.applied


def test_evaluate_without_prior_results_computes_no_cap():
    """Callers that evaluate one Ação in isolation (older scripts) get the plain
    counted score and no claim about dependencies."""
    _wire(_Stub({"3a": True}))
    result = evaluate(3, "P", [_chunk(["3a"])])
    assert result.proposed_score == 3
    assert result.dependency_cap is None


def test_evaluate_prior_absent_from_the_run_is_unknown_not_low():
    _wire(_Stub({"3a": True}))
    result = evaluate(3, "P", [_chunk(["3a"])], prior_results={})
    assert result.proposed_score == 3
    assert not result.dependency_cap.applied
    assert result.dependency_cap.dependencies[0].estado == "desconhecida"


def test_nothing_about_the_cap_reaches_the_scorer_prompt():
    """Decision 4 (2026-10-05): the model never sees the dependency state.

    The IPMP text itself may name Ação 2 (Ação 3's own description does), so
    the guarantee is byte identity: the prompt with a low prerequisite in the
    run is the same prompt as with no prior results at all.
    """
    capped = _Stub({"3a": True})
    _wire(capped)
    evaluate(3, "P", [_chunk(["3a"])], prior_results={2: _result(2, 0)})
    alone = _Stub({"3a": True})
    _wire(alone)
    evaluate(3, "P", [_chunk(["3a"])])
    assert capped.calls == alone.calls
    system, user = capped.calls[0]
    for forbidden in ("dependência", "teto", "pré-requisito", "limitado a"):
        assert forbidden not in system and forbidden not in user


def test_no_evidence_exit_carries_no_cap():
    _wire(_Stub({"3a": True}))
    result = evaluate(3, "P", [], prior_results={2: _result(2, 0)})
    assert result.no_evidence_found and result.proposed_score is None
    assert result.dependency_cap is None


def test_persisted_result_round_trips_the_cap():
    _wire(_Stub({"3a": True}))
    result = evaluate(3, "P", [_chunk(["3a"])], prior_results={2: _result(2, 0)})
    again = EvaluationResult.model_validate(json.loads(result.model_dump_json()))
    assert again.dependency_cap == result.dependency_cap
    assert again.proposed_score == 1
