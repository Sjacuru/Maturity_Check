# PRD — Module 1: Ingestion Layer

**Status:** Ready for implementation
**Date:** 2026-05-25
**ADRs in scope:** 0001, 0003, 0005, 0007, 0008, 0009, 0010
**Architectural state:** `docs/MODULE_01_STATE.md`

---

## Problem Statement

The PPP Maturity Check System evaluates Brazilian PPP case documents against the IPMP framework, producing a 0/1/3 maturity score for each of 46 Ações across 5 Dimensões. Before retrieval, scoring, or LLM evaluation can occur, the system needs a reliable way to load and expose two canonical domain structure collections: IPMP data (46 Ações with rubrics, Expected Products, and scored examples) and Rio Manual data (Rio de Janeiro–specific document names, legal vocabulary, and planning instruments per Ação). These source-of-truth artifacts are JSON files under progressive enrichment — fields may be intentionally incomplete while domain research is ongoing. The system needs to load them safely, enforce structural integrity, and expose validated canonical domain structures to all downstream modules without any downstream module touching the JSON files directly.

---

## Solution

Build the ingestion module (`src/ingestion/`) as a Python package with three internal modules — one per data source — and a single `__init__.py` as the sole public surface. Each internal module owns its Pydantic models, filesystem discovery, structural validation, and singleton accessor end-to-end. Singletons load once on first call and cache for process lifetime. Loading follows a tolerant strategy (ADR-0010): fatal errors crash immediately; non-fatal Pydantic failures skip the individual file with a structured log entry, preserving operational continuity. No retrieval semantics of any kind are introduced at this layer.

---

## User Stories

1. As a developer, I want to call `get_ipmp_store()` and receive a validated `IPMPStore` containing all successfully loaded IPMP Ações, so that downstream modules can access IPMP data without parsing JSON themselves.

2. As a developer, I want to call `get_rio_manual_store()` and receive a validated `RioManualStore` containing all successfully loaded Rio Manual Ações, so that the retrieval module can access Rio-specific document names and legal vocabulary.

3. As a developer, I want to call `get_acronym_store()` and receive a validated `dict[str, str]` containing all acronym mappings, so that downstream modules can expand acronyms as needed.

4. As a developer, I want the ingestion module to auto-discover all `acao_*.json` files in each data directory at load time, so that adding a new Ação requires only dropping a file — no code change required.

5. As a developer, I want the ingestion module to validate that the numeric suffix in each filename matches the internal `acao_id` field, so that filename/content mismatches are caught at load time rather than silently producing wrong data.

6. As a developer, I want the ingestion module to crash immediately with an explicit exception if a data directory is not found, so that missing infrastructure is never silently accepted.

7. As a developer, I want the ingestion module to crash immediately with an explicit exception if a JSON file is syntactically invalid or unreadable, so that corrupted artifacts are never silently skipped.

8. As a developer, I want the ingestion module to crash immediately with an explicit exception if a filename's numeric suffix does not match the internal `acao_id`, so that misnamed artifacts are never silently loaded as a different Ação.

9. As a developer, I want the ingestion module to skip individual files that fail Pydantic validation (without crashing the entire loader), so that the system can start and run even when some source-of-truth artifacts are partially enriched.

10. As a developer, I want every skipped file to produce a structured log entry containing the filename, validation error, and reason for skipping, so that I can diagnose exactly which file failed and why.

11. As a developer, I want a final load summary log at the end of each load (e.g., "Loaded 1/1 IPMP action files") so that the loaded/skipped count is always visible.

12. As a developer, I want the ingestion singletons to load once on first call and cache for process lifetime, so that JSON parsing does not occur on every access.

13. As a developer, I want `src/ingestion/__init__.py` to be the only import surface for the package, so that internal module files are never imported directly by downstream packages, preventing tight coupling to internal layout.

14. As a developer, I want IPMP `AcaoIPMP` models to preserve `produtos_esperados` ids exactly as they appear in the source JSON (e.g., `"1"`, `"1a"`, `"1b"`), so that canonical identifiers are not altered by structural normalization and downstream modules receive the authoritative hierarchy.

15. As a developer, I want IPMP `ProdutoEsperado.id` to be validated against the pattern `r"^\d+[a-z]?$"`, so that malformed ids are caught at load time.

16. As a developer, I want IPMP `Exemplo.score` to be an integer, so that scored examples can be compared to the 0/1/3 maturity rubric without type coercion downstream.

17. As a developer, I want Rio Manual `AcaoRioManual` models to accept empty `regex_variants` lists without validation errors, so that law references with unknown regex patterns are a valid artifact state (intentional incompleteness, not a structural defect).

18. As a developer, I want Rio Manual `AcaoRioManual` models to accept `"UNKNOWN"` as a valid `law_number` value, so that laws with unresolved numbers load successfully pending domain research.

19. As a developer, I want Rio Manual `_meta.known_gaps` to be the sole registry of intentional incompleteness in each artifact, so that Pydantic does not duplicate domain-completeness enforcement and gap tracking is centralised.

20. As a developer, I want the acronym store to validate that all keys and values are non-empty strings, so that structurally malformed entries are caught at load time.

21. As the retrieval module developer, I want the ingestion singletons to be the sole access point for IPMP, Rio Manual, and acronym data, so that no downstream module reads JSON files directly and the ingestion boundary is enforced architecturally.

22. As the retrieval module developer, I want to be able to introspect which Ação ids are present in the loaded stores, so that I can handle missing Ações gracefully without assuming all 46 are present.

23. As the retrieval module developer, I want the canonical `produtos_esperados` list to contain the full hierarchy (both parent numeric ids and letter-suffixed child ids), so that I can apply retrieval semantics to decide which ids generate BM25 queries — this decision is mine, not ingestion's.

24. As the retrieval module developer, I want the `get_acronym_store()` return value to be the flat canonical `dict[str, str]` exactly as defined in the source artifact, so that all derived views (reverse mappings, contextual expansion) are built in the retrieval or orchestration layers, not baked into ingestion.

25. As the LLM evaluation module developer, I want IPMP `exemplos` to be exposed as a list of `Exemplo` objects (with `nivel`, `score`, `texto`), so that the LLM prompt can embed the three scored examples (0/1/3) per Ação without parsing raw JSON.

26. As the Auditor, I want the system to start successfully even when some source-of-truth artifacts are partially enriched, so that Phase 1 evaluation of Ação 1 is not blocked by absent or incomplete Ações 2–46.

27. As the Auditor, I want the ingestion module to log exactly which files were skipped and why, so that I have visibility into data completeness without needing to inspect the JSON files directly.

---

## Implementation Decisions

### Module layout

The ingestion package is organised by canonical data source. Each of the three internal modules owns its Pydantic models, file discovery, structural validation, load logic, and singleton accessor end-to-end. The `__init__.py` is a re-export surface only — no logic lives there.

Files:
- `ipmp.py` — IPMP models and `get_ipmp_store()` singleton
- `rio_manual.py` — Rio Manual models and `get_rio_manual_store()` singleton
- `acronyms.py` — acronym loader and `get_acronym_store()` singleton
- `__init__.py` — sole public surface; re-exports all three accessors

### Public interface

```python
from ingestion import get_ipmp_store, get_rio_manual_store, get_acronym_store

get_ipmp_store()       -> IPMPStore        # .acoes: dict[int, AcaoIPMP]
get_rio_manual_store() -> RioManualStore   # .acoes: dict[int, AcaoRioManual]
get_acronym_store()    -> dict[str, str]
```

No other symbols are exported. Downstream packages must never import from `ingestion.ipmp`, `ingestion.rio_manual`, or `ingestion.acronyms` directly.

### Singleton pattern

Each accessor uses a module-level `_store` variable (initially `None`). On first call, the store is built and assigned; all subsequent calls return the cached value. No thread-safety mechanism is required for Phase 1 (single-process CLI). If the load raises a fatal error, the exception propagates and no partial state is cached.

### File discovery

Both IPMP and Rio Manual loaders use glob `acao_*.json` to discover all files in their respective data directories. The numeric suffix extracted from the filename must match the `acao_id` field inside the JSON — mismatch is a fatal error. There is no explicit file registry.

### IPMP Pydantic models

Finalized in the grill-me session. Type shapes below encode decisions precisely:

```python
class Exemplo(BaseModel):
    nivel: str
    score: int          # 0, 1, or 3 — compared against IPMP rubric downstream
    texto: str

class ProdutoEsperado(BaseModel):
    id: str             # validated: r"^\d+[a-z]?$" — canonical identifier, not a query label
    texto: str

class AcaoIPMP(BaseModel):
    acao_id: int
    titulo: str
    dimensao: str
    por_que_importante: str
    descricao_acao: str
    o_que_esperar: str
    produtos_esperados: list[ProdutoEsperado]
    momento_ideal: str
    excecoes: list[str]
    exemplos: list[Exemplo]

class IPMPStore(BaseModel):
    acoes: dict[int, AcaoIPMP]
```

### Rio Manual Pydantic models

Top-level shape of `AcaoRioManual` follows `data/rio_manual/acao_01.json`. Full field enumeration is deferred to the implementation session — the implementer must enumerate all nested types by reading the current source-of-truth artifact directly. Structural constraints from grill-me:

- `_meta.known_gaps: list[str]` — sole gap registry; Pydantic does not validate domain completeness
- `law_references[*].regex_variants` — may be `[]` (valid state: lei not yet confirmed)
- `law_references[*].law_number` — may be `"UNKNOWN"` (valid state: number not yet researched)

### Error handling

**Fatal — crash immediately with explicit exception:**
- Data directory not found
- JSON syntax error or unreadable file
- Filename numeric suffix does not match internal `acao_id`

**Non-fatal — skip file, emit structured log, continue:**
- Pydantic model validation failure on an individual file

Every skip emits: filename, validation error detail, reason for skip. Every load ends with a count log (e.g., "Loaded 1/1 IPMP action files. Skipped: 0.").

### Normalization scope

Ingestion performs structural normalization only: schema enforcement, type coercion, whitespace cleanup. Content, meaning, and hierarchy are preserved exactly as in the source JSON. No retrieval semantics enter the ingestion layer.

### Ingestion module boundaries

**Owns:** Pydantic models, filesystem discovery, structural validation, singleton lifecycle, load-failure logging.

**Does not own:** BM25 query construction, sub-item filtering for search, acronym expansion, cascade logic, LLM prompt assembly, auditor interface, any derived view of canonical data.

---

## Testing Decisions

Testing strategy is deferred entirely to the implementation session. No tests are specified in this PRD.

---

## Out of Scope

- BM25 query construction or any retrieval semantics
- Sub-item filtering — deciding which `produtos_esperados` ids generate queries belongs to the retrieval module
- Acronym expansion during retrieval
- Reverse acronym mappings
- Cascade logic (exact match → BM25 augmented → dense vector fallback)
- LLM prompt assembly
- Auditor review interface
- Vector database integration
- Validating business-domain completeness of any source-of-truth artifact
- Any awareness of scoring, ranking, or evaluation logic
- Resolving the open gaps in `data/rio_manual/acao_01.json` (Lei Municipal de PPP law number; PPA management strategy) — those are domain research tasks, not implementation tasks

---

## Further Notes

- **Open gap — Lei Municipal de PPP law number:** The law is referenced throughout the Rio Manual by title and article but its municipal law number is unknown. `regex_variants` in `data/rio_manual/acao_01.json` for this law is currently `[]`. This is intentional incompleteness. Resolving it requires a dedicated domain research session.

- **Open gap — PPA management strategy:** The Plano Plurianual is a cyclic document (4–5 year cycle). The strategy for referencing specific PPA editions is undefined. Tracked in `data/rio_manual/acao_01.json` `_meta.known_gaps`.

- **AcaoRioManual full Pydantic field enumeration:** The complete nested type tree for `AcaoRioManual` is deferred to the implementation session. The implementer must derive it from `data/rio_manual/acao_01.json` directly.

- **Minor corrections to `data/rio_manual/acao_01.json`:** The user indicated corrections may be needed. These are to be addressed in a dedicated session before or during implementation of `rio_manual.py`.

- **Phase 1 scope:** Only `data/ipmp/acao_01.json` and `data/rio_manual/acao_01.json` exist. The ingestion module must handle this correctly — a store with one Ação is a valid state, not a load failure.

- **Assumptions downstream modules must preserve:**
  1. Ingestion singletons are the sole access point for IPMP, Rio Manual, and acronym data.
  2. `produtos_esperados` ids are canonical identifiers — retrieval decides which drive BM25 queries.
  3. A loaded store may not contain all 46 Ações — downstream must handle a missing Ação gracefully.
  4. `_meta.known_gaps` in Rio Manual artifacts is authoritative for intentional incompleteness.
  5. `src/ingestion/__init__.py` is the only import surface — internal files are never imported directly.
