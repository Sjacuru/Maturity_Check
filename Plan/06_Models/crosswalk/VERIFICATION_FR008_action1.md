# FR-008 coverage check — Ação 1 crosswalk (Rio + IN TCDF)

## What FR-008 needs from the crosswalk

| FR-008 step | Role of crosswalk data |
|-------------|-------------------------|
| **1 — Exact name** | `document_name_pt` (and optional `match_hints.filename_candidates` when you discover stable filenames). |
| **2 — Approximate name** | Same labels + fuzzy matching on titles/headers in PDFs. |
| **3 — Semantic** | `intencao` (both sources, `compose_order`), `procedimento_pt`, `descricao_pt`, plus M5D sub-task text when linked from FR-001. |

**FR-008A:** All Rio + TCDF rows for a sub-task are **one pooled set** of hooks (ranking by `tipo`, `grau`, similarity).

## Verdict by sub-task

| Sub-task | Rio rows | TCDF rows | Intenção Rio + TCDF | Sufficient for FR-008? |
|----------|----------|-----------|----------------------|---------------------------|
| **1.1** | 3 | 3 | Yes | **Yes** (already in `action_1_subtask_1_1.template.md`) |
| **1.2** | 3 | 2 | Yes | **Yes** |
| **1.3** | 2 | 2 | Yes | **Yes** |
| **1.4** | 2 | 3 | Yes | **Yes** |
| **1.5** | 2 | 2 | Yes | **Yes** |
| **1.6** | 2 | 3 | Yes | **Yes** |

## Interpretation note (important)

Even when you define a shared “blueprint” rule (e.g., complement mapping or default weighting), **each sub-task is evaluated independently** and may diverge. The combined `units` file is storage convenience only.

## Resolved (was gaps)

### 1. M5D text fields (`m5d_subtask_text_pt` / `expected_output_text_pt` / `complement_text_pt`)

Populated from **[M5D.md](../M5D.md)** (Cap. 3, Ação 1 — itens **i–vi** e «Qual deve ser o resultado?»). Complement linkage for Ação 1 is documented in **[OQ-002_action1_complement_rule.md](OQ-002_action1_complement_rule.md)**. FR-001 may still add structured rows later; crosswalk is no longer blocked on nulls for 1.1–1.6.

### 2. TCDF 1.6 — **Análise de Influência Cruzada** (`1.6-tcdf-003`) — **`grau`**

| Option | When it helps | Trade-off |
|--------|----------------|-----------|
| **Alto** | Maximizar recall quando conflitos entre projetos do mesmo concedente são centrais no caso. | Com `tipo` **Contextual**, pode **sobre-pesar** o pool frente a evidências Rio; risco de ruído se o artefato aparece raro ou genérico. |
| **Médio** | Meio-termo entre recall e contenção; útil se quiser simetria com outros hooks **Indiretos** do mesmo sub-task. | Não reflete tão bem o papel **apoiador** do último tier (Contextual). |
| **Baixo** (adotado) | Alinha **Contextual** + **Art. 16, IV** como evidência de apoio; TCDF continua expansor lexical sem dominar ranking (FR-008A pooled). | Menor boost de similaridade para esse rótulo isolado. |

**Decisão no JSON:** **`grau`: `"Baixo"`** em [action_1_subtasks_1_2_to_1_6.template.md](action_1_subtasks_1_2_to_1_6.template.md). Se revisão jurídica preferir **Médio** ou **Alto**, alterar só esse campo e esta tabela.

## Remaining (not FR-008 blockers)

1. **Bundled PDF policy** (Topic A) — merged uploads; ver pendências.

## Files

| File | Content |
|------|---------|
| [action_1_subtask_1_1.template.md](action_1_subtask_1_1.template.md) | Sub-task **1.1** |
| [action_1_subtasks_1_2_to_1_6.template.md](action_1_subtasks_1_2_to_1_6.template.md) | Sub-tasks **1.2–1.6** (single JSON array) |

Extract or split JSON per sub-task in implementation as needed.
