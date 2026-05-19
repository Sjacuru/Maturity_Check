# PHASE 2 — Detailed Plan (2026-05-29 to 2026-11-20)

**Rebuilt:** 2026-05-19 — based on 28-module Architecture + MDAP  
**Duration:** 26 weeks (~1000h)  
**Goal:** All 46 M5D Ações functional + Web UI + production deployment

---

## Block 1 — Weeks 1–3 (2026-05-29 to 2026-06-19): Stabilise Phase 1 Pipeline

**Objective:** Harden the rough Phase 1 implementation; validate on real procurement PDFs; pilot calibration.

| Task | Description | Est. |
|---|---|---|
| TASK-2-003-01 | Improve PDFExtractor — test on real procurement corpus (10+ documents); tune unstructured parameters | 8h |
| TASK-2-004-01 | Add exact filename + approx title methods to ArtifactClassifier | 3h |
| TASK-2-004-02 | Pilot calibration — retrieval_floor_stage2 (initial band 0.35–0.50); hit/weak/none disposition cutoffs; latency measurement (NFR-006) | 10h |
| TASK-2-005-01 | Replace CONFLICTING_INFORMATION heuristic with LLM judge in AssurancePass | 4h |
| TASK-2-006-01 | Build AnnotationService (MODULE-006-04) — deferred from Phase 1 | 2h |
| B1-STAB-01 | Integration tests — 3+ real Ação 1 case evaluations end-to-end | 8h |
| B1-STAB-02 | Error handling audit — review all module failure modes; improve logging | 4h |

**Block 1 milestone:** Ação 1 pipeline reliable on real documents; latency measured and recorded.

---

## Block 2 — Weeks 4–7 (2026-06-20 to 2026-07-17): Reference Document Expansion

**Objective:** Ingest Rio Manual and TCDF IN; validate all reference searches.

| Task | Description | Est. |
|---|---|---|
| TASK-2-001-01 | Ingest Rio Manual PDF → reference_chunks (doc_id: rio_manual_v1) | 4h |
| TASK-2-001-02 | Ingest TCDF IN PDF → reference_chunks (doc_id: tcdf_in_v1) | 4h |
| B2-VAL-01 | Validate Rio Manual + TCDF IN chunk coverage and heading hierarchy | 4h |
| B2-VAL-02 | Run retrieval_test.py equivalents for Rio Manual and TCDF IN sections | 4h |
| B2-CROSS-01 | Author crosswalk templates for Ações 2–10 | 16h |

**Block 2 milestone:** All 3 reference documents searchable; crosswalk for Ações 1–10.

---

## Block 3 — Weeks 8–12 (2026-07-18 to 2026-08-21): Ações 2–20 Expansion

**Objective:** Evaluate all Ações in PII stage (Proposta Inicial de Investimento).

| Task | Description | Est. |
|---|---|---|
| TASK-2-001-03a | Author crosswalk templates for Ações 11–20 | 20h |
| TASK-2-EXP-01a | Expand evaluation pipeline to Ações 2–20 | 8h |
| B3-TEST-01 | 2 full case evaluations covering Ações 1–20 | 12h |
| B3-SCORE-01 | Validate FR-013 scoring formula at action + stage level | 4h |

**Block 3 milestone:** PII (20 Ações) fully evaluable; stage-level aggregation works.

---

## Block 4 — Weeks 13–17 (2026-08-22 to 2026-09-25): Ações 21–46 + Full Framework

**Objective:** Complete all 46 Ações; all 3 stages evaluable.

| Task | Description | Est. |
|---|---|---|
| TASK-2-001-03b | Author crosswalk templates for Ações 21–46 | 60h |
| TASK-2-EXP-01b | Expand evaluation pipeline to Ações 21–46 | 12h |
| B4-TEST-01 | 2 full case evaluations covering all 46 Ações | 16h |
| B4-REPORT-01 | Full M5D report (all stages + dimensions) | 8h |

**Block 4 milestone:** All 46 Ações evaluable; full M5D report generated.

---

## Block 5 — Weeks 18–21 (2026-09-26 to 2026-10-23): Web UI (Vue.js 3)

**Objective:** Functional auditor UI replacing direct API calls.

| Task | Description | Est. |
|---|---|---|
| TASK-2-FE-01a | Vue.js setup + case creation + document upload screens | 20h |
| TASK-2-FE-01b | Run trigger + progress polling UI | 12h |
| TASK-2-FE-01c | Report display — scores, flags, evidence citations | 20h |
| TASK-2-FE-01d | Annotation UI (PERSONA-001) | 8h |
| B5-UX-01 | UX review with domain expert (auditor); iterate | 8h |

**Block 5 milestone:** Auditor can complete full Ação 1 evaluation cycle via browser.

---

## Block 6 — Weeks 22–24 (2026-10-24 to 2026-11-13): Review Access + Auth

**Objective:** PERSONA-002 access; production-ready auth.

| Task | Description | Est. |
|---|---|---|
| TASK-2-007-01 | Build ReviewAccessController — token validation, PERSONA-002 read-only | 3h |
| TASK-2-007-02 | Build SuperiorAnnotationService | 2h |
| TASK-2-FE-03 | Auth middleware — OQ-003 access model (stakeholder sign-off required first) | 8h |
| B6-LEGAL-01 | NFR-008 compliance review for production posture | 4h |

**Block 6 milestone:** PERSONA-002 can view and annotate reports; auth enabled.

---

## Block 7 — Weeks 25–26 (2026-11-14 to 2026-11-20): Production Deployment

**Objective:** System deployed on target server; stable.

| Task | Description | Est. |
|---|---|---|
| TASK-2-FE-02 | PostgreSQL migration (Alembic + asyncpg) | 10h |
| TASK-2-FE-04 | Deployment — nginx + uvicorn workers; systemd service | 4h |
| B7-LOAD-01 | Load test — 5 concurrent users, 3 simultaneous evaluation runs | 4h |
| B7-DOCS-01 | Operational documentation — deployment guide + auditor manual (PT) | 8h |
| B7-SIGN-01 | Stakeholder sign-off — demo to bosses + professor | 4h |

**Block 7 milestone:** System in production; stakeholder sign-off obtained.

---

## Phase 2 Definition of Done

- [ ] All 46 Ações evaluable end-to-end
- [ ] Rio Manual + TCDF IN ingested and searchable
- [ ] Crosswalk templates for all 46 Ações authored
- [ ] Vue.js UI functional for full auditor workflow
- [ ] PERSONA-002 review access with auth
- [ ] PostgreSQL backing database deployed
- [ ] Latency measured and within acceptable range (NFR-006 SLO defined from pilot data)
- [ ] CONFLICTING_INFORMATION detection via LLM judge (not heuristic)
- [ ] NFR-008 legal compliance reviewed and documented
- [ ] Stakeholder sign-off from bosses + professor

---

## Deferred Items (require external inputs)

| Item | Blocked on | Expected |
|---|---|---|
| FR-002 custom weights | Domain expert input | Before Block 4 |
| NFR-006 latency SLO | Pilot data (Block 1) | After Block 1 |
| NFR-008 production compliance | Legal review | Before Block 6 |
| OQ-003 access model | Stakeholder sign-off | Before Block 6 |
