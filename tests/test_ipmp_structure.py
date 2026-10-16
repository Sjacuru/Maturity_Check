"""The IPMP data files load whole and carry the Guide's structure (ADR-0057).

A file that fails validation is logged and skipped (ADR-0010), so one bad field
silently drops an Ação from every assessment: Ações 21-46 were invisible that way
until 2026-09-07. These tests pin what must load and the structural fields.
"""
from collections import Counter

import pytest

import ingestion.ipmp as _ipmp
from ingestion import get_ipmp_store

# The five boxes in the "PONTOS DE TRANSIÇÃO" lane of the Guide's M5D flowcharts
# (Figuras 3-5): 16 closes the initial phase, 37 and 38 the intermediate one,
# 45 and 46 the final one.
TRANSITION_POINTS = {16, 37, 38, 45, 46}


@pytest.fixture
def store(monkeypatch):
    monkeypatch.setattr(_ipmp, "_store", None)  # fresh load from data/ipmp
    return get_ipmp_store()


def test_all_46_acoes_load(store):
    assert set(store.acoes) == set(range(1, 47))


def test_transition_points_are_the_guides_five(store):
    marked = {n for n, a in store.acoes.items() if a.ponto_transicao}
    assert marked == TRANSITION_POINTS


def test_phases_are_the_guides_three_blocks(store):
    """Chapter 4 of the Guide: Ações 1-20, 21-37 and 38-46."""
    by_phase: dict[str, set[int]] = {}
    for n, a in store.acoes.items():
        by_phase.setdefault(a.fase, set()).add(n)
    assert sorted(by_phase.values(), key=min) == [
        set(range(1, 21)),
        set(range(21, 38)),
        set(range(38, 47)),
    ]
    assert by_phase["Estudo das alternativas"] == set(range(1, 21))
    assert by_phase["Aprimoramento da alternativa escolhida"] == set(range(21, 38))
    assert by_phase["Consulta pública, Revisões e atualizações"] == set(range(38, 47))


def test_dimension_counts(store):
    assert Counter(a.dimensao for a in store.acoes.values()) == {
        "Estratégica": 6,
        "Econômica": 9,
        "Comercial": 11,
        "Financeira": 5,
        "Gerencial": 15,
    }


def test_every_acao_has_scored_products(store):
    scored = {n: [p for p in a.produtos_esperados if p.scored] for n, a in store.acoes.items()}
    assert all(scored.values())
    assert sum(len(v) for v in scored.values()) == 164
