"""Narrative sections of instrument documents (ADR-0077)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from extraction import Chunk
from retrieval import configure, get_chunk_genres, get_narrative_sections, index
from retrieval._config import _reset
from retrieval.genre.classifier import INSTRUMENT, OTHER
from retrieval.genre.narrative import heading, is_narrative_title, narrative_sections
from retrieval.schema.ddl import init_db

CLAUSULA = (
    "A CONCESSIONÁRIA deverá manter os bens reversíveis em perfeito estado durante todo o "
    "prazo deste CONTRATO, sob pena das sanções da Cláusula 30. O PODER CONCEDENTE poderá "
    "exigir a substituição dos bens danificados. "
) * 2
NARRATIVA = (
    "O projeto busca requalificar os espaços públicos da cidade, oferecendo informação ao "
    "cidadão e ampliando a oferta de abrigos aos usuários do transporte coletivo. "
) * 3


# ---------------------------------------------------------------- titles --

def test_numbered_title_has_its_level():
    assert heading("1. INTRODUÇÃO", ".") == (1, "INTRODUCAO")
    assert heading("2.3 HISTÓRICO DO PROJETO", ".") == (2, "HISTORICO DO PROJETO")


def test_number_alone_on_the_previous_line_gives_the_level():
    assert heading("INTRODUÇÃO", "1.") == (1, "INTRODUCAO")


def test_unnumbered_title_must_stand_alone():
    assert heading("JUSTIFICATIVA", "fim da frase anterior.") == (0, "JUSTIFICATIVA")
    assert heading("JUSTIFICATIVA", "frase que continua") is None


def test_table_of_contents_line_is_not_a_title():
    assert heading("1. INTRODUÇÃO ........ 3", ".") is None
    assert heading("1. INTRODUÇÃO 3", ".") is None


def test_running_text_is_not_a_title():
    assert heading("1.1 O objeto desta licitação é a concessão do serviço.", ".") is None


@pytest.mark.parametrize("title", [
    "INTRODUÇÃO", "HISTÓRICO", "CONTEXTUALIZAÇÃO", "JUSTIFICATIVA", "BREVE ANÁLISE",
    "CONSIDERAÇÕES FINAIS", "CONCLUSÃO", "ANEXO II - JUSTIFICATIVA",
])
def test_narrative_titles(title):
    assert is_narrative_title(title)


@pytest.mark.parametrize("title", [
    "CRONOGRAMA", "ANEXO VIII - CRONOGRAMA DA LICITAÇÃO", "DAS OBRIGAÇÕES DA CONCESSIONÁRIA",
    "MATRIZ DE RISCOS", "CONSIDERANDO",
])
def test_titles_that_are_not_narrative(title):
    # CRONOGRAMA was measured and left out (ADR-0077): a schedule says what
    # will happen, not that it happened.
    assert not is_narrative_title(title)


# -------------------------------------------------------------- sections --

def test_section_ends_at_the_next_title_of_the_same_level():
    chunks = [
        (1, 0, "1. INTRODUÇÃO\n" + NARRATIVA),
        (1, 1, "1.2 CONTEXTO E HISTÓRICO\n" + NARRATIVA),
        (2, 0, "2. DAS OBRIGAÇÕES\n" + CLAUSULA),
    ]
    assert narrative_sections(chunks, "TERMO DE REFERÊNCIA") == {
        (1, 0): "INTRODUCAO", (1, 1): "INTRODUCAO",
    }


def test_chunk_mostly_outside_the_section_is_not_released():
    chunks = [(1, 0, "texto normativo.\n" + CLAUSULA + "\n1. INTRODUÇÃO\nO projeto.")]
    assert narrative_sections(chunks, None) == {}


def test_document_titled_as_narrative_is_released_whole():
    chunks = [(5, 0, CLAUSULA), (6, 0, CLAUSULA)]
    assert set(narrative_sections(chunks, "ANEXO II - JUSTIFICATIVA")) == {(5, 0), (6, 0)}


def test_schedule_annex_is_not_released():
    chunks = [(9, 0, "ANEXO VIII - CRONOGRAMA DA LICITAÇÃO\nPublicação do edital\n" + CLAUSULA)]
    assert narrative_sections(chunks, None) == {}


def test_considerandos_are_not_a_section():
    chunks = [(1, 0, "CONSIDERANDO que a LICITAÇÃO foi homologada;\n" + CLAUSULA)]
    assert narrative_sections(chunks, "MINUTA DE CONTRATO") == {}


# ----------------------------------------------------------------- index --

def _chunk(page: int, text: str, chunk_index: int = 0, filename: str = "edital.pdf") -> Chunk:
    return Chunk(
        filename=filename, page_number=page, chunk_index=chunk_index, char_offset=0,
        text=text, text_length=len(text), page_total=9, ocr_used=False, source_type="text",
    )


@pytest.fixture()
def db(tmp_path: Path):
    path = tmp_path / "genre.db"
    init_db(path)
    configure(path)
    yield path
    _reset()


def _index_edital():
    index("P950", [
        _chunk(1, "EDITAL DE CONCORRÊNCIA\n1. INTRODUÇÃO\n" + NARRATIVA),
        _chunk(2, "2. DAS CONDIÇÕES DE PARTICIPAÇÃO\n" + CLAUSULA),
        _chunk(3, CLAUSULA),
    ])


def test_narrative_section_of_an_instrument_reads_as_other(db):
    _index_edital()
    genres = get_chunk_genres("P950")
    assert genres[("edital.pdf", 1, 0)] == OTHER
    assert genres[("edital.pdf", 2, 0)] == INSTRUMENT
    assert get_narrative_sections("P950") == {("edital.pdf", 1, 0): "INTRODUCAO"}


def test_release_can_be_switched_off(db):
    _index_edital()
    genres = get_chunk_genres("P950", release_narrative_sections=False)
    assert genres[("edital.pdf", 1, 0)] == INSTRUMENT


def test_older_chunk_genre_table_is_rebuilt(tmp_path: Path):
    path = tmp_path / "old.db"
    con = sqlite3.connect(str(path))
    con.execute(
        "CREATE TABLE chunk_genre (process_number TEXT NOT NULL, filename TEXT NOT NULL, "
        "page_number INTEGER NOT NULL, chunk_index INTEGER NOT NULL, segment_index INTEGER NOT NULL, "
        "chunk_label TEXT NOT NULL, genre TEXT NOT NULL, rules_version TEXT NOT NULL, "
        "PRIMARY KEY (process_number, filename, page_number, chunk_index))"
    )
    con.commit()
    con.close()
    init_db(path)
    configure(path)
    try:
        _index_edital()
        assert get_narrative_sections("P950") == {("edital.pdf", 1, 0): "INTRODUCAO"}
    finally:
        _reset()
