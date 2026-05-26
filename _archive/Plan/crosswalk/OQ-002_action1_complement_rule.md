# OQ-002 — Complement linkage for **Ação 1** (provisional rule)

**Status:** Partial resolution for `action_1` only; other actions need the same pattern when crosswalks exist.

**Source:** [M5D.md](../M5D.md) — Capítulo 3, Ação 1 (pp. 38–42 in guide flow; line refs ~1751–1847 in repo copy).

## Rule

| Crosswalk `subtask.id` | M5D «O que você deve fazer?» | `complement_text_pt` |
|------------------------|------------------------------|----------------------|
| **1.1** | item **i** | `null` (no Quadro/Anexo named solely for i). |
| **1.2** | item **ii** | **Resumo do Quadro 11** (diretrizes e planos orientadores — internacional, nacional, regional, local, setorial). Stored abbreviated in JSON; full text in M5D. |
| **1.3** | item **iii** | `null` unless a later FR-001 row links a complement table row explicitly to objectives. |
| **1.4** | item **iv** | **Ponteiro Anexo 4** — Estrutura de Gênero e Inclusão; ODS/NDCs (texto citado no item iv). |
| **1.5** | item **v** | **Anexo 4** + declarações de impacto/ambição citadas no item v (resumo + remissão ao Anexo 4 no PDF oficial). |
| **1.6** | item **vi** | `null` (item vi não remete a Quadro numerado no trecho analisado). |

**FR-009 context:** evaluation still uses **sub_task_text + expected_output + complement** when complement is non-null; when `null`, use PRD option **A** for OQ-002 (sub-task + output only) for that row unless you later add a complement.

## `expected_output_text_pt` (from «Qual deve ser o resultado?»)

The guide gives **one** brief report with **three** bullets; mapped to sub-tasks as:

| `subtask.id` | `expected_output_text_pt` (synthesis) |
|--------------|----------------------------------------|
| **1.1** | «Porque o projeto é necessário» — bullet 1 do resultado da Ação 1. |
| **1.2** | «Como o projeto se encaixa no contexto estratégico mais amplo do governo» — bullet 2. |
| **1.3** | «Um conjunto de Objetivos Estratégicos» — bullet 3. |
| **1.4** | Conteúdo do relatório breve correspondente ao item **iv** (ODS, gênero, inclusão, compromissos internacionais). |
| **1.5** | Conteúdo do relatório breve correspondente ao item **v** (impactos socioambientais, ambição, Anexo 4). |
| **1.6** | Conteúdo do relatório breve correspondente ao item **vi** (programas/projetos que influenciam o projeto). |
