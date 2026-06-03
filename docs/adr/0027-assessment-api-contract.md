# Assessment API contract: route set, file upload ingress, synchronous execution

## Route set (Phase 1)

Five routes constitute the complete Phase 1 API surface:

```
POST /cases/{process_number}/assess
GET  /cases/{process_number}/evaluations
GET  /cases/{process_number}/evaluations/{acao_id}
POST /cases/{process_number}/evaluations/{acao_id}/review
GET  /cases/{process_number}/evaluations/{acao_id}/review
```

No additional routes are introduced until a concrete workflow requires them.

## Document ingress: multipart file upload

`POST /cases/{process_number}/assess` accepts Document Artifacts as `multipart/form-data`. The Auditor may upload one or more PDFs in a single request. The orchestration service stores each file to disk before passing its path to `extract_document()`.

Path-reference ingress (sending local file paths in a JSON body) was rejected: it leaks filesystem layout into the API contract, couples the server to the caller's filesystem, and does not match the actual business workflow of an Auditor submitting documents for assessment.

## Synchronous execution

`POST /cases/{process_number}/assess` blocks until the full pipeline (Store → Extract → Index → Retrieve → Evaluate) completes for all submitted documents and all in-scope Ações, then returns a success response. No job model, polling endpoint, background task infrastructure, or assessment-state persistence is introduced.

This decision is based on:
- Phase 1 evaluates only Ação 1 — one LLM call per Case submission.
- The workflow is single-user and deliberate — the Auditor submits files and waits for results.
- No demonstrated need for concurrent work during assessment.

## Response contract design

The response to `POST /cases/{process_number}/assess` must not expose implementation details (execution mechanism, job ID, internal timings). It signals assessment completion as an outcome: the Auditor can now retrieve EvaluationResults via the GET routes. This keeps the contract narrow enough that the execution model can be changed to asynchronous in the future without altering the route or its success semantics.

## Considered options

- **Asynchronous (202 + polling):** Returns immediately with a job ID; Auditor polls a status endpoint. Rejected for Phase 1: adds job state table, background task runner, and polling complexity for a single LLM call in a single-user local workflow. Deferred until a demonstrated requirement exists (multi-Ação assessment, long-running workloads, concurrent users).
- **Path-reference ingress:** Sends local file paths in a JSON body. Rejected: leaks filesystem concerns into the API, not portable, not aligned with the business workflow.
