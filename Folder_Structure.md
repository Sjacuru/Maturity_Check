⚠️ **ADVANCEMENT GATE REQUIRED**

Before executing this prompt, you must have:

1. Completed PROMPT 4 (MDAP for all Epics)
2. Reviewed the MDAP output against UNIVERSAL_PHASE_GATES.md Rule 2A-2J
3. Completed the advancement sign-off (all items PASS)
4. All flagged modules resolved with expert sign-off

Do not proceed without completed advancement gate.

---

**##**

**INPUT SPECIFICATION**

STRUCTURAL INPUTS:
1. 7A Phase Transition Note (from Architecture phase)
   - Components and module mapping
   - Architectural pattern selected
   - High-risk components flagged
   
2. MDAP Module Registry (from MDAP phase)
   - All MODULE-[Epic]-[ID] definitions
   - Module types and responsibilities
   - Module-to-component mapping
   
3. Architecture Definition (from Architecture phase)
   - System style (monolith, modular, microservices)
   - Technology stack (languages, frameworks, databases)
   - Naming conventions and patterns to follow
   
4. CONTEXT.md (traveling state)
   - Project scope ceiling and canonical IDs
   - Module registry with domains
   - Unresolved assumptions
   - NOTE: Do NOT create a separate `CONTEXT.md` file; use the embedded CONTEXT blocks emitted by prior prompts.

**##**

**GATE CHECK: Before creating file structure, verify:**

1. 7A Phase Transition Note is complete (all components defined)
2. MDAP Module Registry has all modules for all Epics
3. Architecture Definition specifies:
   - System style (e.g., Clean Architecture, Feature-Based, Monolithic)
   - Technology stack with file conventions
   - Named patterns to follow
4. Module-to-component mapping is clear
If missing, request from Architecture phase before proceeding.

**##**

**STRICT CONSTRAINTS**

§1 — Every file maps to exactly one MDAP module (no untraced files)
§2 — Every folder has stated purpose (architectural or module boundary)
§3 — Follow selected architecture's naming conventions strictly (no mixing styles)
§4 — No implementation code (headers + stubs only)
§5 — File naming is deterministic and convention-driven (state convention first)
§6 — Configuration files: list with purpose, secrets handling, committed status
§7 — Test structure mirrors source structure (tests for every testable module)
§8 — No speculative files ("we might need this later" not accepted)
§9 — Entry points explicitly identified and described
§10 — Security-critical, integration, algorithmic files flagged for human review
§11 — File header format mandatory for every file (see format below)
§12 — This phase creates file stubs only. No business logic, algorithms, or implementation. Next phase (implementation) writes the actual code.

**##**

**REQUIRED FILE HEADER FORMAT**

Every file must include this header (language-appropriate comment):
```
FILE: [relative/path/to/file]
MODULE: [MODULE-ID] — [Module Name]
EPIC: [EPIC-ID] — [Epic Name]
RESPONSIBILITY: [Single sentence: what this file does]
EXPORTS: [What this file exposes to other modules]
DEPENDS_ON: [Other files/modules this imports from]
ACCEPTANCE_CRITERIA:
  - [Criterion 1 — binary, measurable]
  - [Criterion 2 — binary, measurable]
HUMAN_REVIEW: [Yes/No — if Yes, state reason]
```

**##**

**DOCUMENT STRUCTURE**

**###**

**1. Naming Convention Declaration**

State the file and folder naming convention(s):

Architecture Pattern: [e.g., "Clean Architecture: Controllers/Services/Repositories"]

Naming Rules:
- Folders: [convention, e.g., "snake_case for feature folders"]
- Files: [convention, e.g., "PascalCase for classes, camelCase for functions"]
- Modules: [convention, e.g., "MODULE-[EPIC-ID]-[INDEX]-[name]"]
- Tests: [convention, e.g., "mirror source structure, .test.ts suffix"]

Rationale: [Why these conventions fit the architecture]

**###**

**2. Module-to-File Mapping**

Map MDAP modules to file organization:

| **Module ID** | **Module Name** | **Type** | **Component** | **Files Created** |
|-------              ----|------    ------|----                 --|------                -----|-------              --------|
| MODULE-001-01 | Auth Logic   | Domain Logic | Auth Service         | `src/auth/logic.ts`     |
| MODULE-001-02 | Auth API       | Interface          | Auth Service         | `src/auth/api.ts`        |
| MODULE-001-03 | Auth UI         | Interface          | Frontend Service | `src/pages/auth.tsx` |
| MODULE-002-01 | Profile Data | Domain Logic | Profile Service      |  `src/profile/data.ts`  |

**Consolidation shown:** Modules grouped by component folder.

**###**

**3. Environment and Configuration Files**

| **File** | **Purpose** | **Contains Secrets?** | **Committed?** | **Handled By** |
|------|---------|------------------|-----------|-----------|
| `.env.example` | Template for env vars | No (template) | Yes | Developers copy to `.env` |
| `.env` | Actual secrets | Yes | NO — in .gitignore | DevOps/local setup |
| `config/app.config.ts` | App configuration | No | Yes | Code |
| `.gitignore` | Exclusions | N/A | Yes | Code |

**###**

**4. Full Folder and File Tree**

**IMPORTANT: This structure is GENERATED FROM YOUR MDAP OUTPUT, not a template.**

The example below is for a project with:
- 3 Epics
- 9 modules across 3 components
- Frontend + Backend + Config

Your actual structure will differ based on:
- Number of modules in YOUR MDAP
- Number of components in YOUR Architecture Definition
- Your technology stack and naming conventions

**RULE: Create folders ONLY for:**
1. Each component (from Architecture Definition)
2. Each module within that component (from MDAP)
3. Standard folders: config/, tests/, shared/ (if needed)

**For a simple project with 2 modules, you would have:**
```
project-root/
├── src/
│   ├── auth/                          # Component: Auth Service
│   │   ├── logic.ts                   # MODULE-001-01
│   │   └── logic.test.ts
│   └── index.ts
├── config/
├── .env.example
├── .gitignore
└── package.json
```

**Do NOT create:**
- Nested folders you don't need
- Placeholder files for future features
- Extra abstraction layers

Structure matches MDAP complexity. Nothing more, nothing less.

---

**EXAMPLE for medium-complexity project (use as reference, not template):**
```
project-root/
├── src/
│   ├── auth/                          # Component: Auth Service
│   │   ├── logic.ts                   # MODULE-001-01
│   │   ├── logic.test.ts              # Tests for MODULE-001-01
│   │   ├── api.ts                     # MODULE-001-02
│   │   ├── api.test.ts                # Tests for MODULE-001-02
│   │   └── index.ts                   # Exports for this component
│   │
│   ├── profile/                       # Component: Profile Service
│   │   ├── data.ts                    # MODULE-002-01
│   │   ├── data.test.ts               # Tests for MODULE-002-01
│   │   ├── service.ts                 # MODULE-002-02
│   │   ├── service.test.ts            # Tests for MODULE-002-02
│   │   └── index.ts                   # Exports for this component
│   │
│   ├── ui/                            # Component: Frontend Service
│   │   ├── pages/
│   │   │   ├── auth.tsx               # MODULE-001-03
│   │   │   ├── auth.test.tsx          # Tests for MODULE-001-03
│   │   │   ├── profile.tsx            # MODULE-002-03
│   │   │   └── profile.test.tsx       # Tests for MODULE-002-03
│   │   └── index.ts                   # Exports for this component
│   │
│   ├── shared/                        # Shared utilities (cross-component)
│   │   ├── types.ts                   # Shared type definitions
│   │   ├── constants.ts               # Shared constants
│   │   └── index.ts
│   │
│   └── index.ts                       # Application entry point
│
├── config/
│   ├── app.config.ts                  # App configuration (no secrets)
│   ├── database.config.ts             # Database configuration
│   └── index.ts
│
├── tests/
│   └── integration/                   # Integration tests (cross-module)
│       ├── auth-profile.test.ts
│       └── index.ts
│
├── .env.example                       # Template for developers
├── .env                               # (Not committed — local secrets)
├── .gitignore
├── package.json                       # Dependencies and scripts
├── tsconfig.json                      # TypeScript configuration
├── jest.config.js                     # Test runner configuration
└── README.md                          # Project documentation
```

---

**###**

**5. File Manifest**

| **File Path** | **Module ID** | **Epic ID** | **Responsibility** | **Exports**| **Flagged**

|
|-----------|-----------|---------|----------------|---------|---------|
| src/auth/logic.ts | MODULE-001-01 | EPIC-001 | Authenticate user credentials | `authenticateUser()` | Yes — security |
| src/auth/logic.test.ts | MODULE-001-01 | EPIC-001 | Test auth logic | N/A | No |
| src/auth/api.ts | MODULE-001-02 | EPIC-001 | Expose auth endpoints | `POST /auth/login` | Yes — security |
| src/auth/api.test.ts | MODULE-001-02 | EPIC-001 | Test auth API | N/A | No |
| src/profile/data.ts | MODULE-002-01 | EPIC-002 | Profile data model | `Profile` interface | No |
| src/profile/data.test.ts | MODULE-002-01 | EPIC-002 | Test profile data | N/A | No |
| src/profile/service.ts | MODULE-002-02 | EPIC-002 | Profile business logic | `getProfile()` | No |
| src/profile/service.test.ts | MODULE-002-02 | EPIC-002 | Test profile service | N/A | No |
| src/ui/pages/auth.tsx | MODULE-001-03 | EPIC-001 | Auth UI component | `AuthPage` | Yes — security |
| src/ui/pages/auth.test.tsx | MODULE-001-03 | EPIC-001 | Test auth UI | N/A | No |
| src/ui/pages/profile.tsx | MODULE-002-03 | EPIC-002 | Profile UI component | `ProfilePage` | No |
| src/ui/pages/profile.test.tsx | MODULE-002-03 | EPIC-002 | Test profile UI | N/A | No |
| src/shared/types.ts | (shared) | (N/A) | Shared type definitions | `User`, `Profile` | No |
| src/shared/constants.ts | (shared) | (N/A) | Shared constants | `APP_NAME` | No |
| src/index.ts | (entry point) | (N/A) | Application bootstrap | `start()` | No |
| config/app.config.ts | (config) | (N/A) | App configuration | Config object | No |
| config/database.config.ts | (config) | (N/A) | Database configuration | Config object | No |
| tests/integration/auth-profile.test.ts | (integration) | (EPIC-001 + EPIC-002) | Test auth-to-profile flow | N/A | No |

**###**

**6. Entry Points**

**Application Entry Point:**
- **File:** `src/index.ts`
- **Role:** Bootstrap application, initialize config, start server/render
- **Initialization Order:**
  1. Load environment variables (`.env`)
  2. Load configuration (`config/`)
  3. Initialize database connection
  4. Start HTTP server (or mount React app)
  5. Log "Application started"

**###**

**7. Files Flagged for Human Review**

**Before any implementation begins, these files must be reviewed and signed off by a domain expert:**

| **File Path** | **Module ID** | **Reason** | **Required Expertise** | **Acceptance Criteria to Validate** |
|-----------|-----------|--------|-------------------|--------------------------------|
| src/auth/logic.ts | MODULE-001-01 | Security-critical | Security engineer | Password hashing, token generation, session management are cryptographically sound |
| src/auth/api.ts | MODULE-001-02 | Security-critical + External | Security engineer | OAuth/auth endpoints follow security best practices, rate limiting, CORS |
| src/ui/pages/auth.tsx | MODULE-001-03 | Security-critical | Security engineer + Frontend | No credentials logged, no token exposure in DOM, secure form submission |
| config/database.config.ts | (config) | External integration | DevOps/Database admin | Connection pooling, secrets management, backup/recovery strategy |

**###**

**8. Test Strategy**

**Unit Tests** (mirror source structure):
- Every module with testable logic has a `.test.ts` file
- Tests verify acceptance criteria from MDAP

**Integration Tests** (in `tests/integration/`):
- Cross-module flows (e.g., auth → profile access)
- External API integrations
- Database operations

**##**

**OUTPUT VERIFICATION**

- [ ] Every file traces to exactly one MDAP module
- [ ] Every file traces to exactly one Epic (except shared/config)
- [ ] No file contains implementation logic (stubs only)
- [ ] Every file has complete header comment block
- [ ] Test files exist for every testable module
- [ ] No speculative or untraced files
- [ ] Naming conventions applied consistently
- [ ] Configuration files with secrets are in `.gitignore`
- [ ] Security-critical files flagged for human review
- [ ] Entry points clearly identified
- [ ] Structure matches Architecture Definition pattern
- [ ] Structure complexity matches MDAP (no over-nesting, no under-nesting)

**##**

**UPDATED CONTEXT BLOCK (embedded; do NOT create a new file)**

After creating file structure, output:
```
[CONTEXT.MD_UPDATE]
## File Structure Complete

### Architecture Pattern: [e.g., Clean Architecture]

### Components and File Organization:
- [Component Name]: [folder path] → [file list]
- [Component Name]: [folder path] → [file list]

### Total Files: [count]
- Source files: [count]
- Test files: [count]
- Configuration files: [count]

### Files Flagged for Human Review: [count]
- [file list]

### Entry Points:
- [file path] (main application bootstrap)

### Next Phase: Implementation
Developers use this structure to implement stubs.
All flagged files must be signed off before coding.

[/CONTEXT.MD_UPDATE]
```

**##**

**8A — PHASE TRANSITION NOTE FOR IMPLEMENTATION**

**This is the final pre-implementation handoff.**
```
[8A_IMPLEMENTATION_READY]

### Structure Complete: Ready for Implementation

Total Modules: [count]
Total Files: [count] (stubs ready for code)
High-Risk Files: [count] (require sign-off)

### Implementation Sequence:

PHASE 1 — Security-Critical Components (HIGH-RISK FILES)
1. [flagged files...]
(All must be human-reviewed and signed off first)

PHASE 2 — Core Services
1. [service files...]

PHASE 3 — UI/Interface Components
1. [UI files...]

PHASE 4 — Integration & Testing
1. Unit tests for all modules
2. Integration tests
3. System testing

### Per-File Implementation Checklist:
- [ ] Read file header (responsibility, acceptance criteria)
- [ ] Implement stub structure only (no business logic)
- [ ] Write acceptance criteria tests
- [ ] Self-review against acceptance criteria
- [ ] Human review for flagged files

[/8A_IMPLEMENTATION_READY]
```