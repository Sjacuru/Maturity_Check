# Pre-EPIC open items (unresolved only)

Resolved and deferred-baseline decisions are in **[pre_epic_resolved_decisions.md](pre_epic_resolved_decisions.md)** — including **Topic A (bundled PDF v0, actions 2–16 pattern), Topic D/OQ-002 (global default), Topic H (NFR-008 boundary doc), Topic I (FR-001 v0 slice), Topic J (LanceDB + chunk defaults), OQ-001/003/004/005/007/008** (see archive for wording).

**EPIC drafting readiness:** see **[epic_drafting_readiness.md](epic_drafting_readiness.md)** (local-first, explicit must-haves, production gates).

---

## What remains before **production** (not blocking EPIC **draft**)

1. **OQ-005 — legal / security sign-off** for any deployment that sends **case document text** to an **external** LLM or document service. Engineering default is **local-only** (documented in [Plan/07_RETRIEVAL/nfr_008_deployment_boundary.md](../07_RETRIEVAL/nfr_008_deployment_boundary.md)). EPIC may proceed on the local branch.

2. **OQ-004 / NFR-006 — numeric latency SLO** (optional): no hard seconds target until pilot metrics exist; EPIC/MDAP record **measured** wall-clock per sub-task pipeline (retrieval + FR-009/FR-010 + FR-021). You indicated this is acceptable to defer.

---

## Pilot calibration (after first runnable pipeline)

Tune on real Rio cases (not logic blockers for EPIC authorship):

- **Topic J (remaining):** `retrieval_floor_stage2`, **hit / weak / none** cutoffs, embedding model id if defaults are wrong for Portuguese legal prose.
- **FR-020 / OQ-003:** if **superior read access** is in scope for your institution, pick assignment model (institution-wide vs per-case); default for v1 product spec is **institution-wide** (see archive).

---

## Quick reference

| ID | Topic | Status |
|----|--------|--------|
| — | Most pre-EPIC structural items | **Resolved** → see [pre_epic_resolved_decisions.md](pre_epic_resolved_decisions.md) |
| — | Code written **before** EPIC | **Trace** → [pre_epic_implementation_trace.md](pre_epic_implementation_trace.md) (map to EPIC when the prompt runs) |
| OQ-005 | External inference / residency — **production** gate | Open until legal/security |
| OQ-004 | Numeric NFR-006 SLO | Deferred (measure first) |
| Pilot | Vector thresholds + floor + hit/weak | Open (metrics-driven) |
