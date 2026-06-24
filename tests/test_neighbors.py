"""Tests for retrieval.query.neighbors.fetch_neighbor_chunks (ADR-0050)."""

import pytest

from extraction import Chunk
from retrieval import configure, index
from retrieval.query.neighbors import fetch_neighbor_chunks
from retrieval.schema.ddl import init_db


def make_chunk(**kwargs) -> Chunk:
    defaults = dict(
        filename="doc.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        text="texto padrão.",
        text_length=14,
        page_total=10,
        ocr_used=False,
        source_type="text",
    )
    return Chunk(**{**defaults, **kwargs})


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    configure(db_path)
    return db_path


def test_fetch_neighbors_within_same_page(db):
    chunks = [
        make_chunk(page_number=5, chunk_index=0, text="primeiro"),
        make_chunk(page_number=5, chunk_index=1, text="segundo"),
        make_chunk(page_number=5, chunk_index=2, text="terceiro"),
    ]
    index("P001", chunks)
    prev, nxt = fetch_neighbor_chunks("P001", "doc.pdf", 5, 1)
    assert prev.text == "primeiro"
    assert nxt.text == "terceiro"


def test_fetch_neighbors_crosses_page_boundary(db):
    chunks = [
        make_chunk(page_number=5, chunk_index=0, text="fim da pagina 5"),
        make_chunk(page_number=6, chunk_index=0, text="inicio da pagina 6"),
        make_chunk(page_number=6, chunk_index=1, text="meio da pagina 6"),
    ]
    index("P001", chunks)
    prev, nxt = fetch_neighbor_chunks("P001", "doc.pdf", 6, 0)
    assert prev.text == "fim da pagina 5"
    assert nxt.text == "meio da pagina 6"


def test_fetch_neighbors_first_chunk_has_no_previous(db):
    chunks = [
        make_chunk(page_number=1, chunk_index=0, text="primeiro do documento"),
        make_chunk(page_number=1, chunk_index=1, text="segundo"),
    ]
    index("P001", chunks)
    prev, nxt = fetch_neighbor_chunks("P001", "doc.pdf", 1, 0)
    assert prev is None
    assert nxt.text == "segundo"


def test_fetch_neighbors_last_chunk_has_no_next(db):
    chunks = [
        make_chunk(page_number=1, chunk_index=0, text="primeiro"),
        make_chunk(page_number=1, chunk_index=1, text="ultimo do documento"),
    ]
    index("P001", chunks)
    prev, nxt = fetch_neighbor_chunks("P001", "doc.pdf", 1, 1)
    assert prev.text == "primeiro"
    assert nxt is None


def test_fetch_neighbors_scoped_to_same_filename(db):
    chunks = [
        make_chunk(filename="a.pdf", page_number=1, chunk_index=0, text="doc a"),
        make_chunk(filename="b.pdf", page_number=1, chunk_index=0, text="doc b"),
    ]
    index("P001", chunks)
    prev, nxt = fetch_neighbor_chunks("P001", "a.pdf", 1, 0)
    assert prev is None
    assert nxt is None


def test_fetch_neighbors_scoped_to_same_process_number(db):
    index("P001", [make_chunk(page_number=1, chunk_index=0, text="p001 chunk")])
    index("P002", [make_chunk(page_number=1, chunk_index=1, text="p002 chunk")])
    prev, nxt = fetch_neighbor_chunks("P001", "doc.pdf", 1, 0)
    assert prev is None
    assert nxt is None
