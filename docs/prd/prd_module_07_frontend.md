# PRD — Module 7: Frontend (Vue.js 3 + Vuetify 3)

## Problem Statement

The backend is functionally complete (Modules 1–6: ingestion, extraction, retrieval, evaluation, auditor review API, vector fallback). The Auditor has no interface to upload Document Artifacts, trigger assessments, inspect the 7 evaluation artifacts, or submit Review Outcomes without raw API access. The system cannot be used as designed until a thin presentation layer exposes the existing backend capabilities.

---

## Solution

A Vue.js 3 frontend served by FastAPI, providing the Auditor with two views:

1. **Upload View** — enter a Process Number, select PDF Document Artifacts, trigger an assessment, and inspect per-document lifecycle metadata (new/reused/replaced).
2. **Assessment Result View** — one expandable panel per evaluated Ação, each presenting all 7 Auditor Review Interface elements and a score submission form.

Three backend changes accompany the frontend: API namespace separation (`/api/*` prefix), per-document lifecycle metadata on `POST /assess`, and execution-level retrieval query provenance on `RetrievedChunk`.

---

## User Stories

### Backend — API namespace

1. As an Auditor, I want all API endpoints prefixed with `/api/` so that API routing and static file routing are visually and operationally distinct (e.g., `POST /api/cases/{process_number}/assess`).

### Backend — Assessment lifecycle metadata

2. As an Auditor, I want `POST /api/cases/{process_number}/assess` to return a per-document disposition list (new/reused/replaced) alongside the assessment summary so I can see how each Document Artifact was handled during the run.
3. As an Auditor, I want to see an overall assessment status in the `POST /assess` response so I know whether the assessment completed successfully or partially failed.
4. As an Auditor, I want the disposition values to be authoritative — reported by the module that owns the lifecycle decision — so I do not need to infer document processing state from client-side observations.

### Backend — Retrieval provenance

5. As an Auditor, I want each retrieved chunk to carry the exact retrieval expression that produced it (`retrieval_query`) so I can verify not just which cascade step ran, but precisely what was queried.
6. As an Auditor, I want the `retrieval_query` field to be populated for every cascade step: the matched document name (filename_match/variant_match), the FTS5 OR query string (bm25), the regex pattern (regex), and the natural-language query text (vector fallback).
7. As an Auditor, I want the `retrieval_query` to be persisted inside `EvaluationResult` alongside the other chunk provenance fields so audit reconstruction is possible from stored data alone.

### Frontend — Project scaffold and integration

8. As a developer, I want a `frontend/` directory at the repository root containing a Vite + Vue 3 + Vuetify 3 project so the frontend build system is clearly separated from the Python application.
9. As a developer, I want `npm run build` to compile the frontend into `frontend/dist/` so FastAPI can serve it as static files.
10. As a developer, I want FastAPI to mount `frontend/dist/` at `/` (with `html=True`) after the API router is registered so the Auditor accesses the application at `http://localhost:8000/`.
11. As a developer, I want the Vite dev server to proxy `/api/*` requests to FastAPI on port 8000 so local development works with hot module reload without CORS configuration.
12. As a developer, I want Vue Router configured with hash history (`createWebHashHistory`) so no SPA fallback route is needed on the FastAPI side.

### Frontend — Upload View

13. As an Auditor, I want a text input for the Process Number on the Upload View so I can identify the Case I am assessing.
14. As an Auditor, I want a file picker that accepts multiple PDF Document Artifacts so I can submit an entire Case in one operation.
15. As an Auditor, I want a single "Run Assessment" action that uploads the files and triggers the assessment so the workflow has one clear entry point.
16. As an Auditor, I want a progress indicator while the assessment runs so I know the system is working (assessments may take tens of seconds).
17. As an Auditor, I want to see per-document lifecycle metadata (new/reused/replaced) after assessment completes so I understand how each Document Artifact was handled.
18. As an Auditor, I want clear error feedback if the assessment fails (e.g., empty file list, backend error) so I can correct the issue without debugging the API.
19. As an Auditor, I want to navigate to the Assessment Result View automatically after a successful assessment so the workflow proceeds without manual navigation.

### Frontend — Assessment Result View

20. As an Auditor, I want to see all evaluated Ações listed as expandable panels so I can review each one at my own pace.
21. As an Auditor, I want each panel header to show the Ação identifier, title, proposed score, uncertainty flag, `parse_failed` flag, and `no_evidence_found` flag so I can triage the list before expanding any panel.
22. As an Auditor, I want panels with raised flags (`uncertainty_flag`, `parse_failed`, `no_evidence_found`) to be visually prominent so high-attention cases are immediately obvious.
23. As an Auditor, I want panels for already-reviewed Ações to show their Review Outcome (final score, is_override, justification) in read-only form so I can see what was decided.
24. As an Auditor, I want to return to the Assessment Result View by navigating to `/#/cases/{process_number}` so I can resume a review session without re-uploading documents.

### Frontend — Ação panel: 7 Auditor Review Interface elements

25. As an Auditor, I want to see the IPMP criteria and full LLM prompt for each Ação in a collapsible section so I can verify what the LLM was instructed to evaluate (sourced from `EvaluationResult.system_prompt` — the exact artifact presented to the LLM at evaluation time).
26. As an Auditor, I want to see the retrieval query used for each chunk alongside its cascade step, retrieval mode, source document, page number, and chunk text so I have execution-level retrieval provenance.
27. As an Auditor, I want to see the retrieved evidence chunks rendered clearly (filename, page, text, cascade step, retrieval mode, retrieval query) so I can assess whether the right evidence was found.
28. As an Auditor, I want to see the user-side prompt (the evidence block sent to the LLM) in the collapsible full-prompt section so I can verify the complete LLM input.
29. As an Auditor, I want to see the LLM's reasoning text for each Ação so I understand the basis for the proposed score.
30. As an Auditor, I want the uncertainty flag to be displayed prominently within the panel (not only in the header) so its significance is reinforced when I review the evidence.
31. As an Auditor, I want the proposed score (0/1/3) displayed clearly as a read-only value in the panel body before the review form so the context for my decision is always visible.

### Frontend — Review form

32. As an Auditor, I want the score selector (0/1/3) to pre-select the proposed score and visually emphasize it so I can accept the proposal with one click.
33. As an Auditor, I want to see a justification text field appear immediately when I select a score that differs from the proposed score so the override intent is captured inline.
34. As an Auditor, I want the justification field to be required when my selected score differs from the proposed score so that every override is documented.
35. As an Auditor, I want to submit my review for a single Ação without affecting other panels so reviews are independent.
36. As an Auditor, I want the panel to transition to a read-only "Review submitted" state after submission so I can confirm the outcome was recorded.
37. As an Auditor, I want an optional evidence references field in the review form so I can note which chunk indices I relied on (consistent with the `evidence_references` field in `ReviewOutcome`).

---

## Implementation Decisions

### Backend changes

**API namespace — `/api` prefix**
All routes move under `/api/`. The router is included with `prefix="/api"` in the FastAPI app factory. No route logic changes; only the mount point changes. Existing tests must be updated to use the new prefix.

**POST /assess response — document lifecycle metadata**
`AssessmentService.run_assessment()` is extended to return per-document disposition alongside `list[EvaluationResult]`. Disposition values: `"new"` (first-time indexing), `"reused"` (fingerprint match — no re-extraction), `"replaced"` (fingerprint mismatch — stale chunks deleted and re-indexed). The route assembles the final response:

```
{
  "process_number": "...",
  "acao_ids_assessed": [...],
  "count": N,
  "documents": [
    {"filename": "EVTEA.pdf", "disposition": "new"},
    {"filename": "DFE.pdf",   "disposition": "reused"}
  ]
}
```

The module that owns lifecycle decisions (AssessmentService) reports them; the frontend displays, not infers.

**`RetrievedChunk.retrieval_query` field**
A `retrieval_query: str | None = None` field is added to `RetrievedChunk`. Default `None` preserves backward compatibility with stored evaluation rows. Each cascade step populates it:
- `filename_match` / `variant_match` → matched document name string
- `bm25` → FTS5 OR query string from `build_bm25_query()`
- `regex` → combined regex pattern string
- `vector` → natural-language query text passed to the embedding model

Because `RetrievedChunk` serializes inside `EvaluationResult.raw_json`, no schema change is needed — the field is automatically persisted.

### Frontend

**Repository structure**
`frontend/` at repository root. `src/` remains the Python application hierarchy. The two build systems (Python/pyproject.toml and Node/package.json) are separated by directory ownership.

**Framework and tooling**
Vue 3 + Vite + Vuetify 3. Vuetify provides the widget set the review workflow requires (expansion panels, data tables, file input, form controls, status chips) without requiring custom UI construction.

**Routing**
Vue Router with `createWebHashHistory`. Two routes:
- `/` → UploadView
- `/cases/:processNumber` → AssessmentResultView

Hash mode requires no SPA fallback on the FastAPI side.

**State ownership**
No global state manager. Process number lives in the router param. Evaluation list is fetched from `GET /api/cases/:processNumber/evaluations` on AssessmentResultView mount. Per-panel review draft (score selection, justification text) lives in each AcaoPanel component's local state.

**`is_override` derivation**
Computed client-side as `final_score !== proposed_score`. Never exposed as a user-facing toggle. The justification field appears conditionally when this expression is true and is required before submission. The backend independently validates the same invariant via `ReviewOutcome`'s Pydantic validator.

**7 Auditor Review Interface elements → panel sections**
The 7 canonical elements map to panel sections:
1. IPMP criteria → collapsible "Full Prompt" (sourced from `system_prompt` — what the LLM actually saw)
2. Retrieval query → per-chunk metadata in the Evidence section (`retrieval_query` field)
3. Retrieved chunks → Evidence section (filename, page, text, cascade_step, retrieval_mode, retrieval_query)
4. Exact LLM prompt → collapsible "Full Prompt" (`system_prompt` + `user_prompt`)
5. LLM reasoning → Reasoning section (`reasoning` field)
6. Uncertainty flag → panel header chip + prominent in-panel display
7. Proposed score → read-only display above review form

Elements 1 and 4 originate from the same artifact (`system_prompt`) and are presented in a single collapsible section. The governing principle: Auditors review what the LLM actually saw, not what the system currently knows.

**FastAPI static file integration**
`StaticFiles(directory="frontend/dist", html=True)` mounted at `/` in the FastAPI app factory, after `include_router`. API routes registered first always win. No catch-all route, no custom StaticFiles subclass, no Vite base-path customization.

**Development workflow**
Vite dev server on port 5173 with a proxy rule forwarding `/api/*` to FastAPI on port 8000. This is a development convenience only; it has no effect on the production serving model.

---

## Testing Decisions

**What makes a good test here**
Test external behavior — what the API returns and what the UI displays — not implementation mechanics. For the backend changes, tests assert on the shape of API responses and the values of model fields. For the frontend, the build (`npm run build`) is the verification gate.

**Backend tests — what will be tested**
- `retrieval_query` field: each cascade step produces the expected query expression in the returned `RetrievedChunk`
- `POST /assess` response shape: `documents` list present, disposition values correct for new/reused/replaced cases
- `/api` prefix: all 5 existing routes respond correctly under `/api/cases/...`; prior `/cases/...` paths return 404

Prior art: `tests/test_bm25_retrieval.py`, `tests/test_regex_retrieval.py`, `tests/test_vector_retrieval.py` for retrieval-level tests; `tests/test_retrieved_chunk.py` for model field tests.

**Frontend — no automated test suite**
The frontend intentionally owns no domain logic. Correctness is enforced by backend Pydantic validators and the Python test suite. `npm run build` catches compilation and integration failures without creating a parallel testing ecosystem.

---

## Out of Scope

- Dedicated per-Ação route (`AcaoReviewView`) — deferred until Phase 2 evidence shows 46 Ações create navigation complexity
- Pinia or any global state manager — no demonstrated cross-view coordination problem
- Authentication or authorization
- Score aggregation across Ações or Dimensões
- Phases 2+ Ação data (the frontend is general; only Ação 1 data exists)
- Playwright or Vitest automated frontend test suite
- Production CORS configuration (hash routing + same-origin serving eliminates the need)

---

## Further Notes

- **ADR-0042**: FastAPI serves Vue dist; Vite is a development tool only
- **ADR-0043**: Two-view architecture (UploadView + AssessmentResultView); no dedicated Ação route
- **ADR-0044**: `POST /assess` returns authoritative per-document lifecycle metadata
- **ADR-0045**: Vuetify 3 as UI library
- **ADR-0046**: `retrieval_query` on `RetrievedChunk` — execution-level provenance, not a frontend feature
- GitHub issues: #29–#33 (implementation only; no test-only issues)
