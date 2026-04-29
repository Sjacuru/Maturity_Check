# PHASE 2 TASK CHECKLIST / CHECKLIST DE TAREFAS PHASE 2

**Duration:** 29 May — 20 November 2026 (26 weeks, 7 blocks)  
**Total Tasks:** ~120  
**Total Hours:** ~1000 (40h/week)  
**Language / Idioma:** Bilingual PT + EN

---

## 📋 STRUCTURE / ESTRUTURA

Phase 2 is organized into 7 **Blocks**, each lasting ~4 weeks:
- **Block 1 (Weeks 1-4):** Actions 2–5 + Tiered Expansion
- **Block 2 (Weeks 5-8):** Actions 6–10 + Satisficing Logic
- **Block 3 (Weeks 9-12):** Actions 11–15 + UNCERTAINTY Flags
- **Block 4 (Weeks 13-16):** Actions 16–30 + Batch Evaluation
- **Block 5 (Weeks 17-20):** Actions 31–40 + Web UI Development
- **Block 6 (Weeks 21-24):** Actions 41–46 + Groq API Integration
- **Block 7 (Weeks 25-26):** Performance Tuning + Deployment to Rio Server

---

## BLOCK 1: Actions 2–5 Implementation (Weeks 1–4: May 29 — Jun 25)

**Hours Planned / Horas Planejadas:** 120–140h (4 weeks × 40h/week)  
**Actions / Ações:** 2, 3, 4, 5

| ID | Task / Tarefa | Status | Evidence | Hours | Notes / Notas |
|----|----|--------|----------|-------|-------|
| T2.1.1 | Analyze & Extract Ação 2 Crosswalk | ☐ | | 6 | |
| T2.1.2 | Implement Tiered Artifact Expansion | ☐ | | 6 | FR-008C |
| T2.1.3 | Implement Satisficing Logic (FR-008B) | ☐ | | 4 | Stop if conf≥0.90 |
| T2.1.4 | Ação 2 LLM Evaluation Implementation | ☐ | | 8 | Action-specific prompts |
| T2.1.5 | Ação 2 End-to-End Testing | ☐ | | 4 | | 
| T2.1.6 | Extract Ação 3 Crosswalk | ☐ | | 6 | |
| T2.1.7 | Ação 3 LLM Evaluation Implementation | ☐ | | 8 | |
| T2.1.8 | Extract Ação 4 Crosswalk | ☐ | | 6 | |
| T2.1.9 | Ação 4 LLM Evaluation Implementation | ☐ | | 8 | |
| T2.1.10 | Extract Ação 5 Crosswalk | ☐ | | 6 | |
| T2.1.11 | Ação 5 LLM Evaluation Implementation | ☐ | | 8 | |
| T2.1.12 | Block 1 Integration Testing | ☐ | | 4 | All 4 actions work |
| T2.1.13 | Block 1 Documentation (PT+EN) | ☐ | | 4 | Architecture + user guide |

**Key Deliverables / Entregáveis Principais:**
- [ ] Crosswalk extraction for Ações 2–5 (JSON files)
- [ ] Tiered expansion algorithm implemented
- [ ] Satisficing logic working (FR-008B)
- [ ] 4 action-specific evaluation pipelines
- [ ] Integration tests passing
- [ ] Block 1 report (PT+EN)

**Blockers / Bloqueadores:**
- [ ] None / Nenhum
- [ ] Describe / Descrever: ___________________________

**Block Summary / Resumo do Bloco:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## BLOCK 2: Actions 6–10 & Satisficing (Weeks 5–8: Jun 26 — Jul 23)

**Hours Planned / Horas Planejadas:** 120–140h  
**Actions / Ações:** 6, 7, 8, 9, 10
**Key Feature:** Full satisficing logic integration (FR-008B)

| Task Patterns | Count | Hours | Notes |
|---|---|---|---|
| Extract Crosswalks (5×) | 5 | 30h | Ações 6–10 |
| Action Evaluators (5×) | 5 | 40h | Implementation + testing |
| Satisficing Validation | 1 | 4h | Verify stop conditions |
| Block Integration Tests | 1 | 4h | All 5 actions + satisficing |
| Documentation | 1 | 4h | Block 2 report |
| **BLOCK 2 TOTAL** | | **82h** | Sustainable pace |

**Status / Status:**
- Week 5 Progress: ☐ On track / ☐ Behind / ☐ Ahead
- Week 6 Progress: ☐ On track / ☐ Behind / ☐ Ahead
- Week 7 Progress: ☐ On track / ☐ Behind / ☐ Ahead
- Week 8 Progress: ☐ On track / ☐ Behind / ☐ Ahead

**Block Summary / Resumo do Bloco:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## BLOCK 3: Actions 11–15 & UNCERTAINTY Flags (Weeks 9–12: Jul 24 — Aug 20)

**Hours Planned / Horas Planejadas:** 120–140h  
**Actions / Ações:** 11, 12, 13, 14, 15  
**Key Feature:** UNCERTAINTY flag system (OQ-006) — flag if confidence < 0.70

| Task Patterns | Count | Hours | Notes |
|---|---|---|---|
| Extract Crosswalks (5×) | 5 | 30h | Ações 11–15 |
| Action Evaluators (5×) | 5 | 40h | With UNCERTAINTY tracking |
| UNCERTAINTY Validation | 1 | 4h | Test flag generation |
| Block Integration Tests | 1 | 4h | All 5 actions + uncertainties |
| Documentation | 1 | 4h | Block 3 report |
| **BLOCK 3 TOTAL** | | **82h** | |

**UNCERTAINTY Threshold Validation:**
- [ ] Flags triggered when confidence < 0.70
- [ ] Audit log records UNCERTAINTY events
- [ ] Report highlights UNCERTAINTY cases
- [ ] Assurance pass (FR-021) validates consistency

**Block Summary / Resumo do Bloco:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## BLOCK 4: Actions 16–30 & Batch Evaluation (Weeks 13–16: Aug 21 — Sep 17)

**Hours Planned / Horas Planejadas:** 160–180h (larger block: 15 actions)  
**Actions / Ações:** 16–30 (15 actions)  
**Key Feature:** Batch evaluation pipeline (FR-017) for multiple cases

| Task Patterns | Count | Hours | Notes |
|---|---|---|---|
| Extract Crosswalks (15×) | 15 | 90h | Ações 16–30 |
| Action Evaluators (15×) | 15 | 120h | Full implementation |
| Batch Evaluation System | 1 | 10h | Process multiple cases |
| Block Integration Tests | 1 | 4h | All 15 actions |
| Documentation | 1 | 4h | Block 4 report |
| **BLOCK 4 TOTAL** | | **228h** | Largest block |

**Batch Processing Features:**
- [ ] Accept CSV or JSON input (multiple cases)
- [ ] Process all cases without re-initialization
- [ ] Generate consolidated report
- [ ] Error handling + rollback capability

**Block Summary / Resumo do Bloco:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## BLOCK 5: Actions 31–40 & Web UI (Weeks 17–20: Sep 18 — Oct 15)

**Hours Planned / Horas Planejadas:** 160–180h  
**Actions / Ações:** 31–40 (10 actions)  
**Key Feature:** Interactive Web UI for result viewing + annotation (FR-016)

| Task Patterns | Count | Hours | Notes |
|---|---|---|---|
| Extract Crosswalks (10×) | 10 | 60h | Ações 31–40 |
| Action Evaluators (10×) | 10 | 80h | Full implementation |
| Web UI Framework Setup | 1 | 20h | FastAPI + Vue.js |
| Result Viewing Interface | 1 | 20h | Display evaluations |
| Annotation Interface | 1 | 20h | Auditors can dispute/confirm |
| Block Integration | 1 | 4h | All 10 actions + UI |
| Documentation | 1 | 4h | Block 5 report |
| **BLOCK 5 TOTAL** | | **208h** | Complex block (UI) |

**Web UI Features / Recursos da UI:**
- [ ] Dashboard showing all 46 actions status
- [ ] Result details per action (evidence + confidence + UNCERTAINTY flag)
- [ ] Annotation interface for auditors
- [ ] Export reports (PDF, Excel, JSON)
- [ ] Audit trail visualization

**Block Summary / Resumo do Bloco:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## BLOCK 6: Actions 41–46 & Groq API (Weeks 21–24: Oct 16 — Nov 12)

**Hours Planned / Horas Planejadas:** 120–140h  
**Actions / Ações:** 41–46 (6 actions)  
**Key Feature:** Optional Groq API integration (Phase 2+ only) behind feature flag

| Task Patterns | Count | Hours | Notes |
|---|---|---|---|
| Extract Crosswalks (6×) | 6 | 36h | Ações 41–46 (final 6) |
| Action Evaluators (6×) | 6 | 48h | Full implementation |
| Groq API Integration | 1 | 16h | Config-driven backend switching |
| Local vs. Groq Benchmarking | 1 | 8h | Performance + cost analysis |
| Compliance Audit (OQ-005) | 1 | 8h | Final legal review prep |
| Block Integration | 1 | 4h | All 6 actions + Groq optional |
| Documentation (OQ-005 impl) | 1 | 4h | Block 6 report |
| **BLOCK 6 TOTAL** | | **124h** | Final actions + Groq |

**Groq API Integration / Integração Groq:**
- [ ] Config structure for backend selection (local vs. Groq)
- [ ] Groq behind feature flag (default=OFF)
- [ ] Requires explicit config + GROQ_API_KEY environment variable
- [ ] Audit log records which backend was used per case
- [ ] Fallback to local Ollama if Groq fails
- [ ] Cost tracking for Groq API calls (if enabled)

**OQ-005 Final Compliance:**
- [ ] Local Ollama remains default (Phase 1 inheritance)
- [ ] Groq integration fully optional (config flag)
- [ ] Audit trail for all external calls (if Groq enabled)
- [ ] Legal review documentation final

**Block Summary / Resumo do Bloco:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## BLOCK 7: Performance Tuning & Deployment (Weeks 25–26: Nov 13–20)

**Hours Planned / Horas Planejadas:** 80–100h (final 2-week sprint)  
**Key Features:** Performance optimization, Rio server deployment

| Task Patterns | Count | Hours | Notes |
|---|---|---|---|
| Performance Profiling | 1 | 12h | Retrieval, eval latency |
| Query Optimization | 1 | 12h | Index tuning, caching |
| Database Optimization | 1 | 8h | SQLite + LanceDB tuning |
| Vector Model Optimization | 1 | 8h | Quantization if needed |
| Rio Server Setup | 1 | 16h | Hardware provisioning, DB setup |
| Deployment Pipeline | 1 | 12h | Automated deployment script |
| Final Testing | 1 | 8h | Production smoke tests |
| Documentation & Handoff | 1 | 8h | Operation manual (PT+EN) |
| **BLOCK 7 TOTAL** | | **84h** | Deployment ready |

**Performance Targets / Metas de Performance:**
- [ ] Query latency < 500ms (hybrid search)
- [ ] Evaluation latency < 2s per case (LLM call)
- [ ] Batch eval of 100 cases < 5 minutes
- [ ] System memory < 4GB (Ollama + DB + indexes)

**Deployment Checklist / Checklist de Implantação:**
- [ ] All 46 actions working on Rio server
- [ ] SQLite database with full reference + crosswalk corpus
- [ ] LanceDB vector indexes built and verified
- [ ] Ollama service running on server (or Groq configured)
- [ ] Web UI accessible (https if applicable)
- [ ] Audit logs written to Rio server disk
- [ ] Backup strategy configured
- [ ] Monitoring + alerting (basic)
- [ ] Operation manual complete (PT+EN)
- [ ] Support contact + escalation documented

**Block Summary / Resumo do Bloco:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## 📊 PHASE 2 SUMMARY STATISTICS

| Block | Weeks | Actions | Tasks | Hours | Status |
|-------|-------|---------|-------|-------|--------|
| Block 1 | 1–4 | 2–5 | 13 | 120–140 | |
| Block 2 | 5–8 | 6–10 | ~12 | 120–140 | |
| Block 3 | 9–12 | 11–15 | ~12 | 120–140 | |
| Block 4 | 13–16 | 16–30 | ~20 | 160–180 | |
| Block 5 | 17–20 | 31–40 | ~18 | 160–180 | |
| Block 6 | 21–24 | 41–46 | ~12 | 120–140 | |
| Block 7 | 25–26 | Deploy | ~8 | 80–100 | |
| **TOTAL** | **26** | **1–46** | **~95** | **~1000** | |

---

## ✅ PHASE 2 FINAL CHECKLIST (Nov 20, 2026)

Before marking Phase 2 complete and deployment ready:

**All 46 Actions Implemented:**
- [ ] All actions 1–46 evaluation pipelines working
- [ ] Each action has: evaluation logic + artifact retrieval + evidence linking
- [ ] Crosswalks extracted for all 46 actions
- [ ] Action-specific prompts tuned and tested
- [ ] Integration tests passing for all actions
- [ ] Batch evaluation working (FR-017)

**Advanced Features Implemented:**
- [ ] Tiered artifact expansion (FR-008C) active
- [ ] Satisficing logic (FR-008B) working (stop at 0.90 confidence)
- [ ] UNCERTAINTY flags (OQ-006) triggered for conf < 0.70
- [ ] Web UI complete with result viewing + annotation (FR-016)
- [ ] Optional Groq API integration (config-driven, behind feature flag)
- [ ] Audit logging comprehensive + retrievable
- [ ] Deterministic replay via audit log (FR-014A)

**Quality Assurance:**
- [ ] Performance targets met (< 500ms retrieval, < 2s eval per case)
- [ ] Database integrity verified (foreign keys, WAL mode)
- [ ] No memory leaks (profiled)
- [ ] Error handling robust (graceful degradation)
- [ ] Code coverage > 80%
- [ ] All tests passing (unit, integration, e2e)

**Documentation Complete:**
- [ ] All docs bilingual (PT + EN)
- [ ] Architecture documentation updated (7-layer with Phase 2 details)
- [ ] API documentation complete
- [ ] User guide (for Rio auditors)
- [ ] Operation manual (for Rio IT)
- [ ] Troubleshooting guide
- [ ] Migration guide (Phase 1 → Phase 2)

**Compliance & Security:**
- [ ] OQ-005 implementation documented (local Ollama default + Groq optional)
- [ ] NFR-008 deployment boundary enforced (case docs local by default)
- [ ] Audit trail for all operations
- [ ] Data security reviewed
- [ ] Legal compliance checklist satisfied
- [ ] LGPD considerations documented (if applicable)

**Rio Server Deployment:**
- [ ] Server hardware provisioned (CPU, RAM, disk)
- [ ] SQLite database populated + indexes built
- [ ] Ollama service running (or Groq configured)
- [ ] Web UI deployed + accessible
- [ ] All 46 actions verified working on production
- [ ] Monitoring + alerting active
- [ ] Backup + disaster recovery tested
- [ ] Support documentation + contact info documented

**Stakeholder Handoff:**
- [ ] Final presentation to internal bosses (PT, non-technical summary)
- [ ] Final presentation to Master's adviser (technical deep dive)
- [ ] Phase 2 completion report (PT + EN)
- [ ] System demo video (optional)
- [ ] Training session for Rio auditors (if applicable)

---

## 🎯 SUCCESS CRITERIA / CRITÉRIOS DE SUCESSO

### MVP Success (May 29) — COMPLETED ✅
- ✅ Ação 1, Sub-task 1.1 evaluation works end-to-end
- ✅ Upload case → Retrieve artifacts → Evaluate → Report

### Phase 2 Success (Nov 20) — TARGET
- ✅ All 46 M5D actions implemented
- ✅ Web UI deployed for auditor use
- ✅ Performance optimized for production
- ✅ Deployed to Rio municipal server
- ✅ Operational and ready for daily use

### Long-term Success (Beyond Nov 20)
- ✅ System used by Rio auditors for M5D evaluations
- ✅ Evaluation quality validated (low UNCERTAINTY rate)
- ✅ Performance stable at production scale
- ✅ Maintenance procedures documented

---

**Phase 2 Checklist Version:** 1.0  
**Created:** 28 April 2026  
**Target Completion:** 20 November 2026  
*Update block status weekly; submit block reports after each 4-week block completes*
