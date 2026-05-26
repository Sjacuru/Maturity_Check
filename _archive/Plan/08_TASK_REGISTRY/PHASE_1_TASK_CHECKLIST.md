# PHASE 1 TASK CHECKLIST

**Rebuilt:** 2026-05-19 | **Deadline:** 2026-05-29 | **Total:** 37 tasks

`[ ]` pending · `[→]` in progress · `[x]` complete

---

## Infrastructure
- [ ] TASK-1-INF-01 — Extend db.py (10 new tables + FTS5)
- [ ] TASK-1-INF-02 — Create config.py (pydantic-settings)
- [ ] TASK-1-INF-03 — Create main.py (FastAPI + 7 routers)
- [ ] TASK-1-INF-04 — Restructure src/ per Architecture 7A

## EPIC-001 — Reference Store
- [ ] TASK-1-001-01 — Generalise ReferenceDocumentIngester (multi-doc)
- [ ] TASK-1-001-02 — Build CrosswalkStore
- [ ] TASK-1-001-03 — Build FrameworkQueryService
- [ ] TASK-1-001-04 — Wire /framework router

## EPIC-002 — Case Management
- [ ] TASK-1-002-01 — Build CaseService
- [ ] TASK-1-002-02 — Build DocumentUploadService
- [ ] TASK-1-002-03 — Build DocumentValidator
- [ ] TASK-1-002-04 — Build ResidencyGuard (Phase 1 pass-through)
- [ ] TASK-1-002-05 — Wire /cases router

## EPIC-003 — Document Processing
- [ ] TASK-1-003-01 — Install + validate unstructured[pdf]
- [ ] TASK-1-003-02 — Build PDFExtractor
- [ ] TASK-1-003-03 — Build CaseDocumentChunker
- [ ] TASK-1-003-04 — Build EvaluationIntentRecorder
- [ ] TASK-1-003-05 — Wire /documents router

## EPIC-004 — Retrieval Engine
- [ ] TASK-1-004-01 — Build SparseRetriever (FTS5 BM25)
- [ ] TASK-1-004-02 — Build DenseRetriever (LanceDB)
- [ ] TASK-1-004-03 — Build RRFFusion (k=60)
- [ ] TASK-1-004-04 — Build HookAssembler
- [ ] TASK-1-004-05 — Build ArtifactClassifier (semantic path)
- [ ] TASK-1-004-06 — Build ExpansionController
- [ ] TASK-1-004-07 — Build RetrievalAuditLogger
- [ ] TASK-1-004-08 — Wire /retrieval router

## EPIC-005 — Evaluation Engine
- [ ] TASK-1-005-01 — Build EvidencePacketBuilder
- [ ] TASK-1-005-02 — Build LLMAdapter (Ollama + Groq)
- [ ] TASK-1-005-03 — Build SubtaskEvaluator
- [ ] TASK-1-005-04 — Build AssurancePass

## EPIC-006 — Persistence + Reporting
- [ ] TASK-1-006-01 — Build EvaluationPersister
- [ ] TASK-1-006-02 — Build ScoringEngine (FR-013)
- [ ] TASK-1-006-03 — Build ReportGenerator (JSON + Markdown PT)
- [ ] TASK-1-006-04 — Build LifecycleController
- [ ] TASK-1-006-05 — Wire /reports router

## Integration
- [ ] TASK-1-INT-01 — Build Pipeline Orchestrator (BackgroundTask)
- [ ] TASK-1-INT-02 — End-to-end test (Ação 1 full pipeline)

---

## Daily Targets

| Day | Date | Target Tasks | Milestone |
|---|---|---|---|
| 1 | Mon 2026-05-19 | INF-01..04 | FastAPI starts, 7 routers respond |
| 2 | Tue 2026-05-20 | 001-01..03 | /framework/actions/1 returns data |
| 3 | Wed 2026-05-21 | 002-01..05 + 001-04 | Case creation + upload working |
| 4 | Thu 2026-05-22 | 003-01..03 | PDF chunked in SQLite |
| 5 | Fri 2026-05-23 | 003-04..05 + 004-01..02 | FTS5 + dense search return results |
| 6 | Mon 2026-05-26 | 004-03..05 + 004-07 | Fused ranked list from hooks |
| 7 | Tue 2026-05-27 | 004-06 + 004-08 + 005-01..02 | LLMAdapter returns EvaluationResponse |
| 8 | Wed 2026-05-28 | 005-03..04 + 006-01 + 006-04 | Single subtask evaluated + persisted |
| 9 | Thu 2026-05-29 | 006-02..03 + 006-05 + INT-01..02 | Full pipeline end-to-end ✓ |
