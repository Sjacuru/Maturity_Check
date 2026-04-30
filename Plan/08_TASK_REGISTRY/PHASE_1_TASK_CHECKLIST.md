# PHASE 1 TASK CHECKLIST / CHECKLIST DE TAREFAS PHASE 1

**Duration:** 28 April — 29 May 2026 (5 weeks)  
**Total Tasks:** 30  
**Total Hours:** ~200 (40h/week)  
**Language / Idioma:** Bilingual PT + EN

---

## 📋 HOW TO USE / COMO USAR

1. **Copy this week's section** to your weekly report
2. **Check off tasks** as you complete them
3. **Fill in evidence links** (commit hash, screenshot path, doc link)
4. **Update status** column (not-started → in-progress → completed → blocked)
5. **Friday EOD:** Mark all week tasks complete and prepare report

---

## WEEK 1: Environment & Tools Setup (Apr 28 — May 4)

**Hours Planned / Horas Planejadas:** 16–20h  
**Hours Actual / Horas Reais:** [Fill in Friday]

| ID | Task / Tarefa | Status | Evidence | Hours | Notes / Notas |
|----|----|--------|----------|-------|-------|
| T1.1.1 | Install VS Code + Extensions | ☐ | | | |
| T1.1.2 | Install Python 3.11+ via Anaconda | ☐ | | | |
| T1.1.3 | Install Ollama + Mistral Model | ☐ | | | |
| T1.1.4 | Install Python Dependencies | ☐ | | | |
| T1.1.5 | Setup SQLite + LanceDB Dirs | ☐ | | | |
| T1.1.6 | E2E Component Test | ☐ | | | |

**Deliverables / Entregáveis:**
- [ ] vs_code_setup.md (bilingual)
- [ ] requirements.txt
- [ ] Setup screenshots (3+)
- [ ] Ollama test output
- [ ] E2E test report (PT+EN)

**Blockers / Bloqueadores:**
- [ ] None / Nenhum
- [ ] Describe / Descrever: ___________________________

**Weekly Summary / Resumo Semanal:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## WEEK 2: Project Structure & Database (May 5–11)

**Hours Planned / Horas Planejadas:** 20–24h  
**Hours Actual / Horas Reais:** [Fill in Friday]

| ID | Task / Tarefa | Status | Evidence | Hours | Notes / Notas |
|----|----|--------|----------|-------|-------|
| T1.2.1 | Create Project Directory Structure | ☐ | | | |
| T1.2.2 | Design & Implement SQLite Schema | ☐ | | | |
| T1.2.3 | Create Global config.py | ☐ | | | |
| T1.2.4 | Implement db.py Functions | ☐ | | | |
| T1.2.5 | Scaffold CLI Base Command | ☐ | | | |
| T1.2.6 | Documentation: Architecture Overview | ☐ | | | |

**Deliverables / Entregáveis:**
- [ ] folder_tree.txt
- [ ] schema_design.md (PT+EN)
- [ ] schema_diagram.png
- [ ] db.py with CRUD functions
- [ ] db_test.py
- [ ] config.py
- [ ] cli.py with subcommands
- [ ] ARCHITECTURE.md (PT+EN)

**Blockers / Bloqueadores:**
- [ ] None / Nenhum
- [ ] Describe / Descrever: ___________________________

**Weekly Summary / Resumo Semanal:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## WEEK 3: M5D Ingestion & Reference Search (May 12–18)

**Hours Planned / Horas Planejadas:** 24–28h  
**Hours Actual / Horas Reais:** [Fill in Friday]

| ID | Task / Tarefa | Status | Evidence | Hours | Notes / Notas |
|----|----|--------|----------|-------|-------|
| T1.3.1 | Implement Markdown Chunking | ☐ | | | |
| T1.3.2 | Ingest M5D Framework into SQLite | ☐ | | | |
| T1.3.3 | Implement Keyword Search (BM25) | ☐ | | | |
| T1.3.4 | Download & Cache Embedding Model | ☐ | | | |
| T1.3.5 | Embed M5D into LanceDB | ☐ | | | |
| T1.3.6 | Implement Semantic Search | ☐ | | | |

**Deliverables / Entregáveis:**
- [ ] chunking.py complete
- [ ] chunking_test.py with pytest
- [ ] sample_chunks.json
- [ ] m5d_ingest_log.txt
- [ ] reference_documents_count.txt
- [ ] search_reference.py with BM25
- [ ] bm25_search_test.py
- [ ] model_download_log.txt
- [ ] lancedb_ingest_log.txt
- [ ] semantic_search_test.py
- [ ] Search results samples (JSON)

**Blockers / Bloqueadores:**
- [ ] None / Nenhum
- [ ] Describe / Descrever: ___________________________

**Weekly Summary / Resumo Semanal:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## WEEK 4: Case Document Processing & Hybrid Retrieval (May 19–25)

**Hours Planned / Horas Planejadas:** 24–28h  
**Hours Actual / Horas Reais:** [Fill in Friday]

| ID | Task / Tarefa | Status | Evidence | Hours | Notes / Notas |
|----|----|--------|----------|-------|-------|
| T1.4.1 | Validate Uploaded Case Documents | ☐ | | | |
| T1.4.2 | Extract & Parse PDF/DOCX | ☐ | | | |
| T1.4.3 | Build BM25 Index for Case Docs | ☐ | | | |
| T1.4.4 | Build Dense Vector Index | ☐ | | | |
| T1.4.5 | Implement Hybrid Search (RRF) | ☐ | | | |
| T1.4.6 | Implement CLI Upload Command | ☐ | | | |

**Deliverables / Entregáveis:**
- [ ] document_validator.py
- [ ] validation_test.py
- [ ] validation_rules.md (PT+EN)
- [ ] document_parser.py
- [ ] parser_test.py
- [ ] case_bm25_indexer.py
- [ ] case_vector_indexer.py
- [ ] hybrid_search.py with RRF
- [ ] hybrid_search_test.py
- [ ] CLI upload command working
- [ ] upload_screenshot.png

**Blockers / Bloqueadores:**
- [ ] None / Nenhum
- [ ] Describe / Descrever: ___________________________

**Weekly Summary / Resumo Semanal:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## WEEK 5: LLM Evaluation & MVP Final (May 26–29)

**Hours Planned / Horas Planejadas:** 20–24h  
**Hours Actual / Horas Reais:** [Fill in Friday]

| ID | Task / Tarefa | Status | Evidence | Hours | Notes / Notas |
|----|----|--------|----------|-------|-------|
| T1.5.1 | Implement LLM Evaluator (FR-009/010) | ☐ | | | |
| T1.5.2 | Implement Assurance Pass (FR-021) | ☐ | | | |
| T1.5.3 | Persist Results + Evidence Links | ☐ | | | |
| T1.5.4 | Generate Report Interface | ☐ | | | |
| T1.5.5 | End-to-End Pipeline Test | ☐ | | | |
| T1.5.6 | MVP Documentation & Finalization | ☐ | | | |

**Deliverables / Entregáveis:**
- [ ] evaluator.py with LLM call
- [ ] evaluation_test.py
- [ ] sample_evaluation_output.json
- [ ] assurance.py
- [ ] assurance_test.py
- [ ] results_persistence.py
- [ ] audit_log_sample.sql
- [ ] report_generator.py
- [ ] sample_report.html
- [ ] sample_report.md (PT+EN)
- [ ] e2e_test.py
- [ ] e2e_test_report.md (PT+EN)
- [ ] MVP_README.md (PT+EN)
- [ ] installation_guide.md (PT+EN)
- [ ] user_guide.md (PT+EN)
- [ ] release_notes.md

**Blockers / Bloqueadores:**
- [ ] None / Nenhum
- [ ] Describe / Descrever: ___________________________

**MVP Completion Validation / Validação de Conclusão MVP:**
- [ ] Ação 1, Sub-task 1.1 evaluation works end-to-end
- [ ] Upload → Retrieve → Evaluate → Assurance → Report working
- [ ] All evidence links captured
- [ ] Bilingual documentation complete
- [ ] Code committed to GitHub
- [ ] Tests passing
- [ ] Screenshots captured

**Weekly Summary / Resumo Semanal:**
[PT] ________________________________________________________  
[EN] ________________________________________________________

---

## 📊 PHASE 1 SUMMARY STATISTICS

| Week | Tasks | Planned Hours | Actual Hours | % Complete | Status |
|------|-------|---------------|--------------|-----------|--------|
| Week 1 | 6 | 16–20h | | | |
| Week 2 | 6 | 20–24h | | | |
| Week 3 | 6 | 24–28h | | | |
| Week 4 | 6 | 24–28h | | | |
| Week 5 | 6 | 20–24h | | | |
| **TOTAL** | **30** | **~200h** | | | |

---

## ✅ PHASE 1 FINAL CHECKLIST (May 29)

Before marking Phase 1 complete, verify:

**Code & Functionality:**
- [ ] All 30 tasks completed (T1.1.1 through T1.5.6)
- [ ] All deliverables produced and committed
- [ ] Code compiles/runs without errors
- [ ] All tests passing (pytest coverage > 80%)
- [ ] E2E flow works: upload → retrieve → evaluate → report

**Documentation:**
- [ ] All docs bilingual (PT + EN)
- [ ] README complete with installation + usage
- [ ] Architecture documented
- [ ] API documented
- [ ] Troubleshooting guide included

**Evidence & Traceability:**
- [ ] All evidence links in MASTER_TASK_REGISTRY.md
- [ ] All requirements (FR/NFR) satisfied
- [ ] All EPIC decisions respected
- [ ] Time tracking reconciled (actual vs. planned)
- [ ] Weekly reports for 5 weeks complete

**Quality Assurance:**
- [ ] No blockers remaining
- [ ] Code review complete (if applicable)
- [ ] Audit log working
- [ ] Assurance pass (FR-021) validates results
- [ ] UNCERTAINTY flags working for confidence < 0.70

**Stakeholder Readiness:**
- [ ] Phase 1 report prepared for bosses (PT, non-technical)
- [ ] Phase 1 report prepared for professor (EN/PT, technical)
- [ ] Screenshots prepared (2+ per week)
- [ ] MVP demo ready
- [ ] Next phase (Phase 2) plan confirmed

---

**Template Version:** 1.0  
**Created:** 28 April 2026  
**Usage:** Print and fill out each week; submit Friday EOD  
*Update status column daily; fill evidence links as tasks complete*
