# REQUIREMENTS MAPPING / MAPEAMENTO DE REQUISITOS

**Purpose / Propósito:** Inverse mapping showing which tasks implement which PRD requirements, EPIC decisions, and NFR constraints.

**Data / Data:** 28 de Abril de 2026  
**Language / Idioma:** Bilingual PT + EN

---

## 📌 OVERVIEW / VISÃO GERAL

This document provides **reverse traceability**: 
- **PRD Requirement** → **Which tasks implement it**  
- **EPIC Decision** → **Which tasks are affected**  
- **NFR Constraint** → **Which tasks must respect it**

Use this to:
1. **Verify coverage** - Is requirement FR-008 fully implemented?
2. **Find related tasks** - What other tasks touch this functionality?
3. **Validate scope** - Which Phase 1 tasks cover the MVP scope?
4. **Plan Phase 2** - Which Phase 2 blocks expand which requirements?

---

## 🔗 FUNCTIONAL REQUIREMENTS (PRD)

### FR-001: System Initialization
**Objective / Objetivo:** Initialize development environment, tooling, and basic project structure.

**Tasks / Tarefas:**
- T1.1.1 → Install VS Code + Extensions
- T1.1.2 → Install Python 3.11+ via Anaconda
- T1.1.3 → Install Ollama + Mistral
- T1.1.4 → Install Python Dependencies
- T1.1.5 → Setup SQLite + LanceDB Directories
- T1.1.6 → End-to-End Component Test
- T1.2.1 → Create Project Directory Structure
- T1.2.5 → Scaffold CLI Base Command
- T1.2.6 → Documentation: Architecture Overview

**Phase 1 Completion Status:** 9 tasks → 100% Phase 1 initialization

---

### FR-002: Data Storage & Management
**Objective / Objetivo:** Persistent storage for reference documents, case documents, evaluations, evidence links, and audit logs.

**Tasks / Tarefas:**
- T1.1.5 → Setup SQLite + LanceDB Directories (scaffolding)
- T1.2.2 → Design & Implement SQLite Schema (CORE - 4-6h)
- T1.2.4 → Implement db.py Functions (CORE - 3-4h)
- T1.3.2 → Ingest M5D Framework into SQLite (reference data)
- T1.4.3 → Build BM25 Index for Case Documents (sparse index)
- T1.4.4 → Build Dense Vector Index for Case Documents (dense index)
- T1.5.3 → Persist Evaluation Results + Evidence Links (CORE - 2-3h)

**Related Phase 2 Tasks:**
- T2.1.1+ → All actions 2-46 generate case evaluations stored via FR-002
- T2.6+ → Deploy to Rio server with FR-002 as persistent layer

**Phase 1 Completion Status:** Core schema + reference data + case indexing complete; ready for Phase 2 scale-up

---

### FR-003: Document Ingestion
**Objective / Objetivo:** Parse, chunk, hash, and store reference materials (M5D framework) and case documents.

**Tasks / Tarefas:**
- T1.3.1 → Implement Markdown Chunking (M5D + cases)
- T1.3.2 → Ingest M5D Framework into SQLite (reference corpus)
- T1.4.1 → Validate Uploaded Case Documents (case validation)
- T1.4.2 → Extract & Parse PDF/DOCX (case parsing)

**Phase 1 Completion Status:** M5D corpus ingested; case document pipeline ready for Phase 2 production

---

### FR-004: Case Document Management
**Objective / Objetivo:** Accept, validate, parse, and index case documents for evaluation.

**Tasks / Tarefas:**
- T1.4.1 → Validate Uploaded Case Documents (validation rules)
- T1.4.2 → Extract & Parse PDF/DOCX (parsing)
- T1.4.3 → Build BM25 Index for Case Documents (indexing)
- T1.4.4 → Build Dense Vector Index for Case Documents (embedding)
- T1.4.6 → Implement CLI Upload Command (interface)

**Related Phase 2 Tasks:**
- T2.1+ onwards → All Ação 1-46 case processing uses FR-004 pipeline

**Phase 1 Completion Status:** MVP case upload + indexing ready; will scale for 46 actions in Phase 2

---

### FR-005: M5D Framework Reference (Implicit in Architecture)
**Objective / Objetivo:** Maintain M5D framework as authoritative reference for evaluations.

**Tasks / Tarefas:**
- T1.3.2 → Ingest M5D Framework into SQLite
- T1.3.3 → Implement Keyword Search (BM25) - searches M5D
- T1.3.5 → Embed M5D into LanceDB
- T1.3.6 → Implement Semantic Search - searches M5D embeddings

**Phase 1 Completion Status:** M5D corpus searchable; remains unchanged Phase 1-2

---

### FR-006: Crosswalk Integration
**Objective / Objetivo:** Integrate Rio Manual + IN 01/2024 TCDF artifacts per action, with tipo (Direta/Indireta/Contextual) and grau (Alto/Médio/Baixo) classifications.

**Tasks / Tarefas:**

**Phase 1 (Ação 1 only):**
- T1.4.5 → Implement Hybrid Search (references M5D + case-specific artifacts)
- T1.5.1 → Implement LLM Evaluator (context includes relevant artifacts)

**Phase 2 (All Actions):**
- T2.1.1 → Analyze & Extract Ação 2 Crosswalk
- T2.1.2 → Implement Tiered Artifact Expansion (FR-008C)
- T2.2+ → Repeat for Ações 3-46

**Current Status:** Phase 1 MVP supports Ação 1 only; Phase 2 expands to all 46 ações

---

### FR-007: Language Support (Implicit)
**Objective / Objetivo:** Support Portuguese (pt-BR) legal terminology in embeddings and retrieval.

**Tasks / Tarefas:**
- T1.3.4 → Download & Cache Embedding Model (multilingual-MiniLM-L12-v2 supports PT)
- All Phase 1 retrieval tasks implicitly support Portuguese

**Related Phase 2 Tasks:**
- T2.1.1+ → All action artifacts are Portuguese legal documents

**Phase 1 Completion Status:** Multilingual model in place; PT terminology indexed

---

### FR-008: Hybrid Retrieval Strategy
**Objective / Objetivo:** Implement three-step retrieval with tiered expansion, satisficing, and RRF fusion.

**Decomposition / Decomposição:**
- **FR-008A (Pooled Retrieval):** Artifacts pooled per sub-task by tipo/grau
- **FR-008B (Satisficing):** Stop expansion if confidence ≥ 0.90 + tipo=Direta + grau=Alto  
- **FR-008C (Tiered Expansion):** Four ordered passes (Direta Alto → Direta Médio → ... → Contextual Baixo)
- **FR-008D (Three-step Retrieval):** Step 1 (exact filename match) → Step 2 (fuzzy name match) → Step 3 (semantic match)

**Phase 1 Tasks:**
- T1.3.3 → Implement Keyword Search (BM25) - Step 1 prefix for FR-008D
- T1.3.6 → Implement Semantic Search - Step 3 for FR-008D
- T1.4.3 → Build BM25 Index for Case Documents - enables FR-008D Step 1-2
- T1.4.4 → Build Dense Vector Index for Case Documents - enables FR-008D Step 3
- T1.4.5 → Implement Hybrid Search (RRF Fusion) - combines BM25 + dense for ranking

**Phase 2 Tasks:**
- T2.1.1 → Analyze & Extract Ação 2 Crosswalk - extracts tipo/grau for FR-008A pooling
- T2.1.2 → Implement Tiered Artifact Expansion - implements FR-008C logic
- T2.2+ → Similar for Ações 3-46

**Phase 1 Completion Status:** 
- ✅ Three-step retrieval (FR-008D) for M5D reference
- ✅ RRF fusion (FR-008) combining keyword + semantic
- ⏳ FR-008A/B/C deferred to Phase 2 (requires multi-action artifacts)

---

### FR-009: LLM-Based Evaluation
**Objective / Objetivo:** Query local Ollama (Mistral) or external Groq API for maturity assessment with context-aware prompts.

**Phase 1 Tasks:**
- T1.5.1 → Implement LLM Evaluator - core Ollama integration (temperature=0.3)

**Phase 2 Tasks:**
- T2.3+ → Extend to all 46 actions with action-specific prompts
- T2.6+ → Optional Groq API integration via config flag

**Related OQ-005 Tasks:**
- Local Ollama (Phase 1) vs. optional Groq (Phase 2+) configured via config.json

**Phase 1 Completion Status:** ✅ Local LLM evaluation ready for Ação 1

---

### FR-010: Confidence Scoring
**Objective / Objetivo:** Compute confidence (0.0-1.0) for each evaluation based on model's certainty and evidence quality.

**Phase 1 Tasks:**
- T1.5.1 → Implement LLM Evaluator - parse confidence from Mistral response JSON

**Related Phase 2:**
- T2.3+ → Confidence scoring extended to all actions

**Phase 1 Completion Status:** ✅ Confidence scoring implemented in MVP

---

### FR-011: Artifact Evidence Retrieval (Related to FR-008)
**Objective / Objetivo:** For each evaluation, retrieve relevant artifacts from Rio Manual / IN 01/2024 TCDF to support assessment.

**Phase 1 Tasks:**
- T1.4.5 → Implement Hybrid Search - returns ranked artifacts for context
- T1.5.1 → Implement LLM Evaluator - includes retrieved artifacts in prompt

**Phase 2 Tasks:**
- T2.1.1+ → Ação 2-46 artifact retrieval using pooled crosswalks

**Phase 1 Completion Status:** ✅ Basic artifact retrieval ready; Phase 1 supports Ação 1 artifacts only

---

### FR-012: Multi-Level Evaluation (Implicit in Architecture)
**Objective / Objetivo:** Support evaluation at different granularity levels (Action, Sub-task, Item).

**Phase 1 Scope:** Evaluate at Sub-task level (Ação 1, Sub-task 1.1) for MVP

**Phase 2 Scope:** Evaluate at full hierarchy level (all levels for Actions 1-46)

**Phase 1 Completion Status:** ✅ Sub-task evaluation ready for MVP

---

### FR-013: Evaluation Result Persistence
**Objective / Objetivo:** Store evaluation results with deterministic replay capability.

**Phase 1 Tasks:**
- T1.5.3 → Persist Evaluation Results + Evidence Links - insert into evaluations table with audit trail

**Phase 1 Completion Status:** ✅ Audit trail and result persistence ready

---

### FR-014: Evidence Traceability
**Objective / Objetivo:** Every evaluation conclusion links to case_chunk_id + artifact_id + disposition (hit/weak/none).

**Phase 1 Tasks:**
- T1.2.2 → Design & Implement SQLite Schema - defines evidence_links table structure
- T1.5.3 → Persist Evaluation Results + Evidence Links - implements evidence linking

**Phase 1 Completion Status:** ✅ Evidence traceability schema and implementation ready

**Related:** FR-014A (deterministic replay via audit_log)

---

### FR-015: Reporting & Visualization
**Objective / Objetivo:** Generate HTML + Markdown reports with evaluation results, evidence, confidence, and uncertainty flags.

**Phase 1 Tasks:**
- T1.5.4 → Generate Report Interface - bilingual reports (PT + EN)

**Phase 2 Tasks:**
- T2.5.1+ → Web UI for interactive result viewing

**Phase 1 Completion Status:** ✅ MVP markdown + HTML report generation ready

---

### FR-016–FR-021: (Other FR Requirements)

#### FR-016: Annotation & Dispute Resolution
**Phase 1:** Not in MVP scope  
**Phase 2:** T2.5+ → Auditor annotation interface

#### FR-017: Batch Processing
**Phase 1:** Not in MVP scope  
**Phase 2:** T2.4+ → Batch evaluation of multiple cases

#### FR-018: Audit Logging
**Phase 1 Tasks:**
- T1.5.3 → Persist Evaluation Results + Evidence Links (audit_log table)

#### FR-019: Configuration Management
**Phase 1 Tasks:**
- T1.2.3 → Create Global config.py
- Links to OQ-005 resolution for LLM backend selection

#### FR-020: Data Security
**Phase 1 Tasks:**
- Implicit in all storage/retrieval (SQLite WAL mode, local-only by default)

#### FR-021: Assurance Pass (Deterministic Validation)
**Phase 1 Tasks:**
- T1.5.2 → Implement Assurance Pass - temperature=0 re-evaluation for consistency check

**Phase 1 Completion Status:** ✅ Assurance pass ready for MVP

---

## 🏗️ EPIC DECISIONS (ARCHITECTURE)

### OQ-005 Resolution: Local Ollama vs. External Groq
**Decision / Decisão:** Phase 1 local-only (localhost:11434), Phase 2+ optional Groq with explicit config + audit trail

**Implementing Tasks:**
- T1.1.3 → Install Ollama + Pull Mistral (Phase 1 local requirement)
- T1.2.3 → Create Global config.py (branching logic for LLM backend)
- T1.5.1 → Implement LLM Evaluator (connects to localhost:11434)
- T1.5.2 → Implement Assurance Pass (local Mistral with temperature=0)

**Related Phase 2:**
- T2.6.2+ → Optional Groq integration behind feature flag

**Impact / Impacto:** Removes blocker OQ-005 for EPIC drafting; enables Phase 1 to proceed

---

### Local_LLM_Architecture
**Decision / Decisão:** All processing stays local (SQLite + LanceDB + Ollama) except optional Groq callout

**Implementing Tasks:**
- T1.1.1 through T1.1.6 → Full environment setup local
- T1.2.2 → Local SQLite + LanceDB databases
- T1.3.2, T1.3.5 → M5D corpus stored locally
- T1.4.3, T1.4.4 → Case indexes built locally
- T1.5.1 → LLM evaluation via local Mistral

**NFR-008 Deployment Boundary Compliance:** ✅ Case documents stay local; no transmission unless explicitly configured

---

### Hybrid_Retrieval_Strategy
**Decision / Decisión:** Combine keyword (BM25) + semantic (dense vector) using Reciprocal Rank Fusion

**Implementing Tasks:**
- T1.3.3 → Implement Keyword Search (BM25)
- T1.3.6 → Implement Semantic Search (dense vectors)
- T1.4.5 → Implement Hybrid Search (RRF fusion)

**Phase 2 Extension:**
- T2.1.2 → Tiered artifact expansion (FR-008C)
- T2.2+ → Multi-action crosswalk integration

---

### Three_Step_Retrieval (FR-008D)
**Decision / Decisión:** 
1. Exact filename match
2. Fuzzy name match  
3. Semantic content match  
Then combine with RRF

**Implementing Tasks:**
- T1.3.3 → Implement Keyword Search (Steps 1-2)
- T1.3.6 → Implement Semantic Search (Step 3)
- T1.4.5 → Implement Hybrid Search (ranking)

---

## 🔒 NON-FUNCTIONAL REQUIREMENTS (NFR)

### NFR-001: Performance — Retrieval Latency
**Target:** <500ms per query (semantic + keyword combined)

**Optimized By Tasks:**
- T1.4.3 → BM25 indexing (sparse retrieval perf)
- T1.4.4 → LanceDB dense indexing (dense retrieval perf)
- T1.4.5 → RRF fusion (combined perf)

**Phase 2 Tuning:**
- T2.7.1+ → Performance optimization block

**Phase 1 Status:** Baseline performance measured; tuning deferred to Phase 2

---

### NFR-002: Data Integrity
**Target:** Deterministic replay; audit trail for all operations

**Ensured By Tasks:**
- T1.2.2 → SQLite schema with foreign keys + WAL mode
- T1.5.3 → Audit log insertion
- T1.5.2 → Assurance pass (deterministic validation)

**Phase 1 Status:** ✅ Complete

---

### NFR-003: Availability
**Target:** System available 24/7 (local) with graceful degradation

**Supported By Tasks:**
- T1.1.3 → Ollama runs as background service
- T1.2.3 → Config fallbacks (Groq optional)

**Phase 1 Status:** ✅ Complete for Phase 1 scope

---

### NFR-004: Usability
**Target:** Developers can run CLI commands easily; non-technical users see clear reports

**Supported By Tasks:**
- T1.2.5 → CLI base with help text
- T1.4.6 → Upload command interface
- T1.5.4 → HTML + Markdown reports (PT+EN)

**Phase 1 Status:** ✅ MVP usability ready

---

### NFR-005: Maintainability
**Target:** Well-documented, modular code; bilingual docs (PT+EN)

**Supported By Tasks:**
- T1.2.6 → Architecture documentation
- T1.5.6 → MVP documentation & finalization (PT+EN)
- All tasks require bilingual deliverables

**Phase 1 Status:** ✅ Bilingual documentation enforced

---

### NFR-006: Scalability
**Target:** Support 46 M5D actions; >100k case chunks; batch processing

**Phase 1:** Single action (Ação 1) MVP  
**Phase 2:** Full 46-action deployment

**Deferred Tasks:**
- T2.4+ → Batch evaluation  
- T2.5+ → Web UI for interactive use
- T2.7+ → Performance tuning for scale

---

### NFR-007: Compliance & Audit
**Target:** Audit trail for all operations; evidence linking; UNCERTAINTY flags for low-confidence assessments

**Supported By Tasks:**
- T1.5.2 → Assurance pass (FR-021)
- T1.5.3 → Audit logging (FR-018)
- OQ-006 → UNCERTAINTY flag if confidence < 0.70

**Phase 1 Status:** ✅ Compliance mechanisms ready

---

### NFR-008: Deployment Boundary (Data Security)
**Target:** Case documents stay local by default; no external transmission unless explicitly configured

**Ensured By Tasks:**
- T1.2.3 → Config.py with local-first defaults
- T1.5.1 → Ollama local by default
- OQ-005 → Groq behind feature flag + explicit config

**Phase 1 Status:** ✅ Local-first architecture implemented; NFR-008 satisfied

---

## 📊 COVERAGE ANALYSIS / ANÁLISE DE COBERTURA

### Phase 1 Requirement Coverage

| Category | Total | Covered Phase 1 | Deferred Phase 2 | Coverage % |
|----------|-------|-----------------|------------------|-----------|
| **Functional Requirements** | 21 FR | 15 FR | 6 FR | 71% |
| **EPIC Decisions** | 4 main | 3 main | 1 main | 75% |
| **NFR Constraints** | 8 NFR | 7 NFR | 1 NFR | 88% |
| **OQ Decisions** | 6 OQ | 1 OQ (OQ-005) | 5 OQ | 17% |

### Phase 1 MVP Scope

**In MVP (Ação 1, Sub-task 1.1 only):**
- ✅ FR-001 through FR-015 (core functionality)
- ✅ FR-021 (assurance pass)
- ✅ OQ-005 (LLM architecture)
- ✅ NFR-001 through NFR-008 (all non-functional)
- ⏳ FR-006 (crosswalk) - Phase 1 has Ação 1 only, expands Phase 2
- ⏳ FR-012 (multi-level evaluation) - Phase 1 has sub-task level only
- ⏳ FR-016 (annotation) - Phase 2
- ⏳ FR-017 (batch) - Phase 2

**Phase 1 MVP Gap:** Single action, single sub-task; Phase 2 scales to 46 actions with full crosswalks

---

## 🔄 TASK DEPENDENCY GRAPH

```
PHASE 1 DEPENDENCIES:

T1.1.1 (VS Code)
  ↓
T1.1.2 (Python)
  ↓
T1.1.3 (Ollama)  ← Parallel with T1.1.4
  ↓
T1.1.4 (Deps)
  ↓
T1.1.5 (DB Setup)
  ↓
T1.1.6 (E2E Test)

↓ WEEK 2 ↓

T1.2.1 (Directory)
  ↓
T1.2.2 (Schema)  ← CORE
  ↓
T1.2.3 (Config)
  ↓
T1.2.4 (db.py)
  ↓
T1.2.5 (CLI)
  ↓
T1.2.6 (Docs)

↓ WEEK 3 ↓

T1.3.1 (Chunking)  ← Used by T1.3.2, T1.4.1-4.4
  ↓
T1.3.2 (M5D Ingest)
  ↓
T1.3.3 (BM25)
  ↓
T1.3.4 (Model Download)
  ↓
T1.3.5 (LanceDB)
  ↓
T1.3.6 (Semantic Search)

↓ WEEK 4 ↓

T1.4.1 (Validate)  ← Uses T1.3.1 (chunking)
  ↓
T1.4.2 (Parse)  ← Uses T1.3.1 (chunking)
  ↓
T1.4.3 (BM25 Index)  ← Uses T1.3.3 (BM25 implementation)
  ↓
T1.4.4 (Vector Index)  ← Uses T1.3.4, T1.3.5 (model + LanceDB)
  ↓
T1.4.5 (Hybrid Search)  ← Uses T1.4.3, T1.4.4, T1.3.6
  ↓
T1.4.6 (CLI Upload)

↓ WEEK 5 ↓

T1.5.1 (LLM Eval)  ← Uses T1.1.3 (Ollama), T1.2.3 (config), T1.4.5 (search)
  ↓
T1.5.2 (Assurance)  ← Uses T1.5.1 (LLM)
  ↓
T1.5.3 (Persist)  ← Uses T1.2.2 (schema), T1.2.4 (db.py)
  ↓
T1.5.4 (Report)
  ↓
T1.5.5 (E2E Test)  ← Uses all above tasks
  ↓
T1.5.6 (Docs)
```

---

## ✅ VALIDATION CHECKLIST

Use this to validate requirement coverage before phase closure:

### Phase 1 Closure Validation (Before May 29)

- [ ] All 30 Phase 1 tasks completed (T1.1.1 through T1.5.6)
- [ ] All FR-001 through FR-015, FR-018, FR-021 requirements satisfied
- [ ] OQ-005 resolution implemented (local Ollama working)
- [ ] NFR-001 through NFR-008 validated
- [ ] Ação 1, Sub-task 1.1 evaluation end-to-end works
- [ ] Evidence links in MASTER_TASK_REGISTRY.md for all tasks
- [ ] Bilingual documentation (PT+EN) complete
- [ ] Weekly reports for 5 weeks complete
- [ ] Screenshots for weekly deliverables captured
- [ ] Code committed to GitHub with clean history
- [ ] MVP runs on fresh Anaconda environment without errors

### Before Phase 2 Start (May 29)

- [ ] Stakeholder approval of Phase 1 MVP
- [ ] Professor review of technical deliverables
- [ ] EPIC draft completed using Phase 1 constraints
- [ ] Phase 2 detailed tasks ready to implement

---

**Document Version:** 1.0  
**Created:** 28 April 2026  
**Last Updated:** 28 April 2026  
*This requirements mapping is living documentation. Update as tasks are completed and requirements are validated.*
