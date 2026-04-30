# CLAUDE/COPILOT INTEGRATION GUIDE / GUIA DE INTEGRAÇÃO PARA CLAUDE/COPILOT

**Purpose / Propósito:** Enable Claude/Copilot to automatically validate, update, and track task progress while maintaining traceability to PRD/EPIC/MDAP requirements.

**Last Updated / Última Atualização:** 28 de Abril de 2026  
**Version / Versão:** 1.0

---

## 🤖 FOR CLAUDE/COPILOT: HOW TO HELP WITH TASK MANAGEMENT

This guide explains how Claude/Copilot should interpret task updates, validate requirements, and maintain the registry.

---

## 1. WHEN DEVELOPER SUBMITS A TASK UPDATE

### Developer Command Format / Formato do Comando do Desenvolvedor:

```
@Claude: UPDATE TASK [T#.#.#]
Status: [new status]
Evidence: [commit hash / screenshot / doc link]
Details: [what was accomplished]
```

### Claude's Validation Checklist / Checklist de Validação do Claude:

When you receive a task update command:

1. **✅ Task Lookup**
   - [ ] Find task ID in MASTER_TASK_REGISTRY.md
   - [ ] Confirm task exists
   - [ ] Note current status + requirements

2. **✅ Status Transition Validation**
   - [ ] Valid transitions:
     - `not-started` → `in-progress` ✅
     - `in-progress` → `completed` ✅  
     - `in-progress` → `blocked` ✅
     - `blocked` → `in-progress` ✅
     - `not-started` → `completed` ⚠️ (only if estimated < 1h AND trivial)
   - [ ] Reject invalid transitions (e.g., `completed` → `not-started`)

3. **✅ Evidence Validation**
   - [ ] If `completed`: evidence MUST be provided
     - [ ] Commit hash (git) — verify path exists
     - [ ] Screenshot file — verify file extension (.png, .jpg, .gif)
     - [ ] Doc link — verify markdown file path
   - [ ] If `in-progress`: evidence optional (checkpoint)
   - [ ] If `blocked`: blocker_reason required

4. **✅ Requirement Mapping**
   - [ ] Look up PRD requirements for task (from REQUIREMENTS_MAPPING.md)
   - [ ] Verify deliverables described match expected outputs
   - [ ] Confirm EPIC decisions are being respected
   - [ ] If not satisfied, ASK clarifying questions

5. **✅ Bilingual Content Check** (if Phase 1)
   - [ ] Docs include PT + EN versions? 
   - [ ] If not, flag: "Please provide bilingual documentation"

6. **✅ Time Tracking Plausibility**
   - [ ] If hours > 3× estimated, ask: "Unexpectedly long—blockers encountered?"
   - [ ] If hours < 50% estimated, ask: "Completed faster than expected—verify quality?"

---

### Claude's Response / Resposta do Claude:

**IF ALL VALIDATION PASSES:**

```
✅ TASK UPDATE VALIDATED

Task ID: T#.#.#
Name: [Task name]
Previous Status: [old status]
New Status: [new status]
Evidence: [summary of evidence provided]

✅ Requirements satisfied:
- PRD: FR-### ✅
- EPIC: [decision] ✅
- NFR: [constraint] ✅

Registry updated:
- MASTER_TASK_REGISTRY.md: Status → completed, Evidence link added
- PHASE_1_TASK_CHECKLIST.md (or PHASE_2): Week #, Task #.#.# ✅

Next steps: [related dependent tasks, if any]
```

**IF VALIDATION FAILS:**

```
⚠️ TASK UPDATE REQUIRES CLARIFICATION

Task ID: T#.#.#
Issue: [specific validation failure]

Questions for Developer:
1. [Question about evidence / requirements / timing]
2. [Question about dependent tasks]

Please respond with clarification, then I'll update the registry.
```

---

## 2. TASK DEPENDENCY RESOLUTION

### When Task A Depends on Task B / Quando Tarefa A Depende da Tarefa B:

From MASTER_TASK_REGISTRY.md dependency graph (e.g., T1.4.5 "Hybrid Search" depends on T1.3.3 "BM25"):

1. **Check Prerequisites**
   - [ ] Is T1.3.3 marked `completed`?
   - [ ] If not, inform developer: "T1.4.5 blocked by T1.3.3 (not yet completed)"
   - [ ] Allow dev to override if they're doing parallel work

2. **Alert on Dependent Tasks**
   - [ ] When T1.3.3 completes, check which tasks depend on it
   - [ ] If dev starts T1.4.5, remind: "This depends on T1.3.3—verify it's working"

3. **Flag Task Chains**
   - [ ] If T1.5.1 (LLM Evaluator) requires T1.1.3 (Ollama), track this
   - [ ] Before marking T1.5.1 complete, validate: "Is Ollama running?"

---

## 3. WEEKLY CLOSE-OUT PROCESS

### Every Friday (EOD) / Toda Sexta-feira (Final do Dia):

Developer updates PHASE_1_TASK_CHECKLIST.md or PHASE_2_TASK_CHECKLIST.md:
- Mark all completed tasks (checkboxes: ☑)
- Fill in evidence links
- Sum actual hours
- Write weekly summary (PT + EN)

**Claude's Role / Papel do Claude:**

```
@Claude: CLOSE WEEK #

Tasks this week:
- T1.#.1: completed (evidence: ...)
- T1.#.2: in-progress (evidence: ...)
- T1.#.3: blocked (reason: ...)

Summary: [Developer's summary]
```

Claude performs:

1. ✅ **Verify All Tasks Accounted For**
   - [ ] Count: expected X tasks, marked Y completed + Z in-progress + W blocked
   - [ ] If missing: ask "Task T1.#.# not in checklist—status?"

2. ✅ **Validate Evidence Completeness**
   - [ ] All `completed` tasks have evidence links?
   - [ ] Screenshots in proper folder?
   - [ ] Docs bilingual?

3. ✅ **Time Tracking Reconciliation**
   - [ ] Planned hours vs. actual hours ratio
   - [ ] Flag if week is >10% over/under estimate
   - [ ] Aggregate for monthly reporting

4. ✅ **Requirements Coverage Check**
   - [ ] All PRD requirements for this week's tasks satisfied?
   - [ ] Use REQUIREMENTS_MAPPING.md to verify

5. ✅ **Update Master Registry**
   - [ ] Mark all completed tasks in MASTER_TASK_REGISTRY.md
   - [ ] Update evidence links
   - [ ] Calculate running completion %

6. ✅ **Generate Weekly Report Template**
   - [ ] PT section: Non-technical summary for bosses
   - [ ] EN section: Technical details for professor
   - [ ] Include 2-3 key screenshots
   - [ ] Format: markdown file named `Week_#_Report.md`

**Claude's Weekly Close Output / Saída do Fechamento Semanal:**

```
✅ WEEK # CLOSE-OUT COMPLETE

Summary / Resumo:
- Tasks this week: 6 (5 completed ✅, 1 in-progress ⏳)
- Hours: Planned 20h, Actual 22h (+10%)
- PRD Coverage: 4 FR requirements satisfied
- Blockers: None / [list if any]

Updates Applied:
- MASTER_TASK_REGISTRY.md: 5 tasks marked completed, evidence added
- PHASE_1_TASK_CHECKLIST.md: Week # summary updated
- Weekly_Report_Template.md: Generated for PT + EN versions

Status: Ready for stakeholder update
Next week preview: [tasks planned for next week]
```

---

## 4. REQUIREMENT TRACEABILITY VALIDATION

### When PRD Requirement Maps to Tasks / Quando Requisito PRD Mapeia para Tarefas:

Developer wants to verify: "Did we satisfy FR-008 (Hybrid Retrieval)?"

**Claude's Action:**

1. Open REQUIREMENTS_MAPPING.md → Section "FR-008"
2. List all implementing tasks:
   - T1.3.3 ✅ (BM25 search)
   - T1.3.6 ✅ (Semantic search)
   - T1.4.5 ✅ (RRF fusion)
3. Check status of each task in MASTER_TASK_REGISTRY.md
4. Report:

```
✅ FR-008 REQUIREMENT COVERAGE

Functional Requirement: FR-008 (Hybrid Retrieval Strategy)
Status: 100% Complete in Phase 1

Implementing Tasks:
- T1.3.3: Implement Keyword Search (BM25) — ✅ COMPLETED [evidence: ...]
- T1.3.6: Implement Semantic Search — ✅ COMPLETED [evidence: ...]
- T1.4.5: Implement Hybrid Search (RRF) — ✅ COMPLETED [evidence: ...]

Verification:
- ✅ All 3 sub-components completed
- ✅ RRF fusion combines keyword + semantic (as required)
- ✅ Code in src/maturity_check/hybrid_search.py
- ✅ Tests passing: 15/15

Conclusion: FR-008 SATISFIED ✅
```

---

## 5. PHASE TRANSITION CHECKLIST

### Before Phase 1 → Phase 2 Transition (May 29) / Antes da Transição Phase 1 → Phase 2:

Developer asks: "@Claude: VALIDATE PHASE 1 COMPLETION"

**Claude's Comprehensive Check:**

1. ✅ **All 30 Phase 1 Tasks Complete**
   ```
   T1.1.1–T1.1.6: ✅ (6 tasks)
   T1.2.1–T1.2.6: ✅ (6 tasks)
   T1.3.1–T1.3.6: ✅ (6 tasks)
   T1.4.1–T1.4.6: ✅ (6 tasks)
   T1.5.1–T1.5.6: ✅ (6 tasks)
   Total: 30/30 ✅
   ```

2. ✅ **All Evidence Provided**
   - Code commits: All PRs merged to main ✅
   - Screenshots: 25+ captured (5 per week) ✅
   - Docs: Bilingual versions complete ✅
   - Tests: 90%+ coverage ✅

3. ✅ **Requirements Satisfied**
   - PRD: FR-001 through FR-021 (except Phase 2 only) ✅
   - EPIC: OQ-005, Local_LLM, Hybrid_Retrieval ✅
   - NFR: NFR-001 through NFR-008 ✅
   - OQ: OQ-005 (local Ollama) ✅

4. ✅ **MVP Milestone Reached**
   - Ação 1 evaluation end-to-end works ✅
   - Upload → Retrieve → Evaluate → Report ✅
   - Performance baseline established ✅

5. ✅ **Documentation Complete**
   - README ✅
   - Architecture guide ✅
   - User guide ✅
   - Troubleshooting ✅
   - All bilingual (PT + EN) ✅

6. ✅ **Stakeholder Artifacts Prepared**
   - Report for bosses (PT, non-technical) ✅
   - Report for professor (EN/PT, technical) ✅
   - Demo video (optional) [optional]
   - Phase 2 plan ready ✅

**Claude's Output:**

```
✅ PHASE 1 COMPLETION VALIDATED

All conditions met for Phase 2 start (May 29, 2026):
- 30/30 tasks completed ✅
- All evidence links present ✅
- PRD/EPIC/NFR requirements satisfied ✅
- MVP milestone reached (Ação 1 working) ✅
- Stakeholder artifacts ready ✅

READY TO START PHASE 2 ✅

Phase 2 Block 1 (Actions 2–5) scheduled to begin May 29.
First tasks (T2.1.1 and T2.1.2) ready for assignment.
```

---

## 6. QUICK REFERENCE: KEY FILE LOCATIONS

```
MAIN FILES FOR CLAUDE/COPILOT:

/Plan/08_TASK_REGISTRY/
├── README.md ← START HERE (system overview)
├── MASTER_TASK_REGISTRY.md ← Source of truth (all tasks with IDs, status, requirements)
├── REQUIREMENTS_MAPPING.md ← Reverse lookup (PRD → Tasks, EPIC → Tasks)
├── TASK_UPDATE_TEMPLATE.md ← Template for developer to fill out
├── PHASE_1_TASK_CHECKLIST.md ← Weekly checklist (5 weeks, 30 tasks)
└── PHASE_2_TASK_CHECKLIST.md ← Block-based checklist (26 weeks, ~120 tasks)

RELATED FILES (For context):
├── /Plan/01_PRD/prd.md ← Functional requirements (FR-001 through FR-021)
├── /Plan/07_RETRIEVAL/OQ-005_resolution.md ← LLM architecture decision
├── PHASE_1_DETAILED_PLAN.md ← Narrative description (week-by-week)
└── PHASE_2_DETAILED_PLAN.md ← Narrative description (block-by-block)
```

---

## 7. COMMAND SYNTAX FOR CLAUDE/COPILOT

### Basic Task Update / Atualização Básica de Tarefa:

```
@Claude: UPDATE TASK T1.1.1
Status: completed
Evidence: commit:abc123def456 screenshot:screenshots/vs_code_setup.png doc:docs/VS_CODE_GUIDE.md
Details: Installed VS Code with Python, Pylance extensions. Created setup guide. Verified all extensions working.
Hours: 3
```

### Weekly Close-out / Fechamento Semanal:

```
@Claude: CLOSE WEEK 1
Tasks completed: T1.1.1, T1.1.2, T1.1.3, T1.1.4, T1.1.5, T1.1.6
Evidence: [6 screenshots + 6 doc links]
Hours: 18 (planned 16–20)
Summary: All environment setup complete. Ollama running. Python Anaconda environment active. Database directories created. Ready for Week 2.
```

### Phase Validation / Validação de Fase:

```
@Claude: VALIDATE PHASE 1 COMPLETION
Checklist: All 30 tasks done, all evidence provided, MVP working
Prepare: Phase transition report for stakeholders
```

### Requirement Coverage Check / Verificação de Cobertura:

```
@Claude: VALIDATE FR-008 (Hybrid Retrieval)
Show: Which tasks implement FR-008, their status, evidence
Confirm: Requirement is satisfied
```

---

## 8. ERROR HANDLING

### If Developer Provides Invalid Update / Se Desenvolvedor Fornece Atualização Inválida:

```
@Claude: UPDATE TASK T1.5.1 (LLM Evaluator)
Status: completed
Evidence: [none provided]
Details: Implemented the LLM evaluator in one day!
```

**Claude's Response:**

```
⚠️ VALIDATION ERROR: Missing Required Evidence

Task T1.5.1 - Implement LLM Evaluator (FR-009/010)
Current Status: not-started → Proposed: completed
Issue: No evidence provided for task completion

For a task this size (4-5 hours), please provide:
1. ✅ Git commit hash (code changes)
2. ✅ Test results (pytest output showing tests pass)
3. ✅ Screenshot of evaluator working on sample case
4. ✅ Documentation file (evaluator.py docstring + setup guide)

Cannot update registry without evidence.
Please resubmit with evidence links.
```

---

## 9. AUTOMATION OPPORTUNITIES

### Claude Can Automatically:

1. **Generate Weekly Reports** (Friday EOD)
   - Summarize week's progress
   - List completed tasks
   - Flag blockers
   - Prepare PT summary for bosses + EN summary for professor

2. **Check Task Dependencies**
   - When dev starts a task, verify all prerequisites completed
   - If not, warn: "Task X depends on Y (not yet done)—ok to proceed?"

3. **Track Cumulative Progress**
   - Maintain running count: 30 Phase 1 tasks, X completed (Y%)
   - Show weekly burn-down chart (manual copy to reporting)

4. **Validate Requirement Satisfaction**
   - After task marked complete, verify it maps to ≥1 PRD requirement
   - If not, ask: "Which requirement does this task satisfy?"

5. **Prepare Phase Transition**
   - At May 29, automatically generate "Phase 1 Complete" report
   - At Nov 20, automatically generate "Production Ready" report

---

## 10. EXAMPLE WORKFLOW: DEVELOPER + CLAUDE

### Scenario: Developer Completes T1.2.2 (Database Schema Design)

**Step 1: Developer Creates Schema**
- Designs SQLite schema with 8 tables
- Writes db.py with init_schema() function
- Commits via Git (terminal): `git add . && git commit -m "Add database schema with evidence linking" && git push`
- Takes screenshot of schema diagram
- Writes schema_design.md (PT + EN)

**Step 2: Developer Updates Task**
```
@Claude: UPDATE TASK T1.2.2
Status: completed
Evidence: commit:abc123 screenshot:screenshots/schema_diagram.png doc:docs/schema_design.md
Details: Designed 8-table SQLite schema with foreign keys + WAL mode. Implemented init_schema() function. All tables include: reference_documents, reference_chunks, cases, case_documents, case_chunks, evaluations, evidence_links, audit_log. Foreign keys enabled for data integrity. Documentation bilingual (PT+EN).
Hours: 5
```

**Step 3: Claude Validates**
```
✅ TASK UPDATE VALIDATED

Task: T1.2.2 - Design & Implement SQLite Schema
Status: not-started → completed ✅

Evidence Check:
- ✅ Commit abc123 found in repo (5 files modified)
- ✅ schema_diagram.png in screenshots/ folder
- ✅ schema_design.md exists (bilingual PT+EN, 2000 words)

Requirement Mapping:
- ✅ FR-002 (Data Storage): Schema includes all required tables
- ✅ FR-014 (Evidence Traceability): evidence_links table present
- ✅ Local_LLM_Architecture: SQLite for local storage ✅

Hours: Planned 4–6h, Actual 5h (within estimate) ✅

Registry Updated:
- MASTER_TASK_REGISTRY.md → T1.2.2 marked completed, evidence added
- PHASE_1_TASK_CHECKLIST.md → Week 2, Task 2.2 ✅

Ready for next task (T1.2.3 or T1.2.4 parallel).
```

**Step 4: Developer Continues**
- Next task: T1.2.3 (config.py) or T1.2.4 (db.py functions)
- Weekly checklist progressively fills in
- Friday: Claude closes out week

---

## ✅ SUMMARY FOR CLAUDE/COPILOT

**Your Role / Seu Papel:**

1. **Read & Validate** task updates against MASTER_TASK_REGISTRY.md
2. **Verify Requirements** are satisfied (cross-reference REQUIREMENTS_MAPPING.md)
3. **Update Registry** when validation passes
4. **Track Progress** via checklists (weekly % complete)
5. **Escalate** if blockers or requirement mismatches
6. **Generate Reports** for stakeholders (PT + EN)
7. **Ensure Traceability** — every task linked to PRD/EPIC/NFR
8. **Maintain Quality** — bilingual docs, evidence links, test passing

**You Do NOT Need To:**
- ❌ Write code (developer does that)
- ❌ Make architectural decisions (PRD + EPIC define this)
- ❌ Run tests (developer runs tests, you verify results passed)
- ❌ Create new files (unless updating registry)

**Files You MUST Know:**
- 📖 **MASTER_TASK_REGISTRY.md** — your source of truth
- 🔗 **REQUIREMENTS_MAPPING.md** — verify requirements are met
- ✅ **PHASE_1_TASK_CHECKLIST.md** — track weekly progress
- 📋 **TASK_UPDATE_TEMPLATE.md** — validate developer's submission format

---

**Integration Guide Version 1.0**  
**Created:** 28 April 2026  
*Use this guide to understand how Claude/Copilot helps maintain task tracking, traceability, and quality throughout Phase 1 and Phase 2.*
