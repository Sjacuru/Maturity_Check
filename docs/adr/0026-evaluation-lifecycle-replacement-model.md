# Evaluation lifecycle: replacement model with application-layer re-run guard

Phase 1 adopts a replacement model, not a versioning model:
- Exactly one authoritative `EvaluationResult` exists per `(acao_id, process_number)`.
- Exactly one authoritative `ReviewOutcome` exists per `(acao_id, process_number)`.
- Re-running an evaluation replaces both records. History is not preserved.

`review_outcomes` links to `evaluation_results` via the natural key `(acao_id, process_number)`.
No SQLite foreign key constraint is declared between the two tables.

## Why no DB-level FK

`INSERT OR REPLACE` in SQLite is a `DELETE` followed by an `INSERT`. Verified behavior:

| FK clause | `INSERT OR REPLACE` result |
|---|---|
| `ON DELETE CASCADE` | ReviewOutcome silently deleted — rejected (unintended data loss) |
| `ON DELETE RESTRICT` | FK constraint raised — rejected (schema-level blocking, too strong for Phase 1) |
| No FK | No DB enforcement — application layer controls integrity |

A DB-level FK on `(acao_id, process_number)` cannot express "block unless `force=true`" — that logic belongs in the application layer regardless. Omitting the FK removes a constraint that would otherwise conflict with the approved application-layer guard.

## Re-run lifecycle

**Default (no `force`):** When the API receives a re-run request for an `(acao_id, process_number)` pair that already has a ReviewOutcome, return `409 Conflict` with a message indicating that a validated review exists.

**Explicit re-run (`force=true`):** The application service executes, in a single transaction:
1. `DELETE FROM review_outcomes WHERE acao_id = ? AND process_number = ?`
2. `DELETE FROM eval_results WHERE acao_id = ? AND process_number = ?`
3. `INSERT INTO eval_results ...` (new evaluation)

Step 1 must precede step 2 to maintain referential integrity by convention. No `INSERT OR REPLACE` is used anywhere in this flow.

## Consequences

- No evaluation history in Phase 1 — if a re-run produces a different score, the prior EvaluationResult and ReviewOutcome are gone.
- The application layer is the sole enforcement point for the "reviewed Ação is protected" invariant. Tests must cover the 409 path and the `force=true` deletion sequence.
- If future requirements demand evaluation history (e.g., comparing LLM score drift across model versions), a versioning model with a surrogate PK and `version` column can be introduced without conflicting with this decision — the natural key constraint is lifted and the `(acao_id, process_number, version)` tuple becomes the new unique key.
- Referential integrity between `review_outcomes` and `eval_results` is enforced only by the application service. Direct DB writes that bypass the service can create orphaned rows; this is acceptable in Phase 1 (single-user, no concurrent writers).
