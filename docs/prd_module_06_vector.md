# PRD — Module 6: Vector Fallback (LanceDB)

**Status:** Draft  
**Date:** 2026-06-03  
**ADRs:** 0033–0041  
**GitHub issues:** #26–#28 (implementation only; tests accompany each issue)

---

## Problem Statement

The retrieval cascade is entirely lexical (BM25 + regex). When case documents use
atypical vocabulary, legal shorthand, or terminology that diverges from the IPMP
expected-product descriptions, lexical retrieval returns zero chunks. The evaluation
module then produces `no_evidence_found=True` — meaning the Auditor sees a flagged
evaluation with no evidence to review, even when the case document contains genuinely
relevant content written in non-standard language.

---

## Solution

Extend the retrieval cascade with a vector fallback step (LanceDB +
sentence-transformers) that executes only when the lexical cascade (steps A–D)
collectively returns zero chunks. Embeddings are computed on demand the first time
fallback triggers for a given Case, stored in a process-level LanceDB table, and
reused on subsequent fallback calls. Retrieval provenance is tracked per-chunk via a
new `retrieval_mode` field on `RetrievedChunk`.

The lexical cascade remains the architecturally primary path. Vector is a recovery
mechanism for sparse lexical failure, not a co-equal retrieval strategy.

---

## User Stories

### Auditor perspective

1. As an Auditor, I want the evaluation to present evidence even when keyword search
   fails to find relevant chunks, so that cases with atypical document vocabulary are
   not automatically flagged as `no_evidence_found` without first attempting semantic
   retrieval.

2. As an Auditor, I want each evidence chunk to display its retrieval mode (lexical or
   vector fallback), so that I can calibrate my trust in the evidence quality and apply
   appropriate scrutiny to semantically retrieved chunks.

3. As an Auditor, I want vector fallback to behave deterministically (fixed model,
   fixed parameters), so that re-running the same assessment produces the same evidence
   set and the academic reproducibility constraint is satisfied.

4. As an Auditor, I want retrieval provenance to be preserved in the persistent
   evaluation record, so that I can reconstruct exactly which retrieval path was used
   for a given evaluation during post-hoc review.

5. As an Auditor, I want the system to show me when vector fallback was the retrieval
   source, so that I can decide whether to request a document re-upload or accept the
   semantically retrieved evidence.

### Developer perspective

6. As a developer, I want `RetrievedChunk` to carry a `retrieval_mode` field with
   values `"lexical"` or `"vector_fallback"`, so that audit reconstruction can
   identify which retrieval path produced each evidence chunk.

7. As a developer, I want the default value of `retrieval_mode` to be `"lexical"`, so
   that existing code that constructs `RetrievedChunk` without the field continues to
   work correctly without modification.

8. As a developer, I want the retrieval cascade to attempt vector search only when the
   lexical steps collectively return zero chunks, so that the deterministic primary path
   is never bypassed when evidence is available.

9. As a developer, I want vector embeddings to be computed lazily — only when fallback
   actually triggers — so that lexical-only retrieval workflows never incur ML
   initialization or embedding computation overhead.

10. As a developer, I want `sentence_transformers` and `lancedb` to be imported lazily
    at vector call time, so that importing the retrieval module or running lexical-only
    tests never loads the ML stack.

11. As a developer, I want the embedding model to be architecturally fixed
    (`all-MiniLM-L6-v2`), so that retrieval reproducibility is maintained and model
    changes require explicit ADR review and index rebuild.

12. As a developer, I want LanceDB to be stored at a path derived automatically from
    the configured SQLite path (`db_path.parent / "lancedb"`), so that no additional
    persistence configuration is required and test isolation using `tmp_path` works
    naturally for both stores.

13. As a developer, I want LanceDB state to be partitioned at the process level (one
    table per process), so that invalidation is atomic, lifecycle-coherent, and
    requires no filter columns or partial deletes.

14. As a developer, I want `ensure_vector_index_exists(process_number)` to check for
    an existing LanceDB table before computing embeddings, so that repeated fallback
    calls for the same Case are served from the existing index without recomputation.

15. As a developer, I want the LanceDB table for a process to be explicitly invalidated
    when that process's retrieval chunks are replaced (fingerprint mismatch), so that
    the vector index never returns embeddings built from stale document content.

16. As a developer, I want LanceDB invalidation to be owned entirely by the retrieval
    module, so that `AssessmentService` never coordinates persistence across module
    boundaries.

17. As a developer, I want the `retrieval.index(process_number, chunks)` public contract
    to remain unchanged, so that `AssessmentService` and any future callers require no
    modification for Module 6.

18. As a developer, I want vector retrieval to live inside `src/retrieval/` as a new
    query submodule, so that all retrieval strategies remain within a single module
    boundary and cascade orchestration stays in one place.

19. As a developer, I want `retrieval_mode="vector_fallback"` to be explicitly set on
    chunks returned by the vector step, so that provenance is artifact-level metadata
    co-located with each chunk.

20. As a developer, I want the number of chunks returned by vector search to respect
    the same upper bound as BM25 (`MAX_CHUNKS_PER_ACAO`), so that evidence set size is
    consistent regardless of retrieval path.

21. As a developer, I want `retrieval_mode` to serialize naturally into the `raw_json`
    blob of `EvaluationResult`, so that the retrieval path is preserved in the
    persistent audit record without additional infrastructure.

### Reproducibility / academic perspective

22. As a researcher validating reproducibility, I want the same case document to produce
    the same vector retrieval results across runs, so that the reproducibility
    constraint (same input → same score) is satisfied for the vector fallback path.

23. As a researcher, I want a future decision to make vector retrieval primary or
    additive to require an explicit ADR and evaluation evidence, so that architectural
    drift from the reproducibility-first design is always deliberate and documented.

---

## Implementation Decisions

### Modules modified / created

1. **`src/retrieval/interfaces/contracts.py`** — `RetrievedChunk` gains
   `retrieval_mode: Literal["lexical", "vector_fallback"] = "lexical"`. Default
   preserves backward compatibility; all existing chunks are semantically lexical.

2. **`src/retrieval/query/vector.py`** (new) — Implements the vector fallback step:
   - Module-level constant `MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"`.
   - All ML imports (`sentence_transformers`, `lancedb`) are lazy — inside the
     functions that use them.
   - `ensure_vector_index_exists(process_number)`: checks for the process-level
     LanceDB table; if absent, fetches the current chunks from SQLite, computes
     embeddings, and populates the table.
   - `search_vector(process_number, query_text, k) -> list[RetrievedChunk]`: calls
     `ensure_vector_index_exists`, queries the LanceDB table, and returns results
     with `retrieval_mode="vector_fallback"`.
   - `invalidate_vector_index(process_number)`: drops the process-level LanceDB table
     if it exists; called internally by the retrieval replacement flow.
   - LanceDB path derived from `get_db_path().parent / "lancedb"` — no new
     configuration surface.
   - One LanceDB table per process; table name derived from `process_number`.

3. **`src/retrieval/query/cascade.py`** — Adds Step E: after the lexical cascade
   (A–D), if `len(chunks) == 0`, call `search_vector(process_number, query_text)`.
   No changes to the function signature.

4. **Retrieval replacement flow** — Wherever chunks for a `(process_number, filename)`
   pair are deleted and re-indexed (fingerprint mismatch path, currently inside
   `AssessmentService._process_file()`), the corresponding process-level LanceDB table
   must be invalidated. The invalidation call originates from inside the retrieval
   module; `AssessmentService` does not manage LanceDB state directly.

   The recommended integration point is the retrieval module exposing an
   `invalidate_vectors(process_number)` function (or equivalent) that
   `AssessmentService` calls immediately after deleting old chunks and before writing
   new ones — keeping the coordination explicit while ownership remains in retrieval.

### Schema / data

- LanceDB table schema per process: `chunk_index` (int, primary key), `filename`
  (str), `page_number` (int), `text` (str), `embedding` (vector[384]).
- No SQLite schema changes. No new SQLite tables. No changes to `retrieval_results`
  or `evaluation_results`.

### Key constraints (from ADRs)

- Vector executes only when `len(retrieved_chunks) == 0` after full lexical aggregation
  (ADR-0033).
- No minimum chunk thresholds, score thresholds, hybrid fusion, or reranking (ADR-0033).
- No `configure_vector()`, no separate public surface, no caller-managed lifecycle
  (ADR-0034, ADR-0036).
- Embedding model changes require ADR review + full LanceDB index rebuild (ADR-0037).
- Ordinary idempotent `index()` calls do not trigger vector invalidation; invalidation
  occurs only during actual replacement lifecycle events (ADR-0035, ADR-0040).

---

## Testing Decisions

### What makes a good test

Tests validate external behaviour, not implementation details. A test for vector
fallback should verify: (a) the cascade activates vector only when lexical returns
zero, (b) returned chunks carry `retrieval_mode="vector_fallback"`, (c) the
LanceDB table is populated on first fallback and reused on second, (d) the table is
dropped on chunk replacement. Tests should not inspect model weights, embedding
values, or LanceDB internal data structures.

### Modules tested

- **`RetrievedChunk` model** — existing tests in `tests/test_retrieved_chunk.py`
  verify the model contract; the new `retrieval_mode` field with its default value
  should be verified there.
- **`vector.py`** — `tests/test_vector_retrieval.py` (new): patches
  `sentence_transformers.SentenceTransformer` and `lancedb.connect` at the
  `vector.py` import path. Validates: fallback activation, lazy initialization,
  provenance tagging, LanceDB lifecycle (create on demand, reuse, invalidate).
- **`cascade.py`** integration — existing cascade tests verify A–D steps;
  vector tests cover the Step E branch in isolation by patching lexical results to
  return zero and confirming `search_vector` is called.

### Prior art

- `assessment.service.extract_document` is patched at its import path in
  `tests/test_assessment_routes.py` and `tests/test_lifecycle_integrity.py` —
  same pattern applies to ML dependencies in `vector.py`.
- `tmp_path` fixtures already isolate SQLite state; the same fixture naturally
  isolates LanceDB (sibling directory derived from `tmp_path`).
- Existing `retrieval` tests (`test_bm25_retrieval.py`, `test_document_retrieval.py`)
  never load ML dependencies — this property must be preserved.

---

## Out of Scope

- Additive/hybrid retrieval (vector always runs alongside lexical) — requires separate
  ADR and evaluation evidence (ADR-0033).
- Score-based reranking or hybrid score fusion (ADR-0033).
- Semantic reranking of lexical results.
- Vector retrieval as the primary retrieval strategy.
- Runtime embedding model configurability (ADR-0037).
- Explicit Hugging Face revision pinning (ADR-0037).
- Empirical retrieval quality benchmarking (deferred to a future evaluation suite).
- Multi-Ação or multi-process vector index queries.
- Versioned or immutable historical vector indexes (ADR-0040).

---

## Further Notes

- The `all-MiniLM-L6-v2` model is already cached locally at
  `C:\Users\sanseri\.cache\huggingface\hub\`. No download required on first run.
- `pip-system-certs` is required for HuggingFace downloads through the corporate
  proxy if re-caching is ever needed.
- The LanceDB directory (`db_path.parent / "lancedb"`) should be added to
  `.gitignore` alongside the SQLite database file.
- Next ADR number after this module: `0042-`.
- Next DAN number: `0003-`.
