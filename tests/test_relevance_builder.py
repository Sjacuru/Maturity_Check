"""Tests for evaluation.prompt.relevance_builder (ADR-0050 gate prompt)."""

from __future__ import annotations

from evaluation.prompt.relevance_builder import build_relevance_system_prompt, build_relevance_user_prompt


def test_system_prompt_without_concepts_contains_only_evidence_intent():
    prompt = build_relevance_system_prompt("evidência de X")
    assert "evidência de X" in prompt
    assert "Qualquer um dos elementos abaixo" not in prompt


def test_system_prompt_with_empty_concepts_list_matches_no_concepts():
    with_none = build_relevance_system_prompt("evidência de X", None)
    with_empty = build_relevance_system_prompt("evidência de X", [])
    assert with_none == with_empty
    assert "Qualquer um dos elementos abaixo" not in with_empty


def test_system_prompt_with_concepts_lists_each_as_a_bullet():
    prompt = build_relevance_system_prompt(
        "evidência de X", ["Matriz de riscos e alocação de responsabilidades", "Metas de interesse público"]
    )
    assert "evidência de X" in prompt
    assert "Qualquer um dos elementos abaixo também conta como evidência válida" in prompt
    assert "- Matriz de riscos e alocação de responsabilidades" in prompt
    assert "- Metas de interesse público" in prompt


def test_system_prompt_without_negative_patterns_omits_exclusion_section():
    prompt = build_relevance_system_prompt("evidência de X")
    assert "NÃO contam como evidência válida" not in prompt


def test_system_prompt_with_empty_negative_patterns_matches_none():
    with_none = build_relevance_system_prompt("evidência de X", ["c"], None)
    with_empty = build_relevance_system_prompt("evidência de X", ["c"], [])
    assert with_none == with_empty
    assert "NÃO contam como evidência válida" not in with_empty


def test_system_prompt_with_negative_patterns_lists_each_as_a_bullet():
    prompt = build_relevance_system_prompt(
        "evidência de X",
        ["Matriz de riscos e alocação de responsabilidades"],
        ["Cláusulas de sanções administrativas sem relação com o critério"],
    )
    assert "evidência de X" in prompt
    assert "Qualquer um dos elementos abaixo também conta como evidência válida" in prompt
    assert "NÃO contam como evidência válida para este critério" in prompt
    assert "- Cláusulas de sanções administrativas sem relação com o critério" in prompt
    # Negative section must come after the positive concepts section.
    assert prompt.index("também conta como evidência válida") < prompt.index("NÃO contam como evidência válida")


def test_user_prompt_wraps_chunk_text():
    prompt = build_relevance_user_prompt("texto do trecho")
    assert prompt == "[Trecho a avaliar]\ntexto do trecho"


# --------------------------------------------------------------------------
# Identity block (2026-09-29) and sibling contrast + user-prompt tag (V5,
# 2026-10-02, ADR-0064). The block had no tests until the sibling list landed.
# --------------------------------------------------------------------------

from ingestion.ipmp import AcaoIPMP, ProdutoEsperado  # noqa: E402

from evaluation.prompt import relevance_builder as rb  # noqa: E402


def _acao(products: list[tuple[str, str, bool]], acao_id: int = 7) -> AcaoIPMP:
    return AcaoIPMP(
        acao_id=acao_id,
        titulo="Título da Ação",
        dimensao="Gerencial",
        fase="Estudo das alternativas",
        ponto_transicao=False,
        por_que_importante="",
        descricao_acao="",
        o_que_esperar="",
        produtos_esperados=[ProdutoEsperado(id=i, texto=t, scored=s) for i, t, s in products],
        momento_ideal="",
        excecoes=[],
        exemplos=[],
    )


_THREE = [
    ("7", "Documento que contenha, no mínimo:", False),  # section header, not scored
    ("7a", "Texto do produto A", True),
    ("7b", "Texto do produto B", True),
    ("7c", "Texto do produto C", True),
]


def test_identity_block_names_acao_product_and_sibling_count():
    prompt = build_relevance_system_prompt("critério B", acao=_acao(_THREE), product_id="7b")
    assert "## O que está sendo avaliado" in prompt
    assert "Ação 7 — Título da Ação" in prompt
    assert "Dimensão Gerencial, fase Estudo das alternativas." in prompt
    assert "Produto Esperado 7b, um dos 3 Produtos Esperados avaliados nesta Ação." in prompt
    assert rb._SCOPE_RULE in prompt


def test_identity_block_lists_every_other_scored_product_as_not_under_evaluation():
    prompt = build_relevance_system_prompt("critério B", acao=_acao(_THREE), product_id="7b")
    assert "Os demais Produtos Esperados desta Ação, que NÃO estão em avaliação aqui" in prompt
    assert "- 7a — Texto do produto A" in prompt
    assert "- 7c — Texto do produto C" in prompt
    assert "- 7b —" not in prompt            # the product under evaluation is not its own sibling
    assert "- 7 —" not in prompt             # the unscored section header is not a sibling
    # Order: product line -> sibling list -> scope rule -> criterion.
    assert (
        prompt.index("Produto Esperado 7b")
        < prompt.index("Os demais Produtos Esperados")
        < prompt.index(rb._SCOPE_RULE)
        < prompt.index("## Critério de relevância")
    )


def test_identity_block_single_product_has_no_sibling_list():
    acao = _acao([("37", "Conjunto completo dos documentos finalizados.", True)], acao_id=37)
    prompt = build_relevance_system_prompt("critério", acao=acao, product_id="37")
    assert "Produto Esperado 37, o único Produto Esperado avaliado nesta Ação." in prompt
    assert "Os demais Produtos Esperados" not in prompt


def test_sibling_text_is_quoted_whole_by_default():
    # ADR-0071: the enumeration at the end of a long product text is what tells
    # one sibling from another, so nothing is cut unless a limit is set.
    long_text = "palavra " * 60 + "ENUMERAÇÃO FINAL"  # ~500 chars
    acao = _acao([("7a", long_text, True), ("7b", "curto", True)])
    prompt = build_relevance_system_prompt("critério", acao=acao, product_id="7b")
    line = next(l for l in prompt.splitlines() if l.startswith("- 7a — "))
    body = line[len("- 7a — "):]
    assert rb._SIBLING_TEXT_MAX is None
    assert body == " ".join(long_text.split())
    assert body.endswith("ENUMERAÇÃO FINAL") and "…" not in body


def test_sibling_text_limit_still_truncates_when_set(monkeypatch):
    # The diagnostics reproduce the pre-2026-10-09 prompt by setting the limit.
    monkeypatch.setattr(rb, "_SIBLING_TEXT_MAX", 140)
    long_text = "palavra " * 60  # ~480 chars
    acao = _acao([("7a", long_text, True), ("7b", "curto", True)])
    prompt = build_relevance_system_prompt("critério", acao=acao, product_id="7b")
    line = next(l for l in prompt.splitlines() if l.startswith("- 7a — "))
    body = line[len("- 7a — "):]
    assert body.endswith("…")
    assert len(body) <= 140
    assert "palavra palavra" in body


def test_identity_block_quotes_product_text_only_when_the_intent_does_not_restate_it():
    acao = _acao(_THREE)
    different = build_relevance_system_prompt("critério B, formulado de outra maneira",
                                              acao=acao, product_id="7b")
    assert "«Texto do produto B»" in different
    restating = build_relevance_system_prompt("Texto do produto B", acao=acao, product_id="7b")
    assert "«Texto do produto B»" not in restating


def test_system_prompt_without_acao_has_no_identity_block():
    prompt = build_relevance_system_prompt("critério")
    assert "## O que está sendo avaliado" not in prompt
    assert "Os demais Produtos Esperados" not in prompt
    assert "## Critério de relevância" in prompt


def test_user_prompt_with_product_id_tags_it_before_the_chunk():
    prompt = build_relevance_user_prompt("texto do trecho", product_id="14e")
    assert prompt == (
        "[Produto Esperado 14e — avalie SOMENTE este critério]\n"
        "[Trecho a avaliar]\n"
        "texto do trecho"
    )


# --- polarity sentence (2026-10-03, ADR-0066) ---

def test_instructions_say_attested_non_fulfilment_is_still_relevant():
    """Ação 26's parecer stating the budget declaration was NOT met was rejected
    4/4 because the gate read 'evidence for X' as evidence THAT X holds; the
    fulfilment judgement belongs to the scorer, so the instructions say so."""
    prompt = build_relevance_system_prompt("evidência de X")
    assert "NÃO foi atendido" in prompt
    assert "julgar o cumprimento é da etapa seguinte" in prompt
    # and the guard against reading it as looseness
    assert "apenas mencione o tema" in prompt


# --- V4: a concept list that only restates the intent is omitted (2026-10-03) ---

def test_concept_list_that_restates_the_intent_is_omitted():
    intent = "Método de reporte do progresso de cada benefício durante a execução da obra."
    prompt = build_relevance_system_prompt(
        intent, ["Método de reporte do progresso de cada benefício durante a execução da obra"]
    )
    assert "Qualquer um dos elementos abaixo" not in prompt
    assert intent in prompt


def test_concept_list_with_one_distinct_concept_is_kept_whole():
    intent = "Método de reporte do progresso de cada benefício durante a execução da obra."
    prompt = build_relevance_system_prompt(
        intent,
        [
            "Método de reporte do progresso de cada benefício durante a execução da obra",
            "Periodicidade e destinatário dos relatórios de progresso",
        ],
    )
    assert "Qualquer um dos elementos abaixo" in prompt
    assert "- Periodicidade e destinatário dos relatórios de progresso" in prompt
    # the restating entry is not singled out: the rule is all-or-nothing
    assert "- Método de reporte do progresso de cada benefício" in prompt


def test_concepts_restate_intent_rule_is_case_and_punctuation_insensitive():
    from evaluation.prompt.relevance_builder import _concepts_restate_intent

    assert _concepts_restate_intent(["  método DE reporte "], "Método de reporte.")
    assert not _concepts_restate_intent([], "qualquer coisa")
    assert not _concepts_restate_intent(["Periodicidade dos relatórios"], "Método de reporte.")
