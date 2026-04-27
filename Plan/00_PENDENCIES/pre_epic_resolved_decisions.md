# Pre-EPIC — resolved decisions (archive)

This file holds **decisions that are no longer tracked** in [pendencias_pre_epic.md](pendencias_pre_epic.md). The pendencies file lists **only unresolved** items.

Last updated: aligned with stakeholder clarifications (Rio deployment, DF+Rio as breadth for classification, `Plan/06_Models` reference PDFs).

---

## Implementation scope — Ação 1 and PRD relationship

**Acknowledged (product / EPIC framing):** the **first implementation vertical** is **M5D Ação 1** end-to-end (ingest, crosswalk overlay, retrieval, evaluation, reporting for that action). **EPIC and technical design for this phase are anchored on Ação 1.**

The **[PRD](../01_PRD/prd.md)** still describes the **full** eventual system (46 actions, all modules). That is intentional: it is the north star. **Delivery sequencing** is: prove Ação 1 in Rio, then extend (Ação 2+ may reuse schema with **partial or full** crosswalk changes per action).

---

## Pre-EPIC implementation spikes (reconcile when EPIC runs)

Engineering **spikes** may land before the formal EPIC. That is normal: they reduce risk and inform scope. When EPIC/MDAP is produced, **map** each pre-existing artifact to a story/task or mark it superseded so backlog and repo stay aligned.

**Ledger:** [pre_epic_implementation_trace.md](pre_epic_implementation_trace.md)

---

## Jurisdiction — evaluated cases (v1)

**Rio de Janeiro only** for case documents under evaluation. The **Rio Manual** is the **primary** normative overlay. **IN 01/2024 TCDF** is a **secondary** source in the crosswalk for **synonyms, semantic breadth, and retrieval ranking** — not a second “live” jurisdiction profile for case law in v1.

---

## Intenção (semantic bridge) — hierarchical storage

**Resolved:** store **both** jurisdiction-specific intenção strings under `subtask.intencao.by_source`, ordered by **`compose_order`**: **`rio_manual` first**, then **`tcdf_in_01_2024`**. Use this order in **retrieval prompts** and semantic expansion. Optional `synthesized_text_pt` remains **null** unless you later approve a merged line.

---

## Grau — effect on product

**Resolved:** `Grau` (**Alto / Médio / Baixo**) affects **retrieval weighting and ranking only**. It does **not** alter the PRD’s numeric score formula by itself.

---

## Crosswalk completeness — Ação 1 sub-tasks 1.1 through 1.6

**Closed for listing:** Rio + IN TCDF artifact rows for **1.1–1.6** in [action_1_subtask_1_1.template.md](Plan/06_Models/crosswalk/action_1_subtask_1_1.template.md) and [action_1_subtasks_1_2_to_1_6.template.md](Plan/06_Models/crosswalk/action_1_subtasks_1_2_to_1_6.template.md). FR-008 checklist: [VERIFICATION_FR008_action1.md](Plan/06_Models/crosswalk/VERIFICATION_FR008_action1.md).

**Also closed:** `m5d_subtask_text_pt` / `expected_output_text_pt` / `complement_text_pt` sourced from **M5D** (Cap. 3, Ação 1); OQ-002 rule for complements: [OQ-002_action1_complement_rule.md](Plan/06_Models/crosswalk/OQ-002_action1_complement_rule.md). **`grau`** for TCDF **Análise de Influência Cruzada** (`1.6-tcdf-003`): **Baixo** (see verification doc for alternatives).

---

## PRD alignment — pooled retrieval and thresholds (authoritative in PRD)

- **FR-008A:** Pooled Rio + TCDF hooks per sub-task; not jurisdiction-sequential as the only correct behavior.
- **FR-008A (staged):** If Rio-biased first stage is used, second stage MUST run when best score **< retrieval_floor_stage2**; MDAP documents metric + value; calibration band **0.35–0.50** (PRD).
- **FR-008B:** Early exit when **Direta + Alto** and evaluation **confidence ≥ 0.90** (expansion stops; FR-008 semantic check still applies).
- **FR-008C:** Tiered expansion **Direta → Indireta → Contextual**, **Alto → Médio → Baixo** within tipo, fixed budget.
- **OQ-006 / FR-015:** **UNCERTAINTY** when evaluation confidence **< 0.70** (independent of 0.90 satisficing).
- **FR-014A (SHOULD):** Per-artifact **hit / weak / none** when overlay exists.

Detail: [Plan/07_RETRIEVAL/retrieval_satisficing_rules.md](../07_RETRIEVAL/retrieval_satisficing_rules.md). Storage: [vector_storage_options.md](../07_RETRIEVAL/vector_storage_options.md).

---

## Reference materials location (`Plan/06_Models`)

All paths below are under **`Plan/06_Models/`** (no URL encoding required in the working tree).

| File | Role (short) |
|------|----------------|
| `M5D.md` | M5D guide text (dev/reference; official framework PDF remains canonical per PRD decisions) |
| `in_01_2024_TCDF.pdf` | IN 01/2024 TCDF — document/procedure patterns (DF) |
| `ManualparaPreAnaliseAvaliacaoEstruturacaoeImplementacaodePPPsvolume3.pdf` | Rio de Janeiro pre-analysis manual (Vol. 3) |
| `Estruturação de projetos de PPP e concessão no Brasil_P.pdf` | Additional PPP structuring reference |
| `Licitacoes-e-Contratos-Orientacoes-e-Jurisprudencia-do-TCU-5a-Edicao-29-08-2024.pdf` | TCU orientations / jurisprudence (5th ed.) |
| `PROC-IBR-SOCIOAMB-003_2024-Estudos-que-atestem-a-viabilidade-tecnica-economica-social-e-ambiental-v-19set.pdf` | IBR socio-environmental viability studies proc. |

---

## FR-008 — baseline classification rule (v0)

**Problem addressed**  
Procurement files often lack consistent naming; artifacts may be embedded or only titled inside a PDF.

**Agreed v0 rule**  
No mandatory “expected file name” list as the only signal. Classification **records the method used**:

1. **File name** (best case)  
2. **Title/header** extracted from the PDF  
3. **Semantic** match on content  

**Supplementary normative layer (Rio + DF)**  
DF (IN 01/2024 TCDF) and Rio (Manual) documents were developed partly from M5D. **Operational deployment is Rio**; **both sources are retained** to widen synonym and procedure coverage so irregular naming does not alone collapse scores. Cross-source comparison for **Ação 1** is captured in stakeholder analysis (DF vs Rio labels as **synonyms** for the same intent where applicable).

**Grau (Alto / Médio / Baixo)** — definition agreed  
**Grau** = how close the artifact or procedure is to the **reference pattern**, defined as **M5D** interpreted together with **Rio** and **DF** reference materials (not M5D alone). **Use:** **retrieval weighting only** (see section above).

---

## Topic B — Vertical slice and primary key (FR-001)

- Start evaluation pipeline with **Ação 1**; first expansion band **Ação 1–16** (*Proposta Inicial de Investimento*).
- **Stable IDs**: use immutable keys `action_1` … `action_46` (Portuguese titles may change; keys do not).
- **Resolved (stakeholder):** **`action_<N>`** is the **primary key** for **every** M5D action in the structured framework store (FR-001).

---

## Topic C — OQ-001: Sub-task weights (FR-002, FR-013)

**Resolved:** **Option (A)** — equal weights per action until an external custom weight table is supplied for all sub-tasks of that action (FR-002). EPIC implements the default only until that table exists.

---

## Topic F — OQ-006: UNCERTAINTY threshold (FR-015, NFR-002)

**Resolved:** confidence threshold **70%** (below → UNCERTAINTY flag).

---

## Topic G — OQ-007: Pre-M5D documents

**Resolved:** evaluate pre-M5D case documents with M5D (+ overlay) criteria to surface the **maturity gap**; **same methodology and FR-013 formula** as contemporary processes (no era-specific score branch).

---

## Topic K — EPIC gate timing

**Resolved (process):** draft EPIC first, then walk **gates 2A–2J** in [UNIVERSAL_PHASE_GATES.md](../../UNIVERSAL_PHASE_GATES.md) one by one before locking the EPIC baseline.

---

## Topic E — OQ-004 / NFR-006: Latency

**Deferred (explicit):** no **numeric** sub-task SLO until pilot metrics exist. **EPIC/MDAP SHALL** log **measured** wall-clock for the full pipeline (FR-008D retrieval + FR-009/FR-010 + FR-021) per run. A product owner may later set NFR-006 targets without blocking EPIC **drafting**.

---

## Topic A — Bundled PDFs + crosswalk pattern for actions 2–16

**Bundled PDFs (v0 policy):** each **uploaded file** is one **retrieval document** for FR-006 segmentation and FR-008D indexing; **no mandatory** logical split into annexes in v0. If several logical documents live in one PDF, the **supported** v0 workaround is **upload as separate files**; optional auditor page-range labels or automatic TOC/heading split are **later** enhancements (EPIC may stub interfaces behind flags).

**Actions 2–16:** reuse the **same crosswalk JSON schema** as Ação 1 (`m5d_action_id`, `subtask`, `artifact_references`, `intencao`, etc.); each action gets its own machine-readable file(s) under `Plan/06_Models/crosswalk/` when built. Expect **partial or full** row changes per action (not a blind copy). Delivery order: after Ação 1 vertical is proven.

---

## Topic D — OQ-002: Complement linkage (global default)

**Resolved (product default):** use **Option (A)** from the PRD — when no complement row is linked for a sub-task, evaluation context is **sub-task + expected output only** (not the entire summary table as blanket context). When a complement **is** linked (FR-001 or crosswalk), include it per FR-009. **Ação 1** row-level complement mapping remains in [OQ-002_action1_complement_rule.md](../06_Models/crosswalk/OQ-002_action1_complement_rule.md); other actions follow the same pattern when crosswalks are authored.

---

## Topic H — NFR-008 deployment boundary (documentation)

**Resolved:** baseline boundary and default posture documented in [Plan/07_RETRIEVAL/nfr_008_deployment_boundary.md](../07_RETRIEVAL/nfr_008_deployment_boundary.md) (local case text by default; external paths explicit opt-in + audit).

---

## Topic I — FR-001: Canonical PDF → structured data (v0 slice)

**Resolved for first implementation slice:** **Ação 1** is authoritative in repo via **crosswalk JSON** + **M5D.md** excerpts for sub-task/output/complement text. Full automated **PDF → FR-001** ingest for all 46 actions remains **incremental**; it does **not** block standing up SQLite + vectors + evaluation for Ação 1.

---

## Topic J — Chunking + vector library (defaults for EPIC)

**Resolved (stack):** **Option A** from [vector_storage_options.md](../07_RETRIEVAL/vector_storage_options.md): **SQLite** for structured/crosswalk rows + **local** embeddings (**sentence-transformers** or **Ollama**).

**Resolved:** **LanceDB** is the **default** Phase 0 vector store (override to Chroma in EPIC only with written rationale — see [vector_storage_options.md](../07_RETRIEVAL/vector_storage_options.md)).

**Starting chunking defaults (MDAP may adjust after pilot):** target **~512–1024 tokens** (or nearest character window **1500–4000** chars for Latin text) per segment, **~10–15% overlap**, prefer **paragraph / heading boundaries** when extractors provide them; store stable `segment_id` for FR-008D logs and FR-014 citations.

**Still pilot-tuned (not structural):** `retrieval_floor_stage2` within PRD band **0.35–0.50**, FR-014A hit/weak cutoffs, exact embedding model id.

---

## OQ-003 — PERSONA-002 access (FR-020)

**Resolved (v1 product default):** **Option (A)** — audit superiors with an institution/tenant role may read **all cases** for that institution. **Option (B)** (per-case assignment) is deferred unless a stakeholder requires it; if FR-020 stays COULD, this default still guides any early superior-read feature.

---

## OQ-005 — NFR-008 vs external LLM (EPIC engineering default)

**Resolved (engineering default for EPIC drafting):** **Option (B)** — inference that consumes **case document text** runs **locally** by default. **Option (A)** (external LLM API with document text) requires **explicit** configuration + audit + **legal/security sign-off** before production. EPIC tasks MUST branch on this (no silent cloud default).

---

## OQ-008 — FR-021 judge isolation

**Resolved (v1 default):** use the **same local evaluator model** with a **separate system prompt** and **temperature 0** for the judge pass; **forbid** new facts in the judge schema. EPIC may optionally evaluate a **smaller local SLM** for FR-021 later under NFR-006 cost experiments.
