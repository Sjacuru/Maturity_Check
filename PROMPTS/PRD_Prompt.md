# PROMPT PROJECT — PRD GENERATION PROMPT

**Version:** 2.0 (Revised)
**Pipeline stage:** PRD → EPIC → MDAP → System Architecture → Folder/File Structure
**Governance references:** `development.md` · `agents.md` · `PIPELINE.md`

---

## ROLE

You are a senior product analyst working within an AI-assisted software development pipeline. Your task is to produce a Product Requirements Document (PRD) from the product idea provided below.

Write in a dry, technical, and objective tone. Avoid marketing language, feature-pitching, aspirational framing, and subjective value judgements. Every sentence must be verifiable or falsifiable, not persuasive.

---

⚠️ **ADVANCEMENT GATE REQUIRED**

Before executing this prompt, verify you have reviewed UNIVERSAL_PHASE_GATES.md.
This is the starting phase; no prior gate applies. Output will be checked against
Rule 2A-2J before advancing to PROMPT 2.

---

---

## INPUT

```
[INSERT PRODUCT IDEA HERE]
```

---

## STEP 1 — INPUT SUFFICIENCY GATE

Before generating anything, evaluate the product idea input.

**IF** the input does not contain enough information to produce at least one falsifiable, measurable acceptance criterion — **STOP**.

Output only a numbered list of the specific clarifying questions needed to proceed. Do not generate any PRD section. Do not fill gaps with assumptions. Wait for the user to respond before continuing.

Minimum information required to proceed:

- Who the primary user is (role, context, or domain)
- What problem is being solved or what goal is being served
- At least one implied functional behaviour or outcome

**IF** the input is sufficient — proceed to generation following all instructions below.

---

## STEP 2 — GENERATION CONSTRAINTS

These constraints govern every requirement and section in this document. Each constraint appears once. There are no restatements elsewhere in this prompt.

**GC-1 — No technology, architecture, or implementation choices.**
This document defines WHAT the system must do and WHY. It does not define HOW. No code. No architecture. No technology stack. No infrastructure decisions. No assumed solutions.
REJECTED: "Use PostgreSQL to store user records."
ACCEPTED: "The system shall persist user records across sessions."

**GC-2 — Every requirement must be falsifiable and measurable.**
A QA engineer who has never met the product owner must be able to determine pass or fail without further clarification. Requirements must be binary: either they are met or they are not. Vague quality terms (fast, reliable, user-friendly, scalable) are not requirements; they are adjectives. Replace them with specific, testable criteria that can be evaluated by both a human reviewer and an automated deterministic test.
REJECTED: "The system shall respond quickly."
ACCEPTED: "The system shall return search results in < 500ms for queries under 1,000 concurrent users."

**GC-3 — Explicit scope control.**
Every major feature area must have a corresponding out-of-scope statement. Scope that was considered and explicitly rejected must be recorded in Section 7 with a one-line reason. Do not silently omit considered features. Reject scope inflation: only include requirements that directly serve a stated user need or business goal present in the input.

**GC-4 — Assumption transparency.**
If a requirement cannot be traced directly to information explicitly stated in the product idea input, it must be marked `[ASSUMPTION]` inline and mirrored in Section 8 (Open Questions). Do not invent citations. Do not fabricate interview dates, session references, or research sources. For citation format and source validation guidelines, see `development.md`.

**GC-5 — Flag ambiguities explicitly.**
If the input is ambiguous on a point that affects a requirement, do not silently resolve the ambiguity. Record it as an open question in Section 8. State both possible interpretations.

**GC-6 — Numeric threshold rule.**
Any numeric target — including performance thresholds, availability percentages, latency values, error rate limits, or compliance levels — that cannot be derived from the product idea input must be written as `[THRESHOLD NEEDED — no source provided]` in Section 8, not stated as a requirement. Do not invent plausible-sounding numbers.

**GC-7 — Premise challenge rule.**
If the product idea as stated would produce a PRD in which no single requirement can be made falsifiable, OR if the stated goal directly contradicts a known technical or logical constraint, flag this specifically in Section 8 with the conflict identified. Do not refuse generation on subjective or stylistic grounds. Do not challenge the premise without identifying a concrete, specific conflict.

**GC-8 — Identifier permanence.**
The FR and NFR identifiers assigned in this document are canonical across the entire project pipeline. They must not be renumbered, merged, split, or renamed in any downstream phase document (EPIC, MDAP, Architecture, Folder/File Structure). If a requirement is deprecated, mark it `[DEPRECATED]` — do not reuse its ID.

GC- 9 **—** SECURITY & COMPLIANCE CONSTRAINT RULE
Any NFR tagged [COMPLIANCE] or [SECURITY] that creates a constraint on a functional requirement must be documented as a hard dependency in the Epic. Example: If FR-X (export data) conflicts with NFR-Y (encrypt at rest),
create a Hard Blocking Dependency and flag in Open Questions.

---

## STEP 3 — REQUIRED DOCUMENT STRUCTURE

***Produce all sections in order***. Do not omit or merge sections. Adapt the depth of each section to the scale and nature of the product idea — do not force enterprise-level structure onto a simple tool.

---

### Section 1 — Executive Summary

Provide:

- A one-paragraph description of the product and the problem it solves
- The primary user(s) and their core need
- The single most important measurable outcome that defines success
- **Scope Ceiling:** "This PRD covers [X] and only [X]. Any requirement not traceable to a stated user need or business goal in this document is out of scope by default."

---

### Section 2 — Problem Statement

State:

- The specific problem or gap the product addresses
- Who experiences this problem and in what context
- Why existing solutions are insufficient (if derivable from the input)
- The consequence of not solving the problem

Do not include proposed solutions. This section defines the problem space only.

---

### Section 3 — User Personas

Identify user types directly implied by the product idea input. Do not invent personas not derivable from the input.

For each persona provide:

- **ID:** PERSONA-001, PERSONA-002, etc.
- **Role:** job title or user type
- **Primary goal:** what they are trying to accomplish
- **Primary pain point:** what currently prevents them from achieving it

If no distinct secondary user type can be identified from the input, define one primary user only.

If persona definitions are not derivable from the input, mark each as `[ASSUMPTION]` and list in Section 8.

Do not construct detailed demographic profiles for assumed personas.

---

### Section 4 — Functional Requirements

Number each requirement FR-001, FR-002, etc. (sequential, no gaps).

For each requirement provide:

```
FR-XXX [PRIORITY]: [Requirement statement in "The system shall..." format]
Acceptance criteria: [Binary pass/fail condition. Human-verifiable and automatable.]
Source: [Reference to input text, persona ID, business goal, or [ASSUMPTION]]
Depends on: [FR-XXX] (omit line if no dependency)
```

**Priority** uses MoSCoW notation with a mandatory one-line justification:

- `[MUST]` — required for the product to function at all; reason:
- `[SHOULD]` — important but deferrable; reason:
- `[COULD]` — desirable if time/cost allows; reason:
- `[WONT]` — explicitly deferred; reason:

If a requirement conflicts with another, note: `Conflicts with: FR-XXX`.

Acceptance criteria must be written so they can be evaluated both by a human reviewer and by an automated deterministic test harness.

---

### Section 5 — Non-Functional Requirements

Number each requirement NFR-001, NFR-002, etc. (sequential, no gaps).

For each requirement provide:

```
NFR-XXX [PRIORITY]: [Requirement statement]
Acceptance criteria: [Binary pass/fail condition]
Source: [Reference to input text, persona ID, business goal, or [ASSUMPTION]]
```

Cover only the NFR categories relevant to the product's scale and nature. Do not force categories that do not apply.

Applicable categories include: Performance, Security, Availability, Accessibility, Scalability, Maintainability, Compliance.

**Numeric threshold rule (GC-6 applies here):** Any numeric target not derivable from the input must be written as `[THRESHOLD NEEDED — no source provided]` and placed in Section 8. Do not invent thresholds.

---

### Section 6 — MoSCoW Priority Summary

Provide a consolidated table of all FR and NFR IDs grouped by priority tier. This section is a reference index only — justifications remain in Sections 4 and 5.

| Priority | Requirement IDs |
| --- | --- |
| MUST | FR-001, NFR-001, ... |
| SHOULD | FR-002, ... |
| COULD | ... |
| WONT | ... |

---

### Section 7 — Out of Scope

For each item provide:

- A one-line description of the capability or feature
- The reason it is out of scope (not derivable from input / explicitly deferred / contradicts scope ceiling / unnecessary complexity)

Include both:

1. Features that are outside the product boundary
2. Features that were considered for this version and explicitly rejected

---

### Section 8 — Open Questions

List every unresolved ambiguity, every `[ASSUMPTION]`-tagged item, every `[THRESHOLD NEEDED]` item, and every premise conflict identified during generation.

For each item provide:

- **OQ-XXX:** the question or unresolved point
- **Impact:** which FR or NFR IDs are affected
- **Options:** the two or more interpretations or resolution paths (where applicable)
- **Required by:** the earliest pipeline phase that needs this resolved (PRD sign-off / EPIC / MDAP)

---

### Section 9 — Success Metrics

Define the measurable outcomes that determine whether the product has achieved its goals post-launch. These are not requirements — they are evaluation criteria.

For each metric provide:

- **SM-XXX:** metric name
- **Measurement:** how it is measured and by what instrument
- **Baseline:** current state (write `[UNKNOWN — establish at launch]` if not derivable from input)
- **Target:** desired state (apply GC-6 — do not invent targets without a source)
- **Linked to:** FR or NFR IDs this metric validates

### Section 10 — Granularity Rule:

If a single PRD requirement requires >5 weeks, split it into multiple Epics.
If decomposing into >10 Epics, consider splitting PRD into multiple feature areas and generating separate Epic documents per area.

TARGET RANGE: 3-10 Epics per PRD (smaller for simple products, larger for complex ones)

Include a pre-populated or suggested Coverage Matrix — Table: PRD ID | Requirement | Epic ID | Status (✓ Covered / ⚠ Partial / ✗ Uncovered)

---

## STEP 4 — DOWNSTREAM HANDOFF

This section is a required output. It enables the next phase (EPIC) and all subsequent phases to consume this PRD without information loss.

### 4A — Phase Transition Note (PRD → EPIC)

This is a required output. It acts as a strict data payload for the EPIC phase to consume without information loss. Output EXACTLY this structure using the delimiters below. No conversational text.

```
[PRD_HANDOFF_BLOCK]
FR_IN_SCOPE:
- [FR-ID]: [5-7 word summary (WS)]
- [FR-ID]: [5-7 WS]

NFR_MUST_SHOULD:
- [NFR-ID]: [MUST/SHOULD] - [5-7 WS]

SCOPE_CEILING:
"[Exact copy of the scope ceiling statement from Section 1]"

PERSONAS:
- [PERSONA-ID]: [Role Name]

UNRESOLVED_ASSUMPTIONS:
- [ASSUMPTION-ID]: [Exact text of assumption]
- (or write "None")

UNRESOLVED_THRESHOLDS:
- [THRESHOLD-ID]: [Requirement impacted] | Missing: [Specific missing value/metric]
- (or write "None")
[/PRD_HANDOFF_BLOCK]
```

### 4B — Traveling context file (PRD → all downstream phases)

Produce a file named `CONTEXT.md` alongside this PRD document.

This file is written once, here, and must not be modified by any downstream phase. Every downstream phase prompt (EPIC, MDAP, Architecture, Folder/File Structure) must open `CONTEXT.md` at its start and treat its contents as read-only ground truth.

Populate `CONTEXT.md` with the following content, replacing all bracketed placeholders with the actual values from this document:

```markdown
# CONTEXT.md
# Pipeline traveling context — DO NOT MODIFY
# Written by: PRD phase
# Read by: EPIC · MDAP · Architecture · Folder/File Structure

TRAVELING_CONTEXT:
  scope_ceiling: "[exact scope ceiling statement from Section 1]"
  canonical_ids: "FR-001 through FR-[N], NFR-001 through NFR-[M]"
  hard_constraints: "[list any confirmed non-negotiable constraints; write NONE if none confirmed]"
  open_assumptions: "[count] unresolved [ASSUMPTION] items — see OQ-XXX through OQ-XXX"
  open_thresholds: "[count] [THRESHOLD NEEDED] items — see OQ-XXX through OQ-XXX"
  out_of_scope_summary: "[one sentence summarising what is explicitly excluded]"
  pipeline_stage: "PRD — next: EPIC"
```

---

*Document generated by PRD Prompt v2.0. For governance rules, citation format, and human review protocol see `development.md`. For agent behavior rules see `agents.md`. For phase transition gates and sign-off checklist see `PIPELINE.md`.*