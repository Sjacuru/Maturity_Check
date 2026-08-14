"""Tests for evaluation.evidence_selection.select_evidence (ADR-0050)."""

from __future__ import annotations

import json

import pytest

from ingestion.retrieval_profile import (
    AcaoRetrievalProfile,
    ExpectedProductProfile,
    NearQueryTerm,
    PhraseQueryTerm,
    RetrievalProfileStore,
    RetrievalSignalConcept,
)
from retrieval.interfaces.contracts import RetrievedChunk

import evaluation._config as eval_cfg
import evaluation.evidence_selection as es
from evaluation.evidence_selection import select_evidence


def make_chunk(**kwargs) -> RetrievedChunk:
    defaults = dict(
        process_number="P001",
        filename="doc.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        page_total=10,
        ocr_used=False,
        source_type="text",
        text="texto padrão",
        cascade_step="bm25",
        expected_product_ids=["1a"],
        bm25_score=-5.0,
        rank=1,
    )
    return RetrievedChunk(**{**defaults, **kwargs})


class StubGateClient:
    def __init__(self, responder):
        self._responder = responder
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.calls.append((system, user))
        return self._responder(system, user)


_RELEVANT_YES = json.dumps({"relevant": True})
_RELEVANT_NO = json.dumps({"relevant": False})


@pytest.fixture(autouse=True)
def _reset_gate_config():
    yield
    eval_cfg._reset()


def _set_gate(responder):
    eval_cfg._gate_client = StubGateClient(responder)


def _profile_with_evidence_intent(product_id: str, evidence_intent: str) -> RetrievalProfileStore:
    return RetrievalProfileStore(
        acoes={
            1: AcaoRetrievalProfile(
                acao_id=1,
                profile_maturity="seed",
                expected_products={
                    product_id: ExpectedProductProfile(
                        evidence_intent=evidence_intent,
                        retrieval_signal_concepts=[],
                        query_terms=[],
                    )
                },
            )
        }
    )


def _no_neighbors(monkeypatch):
    monkeypatch.setattr(es, "fetch_neighbor_chunks", lambda *a, **k: (None, None))


def test_relevant_chunk_is_accepted_as_anchor(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: _RELEVANT_YES)

    chunk = make_chunk()
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert len(result.accepted) == 1
    assert result.accepted[0].text == "texto padrão"
    assert result.rejected == []


def test_irrelevant_chunk_is_rejected(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: _RELEVANT_NO)

    chunk = make_chunk()
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert result.accepted == []
    assert len(result.rejected) == 1
    assert result.rejected[0].expected_product_id == "1a"
    assert result.rejected[0].filename == chunk.filename


def test_product_without_evidence_intent_passes_through_ungated(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))

    def _boom(system, user):
        raise AssertionError("gate must not be called when no evidence_intent exists")

    _set_gate(_boom)

    chunk = make_chunk()
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert result.accepted == [chunk]
    assert result.rejected == []


def test_anchor_target_caps_at_five(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: _RELEVANT_YES)

    # Use distinct texts so the semantic-dedup step does not collapse them
    # (this test is about the anchor-target cap, not near-duplicate removal).
    chunks = [
        (1.0 - i * 0.01, make_chunk(page_number=i, chunk_index=0, text=f"texto distinto {i}"))
        for i in range(10)
    ]
    result = select_evidence(1, "P001", {"1a": chunks})

    assert len(result.accepted) == 5


def test_max_examined_caps_gate_calls_when_model_keeps_rejecting(monkeypatch):
    """A strict gate model that rejects everything must not traverse the full
    candidate pool — worst-case call count per product is bounded by
    _MAX_EXAMINED, not by len(ranked) (found 2026-06-28: 40+ calls/product)."""
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)

    stub = StubGateClient(lambda system, user: _RELEVANT_NO)
    eval_cfg._gate_client = stub

    chunks = [
        (1.0 - i * 0.01, make_chunk(page_number=i, chunk_index=0, text=f"texto{i}"))
        for i in range(20)
    ]
    result = select_evidence(1, "P001", {"1a": chunks})

    assert result.accepted == []
    assert len(result.rejected) == es._MAX_EXAMINED
    assert len(stub.calls) == es._MAX_EXAMINED


def test_relevant_anchor_triggers_neighbor_expansion(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))

    prev_chunk = make_chunk(page_number=1, chunk_index=0, text="anterior")
    next_chunk = make_chunk(page_number=1, chunk_index=2, text="seguinte")
    monkeypatch.setattr(es, "fetch_neighbor_chunks", lambda *a, **k: (prev_chunk, next_chunk))
    _set_gate(lambda system, user: _RELEVANT_YES)

    anchor = make_chunk(page_number=1, chunk_index=1, text="ancora")
    result = select_evidence(1, "P001", {"1a": [(0.05, anchor)]})

    texts = {c.text for c in result.accepted}
    assert "anterior" in texts
    assert "seguinte" in texts


def test_rejected_neighbor_is_recorded(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))

    prev_chunk = make_chunk(page_number=1, chunk_index=0, text="anterior irrelevante")
    monkeypatch.setattr(es, "fetch_neighbor_chunks", lambda *a, **k: (prev_chunk, None))

    calls = {"n": 0}

    def responder(system, user):
        calls["n"] += 1
        if calls["n"] == 1:
            return _RELEVANT_YES
        return _RELEVANT_NO

    _set_gate(responder)

    anchor = make_chunk(page_number=1, chunk_index=1, text="ancora")
    result = select_evidence(1, "P001", {"1a": [(0.05, anchor)]})

    assert any(r.page_number == 1 and r.chunk_index == 0 for r in result.rejected)


def test_expansion_target_caps_at_five_per_product(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))

    # Each anchor contributes up to 2 neighbors (prev+next); 5 anchors -> up to
    # 10 candidate neighbors, but expansion must cap at 5 total for the product.
    neighbor_counter = {"n": 0}

    def fake_neighbors(process_number, filename, page_number, chunk_index):
        neighbor_counter["n"] += 1
        prev = make_chunk(page_number=page_number, chunk_index=-1, text=f"prev{neighbor_counter['n']}")
        nxt = make_chunk(page_number=page_number, chunk_index=999, text=f"next{neighbor_counter['n']}")
        return prev, nxt

    monkeypatch.setattr(es, "fetch_neighbor_chunks", fake_neighbors)
    _set_gate(lambda system, user: _RELEVANT_YES)

    # Texts are distinct enough that semantic dedup does not collapse them
    # (this test is about the expansion-target cap, not near-duplicate removal).
    anchors = [
        (1.0 - i * 0.01, make_chunk(page_number=i, chunk_index=0, text=f"conteudo da ancora numero {i}"))
        for i in range(5)
    ]
    result = select_evidence(1, "P001", {"1a": anchors})

    expansion_texts = [c.text for c in result.accepted if c.text.startswith(("prev", "next"))]
    assert len(expansion_texts) == 5


def test_trim_expansions_drops_weakest_anchor_score_first(monkeypatch):
    monkeypatch.setattr(es, "_EVIDENCE_BUDGET_CHARS", 600)

    anchors = [(0.5, make_chunk(text="a" * 100))]
    strong_expansion = make_chunk(page_number=2, text="b" * 500)
    weak_expansion = make_chunk(page_number=3, text="c" * 500)
    expansions = [(0.9, strong_expansion), (0.1, weak_expansion)]

    kept = es._trim_expansions_to_budget(anchors, expansions)

    assert weak_expansion not in kept
    assert strong_expansion in kept


def _two_product_profile(intent_a: str = "X", intent_c: str = "Y") -> RetrievalProfileStore:
    return RetrievalProfileStore(
        acoes={
            1: AcaoRetrievalProfile(
                acao_id=1,
                profile_maturity="seed",
                expected_products={
                    "1a": ExpectedProductProfile(
                        evidence_intent=intent_a, retrieval_signal_concepts=[], query_terms=[]
                    ),
                    "1c": ExpectedProductProfile(
                        evidence_intent=intent_c, retrieval_signal_concepts=[], query_terms=[]
                    ),
                },
            )
        }
    )


def test_chunk_accepted_by_two_products_is_deduplicated(monkeypatch):
    """Final scoring is one combined call across all products (ADR-0009) — a
    chunk claimed relevant by two products must still reach evaluate() once."""
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(_rp, "_store", _two_product_profile())
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: _RELEVANT_YES)

    shared_chunk = make_chunk(page_number=3, chunk_index=0, text="conteudo compartilhado")
    result = select_evidence(
        1,
        "P001",
        {
            "1a": [(0.9, shared_chunk)],  # higher score
            "1c": [(0.5, shared_chunk)],  # lower score
        },
    )

    matches = [c for c in result.accepted if c.page_number == 3 and c.chunk_index == 0]
    assert len(matches) == 1
    assert matches[0].expected_product_ids == ["1a", "1c"]  # both products merged


def test_anchor_wins_over_expansion_for_same_physical_chunk(monkeypatch):
    """A chunk that is one product's anchor and another product's fetched
    neighbor must appear once, attributed to the anchor (higher-confidence)."""
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(_rp, "_store", _two_product_profile())

    shared_chunk = make_chunk(page_number=5, chunk_index=1, text="ancora e vizinho")

    def fake_neighbors(process_number, filename, page_number, chunk_index):
        if page_number == 5 and chunk_index == 0:
            return None, shared_chunk  # 1c's anchor's "next" neighbor is shared_chunk
        return None, None

    monkeypatch.setattr(es, "fetch_neighbor_chunks", fake_neighbors)
    _set_gate(lambda system, user: _RELEVANT_YES)

    c_anchor = make_chunk(page_number=5, chunk_index=0, text="ancora de 1c")
    result = select_evidence(
        1,
        "P001",
        {
            "1a": [(0.9, shared_chunk)],  # 1a claims it directly as an anchor
            "1c": [(0.5, c_anchor)],  # 1c's anchor, whose neighbor is shared_chunk
        },
    )

    matches = [c for c in result.accepted if c.page_number == 5 and c.chunk_index == 1]
    assert len(matches) == 1
    # anchor (1a) wins over expansion; expansion's product (1c) is merged in
    assert "1a" in matches[0].expected_product_ids
    assert "1c" in matches[0].expected_product_ids


def test_deduplicate_across_products_prefers_higher_score():
    chunk = make_chunk(page_number=7, chunk_index=2)
    anchors = [(0.3, chunk), (0.8, chunk)]
    deduped_anchors, deduped_expansions = es._deduplicate_across_products(anchors, [])
    assert len(deduped_anchors) == 1
    assert deduped_anchors[0][0] == 0.8


def test_deduplicate_across_products_expansion_loses_to_anchor():
    chunk = make_chunk(page_number=9, chunk_index=4)
    anchors = [(0.5, chunk)]
    expansions = [(0.9, chunk)]  # higher score, but still must lose to the anchor
    deduped_anchors, deduped_expansions = es._deduplicate_across_products(anchors, expansions)
    assert len(deduped_anchors) == 1
    assert deduped_expansions == []


def test_strip_extraction_noise_removes_header_block():
    text = (
        "PREFEITURA DA CIDADE DO RIO DE JANEIRO  \n"
        "Secretaria Municipal de Coordenação Governamental  \n"
        "R. Afonso Cavalcanti, 455 – Cidade Nova  \n"
        "Rio de Janeiro - RJ - CEP 20211-110 \n"
        "Conteúdo substantivo do trecho."
    )
    assert es.strip_extraction_noise(text) == "Conteúdo substantivo do trecho."


def test_strip_extraction_noise_tolerates_ligature_corruption():
    for broken in ("CavalcanƟ", "Cavalcan琀椀"):
        text = (
            "PREFEITURA DA CIDADE DO RIO DE JANEIRO  \n"
            "Secretaria Municipal de Coordenação Governamental  \n"
            f"R. Afonso {broken}, 455 – Cidade Nova  \n"
            "Rio de Janeiro - RJ - CEP 20211-110 \n"
            "Conteúdo substantivo do trecho."
        )
        assert es.strip_extraction_noise(text) == "Conteúdo substantivo do trecho."


def test_strip_extraction_noise_removes_signature_block_with_newline_before_url():
    text = (
        "Conteúdo substantivo do trecho.\n"
        "SMGPRO202400020V02\n"
        "Autenticado digitalmente por FULANO DE TAL - 28/05/2024 às 16:20:57.\n"
        "Documento Nº: 123.456-789 - consulta à autenticidade em\n"
        "https://acesso.processo.rio/sigaex/public/app/autenticar?n=123.456-789"
    )
    assert es.strip_extraction_noise(text) == "Conteúdo substantivo do trecho."


def test_strip_extraction_noise_removes_signature_block_with_space_before_url():
    # Some pages wrap the URL onto the same line (space, not newline) — must
    # not depend on a literal line break being present.
    text = (
        "Conteúdo substantivo do trecho.\n"
        "Autenticado digitalmente por FULANO DE TAL - 28/05/2024 às 16:20:57.\n"
        "Documento Nº: 123.456-789 - consulta à autenticidade em "
        "https://acesso.processo.rio/sigaex/public/app/autenticar?n=123.456-789"
    )
    assert es.strip_extraction_noise(text) == "Conteúdo substantivo do trecho."


def test_strip_extraction_noise_removes_bare_version_tag_without_signature():
    text = "SMGPRO202400020V01\nMINUTA\n13 CONCLUSÃO\nConteúdo substantivo."
    assert es.strip_extraction_noise(text) == "13 CONCLUSÃO\nConteúdo substantivo."


def test_strip_extraction_noise_removes_vertical_watermark_run():
    watermark = "\n".join(list("processo.rio Secretaria"))  # one char per line
    text = f"Conteúdo substantivo do trecho.\n{watermark}\n570"
    assert es.strip_extraction_noise(text) == "Conteúdo substantivo do trecho."


def test_strip_extraction_noise_preserves_short_list_markers():
    # Isolated short lines like "a)" interspersed with real prose must survive
    # — only long uninterrupted runs of single-char lines are the watermark.
    text = (
        "Os resultados pretendidos buscam:\n"
        "a)\n"
        "Promover a renovação tecnológica;\n"
        "b)\n"
        "Modernizar a prestação dos serviços."
    )
    assert es.strip_extraction_noise(text) == text


def test_strip_extraction_noise_is_noop_on_clean_text():
    text = "Texto já limpo, sem nenhum ruído de extração."
    assert es.strip_extraction_noise(text) == text


def test_select_evidence_passes_retrieval_signal_concepts_to_gate(monkeypatch):
    """A chunk that doesn't match evidence_intent's literal framing sentence
    but does match one of the product's retrieval_signal_concepts must still
    reach the gate's prompt — the gap that caused 1c's risk-matrix chunk and
    1b's viability conclusion to be rejected under evidence_intent alone."""
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(
        _rp,
        "_store",
        RetrievalProfileStore(
            acoes={
                1: AcaoRetrievalProfile(
                    acao_id=1,
                    profile_maturity="seed",
                    expected_products={
                        "1c": ExpectedProductProfile(
                            evidence_intent="Seção que define os objetivos estratégicos do projeto.",
                            retrieval_signal_concepts=[
                                RetrievalSignalConcept(
                                    key="risk_framework",
                                    text="Matriz de riscos e alocação de responsabilidades entre as partes",
                                )
                            ],
                            query_terms=[],
                        )
                    },
                )
            }
        ),
    )
    _no_neighbors(monkeypatch)

    captured = []

    def responder(system, user):
        captured.append(system)
        return _RELEVANT_YES

    _set_gate(responder)

    chunk = make_chunk(text="matriz de risco do contrato")
    select_evidence(1, "P001", {"1c": [(0.05, chunk)]})

    assert "objetivos estratégicos do projeto" in captured[0]
    assert "Qualquer um dos elementos abaixo também conta como evidência válida" in captured[0]
    assert "Matriz de riscos e alocação de responsabilidades entre as partes" in captured[0]


def test_select_evidence_strips_noise_before_gating(monkeypatch):
    """The gate must never see raw header/footer noise, and the accepted
    chunk's stored text is always the deterministically-stripped version —
    the gate returns only a binary verdict, no text of its own."""
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)

    captured_user_prompts = []

    def responder(system, user):
        captured_user_prompts.append(user)
        return _RELEVANT_YES

    _set_gate(responder)

    noisy_text = (
        "PREFEITURA DA CIDADE DO RIO DE JANEIRO  \n"
        "Secretaria Municipal de Coordenação Governamental  \n"
        "R. Afonso Cavalcanti, 455 – Cidade Nova  \n"
        "Rio de Janeiro - RJ - CEP 20211-110 \n"
        "Conteúdo substantivo do trecho."
    )
    chunk = make_chunk(text=noisy_text)
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert "PREFEITURA" not in captured_user_prompts[0]
    assert "Conteúdo substantivo do trecho." in captured_user_prompts[0]
    assert result.accepted[0].text == "Conteúdo substantivo do trecho."


_LONG_VIABILITY_TEXT = (
    "13 CONCLUSÃO A partir dos dados e das premissas estabelecidas e evidenciadas neste "
    "estudo referencial, que tiveram como base, em sua maioria, projetos análogos realizados "
    "por outros entes federativos, foi elaborado fluxo de caixa para avaliar o produto dos "
    "investimentos, receitas e custos e despesas operacionais trazidos a valor presente pela "
    "taxa de desconto estabelecida e conclui-se, conforme demonstrado, que há viabilidade "
    "econômico-financeira do projeto em questão."
)


def test_dedup_semantic_drops_near_duplicate_below_threshold():
    """Verified-identical text (> _SEMANTIC_DEDUP_MIN_CHARS) must be collapsed to one."""
    c1 = make_chunk(page_number=14, text=_LONG_VIABILITY_TEXT)
    c2 = make_chunk(page_number=121, text=_LONG_VIABILITY_TEXT)
    result = es._dedup_semantic([c1, c2])
    assert len(result) == 1
    assert result[0].page_number == 14  # first one wins


def test_dedup_semantic_preserves_distinct_chunks():
    """Genuinely different long-form chunks must both survive despite shared legal vocabulary."""
    c1 = make_chunk(page_number=1, text=_LONG_VIABILITY_TEXT)
    c2 = make_chunk(page_number=2, text=(
        "MATRIZ DE RISCO Definição do risco Descrição Alocação Ações para mitigação "
        "Impossibilidade de captação de recursos de terceiros para financiar a execução "
        "do CONTRATO CONCESSIONÁRIA Aporte de capital própria da CONCESSIONÁRIA e/ou de "
        "seus acionistas para cumprir com as obrigações contratuais assumidas. Variação "
        "da taxa de juros CONCESSIONÁRIA Adoção de critérios e políticas internos para "
        "seleção da instituição financeira e das condições para contratação de financiamentos."
    ))
    result = es._dedup_semantic([c1, c2])
    assert len(result) == 2


def test_dedup_semantic_threshold_is_configurable():
    """threshold=1.0 keeps two near-identical-but-not-identical long texts."""
    text_a = _LONG_VIABILITY_TEXT
    text_b = _LONG_VIABILITY_TEXT.replace("há viabilidade", "há clara viabilidade")
    assert len(text_a) >= es._SEMANTIC_DEDUP_MIN_CHARS
    result_strict = es._dedup_semantic([
        make_chunk(page_number=1, text=text_a),
        make_chunk(page_number=2, text=text_b),
    ], threshold=1.0)
    assert len(result_strict) == 2  # strict exact-match threshold keeps both


def test_prefilter_near_duplicates_drops_near_exact_copies():
    """Near-identical long texts (ratio >= 0.92) keep only the highest-ranked copy."""
    c1 = (0.9, make_chunk(page_number=14, text=_LONG_VIABILITY_TEXT))
    c2 = (0.5, make_chunk(page_number=121, text=_LONG_VIABILITY_TEXT))
    result = es._prefilter_near_duplicates([c1, c2])
    assert len(result) == 1
    assert result[0][1].page_number == 14


def test_prefilter_near_duplicates_keeps_distinct_candidates():
    """Genuinely different long texts (ratio < 0.92) both survive."""
    c1 = (0.9, make_chunk(page_number=1, text=_LONG_VIABILITY_TEXT))
    c2 = (0.5, make_chunk(page_number=2, text=(
        "MATRIZ DE RISCO Definição do risco Descrição Alocação Ações para mitigação "
        "Impossibilidade de captação de recursos de terceiros para financiar a execução "
        "do CONTRATO CONCESSIONÁRIA Aporte de capital própria da CONCESSIONÁRIA e/ou de "
        "seus acionistas para cumprir com as obrigações contratuais assumidas. Variação "
        "da taxa de juros CONCESSIONÁRIA Adoção de critérios e políticas internos para "
        "seleção da instituição financeira e das condições para contratação de financiamentos."
    )))
    result = es._prefilter_near_duplicates([c1, c2])
    assert len(result) == 2


def test_prefilter_near_duplicates_short_texts_pass_through():
    """Texts below _SEMANTIC_DEDUP_MIN_CHARS skip comparison and always survive."""
    short = "texto curto"  # well below 100 chars — identical copies both pass
    c1 = (0.9, make_chunk(page_number=1, text=short))
    c2 = (0.5, make_chunk(page_number=2, text=short))
    result = es._prefilter_near_duplicates([c1, c2])
    assert len(result) == 2


def test_prefilter_reduces_gate_calls_for_near_duplicate_candidates(monkeypatch):
    """Pre-gate dedup collapses near-identical candidates so each unique text
    is gated only once, not once per repeated page."""
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)

    stub = StubGateClient(lambda system, user: _RELEVANT_YES)
    eval_cfg._gate_client = stub

    c1 = make_chunk(page_number=14, text=_LONG_VIABILITY_TEXT)
    c2 = make_chunk(page_number=121, text=_LONG_VIABILITY_TEXT)
    result = select_evidence(1, "P001", {"1a": [(0.9, c1), (0.5, c2)]})

    assert len(stub.calls) == 1          # pre-gate dedup collapsed two identical candidates to one
    assert len(result.accepted) == 1
    assert result.accepted[0].page_number == 14


def test_dedup_semantic_applied_in_select_evidence(monkeypatch):
    """Two accepted chunks with identical long content must produce only one
    in the final EvidenceSelectionResult.accepted list."""
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: _RELEVANT_YES)

    c1 = make_chunk(page_number=10, text=_LONG_VIABILITY_TEXT)
    c2 = make_chunk(page_number=20, text=_LONG_VIABILITY_TEXT)
    result = select_evidence(1, "P001", {"1a": [(0.9, c1), (0.5, c2)]})

    assert len(result.accepted) == 1
    assert result.accepted[0].page_number == 10  # higher-ranked chunk survives


# ---------------------------------------------------------------------------
# Concept attribution (_attribute_concepts)
# ---------------------------------------------------------------------------

def _profile_with_concepts(product_id: str) -> RetrievalProfileStore:
    return RetrievalProfileStore(
        acoes={
            1: AcaoRetrievalProfile(
                acao_id=1,
                profile_maturity="seed",
                expected_products={
                    product_id: ExpectedProductProfile(
                        evidence_intent="evidência de viabilidade",
                        retrieval_signal_concepts=[
                            RetrievalSignalConcept(key="viability", text="viabilidade econômico-financeira"),
                            RetrievalSignalConcept(key="capex", text="CAPEX do projeto"),
                        ],
                        query_terms=[
                            PhraseQueryTerm(
                                encoding="phrase",
                                text="viabilidade econômico-financeira",
                                type="B",
                                provenance="real_world",
                                status="active",
                                concept_ref="viability",
                            ),
                            PhraseQueryTerm(
                                encoding="phrase",
                                text="CAPEX",
                                type="B",
                                provenance="real_world",
                                status="active",
                                concept_ref="capex",
                            ),
                            NearQueryTerm(
                                encoding="near",
                                tokens=["fluxo", "caixa"],
                                distance=5,
                                type="C",
                                provenance="real_world",
                                status="active",
                                concept_ref="viability",
                            ),
                        ],
                    )
                },
            )
        }
    )


def test_attribute_concepts_matches_phrase_term():
    profile = _profile_with_concepts("1b")
    product = profile.acoes[1].expected_products["1b"]
    text = "há viabilidade econômico-financeira do projeto."
    result = es._attribute_concepts(text, product)
    assert "viability" in result


def test_attribute_concepts_matches_near_term():
    profile = _profile_with_concepts("1b")
    product = profile.acoes[1].expected_products["1b"]
    text = "foi elaborado fluxo de caixa para avaliar o projeto."
    result = es._attribute_concepts(text, product)
    assert "viability" in result


def test_attribute_concepts_returns_empty_when_no_match():
    profile = _profile_with_concepts("1b")
    product = profile.acoes[1].expected_products["1b"]
    text = "texto totalmente sem nenhum termo relevante."
    result = es._attribute_concepts(text, product)
    assert result == []


def test_attribute_concepts_includes_experimental_terms():
    """Experimental terms ARE included in attribution — they are registered for
    validation purposes and useful for post-hoc concept matching even though
    they are excluded from BM25 retrieval (build_query_from_terms skips them)."""
    from ingestion.retrieval_profile import PhraseQueryTerm as _Phrase
    store = RetrievalProfileStore(
        acoes={
            1: AcaoRetrievalProfile(
                acao_id=1,
                profile_maturity="seed",
                expected_products={
                    "1a": ExpectedProductProfile(
                        evidence_intent="x",
                        retrieval_signal_concepts=[],
                        query_terms=[
                            _Phrase(
                                encoding="phrase",
                                text="CAPEX",
                                type="B",
                                provenance="real_world",
                                status="experimental",
                                concept_ref="investment_scale",
                            ),
                        ],
                    )
                },
            )
        }
    )
    product = store.acoes[1].expected_products["1a"]
    result = es._attribute_concepts("custo de CAPEX estimado do projeto", product)
    assert "investment_scale" in result  # experimental → still used for attribution


def test_attribute_concepts_skips_deprecated_terms():
    """Deprecated terms are excluded from both BM25 retrieval and attribution."""
    from ingestion.retrieval_profile import PhraseQueryTerm as _Phrase
    store = RetrievalProfileStore(
        acoes={
            1: AcaoRetrievalProfile(
                acao_id=1,
                profile_maturity="seed",
                expected_products={
                    "1a": ExpectedProductProfile(
                        evidence_intent="x",
                        retrieval_signal_concepts=[],
                        query_terms=[
                            _Phrase(
                                encoding="phrase",
                                text="termo depreciado",
                                type="B",
                                provenance="real_world",
                                status="deprecated",
                                concept_ref="some_concept",
                            ),
                        ],
                    )
                },
            )
        }
    )
    product = store.acoes[1].expected_products["1a"]
    result = es._attribute_concepts("contém termo depreciado aqui", product)
    assert result == []  # deprecated terms are not used for attribution


def test_accepted_chunk_carries_matched_concepts(monkeypatch):
    """Accepted anchors must have their matched_concepts populated post-gate."""
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_concepts("1a"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: _RELEVANT_YES)

    chunk = make_chunk(text="há viabilidade econômico-financeira do projeto com CAPEX estimado.")
    result = select_evidence(1, "P001", {"1a": [(0.9, chunk)]})

    assert len(result.accepted) == 1
    assert "viability" in result.accepted[0].matched_concepts
    assert "capex" in result.accepted[0].matched_concepts


def test_rejected_chunk_carries_matched_concepts(monkeypatch):
    """Rejected chunks record which concepts were present despite rejection —
    a non-empty list is a signal for auditor review."""
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_concepts("1a"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: _RELEVANT_NO)

    chunk = make_chunk(text="há viabilidade econômico-financeira do projeto.")
    result = select_evidence(1, "P001", {"1a": [(0.9, chunk)]})

    assert len(result.rejected) == 1
    assert "viability" in result.rejected[0].matched_concepts
