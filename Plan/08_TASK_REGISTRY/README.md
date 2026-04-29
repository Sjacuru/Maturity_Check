# 📋 TASK REGISTRY — Sistema de Rastreamento de Tarefas / Task Tracking System

**Versão / Version:** 1.0  
**Data / Date:** 28 de Abril de 2026 / April 28, 2026  
**Propósito / Purpose:** Centralizar e gerenciar todas as tarefas do projeto, mapeando-as para requisitos PRD/EPIC/MDAP e permitindo atualização independente de semana/fase  

---

## 🎯 OBJETIVO / OBJECTIVE

Permitir que **você** e **Claude/Copilot** rastreiem, atualizem e validem tarefas de forma independente da semana em que pertencem, mantendo rastreabilidade completa para requisitos de negócio (PRD), arquitetura (EPIC) e plano detalhado (MDAP).

**Enable you and Claude/Copilot to track, update, and validate tasks independently of the week they belong to, maintaining full traceability to business requirements (PRD), architecture (EPIC), and detailed plan (MDAP).**

---

## 📁 ARQUIVOS NESTA PASTA / FILES IN THIS FOLDER

### 1. **TASK_TRACKING_GUIDE.md** 
Guia de uso para você e para Claude/Copilot.  
*How to use this system — for you and Claude/Copilot.*

### 2. **MASTER_TASK_REGISTRY.md**
Lista mestra de todas as ~150+ tarefas com:
- Task ID único  
- Nome + Descrição
- Phase/Week
- PRD Requirement Mapping
- EPIC Requirement Mapping
- Status (not-started / in-progress / completed)
- Deliverables (o que deve ser entregue)
- Estimated Hours  
- Completion Evidence (links para código, docs, screenshots)

*Master list of all ~150+ tasks with unique IDs, phase mapping, requirement traceability, status, deliverables, hours, and evidence.*

### 3. **REQUIREMENTS_MAPPING.md**
Mapeamento inverso: PRD Requirement → Tasks que implementam  
EPIC Decision → Tasks afetadas  
NFR/FR → Task assignments

*Inverse mapping: which tasks implement which requirements.*

### 4. **TASK_UPDATE_TEMPLATE.md**
Template bilíngue (PT + EN) para você atualizar tarefas:
- Como marcar como in-progress / completed
- Como referenciar código/docs/screenshots  
- Como validar contra requisitos
- Como escalar bloqueadores

*Bilingual template for updating task status with evidence.*

### 5. **PHASE_1_TASK_CHECKLIST.md**
Checklist específico Phase 1 (Semana 1-5) com 30 tarefas.

### 6. **PHASE_2_TASK_CHECKLIST.md**
Checklist específico Phase 2 (26 semanas) com ~120 tarefas.

---

## 🔄 FLUXO DE USO / USAGE FLOW

### Para Você (Developer) / For You:

1. **Abrir MASTER_TASK_REGISTRY.md**
   - Encontrar tarefa pelo ID (ex: `T1.1`, `T2.3`)
   - Ver status atual, fase, requisitos relacionados
   - Clicar em links para PRD/EPIC docs

2. **Atualizar Tarefa**
   - Use template em `TASK_UPDATE_TEMPLATE.md`
   - Marque status: `not-started` → `in-progress` → `completed`
   - Adicione evidência: commit hash, screenshot path, doc link
   - Copie a entrada atualizada para MASTER_TASK_REGISTRY.md

3. **Ver Progresso**
   - Abrir PHASE_1_TASK_CHECKLIST.md ou PHASE_2_TASK_CHECKLIST.md
   - Filtrar por semana/status
   - Ver quantas tarefas completadas vs. planejado

4. **Validar Requisitos**
   - Abrir REQUIREMENTS_MAPPING.md
   - Confirmar que tarefas completadas cobrem PRD requirement
   - Antes de finalizar semana, rodar checklist

### Para Claude/Copilot / For Claude/Copilot:

1. **Ler TASK_TRACKING_GUIDE.md**
   - Entender estrutura de Task ID, Phase, Status
   - Aprender formato de Evidence links
   - Conhecer regras de mapping (PRD → Task, EPIC → Task)

2. **Ao Receber Comando do Developer**
   - Ex: "Update task T2.4 to completed with code commit abc123"
   - Procurar T2.4 em MASTER_TASK_REGISTRY.md
   - Validar que status change é válido (ex: in-progress → completed)
   - Validar que evidência é fornecida
   - Validar que task completada cobre PRD requirement
   - Atualizar MASTER_TASK_REGISTRY.md com nova evidência
   - Atualizar PHASE_1_TASK_CHECKLIST.md ou PHASE_2_TASK_CHECKLIST.md
   - Confirmar ao developer

3. **Ao Implementar Nova Feature**
   - Mapear feature para task ID (ex: "hybrid search" = T4.5)
   - Confirmar requisitos (T4.5 deve cobrir FR-008)
   - Após código pronto, atualizar registry com commit hash

4. **Ao Fazer PR Review**
   - Validar que código mapeia para task IDs
   - Verificar se evidence é completo
   - Confirmar que PRD requirements são satisfeitos

---

## 📊 ESTRUTURA DE TASK ID

```
T[Phase].[Week].[TaskNumber]

Exemplos:
- T1.1.1 = Phase 1, Week 1, Task 1 (VS Code + Extensões)
- T1.5.4 = Phase 1, Week 5, Task 4 (Interface Relatório)
- T2.2.3 = Phase 2, Block 2, Task 3 (Ação 3–5 Implementation)
```

---

## 🔗 RASTREABILIDADE / TRACEABILITY

Cada tarefa tem mapeamento bidirecional:

```
Task T1.1.1
  ↓ implements ↓
PRD Requirement FR-001 (System initialization)
  ↓ fulfills ↓
EPIC Decision Local_LLM_Architecture
  ↓ deliverables ↓
- vs_code_setup.md
- requirements.txt
- venv_created_screenshot.png
```

---

## ✅ COMO VALIDAR / HOW TO VALIDATE

**Antes de completar uma tarefa / Before marking a task completed:**

1. ✅ Status atualizado em MASTER_TASK_REGISTRY.md?
2. ✅ Evidência fornecida (commit, screenshot, doc)?
3. ✅ PRD requirement satisfeito (link em REQUIREMENTS_MAPPING.md)?
4. ✅ EPIC decision respeitado (checklist em task)?
5. ✅ Checklist semana atualizado (PHASE_1_TASK_CHECKLIST.md)?

---

## 🎯 COMANDO PARA CLAUDE/COPILOT

Quando você quiser que Claude atualize tarefas, use este comando:

```
@Claude: Update task [ID] status to [STATUS] with evidence [LINK/HASH/SCREENSHOT]
Example: @Claude: Update task T1.1.1 status to completed with evidence commit:abc123 doc:vs_code_setup.md screenshot:setup_complete.png
```

Claude will then:
1. ✅ Locate task in MASTER_TASK_REGISTRY.md
2. ✅ Validate status transition
3. ✅ Update entry with evidence
4. ✅ Update weekly checklist
5. ✅ Confirm completion message

---

## 📞 ESCALAÇÃO / ESCALATION

Se tarefa está bloqueada ou atrasada:

1. Abra task em MASTER_TASK_REGISTRY.md
2. Mude status para `blocked` (novo status)
3. Adicione `blocker_reason`: "ex: waiting for Ollama installation"
4. Claude verá `blocked` e pedirá ajuda

---

## 🚀 COMEÇAR / GET STARTED

1. **Leia** TASK_TRACKING_GUIDE.md (5 minutos)
2. **Verifique** MASTER_TASK_REGISTRY.md seção Phase 1, Week 1 (10 minutos)
3. **Este semana:** Use PHASE_1_TASK_CHECKLIST.md como dia-a-dia reference
4. **Diariamente:** Commit código + adicione evidência
5. **Sexta-feira:** Conclua todas tarefas semana + update checklists

---

## 📝 VERSÃO HISTÓRICO / VERSION HISTORY

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 28 Abr 2026 | Initial creation |

---

**Sistema criado para máxima clareza e rastreabilidade.**  
*System created for maximum clarity and traceability.*
