"""Profile completeness + query-term recall against the indexed corpus. Offline.

Two questions:

1. Coverage — does every scored IPMP product have a profile product carrying at
   least one active/validated query term? If not, hybrid.py silently degrades
   that product to build_bm25_query() on raw IPMP prose.

2. Recall — what fraction of active query terms actually occur in the indexed
   corpus at all? A term with zero occurrences contributes nothing to the BM25
   lane, so a product whose every term is zero-hit has no lexical lane and its
   candidate pool is 100% vector.

Usage:
    python scripts/diagnostics/measure_profile_coverage.py [--process PN]
"""

from __future__ import annotations

import argparse
import collections
import sqlite3
import statistics as st

from _common import (
    DB_PATH,
    DEFAULT_PROCESS,
    active_terms,
    load_ipmp_scored_products,
    load_profiles,
)

_COUNT_SQL = (
    "SELECT count(*) FROM chunks_fts JOIN chunks c ON chunks_fts.rowid = c.id "
    "WHERE chunks_fts MATCH ? AND c.process_number = ?"
)


def _term_query(term: dict) -> str:
    if term["encoding"] == "phrase":
        return f'"{term["text"]}"'
    tokens = " ".join(f'"{x}"' for x in term["tokens"])
    return f"NEAR({tokens}, {term['distance']})"


def _term_label(term: dict) -> str:
    if term["encoding"] == "phrase":
        return term["text"]
    return "NEAR:" + ",".join(term["tokens"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--process", default=DEFAULT_PROCESS)
    args = ap.parse_args()

    ipmp = load_ipmp_scored_products()
    profiles = load_profiles()

    print("=" * 78)
    print("1. COVERAGE — scored IPMP product -> profile product")
    print("=" * 78)
    missing_profile, orphan_profile, no_terms, no_active = [], [], [], []
    for acao_id, product_ids in sorted(ipmp.items()):
        prof = profiles.get(acao_id, {})
        for pid in product_ids:
            if pid not in prof:
                missing_profile.append((acao_id, pid))
                continue
            if not prof[pid]["query_terms"]:
                no_terms.append((acao_id, pid))
            if not active_terms(prof[pid]):
                no_active.append((acao_id, pid))
        for pid in prof:
            if pid not in product_ids:
                orphan_profile.append((acao_id, pid))

    total = sum(len(v) for v in ipmp.values())
    print(f"scored products in IPMP                     : {total}")
    print(f"without a profile product                   : {len(missing_profile)} {missing_profile or ''}")
    print(f"profile products with no IPMP counterpart   : {len(orphan_profile)} {orphan_profile or ''}")
    print(f"with an empty query_terms list              : {len(no_terms)} {no_terms or ''}")
    print(f"with no active/validated term               : {len(no_active)} {no_active or ''}")
    reachable = bool(missing_profile or no_terms)
    print()
    print(
        "hybrid.py's build_bm25_query() fallback branch is "
        + ("REACHABLE in production" if reachable else "UNREACHABLE in production")
    )

    print()
    print("=" * 78)
    print(f"2. RECALL — active query terms vs corpus '{args.process}'")
    print("=" * 78)
    con = sqlite3.connect(str(DB_PATH))
    try:
        rows = []
        for acao_id, prof in sorted(profiles.items()):
            for pid, product in prof.items():
                for term in active_terms(product):
                    try:
                        hits = con.execute(
                            _COUNT_SQL, (_term_query(term), args.process)
                        ).fetchone()[0]
                    except sqlite3.OperationalError:
                        hits = -1  # FTS5 syntax error
                    rows.append(
                        dict(
                            acao=acao_id,
                            pid=pid,
                            enc=term["encoding"],
                            prov=term["provenance"],
                            words=len(term["text"].split())
                            if term["encoding"] == "phrase"
                            else len(term["tokens"]),
                            hits=hits,
                            label=_term_label(term),
                        )
                    )
    finally:
        con.close()

    if not rows:
        print("no active terms found — nothing to measure")
        return 1

    zero = [r for r in rows if r["hits"] == 0]
    err = [r for r in rows if r["hits"] < 0]
    print(f"active/validated terms                      : {len(rows)}")
    print(f"zero occurrences in corpus                  : {len(zero)} ({100*len(zero)/len(rows):.1f}%)")
    print(f"FTS5 syntax errors                          : {len(err)}")

    print("\nby encoding:")
    for enc in ("phrase", "near"):
        s = [r for r in rows if r["enc"] == enc]
        if s:
            z = sum(1 for r in s if r["hits"] == 0)
            print(f"  {enc:<7} n={len(s):<5} zero-hit={100*z/len(s):>3.0f}%  mean_tokens={st.mean(r['words'] for r in s):.1f}")

    print("\nby provenance:")
    for prov in ("canonical", "real_world", "synthetic"):
        s = [r for r in rows if r["prov"] == prov]
        if s:
            z = sum(1 for r in s if r["hits"] == 0)
            print(f"  {prov:<11} n={len(s):<5} zero-hit={100*z/len(s):>3.0f}%")

    print("\nby phrase length:")
    for lo, hi, label in [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 5, "4-5"), (6, 99, "6+")]:
        s = [r for r in rows if r["enc"] == "phrase" and lo <= r["words"] <= hi]
        if s:
            z = sum(1 for r in s if r["hits"] == 0)
            print(f"  {label:<5} words  n={len(s):<5} zero-hit={100*z/len(s):>3.0f}%")

    by_product = collections.defaultdict(list)
    for r in rows:
        by_product[(r["acao"], r["pid"])].append(r)
    dead = [k for k, v in by_product.items() if all(r["hits"] <= 0 for r in v)]
    print(
        f"\nproducts whose EVERY active term is zero-hit : {len(dead)}/{len(by_product)} "
        f"({100*len(dead)/len(by_product):.0f}%) -> no lexical lane, pool is 100% vector"
    )

    print("\nhighest-recall active terms (these carry the whole BM25 lane):")
    for r in sorted(rows, key=lambda x: -x["hits"])[:15]:
        print(f"  {r['hits']:>5} hits  Acao {r['acao']:>2} {r['pid']:<7} {r['label'][:58]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
