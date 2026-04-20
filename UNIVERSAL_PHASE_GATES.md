## Meta-Rules for PRD → EPIC → MDAP → ARCHITECTURE → FOLDER STRUCTURE Pipeline

**These rules apply to ALL five prompts. They are non-negotiable.**

markdown

**#**

**UNIVERSAL PHASE GATES**

**##**

**Meta-Rules for PRD → EPIC → MDAP → ARCHITECTURE → FOLDER STRUCTURE Pipeline**

**These rules apply to ALL five prompts. They are non-negotiable.**

---

**##**

**RULE 1: NO AUTOMATIC CHAINING**

Do NOT execute prompts in an automated pipeline.

Between each step:
- [ ] Human must review the output
- [ ] Human must verify gate conditions (below)
- [ ] Human must approve advancement
- [ ] Only then is the next prompt executed

**Execution Model:**
```
Prompt 1 → Output Review (HUMAN GATE) → Approval → Prompt 2
Prompt 2 → Output Review (HUMAN GATE) → Approval → Prompt 3
Prompt 3 → Output Review (HUMAN GATE) → Approval → Prompt 4
Prompt 4 → Output Review (HUMAN GATE) → Approval → Prompt 5
```

**No batch execution. No overnight runs. Human-in-the-loop is mandatory.**

---

**##**

**RULE 2: UNIVERSAL ADVANCEMENT GATE (Required Before ANY Next Step)**

Before moving from Step N to Step N+1, VERIFY ALL of these:

**###**

**2A — Scope Creep Check**

- [ ] Does the output introduce ANY feature, requirement, or scope not present in PRD_HANDOFF_BLOCK?
- [ ] Does the output exceed the scope ceiling from PRD Section 1?
- [ ] Has any decision been made because it "seemed like a good idea" vs. traced to a requirement?

**If FAIL:** Flag scope creep in CURRENT step's "Open Questions" section. Do NOT advance until resolved.

**###**

**2B — Traceability Verification**

- [ ] Can you trace EVERY major decision in the output back to:
  - A PRD requirement (FR/NFR ID), OR
  - A prior phase output (EPIC/MDAP/Architecture), OR
  - An explicit architectural constraint?
- [ ] Are there ANY decisions with no cited justification?
- [ ] Are there ANY items labeled "TBD" or "TBD by stakeholders" that are blockers for next step?

**If FAIL:** Flag untraced decisions. Do NOT advance until all are traced.

**###**

**2C — Flagged Items Are NOT Ignored**

- [ ] All items flagged "requires human review" in this step have been:
  - [ ] Reviewed by appropriate domain expert (security, architecture, etc.)
  - [ ] Documented with expert's decision (approved/rejected/rework)
  - [ ] Resolved BEFORE next step begins
- [ ] No flagged items are being deferred to "implementation phase"

**If FAIL:** Do NOT advance. Flagged items block progression.

**###**

**2D — Authoritative Source Verification**

- [ ] Every technology choice, pattern, or architectural decision cites:
  - A PRD/NFR requirement, OR
  - Documented evidence (benchmark, official doc, case study)
- [ ] No technology was selected because "everyone uses it" or "it's trendy"
- [ ] For ARCHITECTURE: Research was documented (if conducted)

**If FAIL:** Require evidence before advancing.

**###**

**2E — Bounded Scope Enforcement**

- [ ] This step did NOT speculate about:
  - Future features not in PRD
  - "Nice to have" conveniences
  - Unnecessary abstraction layers
  - "We might need this later" scope
- [ ] Only features/decisions traceable to current requirements were included

**If FAIL:** Remove speculative scope. Do NOT advance with it.

**###**

**2F — Handoff Clarity Test**

- [ ] Could a new engineer (who has never seen this product) read the output and understand:
  - What was decided?
  - Why it was decided?
  - What depends on this decision downstream?
  - Where to find supporting evidence (linked to prior phases)?
- [ ] Are there unexplained acronyms, insider jargon, or missing context?
- [ ] Is every section self-contained enough to stand alone?

**If FAIL:** Improve documentation. Do NOT advance with unclear output.

**###**

**2G — Self-Audit Prohibition**

- [ ] The output does NOT include statements like:
  - "I have verified that all X are present"
  - "I have confirmed no scope creep"
  - "I have checked all dependencies"
- [ ] If output includes such statements, they are noted as "AI self-assessment" and MUST be independently verified by human before advancing

**If FAIL:** Human must independently verify before advancing.

**###**

**2H — No Autonomous Auth/Payments**

- [ ] This step does NOT delegate authentication decisions to the agent
- [ ] This step does NOT authorize payment or money movement
- [ ] Security-critical decisions are explicitly flagged for expert review (not auto-approved)

**If FAIL:** Require explicit human authorization before advancing.

**###**

**2I — Output Completeness**

- [ ] All required sections from the prompt template are present
- [ ] No sections were skipped or deferred with "N/A"
- [ ] If section is truly not applicable, it is explicitly documented WHY (not just skipped)

**If FAIL:** Complete missing sections before advancing.

**###**

**2J — Acceptance Criteria Traceability (if applicable)**

- [ ] Every user story, module, or component has binary acceptance criteria
- [ ] Acceptance criteria are measurable and testable
- [ ] Acceptance criteria trace back to PRD or prior phase requirements

**If FAIL:** Add/clarify acceptance criteria before advancing.

---

**##**

**RULE 3: UNIFIED SCOPE CREEP DETECTION**

Scope creep manifests as:

**TYPE A: Feature Creep**
- New features not in PRD FRs/NFRs
- Example: "We should add caching" (if not in NFR)
- Example: "Let's add admin dashboard" (if not in PRD)

**TYPE B: Assumption Creep**
- Resolving unresolved assumptions without stakeholder input
- Example: [THRESHOLD NEEDED] for concurrent users → LLM assumes 100
- Example: [ASSUMPTION] about user behavior → treated as fact

**TYPE C: Architectural Creep**
- Adding layers, patterns, or technologies not justified by requirements
- Example: Microservices for a small monolith product
- Example: Event-driven architecture when sync request/response suffices

**TYPE D: Module Creep**
- Creating modules not traceable to MDAP
- Example: "Helper utilities" without Epic reference
- Example: "Common functions" without module ownership

**Detection:**
In EVERY prompt, ask: "Is this decision driven by a requirement (PRD/EPIC/prior phase) or by 'good engineering practice'?"

If the answer is the latter, flag it as potential scope creep.

---

**##**

**RULE 4: TRACEABILITY CHAIN (Unified Across All Phases)**

Every artifact in the pipeline must be traceable:
```
PRD Requirement (FR-XXX)
    ↓ (justified in)
EPIC (EPIC-YYY covers FR-XXX)
    ↓ (decomposed into)
MODULE (MODULE-YYY-ZZ serves EPIC-YYY)
    ↓ (organized into)
COMPONENT (Component contains MODULE-YYY-ZZ)
    ↓ (mapped to)
FILE (src/component/file.ts implements MODULE-YYY-ZZ)
    ↓ (tested by)
Test Case (test/component/file.test.ts validates AC from FR-XXX)
```

**Verification:** At each step, ask: "Can I trace this backwards to the PRD?"

If NO: It's orphaned scope. Flag and remove.

---

**##**

**RULE 5: FLAGGED ITEMS BLOCK ADVANCEMENT**

Items flagged as "requires human review" or marked with ⚠️ are BLOCKERS.

**Definition of Blocker:**
- Authentication flows (must be reviewed by security engineer)
- Payment processing (must be reviewed by security + compliance)
- External integrations (must be reviewed by infrastructure)
- Complex algorithms (must be reviewed by domain expert)
- Unresolved assumptions (must be reviewed by stakeholder)
- Circular dependencies (must be resolved before advancement)

**Action:**
- [ ] Flag is acknowledged in output
- [ ] Domain expert reviews and approves/rejects/reworks
- [ ] Decision is documented with expert name and date
- [ ] If rejected/rework: scope change is documented
- [ ] ONLY after approval: next step may proceed

**Do NOT defer to "implementation phase."** Flagged items at each phase must be resolved at that phase.

---

**##**

**RULE 6: AUTHORITATIVE SOURCE REQUIREMENT**

Every significant decision must cite evidence:

**Acceptable Evidence:**
- ✅ PRD requirement (FR-XXX cites this)
- ✅ Official documentation (AWS docs, database docs, RFC)
- ✅ Benchmark study (published, reproducible)
- ✅ Case study (named company, documented architecture)
- ✅ Academic paper (peer-reviewed, relevant)

**NOT Acceptable:**
- ❌ "Industry best practice" (without citation)
- ❌ "Everyone uses X" (without evidence)
- ❌ "It's trendy" (not evidence)
- ❌ "Seemed like a good idea" (not evidence)
- ❌ ChatGPT/LLM opinion (unless validated)

**Application:**
In ARCHITECTURE phase: Every technology choice must cite one of the above.

---

**##**

**RULE 7: BOUNDED SCOPE ENFORCEMENT**

At every step, ask: "What am I NOT doing and why?"

**Bounded Scope Checklist:**
- [ ] Are there code paths, features, or modules I'm skipping? YES → document why
- [ ] Are there "nice to have" additions I'm excluding? YES → document why
- [ ] Are there future-proofing considerations I'm deferring? YES → document where
- [ ] Are there architectural "levels" I could add but aren't? YES → document why not

**Example (Good Bounded Scope):**
```
Rejected: Microservices architecture
Reason: PRD requires <1,000 concurrent users; monolith sufficient per NFR-004
Future: If NFR changes to >10,000 concurrent, revisit in Architecture phase 2
```

**Example (Bad — Unbounded):**
```
Added: Message queue (just in case we scale)
Added: Redis caching (performance optimization, not required)
Added: Admin dashboard (future feature)
```

---

**##**

**RULE 8: NEW ENGINEER HANDOFF TEST**

Before advancing from Step N to Step N+1, ask:

**Can a new engineer who has NEVER seen this product:**
1. Read the output and understand every decision?
2. Find evidence for every decision (linked to prior docs)?
3. Identify what's still unresolved and blocked?
4. See where to find PRD requirements, Epic definitions, module specs?
5. Know which items require expert review before implementation?

**If NO to any:**
- Clarify documentation
- Add links to prior phases
- Explain unexplained terms
- Document assumptions explicitly
- Do NOT advance until YES to all

---

**##**

**RULE 9: RESEARCH DOCUMENTATION (Architecture Phase Only)**

If research was conducted (web search):

- [ ] What was searched (exact query)
- [ ] What was found (summary of findings)
- [ ] How it influenced decisions (specific architectural choices changed)
- [ ] Contradictions with PRD (if any)

All documented in RESEARCH SUMMARY section.

If research was NOT conducted, section is omitted (not left blank).

---

**##**

**RULE 10: USE THE ADVANCEMENT GATE SIGN-OFF TEMPLATE**

Before advancing from any phase to the next, use the **ADVANCEMENT GATE SIGN-OFF TEMPLATE** 
(provided at the end of this document) to verify ALL rules (2A-2J).

The template provides the structured checklist for Rule 2 verification.
Do not skip this step. Print it, fill it out, sign it, and file it with your project records.

---

**##**

**IMPLEMENTATION: Where These Rules Apply**

|

**Rule**

|

**PRD**

|

**EPIC**

|

**ARCH**

|

**MDAP**

|

**FOLDER**

|
|------|-----|------|------|------|--------|
| Rule 1 (No auto-chaining) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Rule 2 (Advancement gate) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Rule 3 (Scope creep detection) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Rule 4 (Traceability chain) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Rule 5 (Flagged items block) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Rule 6 (Authoritative source) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Rule 7 (Bounded scope) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Rule 8 (New engineer test) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Rule 9 (Research docs) | — | — | ✓ | — | — |
| Rule 10 (Sign-off template) | ✓ | ✓ | ✓ | ✓ | ✓ |

---

**##**

**HOW TO USE THE ADVANCEMENT GATE SIGN-OFF TEMPLATE**

Use this template BEFORE EVERY PHASE TRANSITION:

1. Print it (or copy to document)
2. Go through Rule 2A-2J
3. Mark [PASS] or [FAIL] for each rule
4. Sign and date
5. File with project records

This checklist is static and reusable across all projects.

---

**##**

**ADVANCEMENT GATE SIGN-OFF TEMPLATE**

```
ADVANCEMENT GATE SIGN-OFF

Phase Completed: [PRD / EPIC / ARCHITECTURE / MDAP / FOLDER STRUCTURE]
Output Date: [date]
Reviewer Name: [human reviewer]
Email: [reviewer contact]

---

VERIFICATION (Check all before advancing):

Rule 2A — Scope Creep Check
- [ ] No features beyond PRD_HANDOFF_BLOCK
- [ ] Scope ceiling respected
- [ ] No "good idea" decisions without requirement trace
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2B — Traceability Verification
- [ ] Every decision traced to requirement
- [ ] No orphaned decisions
- [ ] All TBDs acknowledged and resolved
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2C — Flagged Items Resolved
- [ ] All "requires human review" items have expert sign-off
- [ ] No flagged items deferred
- [ ] Decisions documented with expert name/date
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2D — Authoritative Source Verification
- [ ] All tech choices cited with evidence
- [ ] All decisions have authoritative justification
- [ ] Research documented (if ARCHITECTURE phase)
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2E — Bounded Scope Enforcement
- [ ] No speculative features
- [ ] No "nice to have" padding
- [ ] Only traced scope included
- [ ] Rejected scope documented
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2F — Handoff Clarity Test
- [ ] New engineer can understand all decisions
- [ ] Context provided for unexplained terms
- [ ] Evidence linked to prior phases
- [ ] All sections self-contained
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2G — No Self-Audit
- [ ] LLM did not self-validate output
- [ ] Human independently verified
- [ ] No "I have verified" statements in output
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2H — No Autonomous Auth/Payments
- [ ] Security decisions flagged (not auto-approved)
- [ ] Expert review documented
- [ ] No autonomous money movement authorized
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2I — Output Completeness
- [ ] All required sections from template present
- [ ] No sections skipped with "N/A"
- [ ] Missing sections documented with WHY
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

Rule 2J — Acceptance Criteria Traceability
- [ ] Every story/module/component has binary criteria
- [ ] Criteria are measurable and testable
- [ ] Criteria trace to PRD or prior phase
Status: [PASS / FAIL]
Notes (if FAIL): _______________________________________________

---

OVERALL GATE VERDICT:
[✅ APPROVED TO ADVANCE / ❌ BLOCKED — REWORK REQUIRED]

If BLOCKED, list all blockers below:
1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

Next Step Preparation:
- [ ] All blockers resolved and documented
- [ ] Output ready for next phase input
- [ ] Next prompt input prepared and verified

Next Phase Ready: [YES / NO]
Next Prompt: [PROMPT-N-NAME]
Next Prompt Input: [confirm what will be passed]
```

---

**END OF UNIVERSAL_PHASE_GATES.md**