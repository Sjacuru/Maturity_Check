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
    parser.add_argument("--limit", type=int, default=0, help="Max rows to display in heading filter (default: 0 = all)")
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

    # Summary: all heading_paths in document order, indented by depth
    if "heading_path" in df.columns:
        df_sorted = df.sort_values("ordinal")

        seen_order: list[str] = []
        seen_set: set[str] = set()
        for hp in df_sorted["heading_path"].fillna("(no heading)"):
            if hp not in seen_set:
                seen_order.append(hp)
                seen_set.add(hp)

        import re as _re_sort

        def _heading_sort_key(hp: str) -> tuple:
            if hp == "(no heading)":
                return (-1,)
            segments = hp.split(" > ")
            key = []
            for seg in segments:
                m = _re_sort.search(r"\d+", seg)
                key.append(int(m.group()) if m else 0)
            return tuple(key)

        counts = df["heading_path"].fillna("(no heading)").value_counts()

        # depth-0 Ação entries are TOC artifacts (no chapter prefix); separate them
        content_paths = [hp for hp in seen_order if hp == "(no heading)" or " > " in hp]
        toc_paths     = [hp for hp in seen_order if hp != "(no heading)" and " > " not in hp]

        content_paths.sort(key=_heading_sort_key)
        toc_paths.sort(key=_heading_sort_key)

        print("\nContent chunks (logical order):")
        for hp in content_paths:
            depth = 0 if hp == "(no heading)" else hp.count(" > ")
            indent = "  " * depth
            label = hp.split(" > ")[-1] if " > " in hp else hp
            print(f"  {counts.get(hp, 0):4d}  {indent}{label}")

        if toc_paths:
            print("\nTOC artifact chunks (no chapter context — likely table-of-contents lines):")
            for hp in toc_paths:
                print(f"  {counts.get(hp, 0):4d}  {hp}")

    # Heading filter — match any segment that starts with term followed by ":", space, or end-of-segment
    import re as _re
    _term_pat = _re.compile(r"^" + _re.escape(args.heading) + r"(?:[:\s]|$)")

    def _matches_segment(heading_path: str) -> bool:
        return any(_term_pat.match(seg) for seg in heading_path.split(" > "))

    mask = df["heading_path"].fillna("").apply(_matches_segment)
    filtered = df[mask].sort_values("ordinal")
    if args.limit > 0:
        filtered = filtered.head(args.limit)

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
