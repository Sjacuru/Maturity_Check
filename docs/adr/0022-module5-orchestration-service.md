# Module 5 owns orchestration via an application-service layer

Module 5 owns the end-to-end assessment workflow (Document Artifact → extraction → retrieval → evaluation → EvaluationResult). Orchestration lives in an application-service component (e.g., `AssessmentService.run_assessment()` or a standalone `run_assessment()` function), not in FastAPI route handlers. FastAPI is a presentation layer that invokes the service; a future CLI may invoke the same service without code duplication. No separate orchestration runner is introduced in Phase 1. No `EvaluationResult` serialisation contract is introduced solely to support orchestration — the service returns the live Python object.

## Considered Options

- **Route-level orchestration:** FastAPI handlers directly call `extract_document()` → `index()` → `retrieve_for_acao()` → `evaluate()`. Simpler initially, but couples the pipeline to HTTP concerns and forces duplication if a CLI entry point is added later.
- **Pre-built EvaluationResult boundary:** A separate CLI runner orchestrates Modules 1–4 and hands a serialised `EvaluationResult` to a display-only API. Adds a serialisation contract and a second entry point with no domain justification in Phase 1.

## Consequences

- The orchestration service becomes the single integration point for Modules 1–4.
- FastAPI routes stay thin: validate HTTP input, call the service, serialise the response.
- A Phase 2 CLI entry point reuses the service with zero orchestration duplication.
- The service boundary is where `configure_llm()` and `configure()` (retrieval) are called — the API layer never touches module-level configuration directly.
