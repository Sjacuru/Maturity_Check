⚠️ **ADVANCEMENT GATE REQUIRED**

Before executing this prompt, you must have:

1. Completed PROMPT 2 (EPIC generation)
2. Reviewed the EPIC output against UNIVERSAL_PHASE_GATES.md Rule 2A-2J
3. Completed the advancement sign-off (all items PASS)
4. All flagged Epics resolved with expert sign-off

Do not proceed without completed advancement gate.

---

## INPUT SPECIFICATION

ARCHITECTURAL INPUTS:

1. PRD_HANDOFF_BLOCK (from PRD phase) — scope, requirements, personas
2. 5A Phase Transition Note (from EPIC phase) — Epic dependencies, unresolved items
3. MDAP Module Registry (from MDAP phase) — all MODULE-[Epic]-[ID] definitions
4. Embedded **CONTEXT traveling-state block** (from prior phase output; do NOT create a separate `CONTEXT.md` file) — module domain mapping, cross-Epic dependencies

## RESEARCH GATE (Optional)

Before defining architecture, you may search the web for:

- How others solved similar architectural problems
- Industry patterns for your system scale/complexity
- Proven technology combinations for your use case
- Real-world examples of similar systems

**Rules for research:**

1. Research INFORMS decisions, does not DICTATE them
2. All architecture decisions must cite PRD/EPIC justification (not "industry best practice")
3. Document what you searched, what you learned, how it influenced decisions
4. If research contradicts PRD requirements, flag as assumption requiring stakeholder decision
5. Do not adopt external patterns that conflict with your scope ceiling

**Document findings in Architecture output:**

```
RESEARCH SUMMARY (if conducted):
- What was searched: [query]
- What was learned: [findings]
- How it influenced this architecture: [impact]
- Contradictions with PRD (if any): [list]
```

If you conduct research, include this summary section before the "Architecture Overview" section.
If you do not conduct research, skip this section and proceed directly to "Architecture Overview."

## GATE CHECK: Before defining architecture, verify:

1. All MDAP outputs available (modules for all Epics processed)
2. Module registry in the embedded CONTEXT block is complete
3. Domain mapping present (Frontend/Backend/Data consolidation hints)
4. Unresolved assumptions from 5A.3 documented
If insufficient, flag and request missing MDAP outputs.

## STRICT CONSTRAINTS

§1 — Justify every architectural decision with a PRD/EPIC requirement
§2 — Prefer simplest architecture satisfying acceptance criteria
§3 — Explicitly acknowledge trade-offs (what you gain/lose)
§4 — No premature optimization (design for NFR scale, not future scale)
§5 — Technology choices: Why selected + which requirement + limitations
§6 — Security & compliance are first-class concerns (not afterthought)
§7 — Define failure modes explicitly per component
§8 — No code or pseudocode
§9 — Flag decisions requiring human domain expertise
§10 — Map modules (from MDAP) to architectural components
Consolidate by domain/layer (Frontend, Backend, Data, etc.)
§11 — Document consolidation strategy: Why modules grouped this way
§12 — If architectural constraint conflicts with unresolved assumption (from 5A.3),
flag for stakeholder decision. Do not resolve yourself.

## REQUIRED DOCUMENT STRUCTURE

### 1. Architecture Overview

- System style (monolith, modular monolith, microservices, serverless) with PRD justification
- High-level component diagram description
- What was considered and rejected, and why

### 2. Technology Stack

| Layer | Technology | Justification | Alternative | Limitation |
| --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... |

### 3. Module-to-Component Mapping

Map MDAP modules to architectural components:

| Component | Modules | Responsibility | Rationale |
| --- | --- | --- | --- |
| Frontend Service | MODULE-001-03, MODULE-002-03, MODULE-003-02 | UI rendering + user interaction | Consolidated by domain |
| Auth Service | MODULE-001-01, MODULE-001-02 | Authentication & tokens | From EPIC-001 |
| Profile Service | MODULE-002-01, MODULE-002-02 | Profile data + API | From EPIC-002 |

### 4. Module Consolidation Strategy

Document why modules are grouped into components:

```
CONSOLIDATION LOGIC:

By Domain (Technical Deployment):
├─ Frontend Service: All UI modules (MODULE-*-03)
├─ Backend Service: All API/data modules (MODULE-*-01, MODULE-*-02)
├─ Auth Service: Security-critical modules (MODULE-001-*)

By Epic (Logical Organization):
├─ EPIC-001 (Auth): 3 modules
├─ EPIC-002 (Profile): 3 modules
├─ EPIC-003 (Settings): 1 module

Rationale: MDAP decomposes by Epic responsibility (logical).
Architecture consolidates by deployment layer (technical).
Both views preserved in CONTEXT.md for traceability.
```

### 5. System Components (Detail)

For each architectural component:

- Name and responsibility
- Modules it contains
- Interfaces exposed
- Dependencies
- Failure mode and recovery
- PRD requirements satisfied

### 6. Data Architecture

- Entities and relationships
- Data ownership per component
- Data flow
- Data at rest, in transit, retention
- PRD requirements satisfied

### 7. Security Architecture

- Trust boundaries map
- Authentication mechanism + justification
- Authorization model + justification
- Secrets management
- Known attack surfaces + mitigations
- **SECURITY FLAGS (Human Review Required):**
    - [ ]  Authentication flows
    - [ ]  Authorization/permission management
    - [ ]  Payment processing (if applicable)
    - [ ]  Secret management
    - [ ]  External API credentials

### 8. Integration Points

- External systems + expected SLA
- Fallback behavior if unavailable
- Data contracts and versioning

### 9. Scalability & Performance

- Bottleneck identification (from NFRs)
- Horizontal vs. vertical scaling per component
- Caching strategy (if justified by NFRs)
- Load handling approach

### 10. Deployment Architecture

- Environment strategy
- CI/CD pipeline overview
- Infrastructure-as-code (yes/no, justified)
- Rollback strategy

### 11. Architectural Risks & Open Decisions

- Deferred decisions and why
- Assumptions requiring human validation
- Unresolved items from 5A.3 affecting this architecture
- Conditions for revisiting this architecture

## OUTPUT VERIFICATION

- [ ]  Every component maps to MDAP modules
- [ ]  Every technology choice cites PRD/NFR requirement
- [ ]  Failure modes defined for all major components
- [ ]  Trust boundaries explicitly identified
- [ ]  Module consolidation strategy documented
- [ ]  Security-critical components flagged for human review
- [ ]  No code or pseudocode included
- [ ]  Simplest architecture satisfying requirements chosen
- [ ]  Unresolved assumptions (5A.3) acknowledged
- [ ]  If research conducted: documented in Research Summary section

## UPDATED CONTEXT BLOCK (embedded; do NOT create a new file)

After defining architecture, output:

```
[CONTEXT.MD_UPDATE]
## CONTEXT — Architecture Definition Complete (append-only)

### System Style: [e.g., Modular Monolith]

### Components:
- [Component Name]: [Modules], [Responsibility]
- [Component Name]: [Modules], [Responsibility]

### Technology Stack:
- Frontend: [tech]
- Backend: [tech]
- Database: [tech]
- Auth: [tech]

### Module Consolidation:
- Frontend Service: [MODULE list by domain]
- Backend Service: [MODULE list by domain]

### High-Risk Components (Human Review):
- [Component]: [reason]

### Architectural Risks:
- [risk description]

### Unresolved Assumptions Affecting Architecture:
- [list from 5A.3]

### Research Conducted (if any):
- What was researched: [query]
- Key findings: [summary]
- Impact on architecture: [changes made]

[/CONTEXT.MD_UPDATE]
```

## 7A — PHASE TRANSITION NOTE FOR FOLDER/FILE STRUCTURE

After architecture definition, output:

[7A_PHASE_TRANSITION_NOTE]

### Components Ready for File Structuring:
1. [Component]: [Modules], [Responsibility], [Risk Level]
2. [Component]: [Modules], [Responsibility], [Risk Level]

### Module-to-File Mapping Guidance:
Each component should map to a top-level folder:
- /frontend: [MODULE-*-03 list]
- /backend: [MODULE-*-01, MODULE-*-02 list]
- /auth: [MODULE-001-* list]

### High-Risk Components (Implementation Review Before Coding):
- [Component]: [reason]

### Dependency Graph:
- [Component A] depends on [Component B] (explicit)

[/7A_PHASE_TRANSITION_NOTE]