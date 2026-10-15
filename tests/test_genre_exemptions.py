"""Products exempt from the genre filter (data/ipmp/isencoes_genero.json, ADR-0074)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ingestion import get_genre_exemption_store
from ingestion.genre_exemptions import load_genre_exemptions

APPROVED = {
    "22.1", "22.2", "22.2a", "22.2b", "23.1", "23.2", "23.3", "23.4",
    "25a", "25b", "25c", "25d", "25e", "37", "42d", "46.1",
}
SHIPPED = Path(__file__).parent.parent / "data" / "ipmp" / "isencoes_genero.json"


def _write(tmp_path: Path, isencoes: list[dict]) -> Path:
    path = tmp_path / "isencoes.json"
    path.write_text(json.dumps({"isencoes": isencoes}, ensure_ascii=False), encoding="utf-8")
    return path


def _shipped_entry(produto: str) -> dict:
    data = json.loads(SHIPPED.read_text(encoding="utf-8"))
    return next(dict(i) for i in data["isencoes"] if i["produto"] == produto)


def test_the_shipped_file_lists_exactly_the_approved_products():
    """The list the user approved on 2026-10-12 (message L), minus 45, removed on
    2026-10-15 after test cycle 6 (ADR-0074)."""
    assert get_genre_exemption_store().produtos() == APPROVED


def test_exemptions_can_be_read_per_acao():
    store = get_genre_exemption_store()
    assert store.produtos(25) == {"25a", "25b", "25c", "25d", "25e"}
    assert store.produtos(42) == {"42d"}
    assert store.produtos(1) == frozenset()


def test_a_phrase_that_no_longer_matches_the_ipmp_is_refused(tmp_path):
    entry = _shipped_entry("22.2")
    entry["frase"] = entry["frase"] + " (editado)"
    with pytest.raises(RuntimeError, match="não é mais a do IPMP"):
        load_genre_exemptions(_write(tmp_path, [entry]))


def test_a_non_scored_item_cannot_be_exempt(tmp_path):
    entry = {"acao": 25, "produto": "25", "frase": "x", "motivo": "cabeçalho"}
    with pytest.raises(RuntimeError, match="não é um Produto Esperado pontuado"):
        load_genre_exemptions(_write(tmp_path, [entry]))


def test_a_duplicate_is_refused(tmp_path):
    entry = _shipped_entry("37")
    with pytest.raises(RuntimeError, match="duas vezes"):
        load_genre_exemptions(_write(tmp_path, [entry, entry]))


def test_a_missing_file_is_refused(tmp_path):
    with pytest.raises(RuntimeError, match="not found"):
        load_genre_exemptions(tmp_path / "nao_existe.json")
