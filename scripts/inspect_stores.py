"""Side-by-side inspection of SQLite and LanceDB for one or all Ações.

Usage:
    python scripts/inspect_stores.py            # Ação 1 (default)
    python scripts/inspect_stores.py --acao 3   # specific Ação
    python scripts/inspect_stores.py --all      # all 46 Ações
"""
import argparse
import re
import sqlite3
from pathlib import Path

import lancedb
import numpy as np

SQLITE_PATH = Path("data/framework.sqlite")
LANCEDB_DIR = Path("data/lancedb/reference")
TABLE       = "reference_m5d_chunks"
ALL_ACOES   = list(range(1, 47))

_ACAO_EXACT = re.compile(r"Ação (\d+):")


def _exact_match(heading_path, acao_num: int) -> bool:
    """True only if heading_path contains 'Ação N:' (not 'Ação N0:', etc.)."""
    if not isinstance(heading_path, str) or not heading_path:
        return False
    m = _ACAO_EXACT.search(heading_path)
    return m is not None and int(m.group(1)) == acao_num


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_sqlite_all() -> dict[str, dict]:
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT chunk_id, ordinal, heading_path, stage, dimension, "
        "start_char, end_char, length(text) AS text_len, text "
        "FROM reference_chunks ORDER BY ordinal"
    ).fetchall()
    conn.close()
    return {r["chunk_id"]: dict(r) for r in rows}


def load_lancedb_all() -> dict[str, dict]:
    db  = lancedb.connect(str(LANCEDB_DIR))
    tbl = db.open_table(TABLE)
    df  = tbl.to_pandas()
    result = {}
    for _, row in df.iterrows():
        vec = row["vector"]
        result[row["chunk_id"]] = {
            "chunk_id":     row["chunk_id"],
            "ordinal":      int(row["ordinal"]),
            "heading_path": row.get("heading_path"),
            "stage":        row.get("stage"),
            "dimension":    row.get("dimension"),
            "text_len":     len(str(row["text"])),
            "text":         str(row["text"]),
            "vec_dim":      len(vec),
            "vec_norm":     float(np.linalg.norm(vec)),
        }
    return result


# ── Per-Ação table ────────────────────────────────────────────────────────────

def _subtask(heading_path: str | None) -> str:
    if not heading_path:
        return "—"
    m = re.search(r">\s*(i{1,3}|iv|vi{0,3}|ix|xi{0,3}|xiv|xv)\.\s*$", heading_path, re.I)
    return (m.group(1).lower() + ".") if m else "—"


def print_acao_table(
    acao_num: int,
    sq_all: dict[str, dict],
    ldb_all: dict[str, dict],
) -> tuple[int, int, int]:
    """Print compact table for one Ação. Returns (sq_count, ldb_count, mismatches)."""
    sq_chunks  = {cid: c for cid, c in sq_all.items()  if _exact_match(c.get("heading_path"), acao_num)}
    ldb_chunks = {cid: c for cid, c in ldb_all.items() if _exact_match(c.get("heading_path"), acao_num)}

    all_ids = sorted(
        set(sq_chunks) | set(ldb_chunks),
        key=lambda cid: (sq_chunks.get(cid) or ldb_chunks[cid])["ordinal"],
    )

    only_sq    = set(sq_chunks) - set(ldb_chunks)
    only_ldb   = set(ldb_chunks) - set(sq_chunks)
    mismatches = [
        cid for cid in set(sq_chunks) & set(ldb_chunks)
        if sq_chunks[cid]["text"].strip() != ldb_chunks[cid]["text"].strip()
    ]

    flag = ""
    if only_sq or only_ldb:
        flag = "  !! STORE MISMATCH"
    elif mismatches:
        flag = "  !! TEXT MISMATCH"

    print(f"\nAção {acao_num:2d}  [{len(all_ids)} chunks]{flag}")
    print(f"  {'Chunk ID':<20} {'Subtask':<8} {'SQLite chars':<16} {'txt_len':>7}  {'vec_norm':>8}  {'Sync':<6}  Heading tail")
    print(f"  {'-'*20} {'-'*8} {'-'*16} {'-'*7}  {'-'*8}  {'-'*6}  {'-'*40}")

    for cid in all_ids:
        sq  = sq_chunks.get(cid)
        ldb = ldb_chunks.get(cid)
        src = sq or ldb

        subtask   = _subtask(src.get("heading_path"))
        txt_len   = src.get("text_len", 0)
        vec_norm  = f"{ldb['vec_norm']:.4f}" if ldb else "N/A"
        char_span = f"{sq['start_char']}-{sq['end_char']}" if sq else "N/A"

        if sq and ldb:
            sync = "OK"
        elif sq:
            sync = "SQ only"
        else:
            sync = "LDB only"

        if sq and ldb and sq["text"].strip() != ldb["text"].strip():
            sync = "DIFF"

        hp    = src.get("heading_path") or ""
        tail  = hp[-45:] if len(hp) > 45 else hp
        short = cid.split(":")[-1]

        print(f"  :{short:<19} {subtask:<8} {char_span:<16} {txt_len:>7}  {vec_norm:>8}  {sync:<6}  ...{tail}")

    return len(sq_chunks), len(ldb_chunks), len(mismatches)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--acao", type=int, default=None, help="Single Ação number (default: 1)")
    grp.add_argument("--all",  action="store_true",   help="Run all 46 Ações")
    args = parser.parse_args()

    targets = ALL_ACOES if args.all else [args.acao or 1]

    print(f"\n{'='*70}")
    print(f"  STORE INSPECTION — {'all 46 Ações' if args.all else f'Ação {targets[0]}'}")
    print(f"  SQLite : {SQLITE_PATH}")
    print(f"  LanceDB: {LANCEDB_DIR}/{TABLE}")
    print(f"{'='*70}")

    # Load both stores once
    print("  Loading stores...", end=" ", flush=True)
    sq_all  = load_sqlite_all()
    ldb_all = load_lancedb_all()
    print(f"SQLite={len(sq_all)} chunks  LanceDB={len(ldb_all)} chunks")

    total_sq = total_ldb = total_mismatches = 0
    problem_acoes: list[int] = []

    for acao_num in targets:
        sq_n, ldb_n, mm = print_acao_table(acao_num, sq_all, ldb_all)
        total_sq        += sq_n
        total_ldb       += ldb_n
        total_mismatches += mm
        if sq_n != ldb_n or mm > 0:
            problem_acoes.append(acao_num)

    # Grand summary (only meaningful when running all)
    if args.all:
        print(f"\n{'='*70}")
        print(f"  GRAND SUMMARY")
        print(f"  Total SQLite chunks across 46 Ações : {total_sq}")
        print(f"  Total LanceDB chunks across 46 Ações: {total_ldb}")
        print(f"  Text mismatches                     : {total_mismatches}")
        if problem_acoes:
            print(f"  Ações with issues                   : {problem_acoes}")
        else:
            print(f"  All 46 Ações consistent across both stores.")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
