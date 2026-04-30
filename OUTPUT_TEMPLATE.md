# OUTPUT TEMPLATE

## Automated Decomposition from PRD to Epics

**Document Type:** Epic (Decomposition Phase Output)

**Input:** Full PRD document + Revised EPIC Prompt template + `[PRD_HANDOFF_BLOCK]` safeguard

**Process:** LLM automatically analyzes PRD, applies constraints/guardrails, decomposes into Epics

**Output:** This completed Epic document (all sections auto-populated)

**Destination:** MDAP Phase (reads completed Epic + CONTEXT.md + 5A)

---

## WORKFLOW OVERVIEW

```
INPUTS:
├─ Full PRD (complete document)
├─ PRD `[PRD_HANDOFF_BLOCK]` (scope safeguard reference point)
├─ Revised EPIC Prompt (with guardrails: ID preservation, assumption handling, scope ceiling, persona constraint, etc.)
└─ This Epic Document Output Format (structure specification)

↓ LLM PROCESSES:
├─ Reads `[PRD_HANDOFF_BLOCK]` (prevents hallucination)
├─ Uses full PRD for decomposition context
├─ Applies constraints (no tech details, preserve IDs, handle assumptions, enforce scope ceiling)
├─ Follows this output format structure
└─ Automatically populates all sections

↓ RESULT:
Completed Epic Document (shown below)
├─ All EPIC-XXX entries filled with actual User Stories
├─ All acceptance criteria populated from PRD requirements
├─ Dependencies identified and documented
├─ Assumptions tagged and carried forward
├─ Coverage matrix complete (every PRD ID mapped)
├─ CONTEXT.md updated with real values
└─ 5A Phase Transition Note ready for MDAP consumption

(NO BLANKS - fully completed, ready to use)
```

---

# EPIC DOCUMENT — AUTO-POPULATED OUTPUT

**All sections below are automatically filled by LLM based on PRD analysis.**

---

# EPIC HEADER

## Epic Title

[Auto-populated: Clear, outcome-focused title from PRD requirements]

**Example output:** "User Authentication & Profile Management System"

**What LLM does:** Synthesizes PRD requirement titles into coherent Epic title

---

## Epic Goal

[Auto-populated: One sentence from PRD business objectives]

**Example output:** "Enable users to securely access and manage their account information independently"

**What LLM does:** Derives Epic goal from PRD goals; links to specific PRD goal reference

---

## Scope Statement

**In Scope:**
[Auto-populated: List of FR/NFR IDs from PRD that this Epic covers]

- References PRD requirement IDs (FR-001, FR-002, etc.)
- LLM keeps list tight to prevent over-scoping

**Out of Scope:**
[Auto-populated: Explicit boundaries from PRD scope ceiling statement]

- References PRD scope ceiling
- Prevents scope creep during decomposition
- Example: "Payment processing is out of scope per PRD ceiling"

**[ASSUMPTION] & [THRESHOLD NEEDED] Items:**
[Auto-populated: All flagged items from PRD `[PRD_HANDOFF_BLOCK]` that affect this Epic]

- Copied verbatim from `[PRD_HANDOFF_BLOCK]`
- Preserved through entire Epic (Risk/Assumption field → User Stories → CONTEXT.md)
- Example: "[ASSUMPTION-02] Single email per user account" or "[THRESHOLD-NEEDED] Maximum concurrent users undefined"

**What LLM does:** Extracts scope boundaries from `[PRD_HANDOFF_BLOCK]`; preserves assumption tags exactly

---

## Why This Matters

This header establishes boundaries and safeguards against scope creep. `[PRD_HANDOFF_BLOCK]` is consulted during creation (safeguard against hallucination), but the full PRD provides context for decomposition.

---

# EPICS & USER STORIES (Repeating Template)

## EPIC-XXX: [Epic Title]

[AUTO-POPULATED: One EPIC entry per logical grouping of related PRD requirements]

**Derived from:** [PRD Requirement IDs, auto-extracted] (e.g., FR-001, FR-002, NFR-001)

**What LLM does:**

- Cites exact PRD IDs (no renumbering)
- Groups related FRs/NFRs into coherent Epic
- Preserves ID format exactly as in PRD

**Strategic Goal:**
[Auto-populated: Restates PRD goal this Epic serves, or left empty if supporting/enabling only]

**What LLM does:**

- References PRD goal (does not invent)
- Example output: "Serve PRD Goal #2: Reduce account takeover risk"

**Epic Definition of Done:**

- [ ]  All in-scope user needs are covered by User Stories below
- [ ]  Coverage matrix confirms all mapped PRD requirements (FR/NFR IDs) are addressed
- [ ]  Any [ASSUMPTION] or [THRESHOLD NEEDED] items are preserved in Risk/Assumption field
- [ ]  Every User Story is independently valuable (not a "helper" task)
- [ ]  No Stories specify technology choices or implementation methods
- [ ]  All Stories are grouped by persona or outcome (not by tech)

**Guidance:**

- DoD verifies DECOMPOSITION quality, not implementation completeness
- Do not include performance thresholds, technology details, or architecture concerns
- Epic DoD checks: completeness, traceability, user value, boundaries, acceptance criteria

---

## Risk / Assumption Field

[AUTO-POPULATED: All [ASSUMPTION] and [THRESHOLD NEEDED] items from PRD `[PRD_HANDOFF_BLOCK]` that impact this Epic]

**What LLM does:**

- Copies [ASSUMPTION] tags verbatim from PRD `[PRD_HANDOFF_BLOCK]`
- Includes in Risk/Assumption field (preserves tag through entire Epic)
- If assumption is critical, notes impact on Story acceptance criteria
- Example output: "[ASSUMPTION-01] Users will register with single email per account. This affects Story 1 acceptance criteria."

---

## User Stories (Repeating Template)

### US-[ID]: [Story Title]

**Format:**

```
As a [persona],
I want to [action],
So that [benefit/outcome]
```

**Guidance:**

- Persona MUST be from PRD `[PRD_HANDOFF_BLOCK]` persona list (do not invent)
- If persona not in PRD, flag in Open Questions section (don't create story anyway)
- Action should be user-visible outcome, not technical implementation
- Benefit explains WHY this matters

**Example:**

```
As a Standard User,
I want to reset my password via email link,
So that I can regain access if I forget my password
```

---

### Acceptance Criteria

[Minimum 2; binary and measurable; testable by QA without interpretation]

**Format:**

```
- [ ] Criterion 1: [Specific, measurable outcome]
- [ ] Criterion 2: [Different aspect, measurable]
```

**Guidance:**

- Must be testable without threshold ambiguity
- If acceptance criteria depends on [THRESHOLD NEEDED] from PRD, note it:
    - Example: "[THRESHOLD-NEEDED] System accepts N concurrent login attempts without performance degradation"
- Do NOT include performance metrics unless explicitly in PRD
- Do NOT reference technology or implementation

**Example:**

```
- [ ] User receives password reset email within 60 seconds of request
- [ ] Reset link is valid for 24 hours and unusable after clicked
- [ ] User can set new password meeting PRD security requirements
```

---

### References

**PRD Reference:** [Specific FR or NFR ID this story implements]

**Guidance:**

- Cite exact PRD ID (FR-001, not FR1 or FR 1)
- One story can cite one or more IDs
- Verification: Every Story must trace back to PRD

**Example:** "FR-003, NFR-002"

---

**Repeat this User Story template for every story in the Epic.**

---

# DEPENDENCIES

## Hard Blocking Dependencies

[Epics that must complete before this Epic can begin]

**Format:**

```
[Epic ID] → [This Epic]: [reason]
```

**Guidance:**

- Hard blocker means: cannot start development until predecessor delivers working feature
- Example: "EPIC-001 (Authentication) → EPIC-002 (Profile Management): User must authenticate before accessing profile"

---

## Soft Dependencies

[Epics that can run in parallel but work better if sequenced]

**Format:**

```
[Epic ID] ⟹ [This Epic]: [reason]
```

**Guidance:**

- Soft dependency means: can develop in parallel, but UX/logic better if sequenced
- Example: "EPIC-002 (Profile) ⟹ EPIC-005 (Persona Roles): Roles are more useful after profile exists, but can develop together"

---

## External Dependencies

[Services, systems, or contracts outside this Epic scope]

**Format:**

```
[External service]: [reason, impact on Epic]
```

**Guidance:**

- Example: "Email Provider API: Password recovery depends on external email delivery; integration required but not in scope of this release"
- MDAP must plan for external API contracts, fallback error handling

---

**Repeat this Dependencies section for each EPIC-XXX above.**

---

# ASSUMPTIONS & OPEN QUESTIONS

## Unresolved [ASSUMPTION] Items from PRD `[PRD_HANDOFF_BLOCK]`

[Copy any [ASSUMPTION] items not resolved during Epic decomposition]

**Format:**

```
- [ASSUMPTION-XX]: [Requirement text] (impacts: EPIC-ID, EPIC-ID)
  - Reason unresolved: [Why this needs stakeholder validation]
```

**Guidance:**

- Preserve tag exactly as it appears in PRD `[PRD_HANDOFF_BLOCK]`
- List affected Epics (shows scope impact)
- Do NOT invent answers to resolve; flag for stakeholder decision
- Example: "[ASSUMPTION-01] Users will have single email per account (impacts: EPIC-001, EPIC-002) — Reason unresolved: No validation in PRD; confirm scope for multi-email future"

---

## Unresolved [THRESHOLD NEEDED] Items from PRD `[PRD_HANDOFF_BLOCK]`

[Copy any [THRESHOLD NEEDED] items not defined during Epic decomposition]

**Format:**

```
- [THRESHOLD-XX]: [Requirement text]; threshold needed: [what value/range is missing] (impacts: EPIC-ID)
  - Impact on design: [How missing threshold blocks acceptance criteria finalization]
```

**Guidance:**

- Copy exact requirement text from PRD `[PRD_HANDOFF_BLOCK]`
- Describe what threshold is missing (e.g., "concurrent user ceiling", "acceptable delay in seconds")
- Explain design impact (MDAP cannot finalize test criteria without this)
- Example: "[THRESHOLD-01] FR-042: System must support concurrent users; threshold needed: How many? (impacts: EPIC-004) — Impact: Cannot define performance test criteria until ceiling is known"

---

## Open Questions / Decomposition Conflicts

[Anomalies discovered during Epic generation]

### Logical Conflicts

[Requirements that contradict or create circular dependencies]

- Description of conflict
- Affected Epics: [EPIC-IDs]
- Recommended resolution: [What stakeholders should decide]

### Missing Information

[Details required for decomposition but not in PRD]

- Requirement text
- Affected Epics: [EPIC-IDs]
- Impact: [How missing info affects design decisions]

### Out-of-Scope Dependencies

[Features logically needed but explicitly out of scope]

- Feature name
- Affected Epics: [EPIC-IDs]
- Why it matters: [Design/testing impact]

### Persona / Scope Anomalies

[Misalignments between PRD and Epic decomposition]

- Description
- Affected Epics: [EPIC-IDs]
- Resolution needed: [Stakeholder decision required]

**Guidance:**

- Surface anomalies discovered during decomposition
- If no anomalies: write "(No anomalies or conflicts detected)"
- Each question includes: [what], [affected Epic], [why it matters] — MDAP uses this to escalate

---

# COVERAGE MATRIX

## PRD Requirements → Epic Mapping

| PRD ID | Requirement Summary | Epic ID | Status |
| --- | --- | --- | --- |
| FR-001 | [Requirement title] | EPIC-001 | ✓ Covered |
| FR-002 | [Requirement title] | EPIC-002 | ✓ Covered |
| NFR-001 | [Requirement title] | EPIC-001 | ⚠ Partial |
| [ASSUMPTION-01] | [Assumption text] | EPIC-001 | ⚠ Unresolved |

---

**Guidance:**

- Status symbols: ✓ (Fully covered), ⚠ (Partial/unresolved), ✗ (Uncovered)
- Every FR/NFR from `[PRD_HANDOFF_BLOCK]` must appear in this table
- If requirement is uncovered, note explicitly (do not skip)
- This table proves completeness; MDAP will verify it

**Verification Checklist:**

- [ ]  Every PRD ID from `[PRD_HANDOFF_BLOCK]` appears in coverage matrix
- [ ]  No requirements are missing
- [ ]  Status reflects actual coverage (not assumed)

---

# CONTEXT.md UPDATE

[Updated state of traveling context file; used for handoff to MDAP]

```markdown
# CONTEXT.md — Development Pipeline State

## Pipeline Stage
**Current Stage:** EPIC — Decomposition into deliverable units
**Next Stage:** MDAP — Module Design and Action Planning
**Last Updated:** [Timestamp]

## Canonical Scope Summary
**Total In-Scope Requirements (from PRD `[PRD_HANDOFF_BLOCK]`):** [COUNT] FRs, [COUNT] NFRs
**Total Epics Generated:** [COUNT]
**Coverage:** [COUNT] unique PRD IDs mapped to Epics

## Assumption & Threshold Status
**[ASSUMPTION] Items Carried Forward:** [COUNT]
**[THRESHOLD NEEDED] Items Carried Forward:** [COUNT]
**Assumptions Resolved During EPIC Phase:** [COUNT] (list them if any)
**Thresholds Defined During EPIC Phase:** [COUNT] (list them if any)

## List of Unresolved [ASSUMPTION] Items
- [ASSUMPTION-01]: [Requirement text] (from PRD ID: FR-XXX)
- [ASSUMPTION-02]: [Requirement text] (from PRD ID: NFR-YYY)

## List of Unresolved [THRESHOLD NEEDED] Items
- [THRESHOLD-01]: [Requirement text]; required threshold: [description] (from PRD ID: FR-ZZZ)
- [THRESHOLD-02]: [Requirement text]; required threshold: [description] (from PRD ID: NFR-WWW)

## Confirmed Constraints
[Constraints validated or confirmed during EPIC decomposition]
- Constraint A: [Description] (impacts Epics: EPIC-X, EPIC-Y)
- Constraint B: [Description] (impacts Epics: EPIC-Z)

## Key Dependencies Discovered
**External Blocking Dependencies:**
- [Name]: [Description] (blocks: EPIC-X, EPIC-Y)

**Out-of-Scope Dependencies:**
- [Feature]: [Description] (logically needed but out of scope per PRD ceiling)

## Epic Phase Complete
**Epics generated:** EPIC-001 through EPIC-[N]
**Next action:** MDAP phase receives CONTEXT.md update + 5A Phase Transition Note
```

**Guidance:**

- Update all fields with counts and actual values
- If field doesn't apply, write "(None)" or "(0)"
- This file moves to MDAP phase; they use it to understand state at transition
- MDAP will update this again for Architecture phase

---

# 5A — PHASE TRANSITION NOTE FOR MDAP

[Structured handoff to MDAP phase; MDAP uses this as their input anchor]

---

## 5A.1 — Epic Summary List

[One-line scope summary for each Epic]

```
EPIC-001: [Title/outcome]
EPIC-002: [Title/outcome]
EPIC-003: [Title/outcome]
...
```

**Guidance:**

- One line per Epic (not paragraphs)
- Format: "EPIC-ID: [user-facing description]"
- Example: "EPIC-001: User Authentication via Email/Password"
- MDAP uses this for quick reference of all work items

---

## 5A.2 — Coverage Matrix

[PRD → Epic traceability; proof that no requirements were missed]

| PRD ID | Requirement | Epic ID | Status |
| --- | --- | --- | --- |
| FR-001 | [Title] | EPIC-001 | ✓ |
| FR-002 | [Title] | EPIC-002 | ✓ |
| NFR-001 | [Title] | EPIC-001 | ✓ |

**Guidance:**

- Same format as earlier Coverage Matrix section (shows completeness)
- Status: ✓ (Covered), ⚠ (Partial), ✗ (Uncovered)
- MDAP verifies: "Did EPIC cover all PRD requirements?"
- If status is ⚠ or ✗, note in "Open Questions" section of 5A.5

---

## 5A.3 — Unresolved [ASSUMPTION] & [THRESHOLD NEEDED] Items

[All flagged items from PRD `[PRD_HANDOFF_BLOCK]` that remain unresolved]

**Format:**

```
Unresolved [ASSUMPTION] Items:
- [ASSUMPTION-01]: [Requirement text] (impacts: EPIC-001, EPIC-002)
- [ASSUMPTION-02]: [Requirement text] (impacts: EPIC-003)

Unresolved [THRESHOLD NEEDED] Items:
- [THRESHOLD-01]: [Requirement text]; missing: [what value/range] (impacts: EPIC-001)
- [THRESHOLD-02]: [Requirement text]; missing: [what value/range] (impacts: EPIC-004)
```

**Guidance:**

- Preserve tags exactly as they appear in PRD `[PRD_HANDOFF_BLOCK]`
- List affected Epics (shows design scope impact)
- **MDAP must make these decisions BEFORE finalizing detailed design**
- Thresholds directly block acceptance criteria finalization; do not skip
- MDAP escalates to stakeholders if needed, or defines thresholds if scope permits

---

## 5A.4 — Inter-Epic Dependencies

[Hard, soft, and external dependencies for sprint planning]

**Hard Blocking Dependencies** (must sequence in MDAP):

```
[Epic A] → [Epic B]: [reason]
Example: EPIC-001 (Auth) → EPIC-002 (Profile): User must authenticate before profile access
```

**Soft Dependencies** (can parallel, but better if sequenced):

```
[Epic C] ⟹ [Epic D]: [reason]
Example: EPIC-002 (Profile) ⟹ EPIC-005 (Personas): Better UX if sequenced, but can develop together
```

**External Dependencies** (out of scope, affects design):

```
[Service/contract]: [description]
Example: Email Provider API: Password recovery needs external email; MDAP must plan integration + fallback error handling
```

**Guidance:**

- Hard blockers = sequencing constraint (Gantt chart impacts)
- Soft dependencies = optimization hints (parallel sprints possible)
- External dependencies = risk planning (external contracts, fallback handling)
- MDAP uses this to create realistic sprint plan and identify risks

---

## 5A.5 — Open Questions / Conflicts Discovered During EPIC

[Issues, anomalies, or decisions needed before MDAP finalizes design]

### Logical Conflicts

- [Description]: [affected Epics] → [resolution needed]
- Example: "FR-010 (View transaction history) requires transactions to exist, but payment processing is out of scope (EPIC-007) → PO must clarify data source (pre-populate, external system, or defer feature)"

### Missing Information

- [Requirement]: [what's missing] (impacts: [Epics]) → [design impact]
- Example: "NFR-005 (Response time <2s) — missing: Is this server latency only or includes network? (impacts: EPIC-001, 002, 003) → QA cannot finalize test thresholds without this"

### Out-of-Scope Dependencies

- [Feature/service]: [why needed] (impacts: [Epics]) → [MDAP action]
- Example: "Email provider reliability (impacts: EPIC-003, EPIC-008) → MDAP must plan for API contracts and fallback error handling"

### Persona / Scope Anomalies

- [Issue]: [affected Epics] → [stakeholder decision needed]
- Example: "EPIC-005 includes 'Moderator role' story, but PRD defines only 'Standard User' and 'Admin' personas → Is Moderator a new persona (update PRD scope) or should story map to Admin?"

**Guidance:**

- Each item has: [what], [affected Epic], [why it matters]
- MDAP escalates to stakeholders if decisions are needed
- If no open questions: write "(No anomalies or conflicts detected)"
- These are "red flags" for MDAP — not blockers, but awareness

---

# ORCHESTRATION FILE INTEGRATION

[How this Epic document connects to shared governance files]

---

## agents.md — Agent Behavior Rules

**When accessed during Epic creation:**

- Validates assumptions against PRD `[PRD_HANDOFF_BLOCK]`
- Enforces persona constraints (stories reference PRD-defined personas only)
- Ensures [ASSUMPTION] and [THRESHOLD NEEDED] tags are preserved

**What gets written to agents.md (during/after this Epic phase):**

- "If story requires persona not in PRD, flag in Open Questions" → Rule applied during US creation
- "Preserve [ASSUMPTION] tags in three places: Epic Risk/Assumption field, Story acceptance criteria, Open Questions" → Rule enforced throughout
- "Do not resolve [THRESHOLD NEEDED] items; preserve and escalate to stakeholders" → Rule maintained in output

**How it's used downstream:**

- Next Epics (if multiple) reference these rules to ensure consistency
- MDAP team references agents.md to understand why certain decisions were flagged

**Example inline note in this document:**
"During User Story creation: Validate persona is in PRD persona list (agents.md enforcement point). If not found, apply agents.md rule: Flag in Open Questions section, do not create story."

---

## PIPELINE.md — Phase Gates & Verification Workflows

**When accessed (post-Epic creation):**

- After all Epics are generated, PIPELINE.md verification gate is triggered
- Gate: "EPIC → MDAP Phase Transition Verification"

**What gets written to PIPELINE.md (during/after this Epic phase):**

- "EPIC phase complete: Verify coverage matrix (all PRD items covered?)" → Verification requirement
- "EPIC phase complete: Verify [ASSUMPTION] items are carried forward in 5A.3" → Verification requirement
- "EPIC phase complete: Verify no orphaned out-of-scope requirements" → Verification requirement

**How it's used downstream:**

- MDAP team checks PIPELINE.md before beginning Module Design
- Gate verification must complete before MDAP can proceed
- PIPELINE.md records who verified and when

**Example inline note in this document:**
"Post-Epic: Verification gate recorded in PIPELINE.md: 'Coverage matrix reviewed and approved by Product Owner before MDAP begins' (human gate, not LLM self-audit)."

---

## DEVELOPMENT.md — Design Rationale & Context

**When/if accessed:**

- Optional reference for future phases wanting to understand design decisions
- Not required for Epic completion, but useful for knowledge retention

**What gets written to DEVELOPMENT.md (optional, during/after this Epic phase):**

- "Why `[PRD_HANDOFF_BLOCK]` is the input safeguard: Prevents LLM from hallucinating scope by processing entire PRD. Full PRD still used for decomposition context."
- "Why [ASSUMPTION] tags are preserved through entire Epic: Ensures stakeholders never lose visibility into unvalidated decisions"
- "Why scope ceiling is explicitly stated: Prevents logical inference from extending beyond declared boundary"

**How it's used:**

- New team members understand the governance design
- Future projects reference this to understand "why we do things this way"

**Example inline note in this document:**
"Optional: Record in DEVELOPMENT.md why assumption tagging prevents scope creep (for future team context)."

---

# WHEN TO SPLIT THIS EPIC (Large Projects)

If full PRD decomposes into >10 Epics or this document exceeds 20 pages:

1. **Split by feature area** (if PRD covers multiple domains)
    - EPIC-1: Authentication & Session Management
    - EPIC-2: User Profiles & Settings
    - (Create separate Epic document for each)
2. **Coordinate across splits:**
    - Each Epic document includes same 5A structure
    - CONTEXT.md is SHARED (all split Epics update the same CONTEXT.md)
    - 5A outputs from each Epic feed into MDAP collectively
3. **Handoff to MDAP:**
    - MDAP receives: All split Epic documents + single unified CONTEXT.md + combined 5A notes from all splits

---