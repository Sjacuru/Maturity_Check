⚠️ **ADVANCEMENT GATE REQUIRED**

Before executing this prompt, you must have:

1. Completed PROMPT (Architecture definition)
2. Reviewed the Architecture output against UNIVERSAL_PHASE_GATES.md Rule 2A-2J
3. Completed the advancement sign-off (all items PASS)
4. All flagged components resolved with expert sign-off

Do not proceed without completed advancement gate.

---

## INPUT SPECIFICATION

SPECIFIC EPIC TO PROCESS:

- EPIC-ID: [specify which Epic, e.g., EPIC-002]
- Full Epic document for this Epic
- Epic's user stories and acceptance criteria

CONTEXT (read-only reference):

- 5A Phase Transition Note (all Epic dependencies)
- Embedded **CONTEXT traveling-state block** (from prior phase output; do NOT create a separate `CONTEXT.md` file)
- Previous MDAP outputs (modules from prior Epics)
- Architecture Definition

## GATE CHECK: Before creating modules, verify:

1. EPIC-ID is specified and complete
2. All dependencies for this Epic documented in 5A.4
3. Previous modules available in the embedded CONTEXT block (if any)
4. No blocking unresolved assumptions from 5A.3 for THIS Epic
If insufficient, flag and proceed with PARTIAL status.

## STRICT CONSTRAINTS

§1 — Modules must respect architectural boundaries
§2 — One module, one responsibility
§3 — Modules independently testable/deployable
§4 — Define contracts (interface + dependencies), not implementation
§5 — Minimize dependencies; justify each
§6 — Every module traces to THIS Epic's user stories
§7 — Identify parallel workstreams within THIS Epic
§8 — No code, no implementation logic
§9 — Flag high-risk modules for expert review
§10 — Propose minimum modules needed
§11 — Cross-Epic Dependencies: Document if MODULE from THIS Epic depends
on MODULE from prior Epic. Check 5A.4 (Epic blocking order) —
if your Epic is blocked by prior Epic, cross-module dependencies are OK.
If your Epic blocks prior Epic, cross-module dependencies are NOT allowed.
§12 — Conflict Resolution: If THIS Epic's modules conflict with prior Epic's modules,
document in Open Questions. Do not resolve yourself.
§13 — Circular Dependency Check: Check MODULE dependency graph for cycles
(within THIS Epic only; cross-Epic cycles checked in Architecture phase).

## REQUIRED STRUCTURE PER MODULE

MODULE-[EPIC-ID]-[INDEX]: [Name]
| Responsibility | Single sentence |
| User Stories | Which user stories from THIS Epic this module satisfies |
| Module Type | Domain Logic / Infrastructure / Interface / Utility / Integration |
| Public Interface | Inputs/outputs |
| Dependencies | Which modules (from THIS Epic or prior Epics) |
| Consumed By | Which modules will use this |
| Isolation Level | Can test independently? |
| Parallel? | Can start without other modules in THIS Epic? |
| Risk Level | Low / Medium / High |
| Flag for Review | Yes / No |
| Cross-Epic Dep? | If depends on prior module, which one and why |

## DEPENDENCY MAP (THIS EPIC ONLY)

- List module dependencies within THIS Epic
- Identify circular dependencies (must resolve)
- Identify critical path
- Identify parallel workstreams

## COVERAGE MATRIX (THIS EPIC)

| User Story | Module IDs | Covered? |
| --- | --- | --- |
| US-001 | MODULE-002-01 | ✅ |
| US-002 | MODULE-002-02 | ✅ |
| US-003 | — | ⚠️ UNCOVERED |

Every user story for THIS Epic must map to at least one module.

## OUTPUT VERIFICATION

- [ ]  Every module traces to THIS Epic (not other Epics)
- [ ]  Every user story has module coverage
- [ ]  No circular dependencies within THIS Epic
- [ ]  High-risk modules flagged
- [ ]  Cross-Epic dependencies documented and justified
- [ ]  Minimum viable modules
- [ ]  Public interfaces defined
- [ ]  Parallel workstreams identified

## UPDATED CONTEXT BLOCK (embedded; do NOT create a new file)

After generating modules, output:

```
[CONTEXT.MD_UPDATE]
## CONTEXT — MDAP Module Registry (append-only)

### EPIC-002 Modules:
- MODULE-002-01: [name] | Type: [type] | Domain: [domain]
- MODULE-002-02: [name] | Type: [type] | Domain: [domain]

### Cross-Epic Dependencies (NEW):
- MODULE-002-01 depends on MODULE-001-02 (explain why)

### Total Modules So Far: [count] (EPIC-001: X, EPIC-002: Y, ...)

### High-Risk Modules Flagged: [list]

### Unresolved Assumptions Affecting THIS Epic: [list from 5A.3]

[/CONTEXT.MD_UPDATE]
```

## 6A — PHASE TRANSITION NOTE FOR ARCHITECTURE (When All Epics Processed)

This section is generated AFTER all MDAP calls complete.
For now, output:

6A (PRELIMINARY): Processing EPIC-002
All modules for Epics 1-2: [count] modules
Pending Epics 3-N: Full module registry in next MDAP calls