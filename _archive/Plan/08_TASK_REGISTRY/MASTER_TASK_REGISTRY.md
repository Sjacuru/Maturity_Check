# MASTER TASK REGISTRY — M5D Evaluation System

**Rebuilt:** 2026-05-19  
**Basis:** MDAP (28 modules, 7 EPICs) + Architecture document  
**Format:** TASK-{PHASE}-{AREA}-{SEQ}

Status: `[ ]` pending · `[→]` in progress · `[x]` complete · `[!]` blocked

---

## PHASE 1 — Infrastructure (INF)

| Task ID | Description | Module | PRD | Est. | Status | Depends On |
|---|---|---|---|---|---|---|
| TASK-1-INF-01 | Extend `db.py` — add tables: crosswalk_artifacts, cases, case_documents, case_chunks, case_chunks_fts, evaluation_runs, subtask_results, action_scores, retrieval_logs, annotations | — | FR-003,014 | 3h | [ ] | — |
| TASK-1-INF-02 | Create `config.py` — pydantic-settings Config (LLM_PROVIDER, API keys, RESIDENCY_POLICY, data paths) | — | NFR-008 | 1h | [ ] | — |
| TASK-1-INF-03 | Create `main.py` — FastAPI app, 7 routers registered, uvicorn entrypoint, BackgroundTasks setup | — | NFR-005 | 2h | [ ] | INF-02 |
| TASK-1-INF-04 | Restructure `src/` — create packages reference/, cases/, documents/, retrieval/, evaluation/, reporting/, review/; migrate existing files per Architecture 7A | — | NFR-005 | 2h | [ ] | INF-03 |

---

## PHASE 1 — EPIC-001: Reference Store

| Task ID | Description | Module | PRD | Est. | Status | Depends On |
|---|---|---|---|---|---|---|
| TASK-1-001-01 | Generalise ReferenceDocumentIngester — `doc_type` param, normalizer branch for Rio Manual and TCDF IN | MODULE-001-01 | FR-001 | 3h | [ ] | INF-04 |
| TASK-1-001-02 | Build CrosswalkStore — load JSON → crosswalk_artifacts; `get_artifacts(subtask_id)`, `get_complement()` | MODULE-001-02 | FR-001, FR-008A | 3h | [ ] | INF-01 |
| TASK-1-001-03 | Build FrameworkQueryService — `get_action()`, `get_subtasks()`, `list_actions()`, `get_coverage()` | MODULE-001-03 | FR-001 | 2h | [ ] | TASK-1-001-01 |
| TASK-1-001-04 | Wire /framework router — ingest, crosswalk/load, actions endpoints | — | FR-001 | 1h | [ ] | TASK-1-001-03 |

---

## PHASE 1 — EPIC-002: Case Management

| Task ID | Description | Module | PRD | Est. | Status | Depends On |
|---|---|---|---|---|---|---|
| TASK-1-002-01 | Build CaseService — create/get/list; UUID generation; MissingFieldError | MODULE-002-01 | FR-003 | 2h | [ ] | INF-01 |
| TASK-1-002-02 | Build DocumentUploadService — PDF storage to data/cases/{case_id}/; case_documents record; per-file status | MODULE-002-02 | FR-004 | 2h | [ ] | TASK-1-002-01 |
| TASK-1-002-03 | Build DocumentValidator — readability (PyMuPDF probe), language detection (langdetect), plausibility vocab check | MODULE-002-03 | FR-005, NFR-001 | 2h | [ ] | TASK-1-002-02 |
| TASK-1-002-04 | Build ResidencyGuard — Phase 1 always-allow pass-through; config-driven | MODULE-002-04 | NFR-008 | 1h | [ ] | INF-02 |
| TASK-1-002-05 | Wire /cases router — POST /cases, POST /documents, POST /validate | — | FR-003–005 | 1h | [ ] | TASK-1-002-03 |

---

## PHASE 1 — EPIC-003: Document Processing

| Task ID | Description | Module | PRD | Est. | Status | Depends On |
|---|---|---|---|---|---|---|
| TASK-1-003-01 | Install + validate unstructured[pdf] — test on 1 real procurement PDF; confirm element types | MODULE-003-01 | FR-006 | 2h | [ ] | INF-04 |
| TASK-1-003-02 | Build PDFExtractor — partition_pdf(hi_res, languages=["por"]); return ExtractionResult with DocumentElements | MODULE-003-01 | FR-006 | 3h | [ ] | TASK-1-003-01 |
| TASK-1-003-03 | Build CaseDocumentChunker — Table standalone, Title boundary, NarrativeText 800-char cap; persist SQLite + LanceDB | MODULE-003-02 | FR-006 | 3h | [ ] | TASK-1-003-02 |
| TASK-1-003-04 | Build EvaluationIntentRecorder — validate case+action; create evaluation_runs record | MODULE-003-03 | FR-007 | 1h | [ ] | TASK-1-001-03, TASK-1-002-01 |
| TASK-1-003-05 | Wire /documents router — extract, chunks, evaluate-intent endpoints | — | FR-006–007 | 1h | [ ] | TASK-1-003-04 |

---

## PHASE 1 — EPIC-004: Retrieval Engine

| Task ID | Description | Module | PRD | Est. | Status | Depends On |
|---|---|---|---|---|---|---|
| TASK-1-004-01 | Build SparseRetriever — FTS5 DDL (unicode61, remove_diacritics 2); multi-query BM25 union | MODULE-004-03 | FR-008D | 3h | [ ] | INF-01, TASK-1-003-03 |
| TASK-1-004-02 | Build DenseRetriever — refactor reference_search.py for case_chunks; model singleton reuse | MODULE-004-04 | FR-008D | 2h | [ ] | TASK-1-003-03 |
| TASK-1-004-03 | Build RRFFusion — pure-Python RRF k=60; FusedChunk with sparse_rank + dense_rank | MODULE-004-05 | FR-008D | 2h | [ ] | TASK-1-004-01, TASK-1-004-02 |
| TASK-1-004-04 | Build HookAssembler — pool intencao texts from CrosswalkStore + M5D subtask text; deduplicate | MODULE-004-02 | FR-008A | 2h | [ ] | TASK-1-001-02, TASK-1-001-03 |
| TASK-1-004-05 | Build ArtifactClassifier — Phase 1: semantic match only (filename_candidates empty); ArtifactMapping output | MODULE-004-01 | FR-008 | 3h | [ ] | TASK-1-004-02, TASK-1-001-03 |
| TASK-1-004-06 | Build ExpansionController — satisficing (confidence >= 0.90, Direta+Alto); tier loop Direta→Indireta→Contextual | MODULE-004-06 | FR-008B, FR-008C | 2h | [ ] | TASK-1-004-03, TASK-1-001-02 |
| TASK-1-004-07 | Build RetrievalAuditLogger — write retrieval_logs; return log_id | MODULE-004-07 | FR-014A | 1h | [ ] | INF-01 |
| TASK-1-004-08 | Wire /retrieval — retrieval log inspection endpoint | — | FR-014A | 1h | [ ] | TASK-1-004-07 |

---

## PHASE 1 — EPIC-005: Evaluation Engine

| Task ID | Description | Module | PRD | Est. | Status | Depends On |
|---|---|---|---|---|---|---|
| TASK-1-005-01 | Build EvidencePacketBuilder — assemble EvidencePacket; resolve complement_text_pt per OQ-002 | MODULE-005-01 | FR-009, FR-021 | 2h | [ ] | TASK-1-001-02, TASK-1-004-07 |
| TASK-1-005-02 | Build LLMAdapter — Ollama + Groq backends; JSON schema enforcement; retry x3; ResidencyGuard check | MODULE-005-02 | FR-009, NFR-008 | 4h | [ ] | TASK-1-002-04 |
| TASK-1-005-03 | Build SubtaskEvaluator — PT prompt construction; call LLMAdapter; map response → EvaluationResult | MODULE-005-03 | FR-009–012 | 2h | [ ] | TASK-1-005-01, TASK-1-005-02 |
| TASK-1-005-04 | Build AssurancePass — 4 flag conditions (MISSING_DOCUMENT, MISSING_INFORMATION, UNCERTAINTY, CONFLICTING_INFORMATION heuristic) | MODULE-005-04 | FR-015, FR-021 | 2h | [ ] | TASK-1-005-03, TASK-1-004-05 |

---

## PHASE 1 — EPIC-006: Persistence + Reporting

| Task ID | Description | Module | PRD | Est. | Status | Depends On |
|---|---|---|---|---|---|---|
| TASK-1-006-01 | Build EvaluationPersister — AssuranceOutcome persistence gate; write subtask_results with full traceability | MODULE-006-01 | FR-014, NFR-003 | 2h | [ ] | TASK-1-005-04 |
| TASK-1-006-02 | Build ScoringEngine — FR-013 formula verbatim (40/20/20/20); 1/N default weights; write action_scores | MODULE-006-02 | FR-002, FR-013 | 2h | [ ] | TASK-1-006-01 |
| TASK-1-006-03 | Build ReportGenerator — JSON (scores+flags+evidence) + Markdown summary (PT); no uncited claims | MODULE-006-03 | FR-018, NFR-001, NFR-004 | 2h | [ ] | TASK-1-006-02 |
| TASK-1-006-04 | Build LifecycleController — state machine pending→running→paused→completed/failed; rerun | MODULE-006-05 | FR-017, FR-019 | 2h | [ ] | TASK-1-003-04 |
| TASK-1-006-05 | Wire /reports router — GET report, lifecycle, rerun endpoints | — | FR-017–019 | 1h | [ ] | TASK-1-006-03 |

---

## PHASE 1 — Integration

| Task ID | Description | Module | PRD | Est. | Status | Depends On |
|---|---|---|---|---|---|---|
| TASK-1-INT-01 | Build Pipeline Orchestrator — FastAPI BackgroundTask chaining modules 004-01→006-03 per run; LifecycleController state management | — | All | 4h | [ ] | TASK-1-006-04 |
| TASK-1-INT-02 | End-to-end test — upload Ação 1 case doc; run full pipeline; verify JSON + Markdown report produced | — | All | 3h | [ ] | TASK-1-INT-01 |

---

## PHASE 1 TOTALS

| Area | Tasks | Est. Hours |
|---|---|---|
| Infrastructure | 4 | 8h |
| EPIC-001 | 4 | 9h |
| EPIC-002 | 5 | 8h |
| EPIC-003 | 5 | 10h |
| EPIC-004 | 8 | 16h |
| EPIC-005 | 4 | 10h |
| EPIC-006 | 5 | 9h |
| Integration | 2 | 7h |
| **TOTAL** | **37** | **~77h** |

---

## PHASE 2 TASKS (post-2026-05-29)

| Task ID | Description | Module | Est. | Status |
|---|---|---|---|---|
| TASK-2-001-01 | Ingest Rio Manual PDF → reference_chunks (doc_id: rio_manual_v1) | MODULE-001-01 | 4h | [ ] |
| TASK-2-001-02 | Ingest TCDF IN PDF → reference_chunks (doc_id: tcdf_in_v1) | MODULE-001-01 | 4h | [ ] |
| TASK-2-001-03 | Author crosswalk templates for Ações 2–46 | MODULE-001-02 | 40h | [ ] |
| TASK-2-003-01 | Improve PDFExtractor — unstructured hi_res tuning on real procurement corpus | MODULE-003-01 | 8h | [ ] |
| TASK-2-004-01 | Add exact filename + approx title classification to ArtifactClassifier | MODULE-004-01 | 3h | [ ] |
| TASK-2-004-02 | Pilot calibration — retrieval_floor_stage2, hit/weak/none cutoffs; measure latency (NFR-006) | MODULE-004-06 | 10h | [ ] |
| TASK-2-005-01 | Replace CONFLICTING_INFORMATION heuristic with LLM judge | MODULE-005-04 | 4h | [ ] |
| TASK-2-006-01 | Build AnnotationService (MODULE-006-04) | MODULE-006-04 | 2h | [ ] |
| TASK-2-007-01 | Build ReviewAccessController — token validation, PERSONA-002 read-only | MODULE-007-01 | 3h | [ ] |
| TASK-2-007-02 | Build SuperiorAnnotationService | MODULE-007-02 | 2h | [ ] |
| TASK-2-EXP-01 | Expand evaluation pipeline to all 46 Ações | — | 20h | [ ] |
| TASK-2-FE-01 | Vue.js 3 frontend — case creation, upload, run trigger, report view | — | 60h | [ ] |
| TASK-2-FE-02 | PostgreSQL migration (db.py → Alembic + asyncpg) | — | 10h | [ ] |
| TASK-2-FE-03 | Auth middleware (Phase 2 access model, OQ-003) | — | 8h | [ ] |
| TASK-2-FE-04 | Deployment configuration (nginx + uvicorn workers) | — | 4h | [ ] |

---

## PRD Traceability

| PRD ID | Phase 1 Tasks | Phase 2 Tasks | Status |
|---|---|---|---|
| FR-001 | TASK-1-001-01..04 | TASK-2-001-01..03 | [ ] |
| FR-002 | TASK-1-006-02 | — | [ ] |
| FR-003 | TASK-1-002-01 | — | [ ] |
| FR-004 | TASK-1-002-02 | — | [ ] |
| FR-005 | TASK-1-002-03 | — | [ ] |
| FR-006 | TASK-1-003-01..03 | TASK-2-003-01 | [ ] |
| FR-007 | TASK-1-003-04 | — | [ ] |
| FR-008 | TASK-1-004-05 | TASK-2-004-01 | [ ] |
| FR-008A | TASK-1-004-04 | — | [ ] |
| FR-008B | TASK-1-004-06 | — | [ ] |
| FR-008C | TASK-1-004-06 | TASK-2-004-02 | [ ] |
| FR-008D | TASK-1-004-01..03 | — | [ ] |
| FR-009 | TASK-1-005-03 | — | [ ] |
| FR-010 | TASK-1-005-03 | — | [ ] |
| FR-011 | TASK-1-005-03 | — | [ ] |
| FR-012 | TASK-1-005-03 | — | [ ] |
| FR-013 | TASK-1-006-02 | — | [ ] |
| FR-014 | TASK-1-006-01 | — | [ ] |
| FR-014A | TASK-1-004-07 | — | [ ] |
| FR-015 | TASK-1-005-04 | TASK-2-005-01 | [ ] |
| FR-016 | — | TASK-2-006-01 | deferred |
| FR-017 | TASK-1-006-04 | — | [ ] |
| FR-018 | TASK-1-006-03 | — | [ ] |
| FR-019 | TASK-1-006-04 | — | [ ] |
| FR-020 | — | TASK-2-007-01..02 | deferred |
| FR-021 | TASK-1-005-04 | — | [ ] |
| NFR-001 | TASK-1-005-03, 006-03 | — | [ ] |
| NFR-002 | TASK-1-005-03 | — | [ ] |
| NFR-003 | TASK-1-006-01 | — | [ ] |
| NFR-004 | TASK-1-006-03 | — | [ ] |
| NFR-005 | TASK-1-INF-03..04 | — | [ ] |
| NFR-006 | — | TASK-2-004-02 | deferred |
| NFR-007 | TASK-1-001-02 | — | [ ] |
| NFR-008 | TASK-1-002-04 | TASK-2-FE-03 | [ ] |
