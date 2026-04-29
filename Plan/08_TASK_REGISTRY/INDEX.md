# TASK REGISTRY SYSTEM — COMPLETE DOCUMENTATION INDEX

**Folder Name / Nome da Pasta:** `Plan/08_TASK_REGISTRY`  
**Created / Criado:** 28 de Abril de 2026  
**Version / Versão:** 1.0  
**Status:** ✅ Production Ready  
**Total Files / Arquivos Totais:** 7 files (~93 KB of documentation)

---

## 🎯 OBJECTIVE / OBJETIVO

Este sistema centralizado permite que **você e Claude/Copilot** rastreiem, validem e atualizem todas as ~150 tarefas do projeto **independentemente da semana/fase**, mantendo **rastreabilidade completa** para requisitos PRD, decisões EPIC, e arquitetura MDAP.

**This centralized system allows you and Claude/Copilot to track, validate, and update all ~150 project tasks independently of week/phase while maintaining complete traceability to PRD requirements, EPIC decisions, and MDAP architecture.**

---

## 📁 FILE STRUCTURE / ESTRUTURA DE ARQUIVOS

```
Plan/08_TASK_REGISTRY/
├── README.md ⭐ START HERE
│   └─ Overview of entire system
│   └─ How to use + interaction flow
│   └─ 7 KB / ~1,500 words
│
├── MASTER_TASK_REGISTRY.md ⭐ SOURCE OF TRUTH
│   └─ Complete list of all ~150 tasks
│   └─ Task ID, phase, week, PRD mapping, EPIC mapping, status, deliverables
│   └─ Phase 1: 30 tasks (detailed)
│   └─ Phase 2: ~120 tasks (summary structure)
│   └─ 19 KB / ~4,500 words
│
├── REQUIREMENTS_MAPPING.md ⭐ INVERSE INDEX
│   └─ PRD Requirement → Which tasks implement it
│   └─ EPIC Decision → Which tasks are affected
│   └─ NFR Constraint → Which tasks respect it
│   └─ Complete requirement traceability
│   └─ 19 KB / ~4,000 words
│
├── TASK_UPDATE_TEMPLATE.md ⭐ BILINGUAL FORM
│   └─ Template for you to fill when completing tasks
│   └─ Bilingual (PT + EN)
│   └─ Includes: deliverables, evidence, time tracking, approvals
│   └─ Instructions for submitting to Claude/Copilot
│   └─ 9 KB / ~2,000 words
│
├── PHASE_1_TASK_CHECKLIST.md ⭐ WEEKLY TRACKER
│   └─ Week-by-week breakdown (5 weeks × 6 tasks = 30 tasks)
│   └─ Daily + weekly status + evidence tracking
│   └─ Deliverables checklist per week
│   └─ Phase 1 final validation checklist
│   └─ 9 KB / ~2,500 words
│
├── PHASE_2_TASK_CHECKLIST.md ⭐ BLOCK TRACKER
│   └─ Block-by-block breakdown (7 blocks × 4 weeks)
│   └─ 46 M5D actions distributed across blocks
│   └─ Summary statistics per block
│   └─ Phase 2 final deployment checklist
│   └─ 14 KB / ~3,500 words
│
└── CLAUDE_COPILOT_INTEGRATION_GUIDE.md ⭐ AI ASSISTANT MANUAL
    └─ Instructions for Claude/Copilot on how to use this system
    └─ Validation procedures when tasks are submitted
    └─ Requirement traceability checking
    └─ Weekly close-out automation
    └─ Error handling + command syntax
    └─ 16 KB / ~3,500 words
```

---

## 🚀 QUICK START / INÍCIO RÁPIDO

### For You (Developer) / Para Você (Desenvolvedor):

1. **Read** `README.md` (5 min) ← System overview
2. **This Week** ← Use `PHASE_1_TASK_CHECKLIST.md` Week X section daily
3. **Task Complete** ← Fill `TASK_UPDATE_TEMPLATE.md` and submit to Claude
4. **Friday EOD** ← Update weekly checklist and close out week
5. **Next Week** ← Proceed to next week section

### For Claude/Copilot / Para Claude/Copilot:

1. **Read** `CLAUDE_COPILOT_INTEGRATION_GUIDE.md` (understand role)
2. **When Dev Submits** ← Validate against `MASTER_TASK_REGISTRY.md`
3. **Verify Requirements** ← Cross-check with `REQUIREMENTS_MAPPING.md`
4. **Update Registry** ← Mark task complete with evidence
5. **Track Progress** ← Update `PHASE_1_TASK_CHECKLIST.md` or `PHASE_2_TASK_CHECKLIST.md`

---

## 📊 CONTENT SUMMARY / RESUMO DE CONTEÚDO

### MASTER_TASK_REGISTRY.md (THE SOURCE OF TRUTH)

**What it contains:**
- All ~150 tasks with unique IDs (T[Phase].[Week].[Number])
- For each task:
  - Name (EN) + Name PT
  - Phase + Week assignment
  - PRD Requirements (FR-###) it implements
  - EPIC Decisions it supports
  - Current Status (not-started / in-progress / completed / blocked)
  - Deliverables (code/doc/screenshot required)
  - Estimated Hours
  - Evidence Links (commit hash, screenshot path, doc link)
  - Dependencies (what must be done first)
  - Notes (blockers, decisions, lessons)

**Phase 1 Detail:** All 30 tasks described in full detail (2-3 paragraphs each)  
**Phase 2 Summary:** Tasks grouped by block; first few detailed, rest summarized

**You use this to:**
- ✅ Know what task T1.2.4 does + its requirements
- ✅ Track which tasks are blocked vs. completed
- ✅ Find evidence links for code review
- ✅ See task dependencies before starting work

**Claude uses this to:**
- ✅ Validate task updates (is this a real task?)
- ✅ Check requirement satisfaction
- ✅ Verify evidence is provided
- ✅ Flag dependency issues

---

### REQUIREMENTS_MAPPING.md (THE INVERSE INDEX)

**What it contains:**
- **Functional Requirements (FR-001 through FR-021)**
  - Which Phase 1 tasks implement each FR
  - Which Phase 2 blocks implement each FR
  - Current status (complete / partial / deferred)

- **EPIC Decisions**
  - Local_LLM_Architecture → which tasks build it
  - OQ-005_Resolution → which tasks use it
  - Hybrid_Retrieval_Strategy → which tasks enable it

- **NFR Constraints**
  - Performance targets (< 500ms retrieval)
  - Data integrity (WAL mode, foreign keys)
  - Compliance (audit trail, UNCERTAINTY flags)
  - Which tasks satisfy each NFR

- **Dependency Graph**
  - T1.1.1 → T1.1.2 → ... → T1.5.6
  - Visual flowchart showing task sequence

**You use this to:**
- ✅ Verify: "Does my code satisfy FR-008?"
- ✅ Understand: "Why does this task exist?"
- ✅ Confirm: "What other tasks touch hybrid retrieval?"

**Claude uses this to:**
- ✅ Validate that completed tasks satisfy their requirements
- ✅ Identify related tasks
- ✅ Check cross-requirements (e.g., FR-008 + OQ-005)

---

### TASK_UPDATE_TEMPLATE.md (BILINGUAL FORM)

**What it contains:**
- Template form (copy + fill) with sections:
  1. Task information + status
  2. What was accomplished (EN + PT)
  3. Deliverables produced (code/doc/screenshot)
  4. Evidence (commit hash, screenshot path, doc link)
  5. Requirement mapping validation
  6. Blockers & dependencies
  7. Time tracking (estimated vs. actual)
  8. Weekly checklist completion
  9. Approval sign-off
  10. Next steps

- Instructions: How to submit to Claude/Copilot
- Example submission

**You use this to:**
- ✅ Document task completion consistently
- ✅ Provide evidence for code review
- ✅ Verify requirements are satisfied before submitting
- ✅ Track time spent vs. estimated

**Claude uses this to:**
- ✅ Standardize validation (know what fields to check)
- ✅ Extract evidence links easily
- ✅ Verify bilingual content requirement

---

### PHASE_1_TASK_CHECKLIST.md (WEEKLY TRACKER)

**What it contains:**
- 5 week sections (Week 1 through Week 5)
- Each week:
  - 6 tasks with status tracking
  - Hours planned + actual
  - Evidence column (for commit hash, screenshot path, doc link)
  - Deliverables checklist
  - Blockers section
  - Weekly summary (PT + EN)

- Table format for daily/weekly updates
- Estimated vs. actual hours comparison
- Phase 1 final validation checklist (all 30 tasks + evidence + docs)

**You use this to:**
- ✅ Know what tasks are due this week
- ✅ Check off tasks as you complete them daily
- ✅ Track deliverables (screenshots, docs)
- ✅ Estimate vs. actual comparison for planning
- ✅ Friday: Summarize week's progress (PT for bosses, EN for professor)

**Claude uses this to:**
- ✅ Validate weekly close-outs
- ✅ Track cumulative progress (X/30 tasks done)
- ✅ Generate weekly reports
- ✅ Flag weeks that are behind/ahead of plan

---

### PHASE_2_TASK_CHECKLIST.md (BLOCK TRACKER)

**What it contains:**
- 7 Block sections (Block 1 through Block 7)
- Each block:
  - ~4 weeks of work
  - 2-5 M5D actions covered
  - Task table with ID, name, status, hours
  - Key features (tiered expansion, satisficing, UNCERTAINTY, web UI, Groq, deployment)
  - Deliverables for block
  - Block summary (PT + EN)

- 26-week timeline split into manageable chunks
- Performance targets + deployment checklist
- Success criteria

**You use this to:**
- ✅ Plan Phase 2 block by block
- ✅ Track 4-week progress per block
- ✅ See how 46 actions are distributed
- ✅ Understand web UI timeline, Groq integration, deployment

**Claude uses this to:**
- ✅ Track Phase 2 blocks (4 weeks per block)
- ✅ Validate block completion before moving to next
- ✅ Generate block-level reports (vs. weekly for Phase 1)

---

### CLAUDE_COPILOT_INTEGRATION_GUIDE.md (AI MANUAL)

**What it contains:**
- Section 1: How Claude should validate task updates
  - Task lookup → status validation → evidence check → requirement mapping → bilingual check → hours plausibility

- Section 2: Dependency resolution
  - Check if prerequisite tasks completed
  - Alert on dependent tasks

- Section 3: Weekly close-out process
  - Verify all tasks accounted for
  - Validate evidence completeness
  - Time tracking reconciliation
  - Requirements coverage check
  - Generate weekly report template

- Section 4: Requirement traceability validation
  - Look up FR requirement in REQUIREMENTS_MAPPING.md
  - List all implementing tasks + their status
  - Report coverage percentage

- Section 5: Phase transition checklist
  - Before May 29 (Phase 1→2)
  - Before Nov 20 (Phase 2 complete → production)

- Section 6: Command syntax
  - Task update format
  - Weekly close-out format
  - Validation format
  - Requirement check format

- Section 7: Error handling
  - Invalid updates + Claude's response

- Section 8-10: Automation opportunities, example workflow, summary

**Claude uses this to:**
- ✅ Understand its role in the task tracking system
- ✅ Know how to validate submissions
- ✅ Automate weekly reporting + phase transitions
- ✅ Handle errors gracefully

---

## 📋 TASK IDENTIFICATION SCHEME

```
T[Phase].[Week].[TaskNumber]

Examples:
- T1.1.1 = Phase 1, Week 1, Task 1 (VS Code setup)
- T1.5.6 = Phase 1, Week 5, Task 6 (MVP docs)
- T2.1.3 = Phase 2, Block 1 (Week 1-4), Task 3
- T2.7.2 = Phase 2, Block 7 (Week 25-26), Task 2 (deployment)
```

---

## 🔄 WORKFLOW: HOW EVERYTHING FITS TOGETHER

### Daily / Diário:
1. Open `PHASE_1_TASK_CHECKLIST.md` Week X section
2. Work on tasks T1.X.1 through T1.X.6
3. Commit code daily to GitHub
4. Take screenshots when milestones reached

### Friday EOD / Sexta-feira Fim do Dia:
1. Fill `TASK_UPDATE_TEMPLATE.md` for each completed task
2. Submit to Claude: `@Claude: UPDATE TASK T1.X.Y Status: completed Evidence: [...]`
3. Claude validates + updates `MASTER_TASK_REGISTRY.md`
4. Claude updates `PHASE_1_TASK_CHECKLIST.md` Week X summary
5. Claude generates weekly report (PT + EN)
6. You send report to bosses (PT) + professor (EN)

### Monday / Segunda-feira:
1. Review Claude's weekly validation report
2. Fix any issues flagged
3. Plan Week X+1 tasks
4. Continue cycle

### May 29 (Phase 1→2 Transition) / 29 de Maio:
1. Claude runs: `@Claude: VALIDATE PHASE 1 COMPLETION`
2. Claude verifies all 30 tasks done + evidence complete
3. Claude generates Phase 1 completion report
4. You distribute to stakeholders
5. Start Phase 2, Block 1 using `PHASE_2_TASK_CHECKLIST.md`

### Every 4 Weeks / A Cada 4 Semanas (Phase 2):
1. Complete Phase 2 block (T2.X.1 through T2.X.Y)
2. Claude validates block completion
3. Claude generates block report
4. Move to next block

### November 20 (Phase 2 Complete) / 20 de Novembro:
1. Claude runs: `@Claude: VALIDATE PHASE 2 COMPLETION`
2. Claude verifies all 46 actions + deployment checklist
3. Claude generates Production Ready report
4. System deployed to Rio municipal server

---

## ✅ WHEN TO USE EACH FILE

| Situation | File to Use | Action |
|-----------|-------------|--------|
| "What tasks are due this week?" | PHASE_1_TASK_CHECKLIST.md | Check Week X section |
| "What does task T1.2.4 require?" | MASTER_TASK_REGISTRY.md | Look up T1.2.4 entry |
| "Does FR-008 requirement satisfied?" | REQUIREMENTS_MAPPING.md | Look up FR-008, check tasks |
| "I'm completing T1.2.4" | TASK_UPDATE_TEMPLATE.md | Fill form + submit to Claude |
| "Claude, validate my update" | MASTER_TASK_REGISTRY.md + REQUIREMENTS_MAPPING.md | Claude cross-references both |
| "How should Copilot help?" | CLAUDE_COPILOT_INTEGRATION_GUIDE.md | Claude reads this file |
| "System overview" | README.md | Start here for first time |

---

## 🎯 SUCCESS METRICS

### Phase 1 (May 29 Target):
- ✅ 30/30 tasks completed (100%)
- ✅ All evidence links present
- ✅ All PRD/EPIC/NFR requirements satisfied
- ✅ Ação 1 evaluation end-to-end works
- ✅ Bilingual documentation complete
- ✅ All weekly reports delivered (PT + EN)

### Phase 2 (Nov 20 Target):
- ✅ All 46 actions implemented (~120 tasks)
- ✅ Web UI deployed
- ✅ Performance optimized
- ✅ Deployed to Rio server
- ✅ Operational and ready for daily use

### System Quality:
- ✅ 100% requirement traceability (every task → FR/EPIC/NFR)
- ✅ 100% evidence documentation (every task → git/screenshot/doc)
- ✅ 0 blockers remaining (all issues resolved before phase closure)
- ✅ Bilingual delivery (PT for bosses, EN/PT for professor)

---

## 📞 SUPPORT & ESCALATION

### If Task is Blocked / Se Tarefa está Bloqueada:

1. Open task in `MASTER_TASK_REGISTRY.md`
2. Set status to `blocked`
3. Add blocker_reason: "Waiting for Ollama installation"
4. Submit to Claude: `@Claude: BLOCKED TASK T1.X.Y`
5. Claude will flag for escalation

### If Requirement is Not Satisfied / Se Requisito Não é Satisfeito:

1. Check `REQUIREMENTS_MAPPING.md` for requirement
2. List all tasks that should implement it
3. Check status of each task in `MASTER_TASK_REGISTRY.md`
4. If tasks incomplete, schedule them sooner
5. If task complete but requirement not met, file issue

### If Task Takes Longer Than Estimate / Se Tarefa Demora Mais:

1. After 1.5× estimated hours, submit blockers update to Claude
2. Claude flags potential risk
3. If <5% behind: continue
4. If >5% behind: escalate + adjust timeline
5. End of week: document lessons learned for Phase 2 estimation

---

## 🎓 TRAINING MATERIALS FOR STAKEHOLDERS

### For Your 2 Bosses (Non-Technical) / Para Seus 2 Chefes:
- Read: `README.md` (5 min overview)
- Review: Weekly reports generated by Claude (PT section)
- Check: Progress dashboard (X/30 tasks complete)

### For Your Master's Professor (Technical) / Para Seu Professor:
- Read: `README.md` + `CLAUDE_COPILOT_INTEGRATION_GUIDE.md` (15 min)
- Review: `MASTER_TASK_REGISTRY.md` for complete task list
- Check: `REQUIREMENTS_MAPPING.md` for traceability to PRD/EPIC
- Examine: Code commits linked in evidence sections

---

## 📝 VERSION HISTORY / HISTÓRICO DE VERSÃO

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 28 Apr 2026 | Initial creation; 7 files total; ~93 KB documentation |

---

## 🚀 NEXT IMMEDIATE ACTIONS / PRÓXIMAS AÇÕES IMEDIATAS

1. **You (Developer):**
   - [ ] Read `README.md` (5 min)
   - [ ] This week: Use `PHASE_1_TASK_CHECKLIST.md` Week 1 section daily
   - [ ] Friday EOD: Fill `TASK_UPDATE_TEMPLATE.md` for each task completed
   - [ ] Submit to Claude: `@Claude: UPDATE TASK [ID] Status: [status] Evidence: [links]`

2. **Claude/Copilot:**
   - [ ] Read `CLAUDE_COPILOT_INTEGRATION_GUIDE.md`
   - [ ] Understand role: validate → update registry → track progress
   - [ ] When dev submits: cross-check MASTER_TASK_REGISTRY.md + REQUIREMENTS_MAPPING.md
   - [ ] Friday EOD: auto-generate weekly report

3. **Both (Together):**
   - [ ] May 29: Run Phase 1 completion validation
   - [ ] Nov 20: Run Phase 2 completion + deployment checklist
   - [ ] Every Sunday: Review weekly progress + adjust Phase 2 blocks if needed

---

## ✨ FINAL NOTES / NOTAS FINAIS

This task registry system is designed for **maximum transparency + traceability + automation**:

✅ **Transparency:** Everyone (you, Claude, bosses, professor) can see exactly what tasks exist, their status, and what they require  
✅ **Traceability:** Every task links to PRD requirements, EPIC decisions, and code/docs as evidence  
✅ **Automation:** Claude handles validation, registry updates, and report generation automatically  

**Use this system religiously.** Every task completion:
1. Gets validated for requirement satisfaction
2. Gets linked to code/docs as evidence
3. Gets tracked in cumulative progress
4. Gets reported to stakeholders (PT + EN)

By November 20, you'll have **100% audit trail** showing how each line of code satisfies business requirements.

---

**Folder Created:** 28 April 2026  
**System Status:** ✅ Ready for Production  
**Total Documentation:** 93 KB across 7 files  
**Next Milestone:** May 29 (Phase 1 MVP) → November 20 (Full Production Deployment)

*Let's build something transparent, traceable, and excellent.* 🚀

---

**📧 Questions? Use this folder as your single source of truth.**
