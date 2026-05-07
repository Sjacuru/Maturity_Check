# OQ-007 — Hybrid Retrieval Strategy: BM25 + Dense Vector Fusion
# OQ-007 — Estratégia de Recuperação Híbrida: Fusão BM25 + Vetor Denso

**Created:** 2026-05-07
**Status:** OPEN — decision deferred to implementation. Read this file before building `reference_search.py`.
**PRD references:** FR-008, FR-008D (deterministic fusion), NFR-006 (measure before optimising)

---

## Context / Contexto

The retrieval layer must search two types of index over the same chunk corpus:

- **Dense vectors (LanceDB)** — encode *meaning*; match paraphrases and semantically related text even when no exact words overlap.
- **BM25 (whoosh)** — keyword frequency/rarity index; match exact terms, legal decree numbers, acronyms (AIAS, NFR-008), and domain jargon that the embedding model may dilute into a broad semantic neighbourhood.

Neither alone is sufficient. The question is how to combine them.

---

## Three options considered / Três opções consideradas

### Option A — Always run both, always fuse ✅ RECOMMENDED

Every query runs through both BM25 and dense search on the same collection. Results are merged by **Reciprocal Rank Fusion (RRF)** or a weighted linear combination into a single ranked list. No query analysis, no routing logic.

**Short answer: always run both, always fuse. No routing.**

The cleanest solution is to always run both retrievers and use fusion scoring to combine results — this is what production RAG systems do.

- BM25 naturally dominates when exact terms appear in the query.
- Dense naturally dominates when the query is conceptual or paraphrased.
- Fusion weight is the single tuning knob — a config parameter, not code logic.

**Pros:** simple, robust, measurable, explainable to adviser.
**Cons:** slightly more compute per query (negligible at this scale).

---

### Option B — Query-type routing

Analyse each incoming query to detect whether it asks for exact legal references (favour BM25) or conceptual questions (favour dense). Route accordingly.

**Pros:** theoretically optimal per query.
**Cons:** fragile — most queries contain both exact terms and semantic intent simultaneously. Requires a classifier that must be maintained and tested. Violates "no autonomous decision logic" principle.

**Not recommended for v1.**

---

### Option C — Adaptive weighting

Always run both retrievers, but dynamically adjust their contribution based on query characteristics — queries with many exact terms get higher BM25 weight; more abstract queries lean toward dense vectors.

**Pros:** more nuanced than fixed fusion.
**Cons:** adds complexity without a clear measurable gain over Option A at this corpus size. Requires pilot data to calibrate (NFR-006: measure first). Could be introduced in Phase 2 if Option A proves insufficient.

**Defer to Phase 2 unless Option A underperforms.**

---

## Decision guidance for the implementing AI / Orientação para implementação

> **Before writing any code for `reference_search.py` or `case_search.py`:**
>
> 1. Re-read this file.
> 2. Confirm with the user which option to implement. Present the three options above and ask: *"Option A (always fuse) is the recommended default — do you want to proceed with that, or revisit B or C?"*
> 3. If the user confirms Option A, implement RRF fusion with a configurable weight parameter (`bm25_weight`, default `0.5`).
> 4. Do NOT implement routing logic without explicit user approval.

---

## Implementation notes (Option A) / Notas de implementação

- **One BM25 index per collection** — M5D reference gets its own index; case documents get theirs. The caller decides which collection to search, not the retrieval function.
- **Fusion formula (RRF):** `score(d) = Σ 1 / (k + rank_i(d))` where `k=60` is standard. Alternatively: `score(d) = α * bm25_norm(d) + (1-α) * dense_norm(d)`.
- **`bm25_weight` is a config parameter** — start at `0.5` (equal weight), measure recall on Ação 1 test cases, adjust only if data justifies it (NFR-006).
- **Sequence:** finish M5D ingestion validation → build BM25 index over validated chunks → wire hybrid fusion → test on Ação 1 → only then ingest next document.

---

## What the "collection" routing looks like / Como funciona o roteamento de coleção

```
Evaluation pipeline
  └─ for each Ação being evaluated:
       ├─ reference_search(query, collection="m5d")    # always M5D reference index
       └─ case_search(query, collection=case_id)        # always the case document index
```

The retrieval layer always runs hybrid. The pipeline decides *which corpus*, not *which retrieval method*.
