# ADR-0040 — LanceDB vector state is invalidated whenever retrieval chunks are replaced

LanceDB embeddings are a derived representation of canonical retrieval chunks. When
chunk state is replaced (fingerprint mismatch), the corresponding LanceDB partition
is explicitly deleted before new chunks are written, allowing lazy vector rebuild if
fallback triggers later.

## Decision

- LanceDB invalidation is owned entirely by `src/retrieval/` — no cross-module
  coordination; `AssessmentService` does not touch vector persistence.
- During a replacement lifecycle event: delete lexical chunks → delete LanceDB partition
  → write new chunks → allow lazy vector rebuild on next fallback trigger.
- Invalidation granularity follows retrieval partitioning semantics (by `process_number`
  or `(process_number, filename)` — matched to how chunks are partitioned).
- Ordinary idempotent `index()` calls (`INSERT OR IGNORE` on unchanged artifacts) do
  not trigger vector invalidation.
- Explicit invalidation, not heuristic staleness detection (e.g., count comparison).

## Considered Options

- **(b) Count comparison in `ensure_vector_index_exists`** — rejected: count can
  false-negative (same count, different content); adds a round-trip on every fallback.
- **(c) `_force_delete()` in AssessmentService deletes LanceDB** — rejected: Assessment
  would own Retrieval's persistence, violating ADR-0034/0036 module boundaries.
- **(d) Accept the risk** — rejected: staleness on the vector fallback path is a
  correctness bug; the auditor could see evidence from the wrong document version.

## Consequences

If future architectures introduce versioned retrieval artifacts or immutable historical
indexes, vector persistence may evolve toward versioned coexistence rather than
destructive replacement. Current semantics require strict synchronization.
