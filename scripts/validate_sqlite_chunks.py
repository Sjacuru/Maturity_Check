"""
Validate M5D chunks in SQLite by reconstructing text from source offsets.

Each chunk's stored text is compared against md[start_char:end_char] from
the normalized source (normalize_pdf_headings must be applied first, since
offsets are relative to that normalized form — not the raw file).

Run from project root:
    python scripts/validate_sqlite_chunks.py
    python scripts/validate_sqlite_chunks.py --heading "Ação 1"
    python scripts/validate_sqlite_chunks.py --show-matches
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate SQLite reference_chunks against M5D source.")
    parser.add_argument("--m5d-path", default="Plan/06_Models/output.md", help="Path to M5D markdown file")
    parser.add_argument("--sqlite-path", default="data/framework.sqlite", help="Path to SQLite database")
    parser.add_argument("--doc-id", default="m5d_md_v1", help="doc_id to validate (default: m5d_md_v1)")
    parser.add_argument("--heading", default=None, help="Filter by heading_path substring (optional)")
    parser.add_argument("--show-matches", action="store_true", help="Also print OK chunks (default: mismatches only)")
    args = parser.parse_args()

    m5d_path = Path(args.m5d_path)
    sqlite_path = Path(args.sqlite_path)

    if not m5d_path.exists():
        print(f"ERROR: M5D file not found: {m5d_path}", file=sys.stderr)
        sys.exit(1)
    if not sqlite_path.exists():
        print(f"ERROR: SQLite database not found: {sqlite_path}", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from maturity_check.db import connect_sqlite
    from maturity_check.ingest.chunking import normalize_pdf_headings

    print(f"\nNormalizing {m5d_path} ...")
    md = normalize_pdf_headings(m5d_path.read_text(encoding="utf-8"))
    print(f"Normalized length: {len(md):,} chars")

    conn = connect_sqlite(sqlite_path)

    query = (
        "SELECT chunk_id, ordinal, heading_path, start_char, end_char, text "
        "FROM reference_chunks WHERE doc_id = ? "
    )
    params: list = [args.doc_id]
    if args.heading:
        query += "AND heading_path LIKE ? "
        params.append(f"%{args.heading}%")
    query += "ORDER BY ordinal"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    print(f"Chunks to validate: {len(rows)}")
    if args.heading:
        print(f"Filter: heading_path LIKE '%{args.heading}%'")
    print(f"{'='*60}")

    mismatches = 0
    for chunk_id, ordinal, heading_path, start, end, stored_text in rows:
        reconstructed = md[start:end].strip()
        ok = reconstructed == stored_text

        if ok:
            if args.show_matches:
                print(f"OK  ordinal={ordinal:4d}  {chunk_id}  [{start}:{end}]  heading={heading_path!r}")
        else:
            mismatches += 1
            print(f"\nMISMATCH  ordinal={ordinal}  chunk_id={chunk_id}")
            print(f"  heading    : {heading_path!r}")
            print(f"  offsets    : [{start}:{end}]  (len stored={len(stored_text)} recon={len(reconstructed)})")
            print(f"  stored[:80]: {stored_text[:80]!r}")
            print(f"  recon[:80] : {reconstructed[:80]!r}")

    print(f"\n{'='*60}")
    if mismatches == 0:
        print(f"PASSED  {len(rows)} chunks validated — all offsets round-trip correctly.")
    else:
        print(f"FAILED  {mismatches} mismatch(es) out of {len(rows)} chunks.")
        sys.exit(1)


if __name__ == "__main__":
    main()
