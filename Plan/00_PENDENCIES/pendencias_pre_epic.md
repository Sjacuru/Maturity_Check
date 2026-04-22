# Pre-EPIC open items (unresolved only)

Resolved and deferred-baseline decisions moved to **[pre_epic_resolved_decisions.md](pre_epic_resolved_decisions.md)** (includes FR-008 v0 rule, Rio+DF intent, `Plan/06_Models` inventory, Topics C/F/G/K, and decided part of Topic B).

---

## Topic A — FR-008: remaining work (Action 1 crosswalk and product rules)

**Status:** Open (implementation and data artefacts)

**Done conceptually**  
Rio + TCDF materials support **synonyms** and **procedure/description** text for retrieval and evaluation context; **Grau** defined as closeness to pattern (**M5D + Rio + DF**). Files live under [Plan/06_Models](../06_Models/).

**Still required**

1. **Machine-readable crosswalk** (CSV/JSON/SQL) for **Ação 1** — to be built together: sub-task ↔ artifact names ↔ procedures ↔ citations ↔ `Grau` ↔ optional equivalence groups (Rio vs DF). Chat tables are not sufficient for versioned automation.
2. **“Bundled PDF” policy** — when one upload contains several logical documents (annexes, merged files): agree whether we split by TOC, by headings, by human tagging in v0, or retrieval-only without splitting (scheduled deep dive).
3. **Grau → product behaviour** — confirm whether `Alto`/`Médio`/`Baixo` drives **retrieval weighting only**, **quality rubric text**, or **numeric score** (last option may require PRD trace / addendum).
4. **Actions 2–16** — same crosswalk pattern as Action 1, **after** Action 1 pipeline is stable.

---

## Topic B — Confirm stable primary key (FR-001)

**Status:** Open (single confirmation)

Confirm **`action_<N>`** (e.g. `action_1`) as the **primary key** for every M5D action in the structured framework store.

---

## Topic D — OQ-002: Sub-task ↔ complement row linkage

**Status:** Open  

Define the objective rule linking sub-tasks to summary-table / complement rows for FR-009 / FR-014 evaluation context.

---

## Topic E — OQ-004 / NFR-006: Latency

**Status:** Deferred (still “open” for a complete NFR-006 spec)  

No SLO numbers yet; add measurable targets when the system runs end-to-end.

---

## Topic H — OQ-005 / NFR-008: deployment boundary documentation

**Status:** Open (documentation only; policy archived)

Write the **deployment boundary** for the EPIC / sign-off pack: local LLM default, **opt-in** only for any service that sends document text outside the environment (e.g. future cloud OCR / intelligent document).

---

## Topic I — FR-001: Canonical PDF → structured data

**Status:** Open  

Pipeline and ownership: canonical framework PDF → structured store (manual vs automated extraction, edition updates). v0 Python extraction; optional cloud IDP remains **opt-in** under NFR-008.

---

## Topic J — Segmentation and retrieval (vector vs non-vector)

**Status:** Open  

Decide chunking and **dense (embeddings) vs sparse (BM25/structure)** retrieval after sampling real case PDFs (see facts list in resolved archive if you copy it into EPIC — or gather fresh in architecture phase).

---

## Quick reference (unresolved only)

| ID | Topic | Status |
|----|--------|--------|
| A | FR-008 — Action 1 crosswalk, bundled PDF, Grau→score | Open |
| B | Confirm `action_<N>` PK | Open |
| D | OQ-002 complement linkage | Open |
| E | OQ-004 latency SLO | Deferred |
| H | NFR-008 boundary write-up | Open |
| I | FR-001 PDF → structure | Open |
| J | Segmentation + retrieval | Open |
