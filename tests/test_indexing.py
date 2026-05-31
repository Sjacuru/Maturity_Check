import sqlite3
from pathlib import Path

import pytest

from extraction import Chunk
from retrieval import configure, index
from retrieval.schema.ddl import init_db


def make_chunk(**kwargs) -> Chunk:
    defaults = dict(
        filename="Estudo_de_Viabilidade.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        text="Parceria Público-Privada para concessão de saneamento.",
        text_length=54,
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


def _count(db_path: Path, table: str = "chunks") -> int:
    con = sqlite3.connect(str(db_path))
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    return n


# --- Basic persistence ---

def test_index_persists_chunks(db):
    chunks = [make_chunk(), make_chunk(page_number=2)]
    index("P001", chunks)
    assert _count(db) == 2


def test_index_attaches_process_number(db):
    index("P001", [make_chunk()])
    con = sqlite3.connect(str(db))
    row = con.execute("SELECT process_number FROM chunks").fetchone()
    con.close()
    assert row[0] == "P001"


def test_index_persists_all_chunk_fields(db):
    chunk = make_chunk(
        filename="Contrato.pdf",
        page_number=5,
        chunk_index=2,
        char_offset=300,
        text="Texto do contrato.",
        text_length=18,
        page_total=20,
        ocr_used=True,
        source_type="image",
    )
    index("P001", [chunk])
    con = sqlite3.connect(str(db))
    row = con.execute(
        "SELECT filename, page_number, chunk_index, char_offset, text, "
        "text_length, page_total, ocr_used, source_type FROM chunks"
    ).fetchone()
    con.close()
    assert row == (
        "Contrato.pdf", 5, 2, 300, "Texto do contrato.",
        18, 20, 1, "image",
    )


# --- Idempotency ---

def test_index_idempotent_same_chunks(db):
    chunks = [make_chunk()]
    index("P001", chunks)
    index("P001", chunks)
    assert _count(db) == 1


def test_index_same_chunk_different_process_numbers(db):
    chunk = make_chunk()
    index("P001", [chunk])
    index("P002", [chunk])
    assert _count(db) == 2


# --- Empty list ---

def test_index_empty_list_noop(db):
    index("P001", [])
    assert _count(db) == 0


# --- Schema check ---

def test_index_without_init_db_raises(tmp_path):
    configure(tmp_path / "never_initialised.db")
    with pytest.raises(RuntimeError, match="not initialised"):
        index("P001", [make_chunk()])


def test_configure_not_called_raises(tmp_path):
    from retrieval import _config
    original = _config._db_path
    _config._db_path = None
    try:
        with pytest.raises(RuntimeError, match="not configured"):
            index("P001", [make_chunk()])
    finally:
        _config._db_path = original


# --- FTS5 population ---

def test_index_populates_fts(db):
    index("P001", [make_chunk(text="viabilidade econômica do projeto")])
    con = sqlite3.connect(str(db))
    rows = con.execute(
        "SELECT rowid FROM chunks_fts WHERE text MATCH 'viabilidade'"
    ).fetchall()
    con.close()
    assert rows


def test_index_idempotent_no_duplicate_fts_entries(db):
    chunks = [make_chunk(text="viabilidade econômica do projeto")]
    index("P001", chunks)
    index("P001", chunks)
    con = sqlite3.connect(str(db))
    rows = con.execute(
        "SELECT rowid FROM chunks_fts WHERE text MATCH 'viabilidade'"
    ).fetchall()
    con.close()
    assert len(rows) == 1
