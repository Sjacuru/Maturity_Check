# Frontend view architecture — Upload View and Assessment Result View

Two views. No dedicated per-Ação route in Phase 1.

**Upload View** (`/`): process_number entry, file picker, assessment trigger.

**Assessment Result View** (`/cases/:processNumber`): assessment lifecycle metadata (new/reused/fingerprint-rerun/failure) at the top, followed by a list of expandable Ação panels. Each panel contains all 7 auditor review elements and the score submission form.

**Why:** Phase 1 has one Ação. A three-level navigation hierarchy (list → detail route) has no demonstrated justification at this complexity level. The expandable-panel pattern handles 1 Ação today and 46 Ações in Phase 2 without structural redesign. Assessment lifecycle metadata belongs at the result level, not inside individual Ação panels — it is a property of the assessment run, not of any single evaluation.

**Considered alternative:** Three views with a dedicated `AcaoReviewView` at `/cases/:processNumber/evaluations/:acaoId`. Deferred: no evidence from Phase 1 that 46 Ações create a navigation problem requiring a separate route. The decision will be revisited when Phase 2 data reveals actual Auditor navigation pain.
