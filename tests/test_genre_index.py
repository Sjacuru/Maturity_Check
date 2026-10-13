"""The canonical document index in the retrieval DB (ADR-0074)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from extraction import Chunk
from retrieval import configure, get_chunk_genres, get_document_index, index, invalidate_document_index
from retrieval._config import _reset
from retrieval.genre import index as genre_index
from retrieval.genre.classifier import INSTRUMENT, OTHER
from retrieval.schema.ddl import init_db

PROCESS = "P900"
PROSA = " ".join(["texto corrido do documento com frases comuns e sem marcas de titulo"] * 20)
ESTUDO = (
    "Para o cálculo do valor presente líquido estimou-se o fluxo de caixa do projeto. "
    "Foram considerados os cenários de demanda e as premissas de custo da modelagem. "
) * 3
CLAUSULA = (
    "A CONCESSIONÁRIA deverá manter os bens reversíveis em perfeito estado durante todo o "
    "prazo deste CONTRATO, sob pena das sanções da Cláusula 30. O PODER CONCEDENTE poderá "
    "exigir a substituição dos bens danificados. "
) * 2


def _chunk(page: int, text: str, chunk_index: int = 0, filename: str = "processo.pdf") -> Chunk:
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


def _index_case():
    index(PROCESS, [
        _chunk(1, "ESTUDO DE VIABILIDADE\n" + ESTUDO),
        _chunk(2, "MINUTA DE CONTRATO DE CONCESSÃO\n" + CLAUSULA),
        # A page of the minuta that says nothing an instrument says: the chunk
        # vote is OUTRO, but the document it belongs to is a minuta.
        _chunk(3, PROSA),
        # A generic heading opens no document by itself; at the start of a file
        # the document is untyped and its own passages decide its genre.
        _chunk(1, "DECLARAÇÃO\n" + CLAUSULA, filename="anexos.pdf"),
    ])


def test_init_db_creates_the_index_tables(db):
    con = sqlite3.connect(str(db))
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    assert {"document_index", "chunk_genre", "document_index_state"} <= tables


def test_every_chunk_takes_the_genre_of_its_document(db):
    _index_case()
    genres = get_chunk_genres(PROCESS)
    assert genres == {
        ("processo.pdf", 1, 0): OTHER,
        ("processo.pdf", 2, 0): INSTRUMENT,
        ("processo.pdf", 3, 0): INSTRUMENT,
        ("anexos.pdf", 1, 0): INSTRUMENT,
    }
    con = sqlite3.connect(str(db))
    label = con.execute(
        "SELECT chunk_label FROM chunk_genre WHERE filename = 'processo.pdf' AND page_number = 3"
    ).fetchone()[0]
    con.close()
    assert label == OTHER            # its own vote; the document decides the genre


def test_the_index_records_where_each_document_starts_and_ends(db):
    _index_case()
    docs = [(d.filename, d.page_start, d.page_end, d.start_reason, d.doc_type, d.genre,
             d.genre_basis) for d in get_document_index(PROCESS)]
    assert docs == [
        # DECLARAÇÃO is untyped on purpose: the majority of its chunks decides
        ("anexos.pdf", 1, 1, "file_start", None, INSTRUMENT, "majority"),
        ("processo.pdf", 1, 1, "title", "estudo", OTHER, "type"),
        ("processo.pdf", 2, 3, "title", "minuta", INSTRUMENT, "type"),
    ]


def test_a_generic_heading_inside_a_document_does_not_open_another(db):
    """DECLARAÇÃO halfway through the minuta is a page of the minuta."""
    _index_case()
    index(PROCESS, [_chunk(4, "DECLARAÇÃO\n" + PROSA)])
    assert get_chunk_genres(PROCESS)[("processo.pdf", 4, 0)] == INSTRUMENT
    minuta = [d for d in get_document_index(PROCESS) if d.doc_type == "minuta"]
    assert [(d.page_start, d.page_end) for d in minuta] == [(2, 4)]


def test_a_second_read_does_not_rebuild(db, monkeypatch):
    _index_case()
    first = get_chunk_genres(PROCESS)

    def _no_rebuild(*args, **kwargs):
        raise AssertionError("the index was current and should not be rebuilt")

    monkeypatch.setattr(genre_index, "_rebuild", _no_rebuild)
    assert get_chunk_genres(PROCESS) == first


def test_new_chunks_rebuild_the_index(db):
    _index_case()
    get_chunk_genres(PROCESS)
    index(PROCESS, [_chunk(5, "PARECER JURÍDICO\n" + ESTUDO)])
    assert get_chunk_genres(PROCESS)[("processo.pdf", 5, 0)] == OTHER


def test_a_rules_change_rebuilds_the_index(db, monkeypatch):
    _index_case()
    get_chunk_genres(PROCESS)
    monkeypatch.setattr(genre_index, "GENRE_RULES_VERSION", "teste-2")
    get_chunk_genres(PROCESS)
    con = sqlite3.connect(str(db))
    versions = {r[0] for r in con.execute("SELECT DISTINCT rules_version FROM chunk_genre")}
    state = con.execute("SELECT rules_version FROM document_index_state").fetchone()[0]
    con.close()
    assert versions == {"teste-2"} and state == "teste-2"


def test_invalidate_drops_the_index_and_the_next_read_rebuilds_it(db):
    _index_case()
    first = get_chunk_genres(PROCESS)
    invalidate_document_index(PROCESS)
    con = sqlite3.connect(str(db))
    left = con.execute("SELECT COUNT(*) FROM chunk_genre").fetchone()[0]
    con.close()
    assert left == 0
    assert get_chunk_genres(PROCESS) == first


def test_processes_do_not_share_an_index(db):
    _index_case()
    index("P901", [_chunk(1, "EDITAL DE LICITAÇÃO\n" + CLAUSULA, filename="outro.pdf")])
    assert set(get_chunk_genres("P901")) == {("outro.pdf", 1, 0)}
    assert len(get_chunk_genres(PROCESS)) == 4


def test_a_process_with_no_chunks_has_an_empty_index(db):
    assert get_chunk_genres("P999") == {}
