# ADR-0037 — Embedding model is hardcoded as all-MiniLM-L6-v2, not runtime-configurable

The sentence-transformers model is fixed inside `src/retrieval/query/vector.py` as a
module-level constant. No runtime configurability is exposed.

## Decision

- `MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"` defined inside `vector.py`.
- No `configure_model()`, environment-variable model selection, or runtime override.
- The embedding model is part of the retrieval architecture definition, not operational
  configuration.
- Changing the model requires: ADR review, full LanceDB index rebuild, and retrieval
  reproducibility reevaluation. LanceDB indexes are semantically tied to this model.
- No Hugging Face revision pinning in Phase 1. The fixed model name is sufficient.

## Considered Options

- **(b) Configurable via `retrieval._config.py`** — rejected: adds tunability to a
  system whose primary constraint is reproducibility; model changes would silently
  invalidate all prior indexes with no detection mechanism.
- **(c) Revision-pinned** — rejected: adds operational brittleness before a concrete
  reproducibility problem exists; the locally cached model is the reference.

## Consequences

If the project enters a formal benchmarking or experimentation phase, model
configurability may be justified at that point — with explicit index migration semantics
and embedding versioning as first-class architectural concerns.
