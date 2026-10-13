"""Chunk-level genre classifier (ADR-0074): instrument text vs other text."""

from __future__ import annotations

from retrieval.genre import classifier as C
from retrieval.genre.classifier import (
    INSTRUMENT,
    OTHER,
    UNDECIDED,
    chunk_measures,
    classify_chunks,
    decide_chunk,
)

CLAUSULA = (
    "12.3 - A CONCESSIONÁRIA deverá manter os bens reversíveis em perfeito estado de "
    "conservação durante todo o prazo deste CONTRATO, sob pena de aplicação das sanções "
    "previstas na Cláusula 30. O PODER CONCEDENTE poderá exigir a substituição dos bens "
    "danificados, cabendo à CONCESSIONÁRIA arcar com os custos correspondentes."
)

ESTUDO = (
    "Para o cálculo do valor presente líquido estimou-se o fluxo de caixa do projeto ao longo "
    "de vinte anos. Foram considerados os cenários de demanda levantados no estudo de mercado, "
    "e as premissas de custo seguiram a metodologia descrita no capítulo anterior. Conclui-se "
    "que a modelagem indica viabilidade econômico-financeira, com VPL positivo e TIR superior "
    "à taxa de desconto adotada para a análise."
)


def test_a_contract_clause_is_instrument_text():
    assert decide_chunk(chunk_measures(CLAUSULA)) == INSTRUMENT


def test_a_study_passage_is_other_text():
    assert decide_chunk(chunk_measures(ESTUDO)) == OTHER


def test_a_short_silent_chunk_is_undecided():
    assert decide_chunk(chunk_measures("Página 3 de 10")) == UNDECIDED


def test_an_administrative_act_is_other_text():
    despacho = (
        "DESPACHO. Encaminho o presente processo para análise e manifestação. "
        "Solicito a gentileza de devolver os autos após a análise. Atenciosamente, "
        "São Paulo, 3 de março de 2024. Assessora técnica, matrícula 123."
    )
    assert decide_chunk(chunk_measures(despacho)) == OTHER


def test_the_dateline_of_any_city_counts_as_an_act_marker():
    """The prototype named the case's city; the rule is the dateline itself."""
    assert chunk_measures("Belo Horizonte, 12 de dezembro de 2023.")["act"] == 1
    assert chunk_measures("Porto Alegre, 1º de Janeiro de 2024.")["act"] == 1
    assert chunk_measures("conforme a Lei nº 14.133, de 1º de abril de 2021")["act"] == 0


def test_no_rule_names_the_case_city():
    for pattern in (C._ACT.pattern, C._ANALYSIS.pattern, C._PARTY):
        assert "Rio de Janeiro" not in pattern


def test_risk_allocated_to_a_party_counts_as_a_matrix_row():
    m = chunk_measures("Os riscos assumidos pela CONCESSIONÁRIA incluem a variação de demanda.")
    assert m["risk_allocated"] == 1
    assert m["matrix_row"] >= 1


def test_an_undecided_chunk_inherits_chunk_0_of_its_page():
    rows = [
        ("doc.pdf", 4, 0, CLAUSULA),
        ("doc.pdf", 4, 1, "Rubrica"),
    ]
    labels = classify_chunks(rows)
    assert labels[("doc.pdf", 4, 1)] == (INSTRUMENT, UNDECIDED)


def test_an_undecided_chunk_0_follows_the_majority_of_nearby_pages():
    rows = [
        ("doc.pdf", 1, 0, CLAUSULA),
        ("doc.pdf", 2, 0, "Tabela 3"),
        ("doc.pdf", 3, 0, CLAUSULA),
    ]
    assert classify_chunks(rows)[("doc.pdf", 2, 0)] == (INSTRUMENT, UNDECIDED)


def test_an_undecided_chunk_with_no_firm_neighbour_is_other():
    """In doubt, OUTRO: excluding a legitimate passage costs more than keeping
    one of instrument text."""
    assert classify_chunks([("doc.pdf", 9, 0, "Anexo")])[("doc.pdf", 9, 0)] == (OTHER, UNDECIDED)


def test_neighbouring_pages_of_another_file_do_not_vote():
    rows = [
        ("a.pdf", 1, 0, CLAUSULA),
        ("b.pdf", 2, 0, "Tabela 3"),
    ]
    assert classify_chunks(rows)[("b.pdf", 2, 0)][0] == OTHER
