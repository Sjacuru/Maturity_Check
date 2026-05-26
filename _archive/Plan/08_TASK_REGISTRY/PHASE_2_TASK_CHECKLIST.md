# PHASE 2 TASK CHECKLIST

**Rebuilt:** 2026-05-19 | **Duration:** 2026-05-29 to 2026-11-20 | **26 weeks**

`[ ]` pending · `[→]` in progress · `[x]` complete

---

## Block 1 — Stabilise Phase 1 Pipeline (Weeks 1–3)
- [ ] TASK-2-003-01 — Improve PDFExtractor (real procurement PDF corpus)
- [ ] TASK-2-004-01 — ArtifactClassifier exact/title methods
- [ ] TASK-2-004-02 — Pilot calibration (retrieval thresholds + latency)
- [ ] TASK-2-005-01 — AssurancePass LLM judge (replace heuristic)
- [ ] TASK-2-006-01 — Build AnnotationService (MODULE-006-04)
- [ ] B1-STAB-01 — Integration tests: 3+ real Ação 1 evaluations
- [ ] B1-STAB-02 — Error handling audit + logging improvements

## Block 2 — Reference Document Expansion (Weeks 4–7)
- [ ] TASK-2-001-01 — Ingest Rio Manual PDF
- [ ] TASK-2-001-02 — Ingest TCDF IN PDF
- [ ] B2-VAL-01 — Validate coverage of new reference docs
- [ ] B2-VAL-02 — Retrieval tests for Rio Manual + TCDF IN
- [ ] B2-CROSS-01 — Crosswalk templates Ações 2–10

## Block 3 — Ações 2–20 (Weeks 8–12)
- [ ] TASK-2-001-03a — Crosswalk templates Ações 11–20
- [ ] TASK-2-EXP-01a — Pipeline expansion to Ações 2–20
- [ ] B3-TEST-01 — Full case evaluations Ações 1–20
- [ ] B3-SCORE-01 — Stage-level aggregation validated

## Block 4 — Ações 21–46 + Full Framework (Weeks 13–17)
- [ ] TASK-2-001-03b — Crosswalk templates Ações 21–46
- [ ] TASK-2-EXP-01b — Pipeline expansion to Ações 21–46
- [ ] B4-TEST-01 — Full case evaluations all 46 Ações
- [ ] B4-REPORT-01 — Full M5D report (all stages + dimensions)

## Block 5 — Web UI Vue.js 3 (Weeks 18–21)
- [ ] TASK-2-FE-01a — Case creation + document upload screens
- [ ] TASK-2-FE-01b — Run trigger + progress polling
- [ ] TASK-2-FE-01c — Report display (scores, flags, citations)
- [ ] TASK-2-FE-01d — Auditor annotation UI
- [ ] B5-UX-01 — UX review + iteration with domain expert

## Block 6 — Review Access + Auth (Weeks 22–24)
- [ ] TASK-2-007-01 — ReviewAccessController (PERSONA-002)
- [ ] TASK-2-007-02 — SuperiorAnnotationService
- [ ] TASK-2-FE-03 — Auth middleware (pending OQ-003 sign-off)
- [ ] B6-LEGAL-01 — NFR-008 compliance review

## Block 7 — Production Deployment (Weeks 25–26)
- [ ] TASK-2-FE-02 — PostgreSQL migration (Alembic + asyncpg)
- [ ] TASK-2-FE-04 — nginx + uvicorn deployment
- [ ] B7-LOAD-01 — Load test (5 concurrent users)
- [ ] B7-DOCS-01 — Operational docs + auditor manual (PT)
- [ ] B7-SIGN-01 — Stakeholder sign-off demo

---

## Block Milestones

| Block | End Date | Milestone |
|---|---|---|
| 1 | 2026-06-19 | Ação 1 reliable on real docs; latency measured |
| 2 | 2026-07-17 | All 3 reference docs searchable; crosswalk Ações 1–10 |
| 3 | 2026-08-21 | PII stage (20 Ações) evaluable |
| 4 | 2026-09-25 | All 46 Ações evaluable; full report |
| 5 | 2026-10-23 | Auditor UI functional in browser |
| 6 | 2026-11-13 | PERSONA-002 access; auth enabled |
| 7 | 2026-11-20 | Production deployment; stakeholder sign-off |
