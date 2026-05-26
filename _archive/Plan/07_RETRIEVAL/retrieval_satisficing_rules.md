# Retrieval, satisficing, and evidence status (Rio v1)

**Normative PRD references:** FR-008, FR-008A, FR-008B, FR-008C; FR-014A (SHOULD); FR-015; NFR-002; OQ-006 (UNCERTAINTY at **0.70**).

This document expands EPIC/MDAP detail. If PRD and this file conflict, **PRD wins**.

---

## 1) Pooled retrieval hooks (not jurisdiction-sequential)

For each **active sub-task** with a crosswalk:

- All **artifact rows** (Rio Manual + IN TCDF) for that sub-task form **one pool** of labeled hooks.
- Each hook contributes **query text** (document name, procedimento, descrição) and **metadata** (`tipo`, `grau`, `jurisdiction_layer`) for **ranking and weighting**.
- **TCDF** expands **vocabulary / semantic recall**; **Rio** is the **authority anchor** for what the case should demonstrate. Neither source is processed as “finish all Rio before any TCDF” unless you implement a **staged** strategy that satisfies **FR-008A** (equivalent recall or automatic second stage when Rio-biased scores fall below a documented floor).

---

## 2) Satisficing — early stop (FR-008B)

**Condition (all must hold):**

1. Evidence is tied to an overlay artifact with **`tipo = Direta`** and **`grau = Alto`**.
2. The **sub-task evaluation record** (presence path) has **confidence ≥ 0.90** (NFR-002 scale 0.0–1.0).

**Effect:** The system **may cease further artifact-specific retrieval expansions** for that sub-task (no more extra query variants from remaining hooks).

**Non-effects:**

- **FR-008** semantic check (“chunk has connection with the subject”) must still be satisfied for the **selected** document/chunk before finalizing presence.
- **UNCERTAINTY** flag still uses **0.70** on the final record (OQ-006), not 0.90.

---

## 3) Tiered expansion when early exit does not apply (FR-008C)

Apply **artifact-driven** retrieval expansions in this order until **budget exhausted** or **early exit** fires:

| Pass | `tipo`   | `grau` order (each)   |
|------|----------|------------------------|
| 1    | Direta   | Alto → Médio → Baixo   |
| 2    | Indireta | Alto → Médio → Baixo   |
| 3    | Contextual | Alto → Médio → Baixo |

Within each `(tipo, grau)` bucket:

1. Rank candidates by **retrieval score** (similarity / hybrid).
2. Apply **boost** from overlay (`grau` = retrieval weight only; `tipo` = tier).
3. Keep a **fixed top-N** per bucket or a **global token budget** per sub-task (EPIC/MDAP picks N — e.g. SEAL-style fixed budget).

**Staged optimization (optional):** A first pass may use **Rio-biased** queries if a second pass automatically runs when `max_score < retrieval_floor_stage2` (PRD **FR-008A**). MDAP SHALL record the scalar and the similarity metric; initial calibration band **0.35–0.50** unless pilot data justifies otherwise. See [vector_storage_options.md](vector_storage_options.md).

---

## 4) Per-artifact disposition (FR-014A, SHOULD)

For each overlay artifact attempted for the sub-task, store:

| Disposition | Suggested meaning (EPIC calibrates thresholds) |
|-------------|--------------------------------------------------|
| **hit**     | Retrieval score ≥ **strong_hit_floor** (e.g. 0.85 — TBD) |
| **weak**    | Between **weak_floor** and strong floor (e.g. 0.55–0.85 — TBD) |
| **none**    | Below weak_floor or no candidate returned |

Always record **method** when applicable: exact name / approximate name / semantic (FR-008).

---

## 5) Sub-task roll-up and PRD flags

| Level | Rule |
|--------|------|
| **Sub-task `present` / `not_present` / `uncertain`** | From evaluator output; **`uncertain`** aligns with UNCERTAINTY when **confidence < 0.70**. |
| **UNCERTAINTY** | Final evaluation record confidence **< 0.70**. |
| **MISSING DOCUMENT** | No acceptable case document for the action after FR-008 steps (per PRD). |
| **MISSING INFORMATION** | Documents exist but required substance for the sub-task/output is absent or below threshold (per PRD). |

**“Partial compliance” (Rio satisfied vs TCDF asks more):** Not a fifth PRD flag in v1. Represent as **reasoning text** + **per-artifact disposition** + optional **MISSING INFORMATION** if Rio anchor is met but required elements are still absent per overlay; EPIC may add a **report subsection** without new FR-015 enum until stakeholders approve.

---

## 6) Relation to “Audit-Guard” proposal

Ideas worth **adopting**: metadata-first retrieval, **fixed budget** (SEAL-like), explicit **no-hit** paths, Rio anchor + TCDF vocabulary expansion.

Ideas to **defer or simplify**: full **MADAM** multi-agent debate and full **ConRAG** clustering in v1 — replace with **structured prompt + per-artifact table + single aggregator pass** unless evaluation proves insufficient.

---

## 7) Vector store (preview for next step)

**Recommended separation:**

1. **Case corpus index** — chunks from **uploaded** PDFs (case-specific).
2. **Reference index (optional)** — chunks or paragraphs from **M5D**, **Rio Manual**, **IN TCDF** for **definitions** and citations (not a substitute for structured crosswalk JSON).

The **crosswalk JSON** remains the **source of truth** for tipo/grau/artifact labels; vectors **retrieve case evidence**, not replace the overlay.

Details: EPIC/MDAP after chunking policy (Topic J in pendencies).
