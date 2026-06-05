# ADR-0041 — LanceDB is partitioned at process level (one table per process)

Each assessed case (`process_number`) has its own LanceDB table. Invalidation drops
the entire process table atomically.

## Decision

- Table name derived from `process_number`; stored inside `lancedb_path` (ADR-0036).
- `ensure_vector_index_exists(process_number)` creates and populates the table from
  the current canonical chunks if absent; does nothing if present.
- Invalidation during replacement: drop the process table, then allow lazy rebuild.
- No global shared table, no file-level partition orchestration, no cross-process
  vector coordination.

## Considered Options

- **(b) Global table with `process_number` column** — rejected: LanceDB filtered deletes
  are not fully atomic across versions; table grows unbounded; no benefit for the
  bounded case count in this system.
- **(c) One table per `(process_number, filename)`** — rejected: fingerprints are
  file-level for detection accuracy, but lifecycle ownership (reassessment, invalidation)
  is process-oriented; symmetry with fingerprints is not a sufficient reason to
  introduce finer-grained table management.

## Consequences

If future workflows introduce independently managed document lifecycles within the same
process, finer-grained semantic partitioning may later be justified. Current architecture
optimises for lifecycle coherence and simplicity.
