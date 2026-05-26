# Module 1 — Ingestion Layer: Architectural State

**Status:** Design complete. Implementation not started.
**Date:** 2026-05-25
**Next step:** Run to-PRD, then implement `src/ingestion/`.

---

## Finalized Decisions (Q1–Q10)

| Q | Topic | Decision |
|---|---|---|
| Q1 | IPMP fields | Full schema: `acao_id`, `titulo`, `dimensao`, `por_que_importante`, `descricao_acao`, `o_que_esperar`, `produtos_esperados` (flat list `{id, texto}`), `momento_ideal`, `excecoes: list[str]`, `exemplos: list[{nivel, score, texto}]` |
| Q2 | Storage format | JSON files, one per Ação, in `data/ipmp/` and `data/rio_manual/` |
| Q3 | Loading mechanism | Pydantic validation + singleton pattern. Load once on first call, cache for process lifetime |
| Q4 | Module boundary | Ingestion = data + structural normalization only. No retrieval semantics, no BM25, no query logic, no LLM awareness |
| Q5 | Normalization | Schema enforcement + type coercion + whitespace cleanup only. Hierarchy and identifiers (`1`, `1a`, `1b`) preserved exactly as canonical |
| Q6 | Rio Manual strictness | Structural correctness only. Empty `regex_variants`, `"UNKNOWN"` law numbers are valid artifact states. `_meta.known_gaps` is sole gap registry |
| Q7 | Acronym store | `get_acronym_store() -> dict[str, str]`. Validate non-empty keys/values only. All derived views belong to retrieval/orchestration |
| Q8 | File discovery | Glob `acao_*.json` in each data directory. Validate filename suffix matches internal `acao_id`. No registry |
| Q9 | Error handling | **Fatal**: directory missing, JSON syntax error, filename/id mismatch. **Non-fatal**: Pydantic validation failure → skip + structured log |
| Q10 | File structure | `src/ingestion/__init__.py` (sole public surface), `ipmp.py`, `rio_manual.py`, `acronyms.py` |

---

## Public Interface

```python
from ingestion import get_ipmp_store, get_rio_manual_store, get_acronym_store

get_ipmp_store()       -> IPMPStore        # .acoes: dict[int, AcaoIPMP]
get_rio_manual_store() -> RioManualStore   # .acoes: dict[int, AcaoRioManual]
get_acronym_store()    -> dict[str, str]
```

No other symbols are part of the public API. Internal module files (`ingestion.ipmp`, `ingestion.rio_manual`, `ingestion.acronyms`) are never imported directly by other packages.

---

## Pydantic Models — IPMP (implemented in `ipmp.py`)

```python
class Exemplo(BaseModel):
    nivel: str
    score: int          # 0, 1, or 3
    texto: str

class ProdutoEsperado(BaseModel):
    id: str             # validated: r"^\d+[a-z]?$"
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

---

## Pydantic Models — Rio Manual (to be enumerated during implementation in `rio_manual.py`)

Top-level shape of `AcaoRioManual` mirrors `data/rio_manual/acao_01.json`:
- `_meta`: provenance, schema version, known gaps (structural correctness only — empty fields are valid)
- `acao_id: int`
- `document_names: list[DocumentName]`
- `law_references: list[LawReference]` — `regex_variants` may be `[]`; `law_number` may be `"UNKNOWN"`
- `local_planning_instruments: LocalPlanningInstruments`
- `legal_phrases: LegalPhrases`
- `minimum_required_fields: MinimumRequiredFields`
- `process_context: ProcessContext`
- `bm25_search_hints: BM25SearchHints`

Full field enumeration deferred to implementation session.

---

## Ingestion Boundaries

**Owns:** Pydantic models, filesystem discovery, structural validation, singleton lifecycle, load-failure logging.

**Does not own:** BM25 query construction, sub-item filtering for search, acronym expansion, cascade logic, LLM prompt assembly, auditor interface, any derived view of canonical data.

---

## Accepted Trade-offs

| Trade-off | Decision |
|---|---|
| Operational continuity vs. strict reproducibility on load | Tolerant loading — non-fatal Pydantic failures skip file + log; fatal integrity errors crash. Reproducibility via transparency |
| Flat sub-item list vs. annotated query/display split | Flat list preserved exactly — retrieval semantics must not contaminate data layer |
| Lenient Rio Manual model vs. gap-enforcing strictness | Structural correctness only — `_meta.known_gaps` is the gap registry |

---

## Open Gaps (tracked in `data/rio_manual/acao_01.json` `_meta.known_gaps`)

1. **Lei Municipal de PPP number** — `regex_variants` is `[]` until confirmed
2. **PPA management strategy** — cyclic document (4–5 year cycle), not a static law; strategy for referencing specific PPA editions undefined
3. **`AcaoRioManual` full Pydantic field enumeration** — deferred to implementation session
4. **Testing strategy for ingestion module** — deferred to implementation session

---

## Non-Goals

- Building reverse acronym mappings
- Filtering or classifying Expected Products
- Annotating query-relevant vs. display-only fields
- Validating business-domain completeness of any artifact
- Any awareness of retrieval, scoring, or LLM evaluation

---

## Assumptions Future Modules Must Preserve

1. Ingestion singletons are the sole access point for IPMP, Rio Manual, and acronym data — no module reads JSON files directly.
2. `produtos_esperados` ids are canonical identifiers, not query labels — retrieval decides which ids generate BM25 queries.
3. A loaded store may not contain all 46 actions — downstream modules must handle a missing Ação gracefully.
4. `_meta.known_gaps` in Rio Manual artifacts is authoritative for intentional incompleteness.
5. `src/ingestion/__init__.py` is the only import surface — internal files are never imported directly.
