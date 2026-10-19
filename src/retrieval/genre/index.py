"""The canonical document index of a process (ADR-0074).

For every file of a process: the documents it bundles (segmentation.py), the
genre of each document, and the genre every chunk inherits from its document.
A document's genre is its title's type when the title names a known type,
otherwise the majority of its chunk labels (classifier.py), a tie being OUTRO.
Inside an instrument document, a chunk that lies in a narrative section
(introduction, history, justification...; narrative.py, ADR-0077) is marked
with that section's title; get_chunk_genres treats it as OUTRO.

The index is derived data, persisted next to the chunks it describes. It is
rebuilt whenever the chunks of the process change (a checksum of their keys
and lengths) or the rules change (GENRE_RULES_VERSION), so reading it never
returns an index built from other chunks or other rules. The same chunks and
the same rules always give the same index.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from retrieval._config import get_db_path
from retrieval.genre.classifier import INSTRUMENT, OTHER, classify_chunks
from retrieval.genre.narrative import narrative_sections
from retrieval.genre.segmentation import pages_by_file, segment_file
from retrieval.schema.ddl import create_genre_tables

# Bump on any change to the classifier markers, the type lexicon, the
# segmentation rules or the noise stripper both of them read
# (extraction.noise): an index built under another version is rebuilt on its
# next read. 2026-10-16.1: the stripper also removes the signature stamps it
# used to let through. 2026-10-19.1: narrative sections of instrument
# documents (ADR-0077).
GENRE_RULES_VERSION = "2026-10-19.1"


@dataclass(frozen=True)
class DocumentSegment:
    process_number: str
    filename: str
    segment_index: int
    page_start: int
    page_end: int
    start_reason: str           # file_start | cover | title | restart
    doc_type: str | None        # from the type lexicon; None = untyped title or none
    title: str | None
    genre: str                  # INSTRUMENTO | OUTRO
    genre_basis: str            # "type" (the title's type) | "majority" (chunk labels)
    n_chunks: int
    n_chunks_instrument: int    # chunks whose own label is INSTRUMENTO
    rules_version: str


def get_chunk_genres(
    process_number: str, release_narrative_sections: bool = True,
) -> dict[tuple[str, int, int], str]:
    """{(filename, page_number, chunk_index): the genre the filter reads}.

    The genre of the chunk's document, except that a chunk in a narrative
    section of an instrument document reads OUTRO (ADR-0077), unless
    release_narrative_sections is False.
    """
    con = _connect()
    try:
        _ensure(con, process_number)
        rows = con.execute(
            "SELECT filename, page_number, chunk_index, genre, narrative_section FROM chunk_genre "
            "WHERE process_number = ?",
            (process_number,),
        ).fetchall()
    finally:
        con.close()
    return {(f, p, c): OTHER if (release_narrative_sections and section) else genre
            for f, p, c, genre, section in rows}


def get_narrative_sections(process_number: str) -> dict[tuple[str, int, int], str]:
    """{(filename, page_number, chunk_index): narrative section title} of the
    chunks of instrument documents that lie in one (ADR-0077)."""
    con = _connect()
    try:
        _ensure(con, process_number)
        rows = con.execute(
            "SELECT filename, page_number, chunk_index, narrative_section FROM chunk_genre "
            "WHERE process_number = ? AND narrative_section IS NOT NULL",
            (process_number,),
        ).fetchall()
    finally:
        con.close()
    return {(f, p, c): section for f, p, c, section in rows}


def get_document_index(process_number: str) -> list[DocumentSegment]:
    con = _connect()
    try:
        _ensure(con, process_number)
        rows = con.execute(
            "SELECT process_number, filename, segment_index, page_start, page_end, start_reason, "
            "doc_type, title, genre, genre_basis, n_chunks, n_chunks_instrument, rules_version "
            "FROM document_index WHERE process_number = ? ORDER BY filename, segment_index",
            (process_number,),
        ).fetchall()
    finally:
        con.close()
    return [DocumentSegment(*row) for row in rows]


def ensure_document_index(process_number: str) -> None:
    """Build the index if it is missing or stale; otherwise do nothing."""
    con = _connect()
    try:
        _ensure(con, process_number)
    finally:
        con.close()


def build_document_index(process_number: str) -> list[DocumentSegment]:
    """Rebuild the index of one process from its chunks, unconditionally."""
    con = _connect()
    try:
        return _rebuild(con, process_number)
    finally:
        con.close()


def invalidate_document_index(process_number: str) -> None:
    """Drop the index of one process; the next read rebuilds it. Called when a
    file of the process is replaced (the checksum would also catch it, this
    makes the replacement explicit)."""
    con = _connect()
    try:
        with con:
            for table in ("document_index_state", "document_index", "chunk_genre"):
                con.execute(f"DELETE FROM {table} WHERE process_number = ?", (process_number,))
    finally:
        con.close()


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(get_db_path()))
    create_genre_tables(con)
    return con


def _fingerprint(con: sqlite3.Connection, process_number: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for filename, page, chunk_index, length in con.execute(
        "SELECT filename, page_number, chunk_index, text_length FROM chunks "
        "WHERE process_number = ? ORDER BY filename, page_number, chunk_index",
        (process_number,),
    ):
        digest.update(f"{filename}\x1f{page}\x1f{chunk_index}\x1f{length}\n".encode("utf-8"))
        count += 1
    return count, digest.hexdigest()


def _ensure(con: sqlite3.Connection, process_number: str) -> None:
    count, checksum = _fingerprint(con, process_number)
    state = con.execute(
        "SELECT rules_version, chunk_count, chunk_checksum FROM document_index_state "
        "WHERE process_number = ?",
        (process_number,),
    ).fetchone()
    if state is not None and tuple(state) == (GENRE_RULES_VERSION, count, checksum):
        return
    _rebuild(con, process_number, count, checksum)


def _rebuild(
    con: sqlite3.Connection,
    process_number: str,
    count: int | None = None,
    checksum: str | None = None,
) -> list[DocumentSegment]:
    if count is None or checksum is None:
        count, checksum = _fingerprint(con, process_number)
    rows = con.execute(
        "SELECT filename, page_number, chunk_index, text FROM chunks WHERE process_number = ?",
        (process_number,),
    ).fetchall()
    labels = classify_chunks(rows)
    text_of = {(f, p, c): t for f, p, c, t in rows}

    segments: list[DocumentSegment] = []
    chunk_rows: list[tuple] = []
    for filename, pages in sorted(pages_by_file(rows).items()):
        chunks_of_page = {page.page_number: page.chunk_indexes for page in pages}
        for segment_index, segment in enumerate(segment_file(pages)):
            keys = [(filename, p, c) for p in segment.pages for c in chunks_of_page[p]]
            n_instrument = sum(1 for key in keys if labels[key][0] == INSTRUMENT)
            if segment.genre is not None:
                genre, basis = segment.genre, "type"
            else:
                # Untyped title (or none): the document's own passages decide;
                # a tie is OUTRO, the classifier's doubt rule.
                genre = INSTRUMENT if n_instrument > len(keys) - n_instrument else OTHER
                basis = "majority"
            sections = (
                narrative_sections([(p, c, text_of[(filename, p, c)]) for _f, p, c in keys],
                                   segment.title)
                if genre == INSTRUMENT else {}
            )
            segments.append(DocumentSegment(
                process_number=process_number,
                filename=filename,
                segment_index=segment_index,
                page_start=segment.page_start,
                page_end=segment.page_end,
                start_reason=segment.start_reason,
                doc_type=segment.doc_type,
                title=segment.title,
                genre=genre,
                genre_basis=basis,
                n_chunks=len(keys),
                n_chunks_instrument=n_instrument,
                rules_version=GENRE_RULES_VERSION,
            ))
            chunk_rows.extend(
                (process_number, f, p, c, segment_index, labels[(f, p, c)][0], genre,
                 sections.get((p, c)), GENRE_RULES_VERSION)
                for f, p, c in keys
            )

    with con:
        for table in ("document_index_state", "document_index", "chunk_genre"):
            con.execute(f"DELETE FROM {table} WHERE process_number = ?", (process_number,))
        con.executemany(
            "INSERT INTO document_index (process_number, filename, segment_index, page_start, "
            "page_end, start_reason, doc_type, title, genre, genre_basis, n_chunks, "
            "n_chunks_instrument, rules_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (s.process_number, s.filename, s.segment_index, s.page_start, s.page_end,
                 s.start_reason, s.doc_type, s.title, s.genre, s.genre_basis, s.n_chunks,
                 s.n_chunks_instrument, s.rules_version)
                for s in segments
            ],
        )
        con.executemany(
            "INSERT INTO chunk_genre (process_number, filename, page_number, chunk_index, "
            "segment_index, chunk_label, genre, narrative_section, rules_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            chunk_rows,
        )
        con.execute(
            "INSERT INTO document_index_state (process_number, rules_version, chunk_count, "
            "chunk_checksum, built_at) VALUES (?, ?, ?, ?, ?)",
            (process_number, GENRE_RULES_VERSION, count, checksum,
             datetime.now(timezone.utc).isoformat()),
        )
    return segments
