"""Lane composition + retrieval hubness. Offline (embedder runs locally on CPU).

Reproduces exactly what hybrid.py feeds the gate — BM25 top-K, vector top-K,
RRF fusion (k=60), then the first _MAX_EXAMINED of the fused ranking — and
reports:

  * how many products have a dead BM25 lane (zero hits)
  * what the gated candidates are actually made of, per lane
  * how much of the retrieved pool is discarded before gating
  * which chunks are hubs: retrieved for many unrelated products

Hubness matters because the vector lane is always-on and co-equal (ADR-0049):
a chunk close to many different queries gets pulled into many unrelated
products' pools, where it then has to be suppressed one product at a time via
negative_evidence_patterns.

Usage:
    python scripts/diagnostics/measure_retrieval_lanes.py [--process PN] [--max-examined 8]
"""

from __future__ import annotations

import argparse
import collections
import json
import sqlite3
import statistics as st

from _common import (
    DB_PATH,
    DEFAULT_PROCESS,
    LANCEDB_PATH,
    fts_query_for,
    load_profiles,
    vector_query_for,
)

RRF_K = 60
POOL = 20
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_SEARCH_SQL = """
    SELECT c.filename, c.page_number, c.chunk_index
    FROM chunks_fts JOIN chunks c ON chunks_fts.rowid = c.id
    WHERE chunks_fts MATCH ? AND c.process_number = ?
    ORDER BY chunks_fts.rank LIMIT ?
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--process", default=DEFAULT_PROCESS)
    ap.add_argument("--max-examined", type=int, default=8)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    import lancedb
    import numpy as np
    from sentence_transformers import SentenceTransformer

    profiles = load_profiles()
    products = [
        (acao_id, pid, product)
        for acao_id, prof in sorted(profiles.items())
        for pid, product in prof.items()
    ]

    db = lancedb.connect(str(LANCEDB_PATH))
    # Via _table_name, never the raw process number: table names carry a
    # digest suffix so that two process numbers which sanitise alike cannot
    # share one table (see retrieval/query/vector.py).
    from retrieval.query.vector import _table_name

    table = db.open_table(_table_name(args.process))
    frame = table.to_pandas()
    vectors = np.vstack(frame["vector"].values).astype(np.float32)
    keys = [
        (r.filename, int(r.page_number), int(r.chunk_index))
        for r in frame.itertuples()
    ]

    model = SentenceTransformer(MODEL_NAME)
    query_vectors = model.encode(
        [vector_query_for(p) for _, _, p in products], convert_to_numpy=True
    ).astype(np.float32)

    con = sqlite3.connect(str(DB_PATH))
    rows = []
    try:
        for (acao_id, pid, product), qv in zip(products, query_vectors):
            fts = fts_query_for(product)
            try:
                bm25 = [
                    (f, int(p), int(i))
                    for f, p, i in con.execute(_SEARCH_SQL, (fts, args.process, POOL))
                ] if fts else []
            except sqlite3.OperationalError:
                bm25 = []
            order = np.argsort(((vectors - qv) ** 2).sum(1), kind="stable")[:POOL]
            vector = [keys[i] for i in order]

            fused: dict[tuple, float] = collections.defaultdict(float)
            for rank, key in enumerate(bm25, 1):
                fused[key] += 1.0 / (RRF_K + rank)
            for rank, key in enumerate(vector, 1):
                fused[key] += 1.0 / (RRF_K + rank)
            ranked = sorted(fused, key=lambda k: -fused[k])
            gated = ranked[: args.max_examined]

            bset, vset = set(bm25), set(vector)
            rows.append(
                dict(
                    acao=acao_id,
                    pid=pid,
                    n_bm25=len(bm25),
                    n_vector=len(vector),
                    overlap=len(bset & vset),
                    pool=len(fused),
                    gated_vector_only=sum(1 for k in gated if k in vset and k not in bset),
                    gated_bm25_only=sum(1 for k in gated if k in bset and k not in vset),
                    gated_both=sum(1 for k in gated if k in bset and k in vset),
                    bm25_dropped_before_gate=sum(1 for k in bm25 if k not in gated),
                    gated=[list(k) for k in gated],
                )
            )
    finally:
        con.close()

    n = len(rows)
    dead = [r for r in rows if r["n_bm25"] == 0]
    print("=" * 78)
    print(f"LANE COMPOSITION — {n} products, corpus '{args.process}'")
    print("=" * 78)
    print(f"BM25 lane returns ZERO hits : {len(dead)}/{n} ({100*len(dead)/n:.0f}%) -> pool 100% vector")
    print(f"BM25 lane <= 2 hits         : {sum(1 for r in rows if r['n_bm25'] <= 2)}/{n}")
    print(f"mean lane overlap           : {st.mean(r['overlap'] for r in rows):.2f} of {POOL}")
    print()
    print(f"the {args.max_examined} candidates actually gated are made of:")
    print(f"  vector-only : {st.mean(r['gated_vector_only'] for r in rows):.2f}")
    print(f"  bm25-only   : {st.mean(r['gated_bm25_only'] for r in rows):.2f}")
    print(f"  both lanes  : {st.mean(r['gated_both'] for r in rows):.2f}")
    allvec = sum(1 for r in rows if r["gated_vector_only"] == args.max_examined)
    print(f"  products where ALL gated candidates are vector-only: {allvec}/{n} ({100*allvec/n:.0f}%)")
    print()
    mean_pool = st.mean(r["pool"] for r in rows)
    print(f"mean fused pool             : {mean_pool:.1f} candidates")
    print(
        f"discarded before gating     : {100*(1-args.max_examined/mean_pool):.0f}% "
        f"(_MAX_EXAMINED={args.max_examined})"
    )
    print(
        f"BM25 hits retrieved then dropped before the gate: "
        f"{sum(r['bm25_dropped_before_gate'] for r in rows)} total"
    )

    print()
    print("=" * 78)
    print("HUBNESS — chunks appearing in the gated set of the most products")
    print("=" * 78)
    counter: collections.Counter = collections.Counter()
    for r in rows:
        for k in r["gated"]:
            counter[tuple(k)] += 1
    for key, count in counter.most_common(15):
        print(f"  {count:>4} products ({100*count/n:>3.0f}%)  {key[0][-18:]} p{key[1]:<5} i{key[2]}")
    slots = n * args.max_examined
    top10 = sum(c for _, c in counter.most_common(10))
    print(f"\n  top-10 chunks occupy {100*top10/slots:.1f}% of all {slots} gated slots")
    print(f"  distinct chunks ever gated: {len(counter)}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(rows, fh)
        print(f"\nper-product detail written to {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
