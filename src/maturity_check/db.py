import sqlite3
from pathlib import Path


def connect_sqlite(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_framework_schema(conn: sqlite3.Connection) -> None:
    # Minimal schema for static reference ingestion (M5D/Rio/TCDF reference text).
    # Case-document ingestion/indexing uses a separate schema later.
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS reference_documents (
          doc_id TEXT PRIMARY KEY,
          source TEXT NOT NULL,
          title TEXT NOT NULL,
          path TEXT NOT NULL,
          content_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS reference_chunks (
          chunk_id TEXT PRIMARY KEY,
          doc_id TEXT NOT NULL REFERENCES reference_documents(doc_id) ON DELETE CASCADE,
          ordinal INTEGER NOT NULL,
          heading_path TEXT,
          start_char INTEGER NOT NULL,
          end_char INTEGER NOT NULL,
          text TEXT NOT NULL,
          text_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_reference_chunks_doc_ordinal
          ON reference_chunks(doc_id, ordinal);
        """
    )
    conn.commit()

