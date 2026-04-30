# MASTER TASK REGISTRY / REGISTRO MESTRE DE TAREFAS

**Last Updated / Última Atualização:** 28 de Abril de 2026  
**Total Tasks / Total de Tarefas:** ~150  
**Phase 1 Tasks:** 30  
**Phase 2 Tasks:** ~120

---

## LEGEND / LEGENDA

| Status | Significado |
|--------|-------------|
| `not-started` | Não iniciada / Task not begun |
| `in-progress` | Em progresso / Currently working |
| `completed` | Completa / Finished with evidence |
| `blocked` | Bloqueada / Waiting on dependency |
| `deferred` | Adiada / Moved to next phase |

| Field | Descrição |
|-------|-----------|
| **ID** | Task identifier (T[Phase].[Week].[Number]) |
| **Name** | Short English name |
| **Nome PT** | Nome curto em Português |
| **Phase** | Phase 1 or 2 |
| **Week** | Which week (1-5 for Phase 1, 1-26 for Phase 2) |
| **PRD-Map** | Which PRD requirement(s) it implements |
| **EPIC-Map** | Which EPIC decision it supports |
| **Status** | Current status |
| **Deliverables** | What must be delivered (code/doc/screenshot) |
| **Evidence** | Links to proof (commit hash, file path, screenshot) |
| **Hours** | Estimated hours to complete |
| **Completed** | Actual hours or % complete |
| **Notes** | Any blockers or dependencies |

---

## PHASE 1 TASKS (5 WEEKS, 30 TASKS)

### WEEK 1: Environment & Tools Setup (Apr 28 — May 4)

#### T1.1.1 — Install VS Code + Extensions
**PT:** Instalar VS Code + Extensões  
**Phase:** 1 | **Week:** 1 | **Hours:** 2-3  
**PRD-Map:** FR-001 (System Initialization)  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** vs_code_setup.md (bilingual), extensions_list.txt  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Prerequisites for all subsequent work. Requires: Python extension, Pylance, Markdown All in One.

---

#### T1.1.2 — Install Python 3.11+ via Anaconda & Create Environment
**PT:** Instalar Python 3.11+ via Anaconda e criar ambiente  
**Phase:** 1 | **Week:** 1 | **Hours:** 2  
**PRD-Map:** FR-001  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** requirements.txt, conda_env_created_screenshot.png  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Python must be 3.11+. Use Anaconda: `conda create -n maturity_check python=3.11` then `conda activate maturity_check`.

---

#### T1.1.3 — Install Ollama + Pull Mistral Model
**PT:** Instalar Ollama e fazer pull do Mistral  
**Phase:** 1 | **Week:** 1 | **Hours:** 3-4  
**PRD-Map:** FR-001, OQ-005  
**EPIC-Map:** OQ-005_Resolution (local Ollama default)  
**Deliverables:** ollama_installed.png, mistral_model_pulled.png, ollama_test_output.txt  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** ~4GB download. Mistral model = default LLM. Must run `ollama pull mistral`. Test with `curl http://localhost:11434/api/tags`.

---

#### T1.1.4 — Install Python Dependencies  
**PT:** Instalar dependências Python  
**Phase:** 1 | **Week:** 1 | **Hours:** 1-2  
**PRD-Map:** FR-001  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** pip_install_log.txt, dependency_versions_list.md  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** `pip install -r requirements.txt` with: pydantic, lancedb, pyarrow, numpy, tqdm, sentence-transformers.

---

#### T1.1.5 — Setup SQLite + LanceDB Directories  
**PT:** Configurar diretórios SQLite + LanceDB  
**Phase:** 1 | **Week:** 1 | **Hours:** 1  
**PRD-Map:** FR-001, FR-002 (Data Storage)  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** folder_structure_screenshot.png, db_init_script.py  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Create `data/sqlite/` and `data/lancedb/` folders. Test SQLite WAL mode.

---

#### T1.1.6 — End-to-End Component Test  
**PT:** Teste E2E de todos componentes  
**Phase:** 1 | **Week:** 1 | **Hours:** 2-3  
**PRD-Map:** FR-001  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** e2e_test_report.md (PT+EN), test_results.txt  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Verify: VS Code launches, Python 3.11 works, Anaconda environment active, Ollama responds on localhost:11434, SQLite creates schema, LanceDB directory writable.

---

### WEEK 2: Project Structure & Database Schema (May 5–11)

#### T1.2.1 — Create Project Directory Structure  
**PT:** Criar estrutura de diretórios do projeto  
**Phase:** 1 | **Week:** 2 | **Hours:** 1-2  
**PRD-Map:** FR-001  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** folder_tree.txt, __init__.py files  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Follow existing pattern in `src/maturity_check/` + new subdirs for Phase 1.

---

#### T1.2.2 — Design & Implement SQLite Schema  
**PT:** Desenhar e implementar schema SQLite  
**Phase:** 1 | **Week:** 2 | **Hours:** 4-6  
**PRD-Map:** FR-002, FR-014 (Evidence Traceability)  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** schema_design.md (PT+EN), db.py updated with full schema, schema_diagram.png  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Must include: reference_documents, reference_chunks, cases, case_documents, case_chunks, evaluations, evidence_links, audit_log, annotations. Foreign keys ON, WAL mode.

---

#### T1.2.3 — Create Global config.py  
**PT:** Criar config.py global  
**Phase:** 1 | **Week:** 2 | **Hours:** 2-3  
**PRD-Map:** FR-001  
**EPIC-Map:** OQ-005_Resolution (LLM backend config)  
**Deliverables:** config.py with environment variables, config_template.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Define: DB paths, LanceDB paths, LLM backend (default="ollama"), temperature settings, vector model path, batch sizes.

---

#### T1.2.4 — Implement db.py Functions  
**PT:** Implementar funções db.py  
**Phase:** 1 | **Week:** 2 | **Hours:** 3-4  
**PRD-Map:** FR-002  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** db.py with CRUD functions, db_test.py with pytest tests  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Implement: connect_sqlite(), init_schema(), insert_reference_doc(), query_by_id(), etc.

---

#### T1.2.5 — Scaffold CLI Base Command  
**PT:** Scaffolding de comando CLI base  
**Phase:** 1 | **Week:** 2 | **Hours:** 2-3  
**PRD-Map:** FR-001  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** cli.py with argparse subcommands structure, cli_help_output.txt  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Create main() with subcommand placeholders: ingest-m5d, ingest-case, search, evaluate, view-results.

---

#### T1.2.6 — Documentation: Architecture Overview  
**PT:** Documentação: Visão geral da arquitetura  
**Phase:** 1 | **Week:** 2 | **Hours:** 2-3  
**PRD-Map:** FR-001  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** ARCHITECTURE.md (PT+EN), layer_diagram.md, component_interactions.md  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Document 7-layer architecture from PRD analysis. Include database schema diagram.

---

### WEEK 3: M5D Ingestion & Reference Search (May 12–18)

#### T1.3.1 — Implement Markdown Chunking  
**PT:** Implementar chunking de markdown  
**Phase:** 1 | **Week:** 3 | **Hours:** 3-4  
**PRD-Map:** FR-003 (Ingestion), FR-002 (Data Storage)  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** chunking.py complete, chunking_test.py with pytest, sample_chunks.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Implement iter_markdown_blocks() and chunk_text(). Preserve heading hierarchy. Handle overlaps.

---

#### T1.3.2 — Ingest M5D Framework into SQLite  
**PT:** Ingerir M5D para SQLite  
**Phase:** 1 | **Week:** 3 | **Hours:** 3-4  
**PRD-Map:** FR-003  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** m5d_ingest_log.txt, reference_documents_count.txt, m5d_chunks_sample.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Read Plan/06_Models/M5D.md, chunk, hash, insert into reference_documents + reference_chunks. Verify SHA256 consistency.

---

#### T1.3.3 — Implement Keyword Search (BM25)  
**PT:** Implementar busca por keywords (BM25)  
**Phase:** 1 | **Week:** 3 | **Hours:** 2-3  
**PRD-Map:** FR-008 (Hybrid Retrieval)  
**EPIC-Map:** FR-008 (Three-step retrieval)  
**Deliverables:** search_reference.py with BM25 function, bm25_search_test.py, search_results_sample.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Use Whoosh or rank-bm25. Test queries on M5D corpus. Return ranked results with scores.

---

#### T1.3.4 — Download & Cache Embedding Model  
**PT:** Download & cache modelo de embedding  
**Phase:** 1 | **Week:** 3 | **Hours:** 2  
**PRD-Map:** FR-003, FR-008  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** model_download_log.txt, model_cached_screenshot.png  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Download multilingual-MiniLM-L12-v2 (~400MB). Cache in ~/.cache/huggingface/. Test loading.

---

#### T1.3.5 — Embed M5D into LanceDB  
**PT:** Embedar M5D em LanceDB  
**Phase:** 1 | **Week:** 3 | **Hours:** 3-4  
**PRD-Map:** FR-008, FR-002  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** lancedb_ingest_log.txt, vector_count.txt, embedding_sample.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Convert M5D chunks to 384-dim embeddings. Insert into LanceDB. Verify row count matches SQLite.

---

#### T1.3.6 — Implement Semantic Search  
**PT:** Implementar busca semântica  
**Phase:** 1 | **Week:** 3 | **Hours:** 3  
**PRD-Map:** FR-008, FR-002  
**EPIC-Map:** FR-008 (Hybrid retrieval)  
**Deliverables:** semantic_search_test.py, semantic_search_results_sample.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Embed query, search LanceDB by cosine distance. Return top-k results with scores. Test on real queries.

---

### WEEK 4: Case Document Processing & Hybrid Retrieval (May 19–25)

#### T1.4.1 — Validate Uploaded Case Documents  
**PT:** Validar documentos de caso uploaded  
**Phase:** 1 | **Week:** 4 | **Hours:** 2  
**PRD-Map:** FR-004 (Case Document Ingestion)  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** document_validator.py, validation_test.py, validation_rules.md (PT+EN)  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Check: file format (PDF/DOCX/TXT), file size < 50MB, mimetype validation, virus scan stub.

---

#### T1.4.2 — Extract & Parse PDF/DOCX  
**PT:** Extrair e parsear PDF/DOCX  
**Phase:** 1 | **Week:** 4 | **Hours:** 3-4  
**PRD-Map:** FR-004  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** document_parser.py, parser_test.py with sample PDFs  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Use pypdf or python-docx. Extract text preserving structure. Handle images as [IMAGE] placeholder.

---

#### T1.4.3 — Build BM25 Index for Case Documents  
**PT:** Construir índice BM25 para casos  
**Phase:** 1 | **Week:** 4 | **Hours:** 2-3  
**PRD-Map:** FR-008 (Hybrid Retrieval)  
**EPIC-Map:** FR-008  
**Deliverables:** case_bm25_indexer.py, index_sample.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Index case_chunks for BM25. Store in Whoosh directory in data/. Test indexing speed.

---

#### T1.4.4 — Build Dense Vector Index for Case Documents  
**PT:** Construir índice de vetores densos para casos  
**Phase:** 1 | **Week:** 4 | **Hours:** 3-4  
**PRD-Map:** FR-008  
**EPIC-Map:** FR-008  
**Deliverables:** case_vector_indexer.py, lancedb_case_ingest_log.txt  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Embed case_chunks and insert into separate LanceDB table. Verify row count.

---

#### T1.4.5 — Implement Hybrid Search (RRF Fusion)  
**PT:** Implementar busca híbrida (RRF)  
**Phase:** 1 | **Week:** 4 | **Hours:** 3-4  
**PRD-Map:** FR-008  
**EPIC-Map:** FR-008 (Hybrid retrieval with RRF)  
**Deliverables:** hybrid_search.py with RRF function, hybrid_search_test.py, rrf_results_sample.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Implement Reciprocal Rank Fusion combining BM25 + dense scores. Weight BM25:Dense = 0.4:0.6.

---

#### T1.4.6 — Implement CLI Upload Command  
**PT:** Implementar comando CLI para upload  
**Phase:** 1 | **Week:** 4 | **Hours:** 2-3  
**PRD-Map:** FR-004  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** cli_upload_command.py, upload_screenshot.png, upload_help_output.txt  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** `maturity-check upload-case --file=case.pdf`. Validate → parse → index → return case_id.

---

### WEEK 5: LLM Evaluation & MVP Final (May 26–29)

#### T1.5.1 — Implement LLM Evaluator (FR-009, FR-010)  
**PT:** Implementar avaliador LLM  
**Phase:** 1 | **Week:** 5 | **Hours:** 4-5  
**PRD-Map:** FR-009 (Evaluation), FR-010 (Confidence)  
**EPIC-Map:** OQ-005_Resolution (local Ollama)  
**Deliverables:** evaluator.py with LLM call, evaluation_test.py, sample_evaluation_output.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Connect to localhost:11434. Query Mistral with context + question. Parse JSON response. Extract confidence (0-1).

---

#### T1.5.2 — Implement Assurance Pass (FR-021)  
**PT:** Implementar assurance pass  
**Phase:** 1 | **Week:** 5 | **Hours:** 3-4  
**PRD-Map:** FR-021 (Assurance Pass)  
**EPIC-Map:** OQ-005_Resolution  
**Deliverables:** assurance.py, assurance_test.py, assurance_check_sample.json  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Re-evaluate same case with temperature=0, different prompt. Flag UNCERTAINTY if confidence < 0.70. Deterministic replay.

---

#### T1.5.3 — Persist Evaluation Results + Evidence Links (FR-014, FR-014A)  
**PT:** Persistir resultados e evidence links  
**Phase:** 1 | **Week:** 5 | **Hours:** 2-3  
**PRD-Map:** FR-014 (Evidence Traceability)  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** results_persistence.py, audit_log_sample.sql  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Insert into: evaluations, evidence_links, audit_log. Link to case_chunk_id + artifact_id + disposition.

---

#### T1.5.4 — Generate Report Interface  
**PT:** Gerar interface de relatório  
**Phase:** 1 | **Week:** 5 | **Hours:** 2-3  
**PRD-Map:** FR-015 (Reporting)  
**EPIC-Map:** Local_LLM_Architecture  
**Deliverables:** report_generator.py, sample_report.html, sample_report.md (PT+EN)  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Generate HTML + Markdown report with results, evidence, confidence, UNCERTAINTY flags.

---

#### T1.5.5 — End-to-End Pipeline Test  
**PT:** Teste E2E do pipeline completo  
**Phase:** 1 | **Week:** 5 | **Hours:** 2-3  
**PRD-Map:** FR-001 through FR-015  
**EPIC-Map:** All Phase 1 decisions  
**Deliverables:** e2e_test.py, e2e_test_report.md (PT+EN), e2e_test_screenshots.png  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Upload real case → M5D search → LLM eval → assurance → report. Verify end-to-end flow.

---

#### T1.5.6 — MVP Documentation & Finalization  
**PT:** Documentação MVP e finalização  
**Phase:** 1 | **Week:** 5 | **Hours:** 2-3  
**PRD-Map:** FR-001  
**EPIC-Map:** All Phase 1  
**Deliverables:** MVP_README.md (PT+EN), installation_guide.md (PT+EN), user_guide.md (PT+EN), release_notes.md  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Document everything for production handoff. Include troubleshooting guide.

---

## PHASE 2 TASKS (26 WEEKS, ~120 TASKS)

### BLOCK 1: Actions 2–5 Implementation (Weeks 1–4, starting May 29)

#### T2.1.1 — Analyze & Extract Ação 2 Crosswalk
**PT:** Analisar e extrair crosswalk Ação 2  
**Phase:** 2 | **Week:** 1 | **Hours:** 6  
**PRD-Map:** FR-006 (Crosswalk Integration)  
**EPIC-Map:** Ação_2  
**Deliverables:** acao_2_artifacts.json, crosswalk_structure.md, verification_checklist.md  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Extract artifacts from Plan/06_Models/crosswalk/. Map tipo (Direta/Indireta/Contextual) + grau (Alto/Médio/Baixo).

---

#### T2.1.2 — Implement Tiered Artifact Expansion (FR-008C)
**PT:** Implementar tiered artifact expansion  
**Phase:** 2 | **Week:** 1 | **Hours:** 5-6  
**PRD-Map:** FR-008C (Tiered Expansion)  
**EPIC-Map:** Hybrid_Retrieval_Strategy  
**Deliverables:** tiered_expansion.py, tiered_expansion_test.py  
**Status:** `not-started`  
**Evidence:** `None yet`  
**Completed:** 0%  
**Notes:** Implement four passes: Direta Alto → Direta Médio → Direta Baixo → Indireta Alto → ... etc.

---

### [REMAINING PHASE 2 BLOCKS: To be detailed as Phase 1 completes]

**Summary of Phase 2 blocks:**
- **Block 1 (Weeks 1-4):** Actions 2–5 + Tiered Expansion
- **Block 2 (Weeks 5-8):** Actions 6–10 + Satisficing (FR-008B)
- **Block 3 (Weeks 9-12):** Actions 11–15 + UNCERTAINTY Flags
- **Block 4 (Weeks 13-16):** Actions 16–30 + Batch Evaluation
- **Block 5 (Weeks 17-20):** Actions 31–40 + Web UI  
- **Block 6 (Weeks 21-24):** Actions 41–46 + Groq Integration (optional)
- **Block 7 (Weeks 25-26):** Performance Tuning + Deployment to Rio Server

---

## 📊 SUMMARY STATISTICS

| Metric | Value |
|--------|-------|
| **Total Tasks Phase 1** | 30 |
| **Total Tasks Phase 2** | ~120 |
| **Total Tasks Overall** | ~150 |
| **Phase 1 Hours** | ~200 |
| **Phase 2 Hours** | ~1000 |
| **Total Hours** | ~1200 |
| **Weeks Total** | 31 |
| **Actions Covered (Phase 1)** | 1 |
| **Actions Covered (Phase 2)** | 46 |

---

## 🔗 RELATED DOCUMENTS

- **PHASE_1_DETAILED_PLAN.md** → Week-by-week breakdown (narrative)
- **PHASE_2_DETAILED_PLAN.md** → Block-by-block breakdown (narrative)
- **Plan/01_PRD/prd.md** → Functional requirements (FR-001 through FR-021)
- **Plan/07_RETRIEVAL/OQ-005_resolution.md** → LLM architecture decision
- **REQUIREMENTS_MAPPING.md** → Which tasks implement which requirements (this folder)

---

**Last updated:** 28 de Abril de 2026  
*This registry is the source of truth for task tracking. Update it as work progresses.*
