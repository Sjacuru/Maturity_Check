"""
Spot-check M5D chunks stored in LanceDB.

Run from project root:
    python scripts/check_lancedb_chunks.py
    python scripts/check_lancedb_chunks.py --heading "Ação 3"
    python scripts/check_lancedb_chunks.py --show-text
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect reference_m5d_chunks in LanceDB.")
    parser.add_argument("--lancedb-dir", default="data/lancedb/reference", help="LanceDB directory")
    parser.add_argument("--heading", default="Ação 1", help="Substring to filter heading_path (default: 'Ação 1')")
    parser.add_argument("--show-text", action="store_true", help="Print full chunk text (default: first 120 chars)")
    parser.add_argument("--limit", type=int, default=10, help="Max rows to display in heading filter (default: 10)")
    args = parser.parse_args()

    lancedb_dir = Path(args.lancedb_dir)
    if not lancedb_dir.exists():
        print(f"ERROR: LanceDB directory not found: {lancedb_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        import lancedb
        import pandas as pd
    except ImportError as e:
        print(f"ERROR: Missing dependency — {e}", file=sys.stderr)
        sys.exit(1)

    db = lancedb.connect(str(lancedb_dir))

    try:
        tbl = db.open_table("reference_m5d_chunks")
    except Exception as e:
        print(f"ERROR: Could not open table 'reference_m5d_chunks' — {e}", file=sys.stderr)
        sys.exit(1)

    total = tbl.count_rows()
    print(f"\n{'='*60}")
    print(f"Table : reference_m5d_chunks")
    print(f"Total : {total} chunks")
    print(f"{'='*60}")

    df: pd.DataFrame = tbl.to_pandas()

    # Summary: chunks per heading (top level only)
    if "heading_path" in df.columns:
        top_headings = (
            df["heading_path"]
            .fillna("(no heading)")
            .str.split(" > ")
            .str[0]
            .value_counts()
            .head(20)
        )
        print("\nChunks by top-level heading (top 20):")
        for heading, count in top_headings.items():
            print(f"  {count:4d}  {heading}")

    # Heading filter spot-check
    mask = df["heading_path"].fillna("").str.contains(args.heading, regex=False)
    filtered = df[mask].head(args.limit)

    print(f"\n{'='*60}")
    print(f"Filter: heading_path contains '{args.heading}'  ({mask.sum()} matches, showing {len(filtered)})")
    print(f"{'='*60}")

    if filtered.empty:
        print("  (no chunks matched)")
    else:
        for _, row in filtered.iterrows():
            print(f"\n  ordinal    : {row['ordinal']}")
            print(f"  chunk_id   : {row['chunk_id']}")
            print(f"  heading    : {row['heading_path']}")
            text = row["text"] if args.show_text else row["text"][:120] + ("..." if len(row["text"]) > 120 else "")
            print(f"  text       : {text!r}")
            has_vector = "vector" in row and row["vector"] is not None
            if has_vector:
                import numpy as np
                vec = np.asarray(row["vector"])
                print(f"  vector dim : {vec.shape[0]}  norm={float(np.linalg.norm(vec)):.4f}")


if __name__ == "__main__":
    main()
