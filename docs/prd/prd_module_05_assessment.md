# PRD — Module 5: Auditor Review Interface (Assessment)

**Status:** Ready for implementation
**Date:** 2026-06-02
**ADRs in scope:** 0022–0032

---

## Problem Statement

Modules 1–4 produce an `EvaluationResult` for each Ação/Case pair — carrying a proposed Maturity Score, the full prompt audit trail, retrieved evidence, and three status flags — but there is no way to persist that result, present it to the Auditor for validation, or record the Auditor's final decision. The system currently has no runtime entry point: no HTTP server, no orchestration layer that connects PDF ingestion to scored output, and no storage for human review decisions. The Auditor cannot trigger an assessment, navigate its results, or register acceptance or override of any proposed score.

---

## Solution

Build the assessment module (`src/assessment/`) as the system's application layer: an orchestration service (`AssessmentService`) that drives the full pipeline from uploaded Document Artifacts to persisted `EvaluationResult`s, and a FastAPI presentation layer that exposes five routes giving the Auditor access to assessment results and a structured review workflow. Add a top-level `main.py` as the runtime entry point that sequences startup, initialises the shared database, and creates the FastAPI application. Introduce three new SQLite tables (owned by Module 5) for evaluation result persistence, review outcome persistence, and document fingerprint tracking. The Auditor's validated decision — the Review Outcome — always produces a Final Score in {0, 1, 3} and carries a complete audit trail of whether the LLM proposal was accepted or overridden.

---

## User Stories

### `ReviewOutcome` contract

1. As a developer, I want `ReviewOutcome` to be a Pydantic `BaseModel` defined in `src/assessment/interfaces/contracts.py`, carrying `acao_id: int`, `process_number: str`, `final_score: int`, `is_override: bool`, `justification: str | None`, `evidence_references: list[int] | None`, and `created_at: datetime`, so that the Auditor's decision is a typed, validated domain object — consistent with `EvaluationResult` and `RetrievedChunk` as boundary contracts in prior modules.

2. As a developer, I want `ReviewOutcome.final_score` to be validated against the set {0, 1, 3} via a Pydantic validator — the same pattern as `EvaluationResult.proposed_score` — so that an invalid score value raises at construction time rather than propagating silently into the database.

3. As a developer, I want a Pydantic validator to enforce that `is_override=True` implies `justification` is a non-empty string, and `is_override=False` implies `justification` is `None`, so that the override intent is auditable and the absence of justification on accepted scores is unambiguous rather than a missing field.

4. As a developer, I want `evidence_references` to be `list[int] | None` — where `None` means the Auditor did not use the field, and `[]` means the Auditor explicitly supplied an empty set — so that auditor intent is preserved without conflating "field not used" with "no chunks selected".

5. As a developer, I want `created_at` to be set at the persistence layer (not from client input) so that the timestamp is authoritative and cannot be forged or omitted by API callers.

### Database schema

6. As a developer, I want `assessment.init_db(db_path)` to create an `evaluation_results` table with normalised columns (`acao_id`, `process_number`, `proposed_score`, `uncertainty_flag`, `parse_failed`, `no_evidence_found`, `provider`, `model`, `created_at`) plus a `raw_json TEXT` column holding the full `EvaluationResult.model_dump_json()`, and a `UNIQUE (acao_id, process_number)` constraint, so that evaluations are queryable by status and the complete audit snapshot is always available for display.

7. As a developer, I want `assessment.init_db(db_path)` to create a `review_outcomes` table with columns matching `ReviewOutcome` fields plus a `UNIQUE (acao_id, process_number)` constraint, so that exactly one authoritative Review Outcome exists per Ação/Case pair.

8. As a developer, I want `assessment.init_db(db_path)` to create a `document_fingerprints` table with `(process_number, filename, sha256, indexed_at)` and a `PRIMARY KEY (process_number, filename)`, so that document identity is persisted and drives fingerprint-based reuse decisions.

9. As a developer, I want Module 5's `init_db()` to create only Module 5-owned tables and never read, write, or alter retrieval-owned tables (`chunks`, `chunks_fts`), so that schema ownership boundaries defined in ADR-0024 are enforced at the DDL level.

10. As a developer, I want `assessment.configure(db_path)` to store the path at module level and `assessment.get_db_path()` to return it, following the same pattern as `retrieval.configure()` and `retrieval.get_db_path()`, so that Module 5 is self-contained and does not read Module 3's private configuration.

### Document fingerprinting

11. As a developer, I want `AssessmentService.run_assessment()` to compute the SHA-256 hash of each uploaded file's bytes before any other processing, so that document identity is established from the content itself rather than from filename or file size.

12. As a developer, I want the service to look up each `(process_number, filename)` in the `document_fingerprints` table and compare the stored SHA-256 against the computed hash, so that the reuse/replacement decision is deterministic and based on content identity.

13. As a developer, I want the service to skip extraction and indexing for files whose SHA-256 matches the stored fingerprint — using the existing chunks in the retrieval database — so that repeated assessment calls with identical documents do not redundantly re-extract and re-index.

14. As a developer, I want the service to delete existing chunks for any `(process_number, filename)` pair whose SHA-256 differs from the stored fingerprint, then re-extract, re-index, and update the stored fingerprint, so that replacement uploads are handled explicitly and stale indexed text never silently persists alongside new document content.

15. As a developer, I want fingerprint replacement to be per-file rather than per-Case, so that a Case with multiple Document Artifacts can replace one file without discarding the indexed chunks of unchanged files.

### `AssessmentService` orchestration

16. As a developer, I want `AssessmentService.run_assessment(process_number: str, document_paths: list[Path]) -> list[EvaluationResult]` to be the sole orchestration entry point — coordinating fingerprint checking, extraction, indexing, retrieval, and evaluation — so that FastAPI routes and any future CLI entry point share a single, typed integration point for Modules 1–4.

17. As a developer, I want `run_assessment()` to determine assessment scope by iterating `get_ipmp_store().acoes` rather than a hardcoded Ação list, so that adding a new source-of-truth artifact to `data/ipmp/` expands assessment scope at the next service restart without any orchestration code change.

18. As a developer, I want `run_assessment()` to call `retrieve_for_acao(acao_id, process_number)` and then `evaluate(acao_id, process_number, chunks)` for each Ação in the store, so that the full retrieval cascade and LLM evaluation are executed per Ação in store-iteration order.

19. As a developer, I want `run_assessment()` to persist each `EvaluationResult` to the `evaluation_results` table immediately after it is returned by `evaluate()`, so that results are durable even if the service raises on a later Ação.

20. As a developer, I want `run_assessment()` to return the in-memory `list[EvaluationResult]` to the calling route handler so that the API response is assembled without a second database read.

21. As a developer, I want `run_assessment()` to raise an explicit exception when `document_paths` is empty and no indexed chunks exist for `process_number`, so that the case of "no documents and no prior index" is surfaced immediately rather than silently producing empty EvaluationResults.

22. As a developer, I want `run_assessment()` to require that `retrieval.configure()` and `evaluation.configure_llm()` have been called before it runs — raising on missing configuration — so that misconfiguration at startup is detected at the first assessment call, consistent with Module 4's behaviour.

### API routes

23. As an Auditor, I want `POST /cases/{process_number}/assess` to accept one or more PDF files as `multipart/form-data` and return a success response after the full pipeline completes, so that I can trigger assessment by submitting documents and wait for results without managing file paths or running command-line scripts.

24. As an Auditor, I want `POST /cases/{process_number}/assess` to return `409 Conflict` (with a message explaining that a validated Review Outcome already exists) if any Ação in the Case has been reviewed, unless `force=true` is explicitly passed as a query parameter, so that I cannot accidentally overwrite a validated score without explicit intent.

25. As an Auditor, I want `POST /cases/{process_number}/assess?force=true` to delete all existing Review Outcomes and EvaluationResults for the Case before running the new assessment, so that replacement is explicit and deterministic — with no stale data surviving from the prior run.

26. As a developer, I want the force-replacement sequence to execute as `DELETE review_outcomes → DELETE evaluation_results → run pipeline` within a single transaction, so that referential integrity between the two tables is preserved and a partially completed replacement is never persisted.

27. As an Auditor, I want `GET /cases/{process_number}/evaluations` to return a list of all stored EvaluationResults for the Case, so that I can see which Ações have been evaluated and their status at a glance before opening individual results.

28. As an Auditor, I want `GET /cases/{process_number}/evaluations/{acao_id}` to return the full EvaluationResult for that Ação — including retrieved chunks, both prompts, raw LLM response, reasoning, proposed score, and all three status flags — so that all 7 Auditor review elements are available in a single response.

29. As an Auditor, I want `POST /cases/{process_number}/evaluations/{acao_id}/review` to accept a review submission body with `final_score`, `is_override`, `justification`, and optional `evidence_references`, persist it as a ReviewOutcome, and return the stored outcome, so that I can record my validation decision without accessing the database directly.

30. As an Auditor, I want `POST /cases/{process_number}/evaluations/{acao_id}/review` to return `409 Conflict` if a ReviewOutcome already exists for that Ação/Case pair, so that accidental double-submission is caught at the API level rather than silently overwriting a prior decision.

31. As an Auditor, I want `GET /cases/{process_number}/evaluations/{acao_id}/review` to return the stored ReviewOutcome for that Ação — including `final_score`, `is_override`, `justification`, `evidence_references`, and `created_at` — so that I can retrieve the record of my prior decision without re-navigating the full evaluation.

32. As a developer, I want GET routes returning evaluation data to serialise `EvaluationResult` and `ReviewOutcome` via `.model_dump()` directly, without a translation layer, so that all fields are exposed as-is and the domain model is the Phase 1 HTTP response contract.

### Module interfaces and startup

33. As a developer, I want `from assessment import configure, init_db, AssessmentService, ReviewOutcome` to be the complete public surface of the module, so that callers are isolated from internal sub-package layout, consistent with Modules 1–4.

34. As a developer, I want `create_app()` to be importable from `assessment.api.app` by `main.py` directly, rather than re-exported through `assessment.__init__`, so that the runtime entry point is not part of the package's library API.

35. As a developer, I want `main.py` to own the startup sequence — calling `retrieval.configure()`, `retrieval.init_db()`, `assessment.configure()`, `assessment.init_db()`, `configure_llm()`, and finally `create_app()` — so that startup order is visible in one place and each module's `init_db()` is never triggered as a side effect of package import.

---

## Implementation Decisions

### Module layout

```
src/assessment/
    __init__.py          ← public surface: configure, init_db, AssessmentService, ReviewOutcome
    _config.py           ← module-level DB path: configure() / get_db_path()
    service.py           ← AssessmentService: run_assessment()
    interfaces/
        __init__.py
        contracts.py     ← ReviewOutcome Pydantic model (7 fields, validator invariants)
    schema/
        __init__.py
        ddl.py           ← init_db(): evaluation_results, review_outcomes, document_fingerprints
    api/
        __init__.py
        app.py           ← create_app(): FastAPI app construction; imported by main.py only
        routes.py        ← all 5 Phase 1 routes, mounted as a router
        schemas.py       ← write-side request body Pydantic models only
main.py                  ← runtime entry point: configure → init_db → create_app
```

### `ReviewOutcome` model

```python
class ReviewOutcome(BaseModel):
    acao_id: int
    process_number: str
    final_score: int                       # {0, 1, 3} — enforced by validator
    is_override: bool
    justification: str | None             # required (non-empty) when is_override=True; None otherwise
    evidence_references: list[int] | None # None = field unused; [] = explicit empty set
    created_at: datetime                  # set at persistence boundary, not from client
```

Validator invariants:
- `final_score` must be in `{0, 1, 3}`
- `is_override=True` → `justification` must be a non-empty `str`
- `is_override=False` → `justification` must be `None`

### Database schema (Module 5-owned tables)

`evaluation_results`:
- Normalised columns: `acao_id`, `process_number`, `proposed_score`, `uncertainty_flag`, `parse_failed`, `no_evidence_found`, `provider`, `model`, `created_at`
- `raw_json TEXT` — full `EvaluationResult.model_dump_json()`, authoritative for display
- `UNIQUE (acao_id, process_number)`

`review_outcomes`: all `ReviewOutcome` fields as columns; `UNIQUE (acao_id, process_number)`

`document_fingerprints`: `(process_number TEXT, filename TEXT, sha256 TEXT, indexed_at TEXT)`; `PRIMARY KEY (process_number, filename)`

### Shared SQLite, independent configuration

Both `retrieval` and `assessment` call `configure(db_path)` independently from `main.py` with the same physical path. `assessment` must not read `retrieval._config`. Each module's `init_db()` creates only its own tables.

### Fingerprint-based reuse/replacement

`run_assessment()` computes SHA-256 of each uploaded file. Per `(process_number, filename)`:
- **Match:** skip extract + index; use existing chunks.
- **Mismatch or absent:** delete existing chunks for that filename, re-extract, re-index, update fingerprint.

Replacement is per-file. The mechanism is explicit DELETE + INSERT, not `INSERT OR REPLACE` (SQLite's `INSERT OR REPLACE` = DELETE + INSERT, which breaks FK integrity — verified by test).

### Assessment scope

`run_assessment()` iterates `get_ipmp_store().acoes` for scope. No hardcoded Ação list.

### Re-run lifecycle

- Default: `POST /assess` returns `409 Conflict` if any ReviewOutcome exists for the Case.
- `force=true`: explicit `DELETE review_outcomes → DELETE evaluation_results → new pipeline` in one transaction.
- No versioning; one authoritative record per `(acao_id, process_number)`.

### HTTP response contracts

- `GET /evaluations/{acao_id}`: `evaluation_result.model_dump()` — no shaped DTO.
- `GET /evaluations/{acao_id}/review`: `review_outcome.model_dump()`.
- `api/schemas.py` holds only request body models (review submission, etc).

### `POST /assess` response

Must signal completion without exposing implementation details (execution mechanism, DB row IDs, internal timings). Returns a summary that the Auditor can use to navigate to results via the GET routes.

---

## Testing Decisions

**What makes a good test for this module:** tests must verify behaviour through the public interface and the HTTP routes. Tests must not assert on SQL query internals, column names not visible to callers, or internal service method call sequences. A route test must verify that the correct HTTP status code and response body are returned; a persistence test must verify what is retrievable via the GET routes after a POST completes.

**What is tested:**

- **Unit tests — `ReviewOutcome` model:** Pydantic validation for each field; `final_score` rejection for values outside {0, 1, 3}; `is_override=True` without `justification` raises; `is_override=False` with `justification` raises; `evidence_references=None` vs `[]` serialises distinctly.

- **Unit tests — database schema:** `init_db()` creates all three Module 5-owned tables; `init_db()` is idempotent (safe to call twice); `init_db()` does not create retrieval-owned tables; `configure()` + `get_db_path()` round-trips correctly.

- **Unit tests — document fingerprinting:** SHA-256 of identical content produces the same hash; same fingerprint triggers reuse path (extract not called); different fingerprint triggers replacement path (chunks deleted, extract called, fingerprint updated); per-file replacement leaves unchanged files' chunks intact.

- **Integration tests — `AssessmentService`:** End-to-end orchestration with a temporary SQLite DB and stub LLM client — upload synthetic PDFs, verify EvaluationResults persisted; re-run with identical files reuses chunks; re-run with changed file replaces only that file's chunks; `run_assessment()` with no files and no prior index raises; assessment scope matches IPMPStore contents.

- **Integration tests — re-run lifecycle:** First assess → ReviewOutcome submitted → second assess without force returns 409; second assess with `force=true` deletes prior ReviewOutcome and EvaluationResult and produces new results; force-replacement transaction is atomic (no partial state if pipeline raises mid-run).

- **Route tests (FastAPI `TestClient`):** `POST /assess` with valid upload returns success; `GET /evaluations` lists persisted results; `GET /evaluations/{acao_id}` returns full EvaluationResult fields; `POST /review` persists ReviewOutcome and returns it; duplicate `POST /review` returns 409; `GET /review` retrieves stored outcome; `POST /assess` with existing ReviewOutcome returns 409 without force; `created_at` in ReviewOutcome is set server-side.

**First-class regression targets** (must never be left without explicit test coverage):
- `force=true` replacement semantics — the DELETE sequence and its atomicity
- Document fingerprint reuse vs. replacement — the two branching paths
- Review Outcome validator invariants (`is_override` ↔ `justification`)

**Prior art:** `tests/test_evaluation_contract.py` (Module 4) established the Pydantic invariant test pattern; `tests/test_evaluate_orchestration.py` established the stub-client integration test pattern with a `StubLLMClient`. Module 5 route tests follow the FastAPI `TestClient` pattern (new to this codebase, but standard FastAPI).

**No slow marker needed** for Module 5 fast tests — all use stub LLM clients and temporary SQLite databases. Real PDF extraction and real LLM calls are not part of the automated fast test suite.

---

## Out of Scope

- Score aggregation, dimensional rollup, or overall maturity computation — deferred to a future architectural decision (ADR-0030)
- Frontend / Vue.js 3 rendering — Phase 2 (Module 7)
- Dense vector (LanceDB) retrieval fallback — Module 6
- Evaluation history / versioning — Phase 1 is replacement-only (ADR-0026)
- Batch review (reviewing multiple Ações in a single API call)
- Re-extraction with different extraction parameters without re-upload (PDFs are discarded after indexing — ADR-0028)
- Authentication, authorisation, or multi-user session management — single Auditor, local system
- Streaming assessment progress — synchronous execution only (ADR-0027)
- Shaped response DTOs for GET read routes — direct `model_dump()` (ADR-0031)
- Separate database file for Module 5 — shared SQLite (ADR-0024)
- PDF storage as a persistent artefact — extracted chunks are the canonical representation (ADR-0028)

---

## Further Notes

- **GitHub issues:** Issues for this module start at **#21**. Suggested grouping:
  - **#21** — `ReviewOutcome` contract + `configure()` + `init_db()` (three tables)
  - **#22** — `AssessmentService`: fingerprinting, orchestration, persistence
  - **#23** — API routes: all 5 routes, `POST /assess` sync + force, 409 guards
  - **#24** — Review submission: `POST /review`, `GET /review`, validator enforcement
  - **#25** — `main.py` runtime entry point, startup sequencing, `create_app()`

- **`raw_json` as authoritative snapshot:** If a normalised column and `raw_json` disagree, `raw_json` wins. Normalised columns exist only to serve known Phase 1 query workflows (list view, status filter). Schema migrations for new `EvaluationResult` fields only require updating `raw_json`; normalised columns change only when a new Phase 1 query is justified.

- **`None` vs `[]` in `evidence_references`:** This distinction must be preserved through serialisation and deserialisation. `None` serialises to `null` in JSON; `[]` serialises to `[]`. Both are valid states with different meanings (field unused vs. explicit empty set). Tests must cover both.

- **`INSERT OR REPLACE` prohibition:** Do not use `INSERT OR REPLACE` anywhere in Module 5's persistence layer. Verified: with `ON DELETE CASCADE`, it silently deletes ReviewOutcome when EvaluationResult is replaced; with `ON DELETE RESTRICT`, it raises a FK error. Both outcomes are wrong. Use explicit DELETE + INSERT sequences in application code.

- **FastAPI `TestClient` pattern:** Module 5 introduces the first HTTP layer in this codebase. `TestClient` from `httpx` (bundled with `fastapi[testing]`) allows synchronous test calls against the FastAPI app without a running server. Tests should use a `pytest` fixture that creates a temporary SQLite DB, calls `configure()` + `init_db()` for both `retrieval` and `assessment`, then calls `create_app()` and wraps it in `TestClient`.

- **`created_at` generation:** Use `datetime.now(UTC)` at the point of INSERT into `review_outcomes`, not from the request body. The Pydantic model accepts `datetime` for type validation, but the value is always injected by the persistence layer, never taken from client input.
