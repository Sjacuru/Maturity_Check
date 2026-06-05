# ADR-0035 — Vector indexing is demand-driven, not eager

Embeddings are computed and written to LanceDB only when the vector fallback actually
triggers (BM25+regex returned zero chunks and no vector index yet exists for that
process). The public `retrieval.index()` contract is unchanged — it prepares lexical
retrieval only.

## Decision

- `retrieval.index(process_number, chunks)` remains lexical-only.
- No `index_vectors()`, separate orchestration steps, or vector lifecycle APIs.
- `cascade.py` calls vector fallback when lexical returns zero; `vector.py` internally
  calls `ensure_vector_index_exists(process_number)`, computing embeddings and
  populating LanceDB on demand if absent.
- All vector-index state management is encapsulated inside `src/retrieval/query/vector.py`.
- `sentence_transformers`, the embedding model, and LanceDB are lazily initialized on
  first vector fallback call.

## Considered Options

- **(a) Eager at `index()` time** — rejected: loads ML stack on every index() call even
  when vector fallback never triggers; breaks callers who configured retrieval for
  lexical-only workflows; adds ML cost to the normal (non-fallback) path.
- **(c) Explicit `index_vectors()` call** — rejected: pushes coordination into callers
  (AssessmentService, main.py); adds a new required step to the retrieval lifecycle.

## Consequences

Optimization for present workflow semantics (vector fallback is rare) over hypothetical
future dominance. If semantic retrieval later becomes primary, frequent, or
benchmark-superior, eager indexing may be justified — but that requires a separate ADR
and evaluation evidence.
