import argparse
from pathlib import Path

from maturity_check.crosswalk_extract import extract_templates_to_dir
from maturity_check.ingest.m5d_ingest import ingest_m5d
from maturity_check.reference_search import search_reference_lancedb, search_reference_sqlite


def main() -> None:
    # Ensure UTF-8 output on Windows terminals (avoids cp1252 failures for PDF-origin glyphs).
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(prog="maturity-check")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingest-m5d", help="Ingest Plan/06_Models/M5D.md into SQLite + optional LanceDB.")
    ing.add_argument(
        "--m5d-path",
        type=Path,
        default=Path("Plan/06_Models/M5D.md"),
        help="Path to M5D.md",
    )
    ing.add_argument(
        "--sqlite-path",
        type=Path,
        default=Path("data/framework.sqlite"),
        help="SQLite file to create/update",
    )
    ing.add_argument(
        "--lancedb-dir",
        type=Path,
        default=Path("data/lancedb/reference"),
        help="LanceDB directory for reference index",
    )
    embed_group = ing.add_mutually_exclusive_group()
    embed_group.add_argument(
        "--embed",
        dest="embed",
        action="store_true",
        default=True,
        help="Write embeddings to LanceDB using sentence-transformers (default).",
    )
    embed_group.add_argument(
        "--no-embed",
        dest="embed",
        action="store_false",
        help="Skip embeddings and write SQLite only.",
    )
    ing.add_argument(
        "--model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Sentence-transformers model id (if --embed).",
    )
    ing.add_argument(
        "--max-chars",
        type=int,
        default=3500,
        help="Max characters per chunk (soft cap).",
    )
    ing.add_argument(
        "--overlap-chars",
        type=int,
        default=350,
        help="Character overlap between consecutive chunks.",
    )

    sref = sub.add_parser("search-ref-sqlite", help="Search reference chunks in SQLite by keyword.")
    sref.add_argument(
        "--sqlite-path",
        type=Path,
        default=Path("data/framework.sqlite"),
        help="SQLite database (reference_chunks).",
    )
    sref.add_argument("query", help="Substring search query (SQL LIKE).")
    sref.add_argument(
        "--heading-contains",
        default=None,
        help="Optional heading_path filter (SQL LIKE).",
    )
    sref.add_argument("--limit", type=int, default=10, help="Max hits.")
    sref.add_argument(
        "--snippet-chars",
        type=int,
        default=240,
        help="Snippet length in characters.",
    )

    vref = sub.add_parser("search-ref-vector", help="Vector search reference chunks in LanceDB.")
    vref.add_argument(
        "--lancedb-dir",
        type=Path,
        default=Path("data/lancedb/reference"),
        help="LanceDB directory containing reference table.",
    )
    vref.add_argument(
        "--model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Sentence-transformers model id.",
    )
    vref.add_argument(
        "--table",
        default="reference_m5d_chunks",
        help="LanceDB table name.",
    )
    vref.add_argument("query", help="Semantic search query.")
    vref.add_argument("--limit", type=int, default=5, help="Top-K hits.")
    vref.add_argument(
        "--snippet-chars",
        type=int,
        default=240,
        help="Snippet length in characters.",
    )

    xw = sub.add_parser(
        "extract-crosswalk-md",
        help=(
            "Extract the first ```json fence from crosswalk template .md files into .json "
            "(for tooling; templates remain source of truth)."
        ),
    )
    xw.add_argument(
        "templates",
        nargs="+",
        type=Path,
        help="Paths to *.template.md (or any .md with one JSON fence).",
    )
    xw.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/crosswalk"),
        help="Directory for extracted JSON (default: data/crosswalk).",
    )

    args = parser.parse_args()

    if args.cmd == "ingest-m5d":
        ingest_m5d(
            m5d_path=args.m5d_path,
            sqlite_path=args.sqlite_path,
            lancedb_dir=args.lancedb_dir,
            embed=args.embed,
            model_id=args.model,
            max_chars=args.max_chars,
            overlap_chars=args.overlap_chars,
        )
    elif args.cmd == "search-ref-sqlite":
        hits = search_reference_sqlite(
            sqlite_path=args.sqlite_path,
            query=args.query,
            heading_contains=args.heading_contains,
            limit=args.limit,
        )
        for h in hits:
            snippet = h.text[: args.snippet_chars].replace("\n", " ").strip()
            heading = h.heading_path or "(no heading)"
            print(f"{h.chunk_id} | {heading} | {snippet}")
    elif args.cmd == "search-ref-vector":
        hits = search_reference_lancedb(
            lancedb_dir=args.lancedb_dir,
            query=args.query,
            limit=args.limit,
            model_id=args.model,
            table=args.table,
        )
        for h in hits:
            snippet = h.text[: args.snippet_chars].replace("\n", " ").strip()
            heading = h.heading_path or "(no heading)"
            print(f"{h.chunk_id} | {heading} | {snippet}")
    elif args.cmd == "extract-crosswalk-md":
        written = extract_templates_to_dir(template_paths=list(args.templates), out_dir=args.out_dir)
        for p in written:
            print(p)


if __name__ == "__main__":
    main()
