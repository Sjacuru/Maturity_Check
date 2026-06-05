# ADR-0036 — LanceDB path is derived from the retrieval storage root, not independently configured

LanceDB storage is placed at `db_path.parent / "lancedb"`, where `db_path` is the
SQLite path already configured via `retrieval.configure(db_path)`. No separate vector
storage configuration is exposed.

## Decision

- `lancedb_path = db_path.parent / "lancedb"` — deterministic, derived, zero new API.
- `retrieval.configure(db_path)` remains the single persistence configuration surface.
- Callers never manage LanceDB lifecycle; it is an implementation detail of `vector.py`.
- Replacement and cleanup semantics treat SQLite artifacts and LanceDB artifacts as the
  same retrieval-owned persistence domain (same root, managed together).
- `tmp_path`-based tests naturally isolate both SQLite and LanceDB without additional
  configuration.

## Considered Options

- **(b) Configurable path via `configure_vector()`** — rejected: contradicts ADR-0034
  (no separate configure for vector); adds surface for a concern that is not operationally
  distinct.
- **(c) Fixed global path (`./data/lancedb/`)** — rejected: breaks `tmp_path` test
  isolation; couples tests to the project filesystem.

## Consequences

Independent vector persistence configuration should only be introduced if vector
infrastructure becomes operationally distinct enough to justify separate lifecycle
management.
