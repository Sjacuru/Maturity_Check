import sqlite3
import tempfile
from pathlib import Path

from retrieval.schema.ddl import init_db


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(path))


def test_init_db_creates_chunks_table(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    con = _connect(db)
    rows = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'"
    ).fetchall()
    con.close()
    assert rows, "chunks table not found"


def test_init_db_creates_chunks_fts_table(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    con = _connect(db)
    rows = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks_fts'"
    ).fetchall()
    con.close()
    assert rows, "chunks_fts table not found"


def test_init_db_idempotent(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    init_db(db)  # must not raise


def test_init_db_wal_mode(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    con = _connect(db)
    mode = con.execute("PRAGMA journal_mode;").fetchone()[0]
    con.close()
    assert mode == "wal"


def test_chunks_table_has_unique_constraint(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    con = _connect(db)
    row = dict(
        process_number="P001", filename="doc.pdf",
        page_number=1, chunk_index=0, char_offset=0,
        text="hello", text_length=5, page_total=10,
        ocr_used=0, source_type="text",
    )
    sql = """
        INSERT INTO chunks
        (process_number, filename, page_number, chunk_index, char_offset,
         text, text_length, page_total, ocr_used, source_type)
        VALUES (:process_number, :filename, :page_number, :chunk_index,
                :char_offset, :text, :text_length, :page_total,
                :ocr_used, :source_type)
    """
    con.execute(sql, row)
    con.commit()
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(sql, row)
        con.commit()
    con.close()
