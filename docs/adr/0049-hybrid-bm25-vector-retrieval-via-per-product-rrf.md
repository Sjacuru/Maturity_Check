# Hybrid BM25 + vector retrieval via per-product Reciprocal Rank Fusion

**Status:** accepted — supersedes ADR-0033

Vector retrieval (LanceDB + sentence-transformers) becomes a co-equal, always-on retrieval strategy for each letter-suffixed Expected Product (1a, 1b, 1c, 1d), fused with BM25 via Reciprocal Rank Fusion (RRF). This replaces ADR-0033's "fallback only on zero lexical results" trigger.

## Why this reverses ADR-0033

ADR-0033 considered and rejected exactly this option ("(b) Additive always... mixes similarity spaces, undermines determinism, harder to explain academically") and required "a separate ADR and evaluation evidence before becoming default behavior" to adopt it. That evidence now exists: diagnostic runs on Ação 1 / process 040_101607_2024 showed lexical retrieval filling all 20 of `MAX_CHUNKS_PER_ACAO` slots, but with severely imbalanced per-product representation (1b's strong BM25 matches, scores -19 to -13, monopolized the global cap while 1c's best match scored only -12.2 and 1d's best scored -9.7). Lexical retrieval was not failing (zero results) — it was succeeding unevenly across products. ADR-0033's "if and only if zero" trigger cannot address uneven-but-nonzero recall; only an always-on complementary signal can.

## Decision

**Trigger:** Vector search runs unconditionally, once per letter-suffixed Expected Product, on every assessment. It is no longer gated on lexical result count.

**Fusion structure — per-product, not global:** For each Expected Product (1a, 1b, 1c, 1d), BM25 and vector each produce an independent ranked candidate list. The two rankings are fused via RRF *within that product* before the existing per-product top-5 selection (`_PER_PRODUCT_TARGET`) applies. Vector does not become a 6th competing lane alongside the products — it reinforces each product's own signal.

**RRF formula:** `score(chunk) = Σ 1/(k + rank)` summed over whichever ranked list(s) the chunk appears in (BM25, vector, or both). `k = 60`, the literature-standard constant from Cormack et al. (2009), used by Elasticsearch/OpenSearch RRF implementations. No corpus-specific tuning — required for the reproducibility argument (CLAUDE.md: "BM25 + temperature=0 = same input → same score" must extend to any added retrieval signal).

**Candidate pool size:** Both BM25 and vector candidate lists are truncated to their top 20 before RRF runs, so neither side's raw pool size (BM25's SQL `LIMIT 80` vs. vector's full-corpus scan) implicitly biases the fused ranking. RRF's `1/(k+rank)` contribution beyond rank ~20 is negligible regardless.

**Vector query text per product:** `evidence_intent` concatenated with the text of all `retrieval_signal_concepts` for that product, from the retrieval profile (`data/retrieval_profiles/acao_NN.json`). Falls back to the raw IPMP `produto.texto` when no retrieval profile exists for that product yet — mirroring the same fallback `build_bm25_query()` already uses, keeping both retrieval modes symmetric for Ações without a curated profile (Phase 1 is Ação 1 only, but the cascade code is generic).

**rio_hints stays BM25-only.** It is a flat list of Rio Manual document names/phrases (e.g. "Relatório de Pré-Análise", "LC 105"), not a coherent semantic evidence description — there is no good embedding query to build from it. It keeps its existing raw BM25 score.

**Cross-product dedup tie-break:** Within 1a–1d, scores are now RRF-fused (positive, higher-is-better) and compare directly. rio_hints keeps a raw BM25 score (negative, lower-is-better) — numerically incomparable to RRF scores on any shared scale. Rather than attempt a scale conversion, the tie-break is categorical: **if a chunk is nominated by both an IPMP product lane (1a–1d) and by rio_hints, the IPMP product lane always wins**, regardless of either score. rio_hints only keeps a chunk when no product lane also claimed it. Justification: a curated IPMP-aligned match (now reinforced by two independent retrieval signals) is structurally a stronger relevance signal than a generic document-name hint; this doesn't need to be "earned" by comparing incommensurable numbers.

**Pipeline-wide invariant — one physical chunk, one attribution, in any evidence set reaching `evaluate()`.** This isn't just `retrieve_hybrid_for_acao()`'s internal implementation detail; it's a property the whole retrieval-to-scoring pipeline must preserve, because of ADR-0009: scoring is a *single combined LLM call* per Ação, covering all Expected Products at once. `build_user_prompt()` concatenates chunk text without even including `expected_product_id` — the LLM cannot tell two copies of the same chunk apart, so a physical chunk appearing twice (once per product that found it relevant) adds zero information and spends the character budget twice for nothing. Any function that produces a final evidence set for `evaluate()` — `retrieve_hybrid_for_acao()` today, `evidence_selection.select_evidence()` (ADR-0050) — must deduplicate by physical identity (`filename`, `page_number`, `chunk_index`) before returning, using this ADR's "best score wins" rule as the tie-break when more than one product independently claims the same chunk. (Discovered as a live gap in ADR-0050's first implementation — see that ADR's amendment.)

## Determinism

LanceDB's `tbl.search(query_vec).limit(k)` performs exact (flat/brute-force) nearest-neighbor search for tables this size — no approximate index is created (`vector.py` never calls `create_index()`). Combined with `sentence-transformers` deterministic inference at fixed model weights, vector ranking is fully reproducible for a fixed corpus and fixed query text, preserving the project's core reproducibility constraint.

## Consequences

- ADR-0034's rationale for lazy ML imports ("execute only when lexical cascade returned zero") no longer holds in its original form — `sentence-transformers` and LanceDB now load on every assessment, not just the rare fallback case. The module location decision in ADR-0034 (vector code lives in `src/retrieval/`) is unaffected and still stands.
- ADR-0035 ("vector indexing is demand-driven") is compatible as-is: "demand" now means every assessment by definition, but the LanceDB table is still built once per process and reused (idempotent via `ensure_vector_index_exists()`), not rebuilt per query.
- Every assessment now incurs embedding-model inference cost for up to 4 per-product query strings (cheap — encoding a handful of short strings, not the corpus) plus one egress to LanceDB per product. Corpus embedding itself still happens once at first index build, unchanged.
- `search_vector()` must change from a single whole-Ação query (today's `_build_vector_query()` concatenation) to a per-product call accepting product-specific query text and returning a ranked list (not pre-truncated to `MAX_CHUNKS_PER_ACAO`, since the cascade now truncates to top-20 itself before RRF).
- The old "fallback-only" path (Step E in `retrieve_for_acao()`, triggered when lexical returns zero) is removed entirely — replaced by the always-on per-product fusion inside Step C.

## Considered options

- **Threshold-gated top-off** (vector only fills remaining slots when lexical returns fewer than 20) — rejected by explicit choice: doesn't address uneven-but-nonzero recall, the actual problem observed.
- **Vector additive on top, uncapped like regex (Step D)** — rejected: avoids the fusion-formula complexity but leaves BM25 and vector scores in separate lanes with no way to let a strong vector match outrank a weak BM25 match for the same product; doesn't fix the per-product imbalance, only adds more candidates after the imbalance has already been baked in.
- **Global fusion (vector as a 6th lane)** — rejected: vector chunks would carry no per-product attribution, so a single whole-Ação vector query could end up reinforcing whichever product already dominates rather than filling gaps for weak products (1c, 1d).
- **Score normalization (min-max or z-score) instead of RRF** — rejected: requires a fusion weight to be chosen and justified per corpus, which conflicts with the reproducibility argument; RRF's rank-based formula needs no such calibration.
