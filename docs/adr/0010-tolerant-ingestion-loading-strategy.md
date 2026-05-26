# Tolerant ingestion loading strategy: fatal errors vs. non-fatal domain incompleteness

Source-of-truth artifacts (`acao_*.json`) are under progressive enrichment — fields may be intentionally empty while domain research is ongoing (e.g., unknown law numbers, empty `regex_variants`). A strict all-or-nothing loader would crash the system whenever any artifact contains incomplete business-domain data, blocking operational use during enrichment cycles. At the same time, artifacts with compromised structural integrity must never be silently accepted, as they represent broken inputs rather than incomplete data.

The ingestion module distinguishes two failure classes:

**Fatal errors** — crash the singleton immediately with an explicit exception:
- Data directory not found
- Unreadable or syntactically invalid JSON
- Filename numeric suffix does not match internal `acao_id`

**Non-fatal validation failures** — skip the individual file, emit a structured log entry, continue loading remaining files:
- Pydantic model validation errors on an individual file (missing required structural fields, type mismatches)

Skipped files are never silent. The loader always emits: filename, validation error, reason for skipping, and a final loaded/skipped count (e.g., "Loaded 43/46 action files. Skipped: acao_17.json — validation error: ...").

**Rationale:** Fatal and non-fatal conditions map to fundamentally different problem types. Fatal conditions indicate the artifact itself is corrupted — the data cannot be trusted regardless of intent. Non-fatal conditions indicate the artifact is structurally sound but contains intentionally incomplete business data, which is an expected and valid state during progressive enrichment. Treating these identically would conflate infrastructure failures with deliberate domain decisions, coupling ingestion stability to domain research progress.

**Considered Options:** All-or-nothing (fail on any error) — rejected because it would block system operation whenever a partially enriched artifact fails Pydantic validation, penalising operational continuity for a domain research gap rather than a structural defect.

**Consequences:** Downstream modules must handle the case that the ingestion store does not contain all 46 actions. Reproducibility is preserved through explicit logging transparency rather than loading rigidity. The `_meta.known_gaps` field in each artifact remains the sole registry of intentional incompleteness; Pydantic does not duplicate domain-completeness enforcement.
