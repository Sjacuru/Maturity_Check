"""
Diagnostic: show all retrieval steps for Ação 1, process 040_101607_2024.
Output written to retrieval_diagnostic.txt (UTF-8).
"""

from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestion import get_acronym_store, get_ipmp_store, get_retrieval_profile_store, get_rio_manual_store
from retrieval._config import configure, get_db_path
from retrieval.query.bm25 import MAX_CHUNKS_PER_ACAO, _PER_PRODUCT_TARGET, _run_queries
from retrieval.query.query_builder import build_bm25_query, build_query_from_terms

configure(Path("data/app.db"))

PROCESS_NUMBER = "040_101607_2024"
ACAO_ID = 1
DB_PATH = get_db_path()

# ── Build queries (same logic as retrieve_bm25_for_acao) ─────────────────────

acao = get_ipmp_store().acoes[ACAO_ID]
profile_acao = get_retrieval_profile_store().acoes.get(ACAO_ID)
acronym_map = get_acronym_store()

queries: dict[str, str] = {}
for product in acao.produtos_esperados:
    if product.id[-1:].isalpha():
        profile_product = (
            profile_acao.expected_products.get(product.id)
            if profile_acao else None
        )
        if profile_product and profile_product.query_terms:
            q = build_query_from_terms(profile_product.query_terms)
        else:
            q = build_bm25_query(product.texto, acronym_map)
        if q:
            queries[product.id] = q

rio_acao = get_rio_manual_store().acoes.get(ACAO_ID)
if rio_acao:
    hints = rio_acao.bm25_search_hints
    all_hints = hints.primary_terms + hints.secondary_terms
    if all_hints:
        queries["rio_hints"] = " OR ".join(f'"{t}"' for t in all_hints)

# ── Output helpers ────────────────────────────────────────────────────────────

out: list[str] = []
w = out.append


def section(title: str) -> None:
    w("")
    w("=" * 72)
    w(f"  {title}")
    w("=" * 72)


def safe(text: str, limit: int = 150) -> str:
    return text[:limit].replace("\n", " ").replace("\r", "")


# ── Section 0: Queries ────────────────────────────────────────────────────────

section("QUERIES PER EXPECTED PRODUCT")
for pid, q in queries.items():
    w(f"\n[{pid}]  ({len(q)} chars)")
    for part in q.split(" OR "):
        w(f"  {part.strip()}")

# ── Section 1: RAW HITS (before any merge/dedup) ─────────────────────────────

section("RAW HITS — before any dedup")
w(f"  PER_PRODUCT_TARGET={_PER_PRODUCT_TARGET}  MAX_CHUNKS={MAX_CHUNKS_PER_ACAO}")
w(f"  SQL LIMIT per query = {MAX_CHUNKS_PER_ACAO * 4}")

con = sqlite3.connect(str(DB_PATH))
raw_hits = _run_queries(con, queries, PROCESS_NUMBER)
con.close()

by_product: dict[str, list] = defaultdict(list)
for h in raw_hits:
    by_product[h.product_id or "?"].append(h)

# Track all products×chunks occurrences
chunk_to_products: dict[int, list[tuple[str, float]]] = defaultdict(list)
for h in raw_hits:
    chunk_to_products[h.chunk_id].append((h.product_id or "?", h.score))

total_raw = sum(len(v) for v in by_product.values())
unique_raw = len(chunk_to_products)
w(f"\n  Total raw hits: {total_raw}  |  Unique chunks: {unique_raw}")

for pid in sorted(by_product.keys()):
    hits = sorted(by_product[pid], key=lambda h: h.score)
    w(f"\n  [{pid}] — {len(hits)} hits (sorted best→worst BM25)")
    for i, h in enumerate(hits):
        others = [(p, s) for p, s in chunk_to_products[h.chunk_id] if p != pid]
        overlap = f"  *** also in {[p for p,_ in others]}" if others else ""
        w(f"    #{i+1:2d}  id={h.chunk_id:5d}  score={h.score:8.3f}  pg={h.row[2]:3d} | {safe(h.row[8], 90)}{overlap}")

# ── Section 2: Cross-product overlap ─────────────────────────────────────────

section("CROSS-PRODUCT OVERLAP — chunks matching queries from multiple products")
overlap_chunks = {cid: entries for cid, entries in chunk_to_products.items() if len(entries) > 1}
if overlap_chunks:
    w(f"\n  {len(overlap_chunks)} chunks appear under more than one product:")
    for cid, entries in sorted(overlap_chunks.items()):
        best = min(entries, key=lambda e: e[1])
        w(f"  chunk_id={cid:5d}  products+scores={[(p, round(s,2)) for p,s in sorted(entries, key=lambda e: e[1])]}  → dedup winner={best[0]}")
        # Find the chunk text
        for h in raw_hits:
            if h.chunk_id == cid:
                w(f"           text: {safe(h.row[8], 120)}")
                break
else:
    w("\n  No cross-product overlap in raw hits.")

# ── Section 3: After Step 1 — per-product top-5 selection ────────────────────

section("AFTER STEP 1 — per-product top-5 (before cross-product dedup)")
step1: list = []
for pid in sorted(by_product.keys()):
    hits = sorted(by_product[pid], key=lambda h: h.score)
    kept = hits[:_PER_PRODUCT_TARGET]
    dropped = hits[_PER_PRODUCT_TARGET:]
    step1.extend(kept)
    w(f"\n  [{pid}]  keeps {len(kept)} of {len(hits)}")
    for h in kept:
        w(f"    KEEP  id={h.chunk_id:5d}  score={h.score:8.3f}  pg={h.row[2]:3d} | {safe(h.row[8], 90)}")
    for h in dropped:
        w(f"    DROP  id={h.chunk_id:5d}  score={h.score:8.3f}  pg={h.row[2]:3d} | [per-product cap] {safe(h.row[8], 70)}")

w(f"\n  Pool entering cross-product dedup: {len(step1)} hits")

# ── Section 4: After Step 2 — cross-product dedup ────────────────────────────

section("AFTER STEP 2 — cross-product dedup (final _merge() output, top-20)")
best_map: dict[int, object] = {}
for h in step1:
    if h.chunk_id not in best_map or h.score < best_map[h.chunk_id].score:
        best_map[h.chunk_id] = h

merged = sorted(best_map.values(), key=lambda h: h.score)
final = merged[:MAX_CHUNKS_PER_ACAO]
w(f"\n  {len(merged)} unique chunks after dedup  →  top {len(final)} sent to evaluator")
w("")
for rank, h in enumerate(final, 1):
    w(f"  #{rank:2d}  [{h.product_id:10s}]  id={h.chunk_id:5d}  score={h.score:8.3f}  pg={h.row[2]:3d} | {safe(h.row[8], 95)}")

if len(merged) > MAX_CHUNKS_PER_ACAO:
    w(f"\n  DROPPED by MAX_CHUNKS cap (score too weak to make top-{MAX_CHUNKS_PER_ACAO}):")
    for h in merged[MAX_CHUNKS_PER_ACAO:]:
        w(f"    [{h.product_id:10s}]  id={h.chunk_id:5d}  score={h.score:8.3f}  pg={h.row[2]:3d} | {safe(h.row[8], 90)}")

# ── Section 5: Full text of every BM25 chunk sent to evaluator ───────────────

section("FULL TEXT — every BM25 chunk in evaluator order (best score first)")
w("  (Step D regex chunks are additive and listed in the evaluation API, not here)")
for rank, h in enumerate(final, 1):
    w("")
    w(f"{'─'*72}")
    w(f"  #{rank:2d}  [{h.product_id}]  chunk_id={h.chunk_id}  score={h.score:.3f}")
    w(f"       file={h.row[1]}  page={h.row[2]}  chunk_index={h.row[3]}")
    w(f"{'─'*72}")
    w(h.row[8])

# ── Write ─────────────────────────────────────────────────────────────────────

out_path = Path("retrieval_diagnostic.txt")
out_path.write_text("\n".join(out), encoding="utf-8")
print(f"Written {len(out)} lines to {out_path}")
