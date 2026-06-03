# EvaluationResult persistence: hybrid normalised columns + JSON blob

The retrieval module (Module 3) establishes a fully-normalised column pattern for `Chunk` persistence — every field becomes its own column, nothing is stored as a blob. This pattern is appropriate for `Chunk` because the model is flat and every field participates in FTS5 search or retrieval filtering.

`EvaluationResult` does not fit this pattern: it contains `retrieved_chunks: list[RetrievedChunk]` (a complex nested list, not flattenable without a join table) and four large display-only text fields (`system_prompt`, `user_prompt`, `raw_llm_response`, `reasoning`) that are never queried — only displayed to the Auditor on demand. Fully normalising these would require either a join table for chunks or artificial blob columns anyway.

The chosen pattern is hybrid:
- **Normalised columns** for fields that support known Phase 1 query workflows.
- **`raw_json TEXT` column** containing the full `EvaluationResult.model_dump_json()` as the authoritative snapshot for display and audit reconstruction.

The `raw_json` column is the authoritative record. Normalised columns are query and indexing aids, not a second authoritative representation. If `raw_json` and a normalised column ever disagree, `raw_json` wins.

## Normalised columns justified by Phase 1 workflows

| Column | Justification |
|---|---|
| `acao_id` | Navigate to a specific Ação within a Case |
| `process_number` | Retrieve all evaluations for a Case |
| `proposed_score` | Display evaluation status at-a-glance; Auditor review queue |
| `uncertainty_flag` | Auditor may prioritise uncertain evaluations for review |
| `parse_failed` | Auditor UI renders a distinct state; query identifies parse failures |
| `no_evidence_found` | Auditor UI renders a distinct state; query identifies missing evidence |
| `provider` | Reproducibility metadata; filter by provider if multiple runs exist |
| `model` | Reproducibility metadata; filter by model if multiple runs exist |
| `created_at` | Timestamp for ordering evaluations within a Case |

Fields stored **only** in `raw_json` (display-only, never queried):
`system_prompt`, `user_prompt`, `raw_llm_response`, `reasoning`, `retrieved_chunks`, `evidence_char_count`.

## Considered Options

- **Fully normalised:** Would require a join table for `retrieved_chunks` (a list of complex Pydantic objects). Adds DDL complexity with no Phase 1 query benefit, since chunks are already in the retrieval module's `chunks` table.
- **Full JSON blob only:** No individual columns queryable. The Auditor review queue (which Ações are pending? which have parse_failed?) would require full-table JSON extraction scans. Rejected.

## Consequences

- Schema migrations for `EvaluationResult` field additions only need to update `raw_json`; normalised columns only change if a new Phase 1 query workflow is identified and justified.
- `retrieved_chunks` is not duplicated in both the `chunks` table and a join table — the `raw_json` blob carries it for display, and the `chunks` table carries it for retrieval.
- The `UNIQUE (acao_id, process_number)` constraint on the `evaluation_results` table ensures at most one stored evaluation per Ação/Case pair; re-running replaces the row.
