# TASK UPDATE TEMPLATE / MODELO DE ATUALIZAÇÃO DE TAREFA

Bilingual: **Portuguese (PT) / English (EN)**

---

## 📋 COMO USAR / HOW TO USE

1. **Copiar este template** abaixo
2. **Preencher todos os campos** (PT + EN)
3. **Adicionar evidências** (commit hash, screenshot path, doc link)
4. **Compartilhar com Claude/Copilot** com comando: `@Claude: UPDATE TASK [ID]`
5. **Claude irá validar** e atualizar MASTER_TASK_REGISTRY.md

---

## ✏️ TEMPLATE

```
==============================================
TASK UPDATE FORM / FORMULÁRIO DE ATUALIZAÇÃO
==============================================

DATE / DATA: [Date in format DD/MM/YYYY]
DEVELOPER / DESENVOLVEDOR: [Your name]
TASK ID / ID DA TAREFA: [ex: T1.1.1]

---

## 1. TASK INFORMATION / INFORMAÇÕES DA TAREFA

**Task Name (EN) / Nome da Tarefa (PT):**
[Brief name in English and Portuguese]

**Current Status / Status Atual:**
- [ ] not-started (não iniciada)
- [ ] in-progress (em progresso)
- [ ] completed (completa)
- [ ] blocked (bloqueada)
- [ ] deferred (adiada)

**New Status / Novo Status:**
[Select new status above]

---

## 2. WHAT WAS DONE / O QUE FOI FEITO

### English Version:
[Describe in detail what was accomplished. Include:
- What code was written/modified
- What tests were run
- What documentation was created
- Any blockers encountered
- Estimated time spent vs. planned
]

### Versão em Português:
[Descrever em detalhes o que foi realizado. Incluir:
- Qual código foi escrito/modificado
- Que testes foram executados
- Qual documentação foi criada
- Qualquer bloqueador encontrado
- Tempo estimado gasto vs. planejado
]

---

## 3. DELIVERABLES / ENTREGÁVEIS

List all deliverables produced (code files, docs, screenshots, etc.):

| Deliverable / Entregável | Location / Localização | Status / Status |
|---|---|---|
| [ex: CLI command] | `src/maturity_check/cli.py` | ✅ Complete |
| [ex: Documentation] | `docs/CLI_GUIDE.md` | ✅ Complete |
| [ex: Screenshot] | `screenshots/week1_setup.png` | ✅ Complete |
| | | |

---

## 4. EVIDENCE / EVIDÊNCIA

Provide proof of completion. Include:

### Code Evidence (Código):
- **Commit Hash / Hash do Commit:** [ex: abc123def456]
- **Repository / Repositório:** GitHub Maturity_Check
- **Branch / Ramo:** [ex: main, week1-setup]
- **Files Modified / Arquivos Modificados:**
  - `src/maturity_check/cli.py`
  - `src/maturity_check/db.py`
  - [add more...]

### Documentation Evidence (Documentação):
- **File Path / Caminho:** `docs/ARCHITECTURE.md` or `Plan/08_TASK_REGISTRY/...`
- **Bilingual / Bilíngue:** ☐ PT only / ☐ EN only / ☑ PT + EN

### Screenshots / Prints de Tela:
- **File Path / Caminho:** `screenshots/week1_setup_complete.png`
- **What Shows / O que Mostra:** [Brief description of what the screenshot demonstrates]
- **Format / Formato:** PNG / JPEG / GIF

### Test Results / Resultados de Testes:
- **Test Framework / Framework de Teste:** pytest / unittest / [other]
- **Tests Passed / Testes Passaram:** [X] of [Y] tests (XX%)
- **Test Report / Relatório de Testes:** `logs/test_report.txt` or `logs/pytest_output.log`
- **Coverage / Cobertura:** [X]% (if applicable)

---

## 5. REQUIREMENT MAPPING / MAPEAMENTO DE REQUISITOS

Validate that this task satisfies its requirements:

### PRD Requirements Implemented / Requisitos PRD Implementados:
- [ ] FR-001 (if applicable) → Describe how / Descrever como
- [ ] FR-008 (if applicable) → Describe how / Descrever como
- [ ] [Add more FR numbers if applicable]

### EPIC Decisions Respected / Decisões EPIC Respeitadas:
- [ ] Local_LLM_Architecture → How implemented / Como implementado
- [ ] OQ-005_Resolution → How respected / Como respeitado
- [ ] [Add others if applicable]

---

## 6. BLOCKERS & NOTES / BLOQUEADORES E NOTAS

### Blockers / Bloqueadores:
- [ ] No blockers / Sem bloqueadores
- [ ] Blocked by: [Describe what is blocking and expected resolution]

### Dependencies for Next Tasks / Dependências para Próximas Tarefas:
[List any tasks that depend on this task being completed]

### Notes / Notas:
[Any additional information: lessons learned, decisions made, recommendations for next week, etc.]

---

## 7. TIME TRACKING / RASTREAMENTO DE HORAS

| Activity / Atividade | Estimated / Estimado | Actual / Real | Variance / Variação | Notes / Notas |
|---|---|---|---|---|
| Planning / Planejamento | [X]h | [Y]h | ±[Z]h | |
| Implementation / Implementação | [X]h | [Y]h | ±[Z]h | |
| Testing / Testes | [X]h | [Y]h | ±[Z]h | |
| Documentation / Documentação | [X]h | [Y]h | ±[Z]h | |
| **TOTAL / TOTAL** | [X]h | [Y]h | ±[Z]h | |

---

## 8. WEEK CHECKLIST / CHECKLIST DA SEMANA

Mark checklist items for this task:

- [ ] Code committed to GitHub (commit hash provided above)
- [ ] All deliverables produced and linked
- [ ] Documentation bilingual (PT + EN) where required
- [ ] Screenshots captured and stored
- [ ] Tests passed and documented
- [ ] PRD requirements verified
- [ ] EPIC decisions respected
- [ ] No blockers remaining
- [ ] Time tracking filled in
- [ ] Ready for code review (if applicable)

---

## 9. APPROVAL / APROVAÇÃO

### Code Review / Revisão de Código:
- Reviewer / Revisor: [Name or "Claude/Copilot"]
- Status: ☐ Approved / ☐ Needs changes / ☐ Not yet reviewed

### Requirement Validation / Validação de Requisitos:
- Validator / Validador: [Name or "Claude/Copilot"]
- Status: ☐ Satisfied / ☐ Partially satisfied / ☐ Not satisfied

### Week Closure / Fechamento da Semana:
- [ ] All tasks for this week completed
- [ ] All deliverables for week produced
- [ ] Weekly report generated (PT + EN)
- [ ] Time log reconciled
- [ ] Next week plan confirmed

---

## 🔄 NEXT STEPS / PRÓXIMOS PASSOS

### For Next Task / Para Próxima Tarefa:
[ID of next task to work on]

### For Next Week / Para Próxima Semana:
[Brief summary of what will be accomplished]

### For Stakeholder Update / Para Atualização de Stakeholders:
[2-3 sentences in Portuguese for your bosses, highlighting what changed visibly this week]

---

## 📧 SUBMISSION / ENVIO

To submit this update to Claude/Copilot:

**COMMAND / COMANDO:**
```
@Claude: UPDATE TASK [T1.1.1] 
Status: [in-progress|completed]
Evidence: [commit:abc123] [screenshot:path/to/file.png] [doc:path/to/file.md]
Details: [Paste contents of section 2 above]
```

**EXAMPLE / EXEMPLO:**
```
@Claude: UPDATE TASK T1.1.1
Status: completed
Evidence: commit:abc123def screenshot:screenshots/vs_code_setup.png doc:docs/VS_CODE_GUIDE.md
Details: Installed VS Code with Python, Pylance, Git Graph extensions on Windows 11. Created detailed installation guide (PT+EN). Verified all extensions working correctly with test workspace.
```

---

## 📋 CHECKLIST PARA SUBMISSÃO / SUBMISSION CHECKLIST

Before submitting / Antes de enviar:

- [ ] All sections filled (1-9)
- [ ] Bilingual content where required (PT + EN)
- [ ] Evidence links are correct and accessible
- [ ] No incomplete fields marked with [ex: ...]
- [ ] Time tracking is realistic and honest
- [ ] Blockers clearly described if any
- [ ] Screenshots captured and stored in proper folder
- [ ] Code committed with meaningful message
- [ ] Documentation updated in both languages

---

**NOTA IMPORTANTE / IMPORTANT NOTE:**

This template ensures complete traceability and professional documentation. Fill it out thoroughly for each task completion. Claude/Copilot will validate your submission and update the master registry automatically.

Use this for EVERY task completion to maintain transparency and enable proper stakeholder reporting (Portuguese for bosses, full technical details for professor).

---

*Template Version 1.0 — Created 28 April 2026*
*Last Updated: [Update this when you use the template]*
```

---

## ⚡ QUICK REFERENCE

**When to use this template:**
- ✅ Every time you complete a task
- ✅ When moving task status (not-started → in-progress OR in-progress → completed)
- ✅ For weekly closure (Friday end-of-week)
- ✅ When blocked (describe blocker in section 6)

**NOT when to use:**
- ❌ For daily checkpoints (use git commits instead)
- ❌ For sub-task items (only for formal tasks T#.#.#)

---

**Copilot/Claude will verify:**
1. ✅ Task ID exists in MASTER_TASK_REGISTRY.md
2. ✅ Status transition is valid (not-started → in-progress → completed)
3. ✅ Evidence is provided and accessible
4. ✅ PRD requirements are covered
5. ✅ EPIC decisions are respected
6. ✅ All fields are bilingual if required

---

**In case of failure to validate:**
- ❌ Claude will request clarification
- ❌ Will ask for missing evidence
- ❌ Will check PRD mapping
- ❌ Will not update registry until all validation passes

---

*Use this template religiously for perfect tracking.*
