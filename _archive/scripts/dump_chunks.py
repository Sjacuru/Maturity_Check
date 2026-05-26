"""
Dump chunk text for side-by-side comparison with the source document.

Usage:
    python scripts/dump_chunks.py                        # all chunks in order
    python scripts/dump_chunks.py --heading "Ação 1"     # exact segment match
    python scripts/dump_chunks.py --no-heading           # only null-heading chunks
    python scripts/dump_chunks.py --from 0 --to 10       # ordinal range
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lancedb-dir", default="data/lancedb/reference")
    parser.add_argument("--heading", default="", help="Exact segment to filter on")
    parser.add_argument("--no-heading", action="store_true", help="Show only null-heading chunks")
    parser.add_argument("--from", dest="from_ord", type=int, default=None)
    parser.add_argument("--to", dest="to_ord", type=int, default=None)
    args = parser.parse_args()

    try:
        import lancedb
        import pandas as pd
    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    db = lancedb.connect(str(Path(args.lancedb_dir)))
    df = db.open_table("reference_m5d_chunks").to_pandas().sort_values("ordinal")

    if args.no_heading:
        mask = df["heading_path"].isna() | (df["heading_path"].fillna("") == "")
    elif args.heading:
        term_pat = re.compile(r"^" + re.escape(args.heading) + r"(?:[:\s]|$)")
        mask = df["heading_path"].fillna("").apply(
            lambda hp: any(term_pat.match(s.strip()) for s in hp.split(" > "))
        )
    else:
        mask = pd.Series([True] * len(df), index=df.index)

    filtered = df[mask]
    if args.from_ord is not None:
        filtered = filtered[filtered["ordinal"] >= args.from_ord]
    if args.to_ord is not None:
        filtered = filtered[filtered["ordinal"] <= args.to_ord]

    print(f"\nShowing {len(filtered)} chunks\n{'='*60}")
    for _, row in filtered.iterrows():
        hp = row["heading_path"] if pd.notna(row["heading_path"]) else "(no heading)"
        print(f"\nordinal  : {row['ordinal']}")
        print(f"heading  : {hp}")
        print(f"text     :")
        print(row["text"])
        print("-" * 60)


if __name__ == "__main__":
    main()
