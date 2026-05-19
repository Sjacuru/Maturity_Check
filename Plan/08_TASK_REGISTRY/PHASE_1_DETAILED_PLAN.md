# PHASE 1 — Detailed Plan (2026-05-19 to 2026-05-29)

**Rebuilt:** 2026-05-19 — now based on 28-module Architecture + MDAP  
**Remaining:** 9 working days (May 19–29, excluding May 24–25 weekend)  
**Goal:** End-to-end pipeline — case upload → hybrid retrieval → LLM evaluation → scored report (Ação 1, rough but functional)  
**Interface:** FastAPI (primary) — CLI retained as thin wrapper

---

## Honest Assessment

37 tasks, ~77 estimated hours, 9 working days. This requires ~8.5h/day of focused implementation. **Rough is acceptable — every module must function, not be polished.** If time runs short, the pipeline integrity takes priority over completeness of any individual module.

---

## Day-by-Day Plan

### DAY 1 — Mon 2026-05-19: Infrastructure + Repo Structure
**Goal:** FastAPI app running on localhost:8000 with 7 empty routers

| Task | Description | Est. |
|---|---|---|
| TASK-1-INF-01 | Extend db.py — all 10 new tables + FTS5 DDL | 3h |
| TASK-1-INF-02 | Create config.py — pydantic-settings Config | 1h |
| TASK-1-INF-03 | Create main.py — FastAPI + 7 routers + uvicorn | 2h |
| TASK-1-INF-04 | Restructure src/ per Architecture 7A — create packages, migrate files | 2h |

**Day 1 milestone:** `uvicorn src.maturity_check.main:app` starts without errors; all 7 router prefixes respond with 200/404.

---

### DAY 2 — Tue 2026-05-20: EPIC-001 Reference Store
**Goal:** Framework queryable via API; crosswalk loaded

| Task | Description | Est. |
|---|---|---|
| TASK-1-001-01 | Generalise ReferenceDocumentIngester — doc_type param, multi-doc normalizer branches | 3h |
| TASK-1-001-02 | Build CrosswalkStore — JSON load → SQLite; get_artifacts(), get_complement() | 3h |
| TASK-1-001-03 | Build FrameworkQueryService — get_action(), get_subtasks(), list_actions() | 2h |

**Day 2 milestone:** `GET /framework/actions/1` returns Ação 1 definition; `GET /framework/actions/1/subtasks` returns 6 subtasks.

---

### DAY 3 — Wed 2026-05-21: EPIC-002 Case Management
**Goal:** Case creation + document upload + validation working via API

| Task | Description | Est. |
|---|---|---|
| TASK-1-002-01 | Build CaseService — create/get/list; MissingFieldError | 2h |
| TASK-1-002-02 | Build DocumentUploadService — file storage + case_documents record | 2h |
| TASK-1-002-03 | Build DocumentValidator — readability + language + plausibility | 2h |
| TASK-1-002-04 | Build ResidencyGuard — Phase 1 pass-through | 1h |
| TASK-1-001-04 + TASK-1-002-05 | Wire /framework + /cases routers | 1h |

**Day 3 milestone:** `POST /cases` creates a case; `POST /cases/{id}/documents` accepts a PDF and returns upload status.

---

### DAY 4 — Thu 2026-05-22: EPIC-003 Document Processing
**Goal:** PDF extracted and chunked into SQLite + LanceDB

| Task | Description | Est. |
|---|---|---|
| TASK-1-003-01 | Install + validate unstructured[pdf] on 1 sample procurement PDF | 2h |
| TASK-1-003-02 | Build PDFExtractor — partition_pdf hi_res, ExtractionResult | 3h |
| TASK-1-003-03 | Build CaseDocumentChunker — element-type chunking; SQLite + LanceDB | 3h |

**Day 4 milestone:** `POST /documents/{case_id}/documents/{doc_id}/extract` produces chunks in SQLite case_chunks table.

---

### DAY 5 — Fri 2026-05-23: EPIC-003 completion + EPIC-004 retrievers
**Goal:** Intent recorder + FTS5 + dense retrieval working independently

| Task | Description | Est. |
|---|---|---|
| TASK-1-003-04 | Build EvaluationIntentRecorder | 1h |
| TASK-1-003-05 | Wire /documents router | 1h |
| TASK-1-004-01 | Build SparseRetriever — FTS5 multi-query BM25 | 3h |
| TASK-1-004-02 | Build DenseRetriever — refactor reference_search.py for case_chunks | 2h |

**Day 5 milestone:** Direct SparseRetriever and DenseRetriever calls return ranked chunk lists for a test query.

---

### DAY 6 — Mon 2026-05-26: EPIC-004 fusion + hooks
**Goal:** Full hybrid retrieval pipeline producing fused ranked list

| Task | Description | Est. |
|---|---|---|
| TASK-1-004-03 | Build RRFFusion — RRF k=60; FusedChunk output | 2h |
| TASK-1-004-04 | Build HookAssembler — pool intencao texts; deduplicate | 2h |
| TASK-1-004-05 | Build ArtifactClassifier — semantic match path; ArtifactMapping | 3h |
| TASK-1-004-07 | Build RetrievalAuditLogger | 1h |

**Day 6 milestone:** HookAssembler produces 3 query hooks for subtask 1.1; RRFFusion merges sparse + dense results correctly.

---

### DAY 7 — Tue 2026-05-27: EPIC-004 expansion + EPIC-005 evidence + LLM
**Goal:** Full retrieval pipeline complete; LLM adapter functional with Ollama

| Task | Description | Est. |
|---|---|---|
| TASK-1-004-06 | Build ExpansionController — satisficing + tier loop | 2h |
| TASK-1-004-08 | Wire /retrieval router | 1h |
| TASK-1-005-01 | Build EvidencePacketBuilder — complement resolution (OQ-002) | 2h |
| TASK-1-005-02 | Build LLMAdapter — Ollama + Groq; JSON schema; retry x3 | 4h |

**Day 7 milestone:** LLMAdapter returns structured EvaluationResponse from Ollama/Mistral for a test prompt.

---

### DAY 8 — Wed 2026-05-28: EPIC-005 evaluator + assurance + EPIC-006 persistence
**Goal:** Full evaluation cycle working for one subtask

| Task | Description | Est. |
|---|---|---|
| TASK-1-005-03 | Build SubtaskEvaluator — PT prompt; map response → EvaluationResult | 2h |
| TASK-1-005-04 | Build AssurancePass — 4 flag conditions | 2h |
| TASK-1-006-01 | Build EvaluationPersister — persistence gate; subtask_results | 2h |
| TASK-1-006-04 | Build LifecycleController — state machine; rerun | 2h |

**Day 8 milestone:** Single subtask evaluated end-to-end: evidence packet → LLM → assurance → persisted result.

---

### DAY 9 — Thu 2026-05-29: EPIC-006 scoring + report + Pipeline Orchestrator + integration test
**Goal:** Full pipeline end-to-end for Ação 1 (all 6 subtasks)

| Task | Description | Est. |
|---|---|---|
| TASK-1-006-02 | Build ScoringEngine — FR-013 formula; action_scores | 2h |
| TASK-1-006-03 | Build ReportGenerator — JSON + Markdown summary (PT) | 2h |
| TASK-1-006-05 | Wire /reports router | 1h |
| TASK-1-INT-01 | Build Pipeline Orchestrator — BackgroundTask; chain all modules | 4h |
| TASK-1-INT-02 | End-to-end test — upload case doc; run pipeline; verify report | 3h |

**Day 9 milestone (Phase 1 complete):** Upload a PDF, trigger evaluation for Ação 1, receive a JSON + Markdown report with presence/quality scores for all 6 subtasks.

---

## Critical Path

```
INF-01 → INF-02 → INF-03 → INF-04
               ↓                ↓
         001-01/02/03      002-01/02/03/04
               ↓                ↓
         003-01/02/03 ←────────┘
               ↓
         004-01, 004-04 (parallel: 004-01 + 004-02)
               ↓
         004-03 (RRFFusion)
               ↓
         004-06 (ExpansionController)
               ↓
         005-01 → 005-02 → 005-03 → 005-04
               ↓
         006-01 → 006-02 → 006-03
               ↓
         INT-01 → INT-02
```

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| unstructured[pdf] installation fails (corporate proxy) | Medium | High | Pre-install on Day 1; use pip-system-certs |
| Ollama/Mistral JSON output unreliable | High | Medium | Add retry x3; log raw responses; fallback to Groq |
| unstructured OCR too slow for test | Medium | Medium | Use hi_res only on flagged pages; accept slow for Phase 1 |
| 9 days insufficient | High | High | Prioritise pipeline integrity over module polish; defer annotations |
| LanceDB case_chunks table schema issues | Low | High | Validate schema on Day 4 before chunking |

---

## Phase 1 Definition of Done

- [ ] FastAPI app starts on localhost:8000
- [ ] Case can be created and document uploaded via API
- [ ] PDF extracted and chunked (unstructured, hi_res OCR)
- [ ] Hybrid retrieval (FTS5 + LanceDB + RRF) returns ranked evidence for Ação 1 subtasks
- [ ] LLM evaluates all 6 Ação 1 subtasks against retrieved evidence
- [ ] AssurancePass validates outputs; flags raised where applicable
- [ ] ScoringEngine produces FR-013 4-component score
- [ ] ReportGenerator produces JSON + Markdown summary in Portuguese
- [ ] Full pipeline runs as a background task triggered by a single API call
