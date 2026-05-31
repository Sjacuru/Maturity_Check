# PRD — Module 3: BM25 Retrieval

**Status:** Ready for implementation
**Date:** 2026-05-30
**ADRs in scope:** 0003, 0006, 0007, 0015, 0016, 0017, 0018
**Deferred architecture:** DAN-0002 (`docs/dan/0002-bm25-query-generation-strategy.md`) — closed

---

## Problem Statement

The system has Document Artifact Chunks stored as extraction output and IPMP/Rio Manual domain
structures loaded by the ingestion module. Before LLM evaluation can occur, the system must find
the chunks most likely to contain evidence for each Ação's Expected Products. PPP procurement
documents use inconsistent naming — some follow Rio Manual conventions exactly, others don't.
A single retrieval strategy fails both extremes: pure BM25 misses exact-name documents ranked low
by term frequency; exact-match-only fails garbled names or unlabelled files. The system needs a
retrieval mechanism that is deterministic (same input → same output), traceable to its Auditor,
and capable of finding both exact-document matches and free-text content evidence within the corpus.

---

## Solution

Build the retrieval module (`src/retrieval/`) as a Python package with four sub-packages:
`indexing/` (write path: persist Chunks to SQLite + FTS5), `query/` (read path: cascade execution,
BM25 query construction, acronym expansion), `schema/` (SQLite schema ownership), and `interfaces/`
(public Pydantic contracts and Protocol stubs). The module exposes two operations: `index()` stores
Chunks for a Case, and `retrieve_for_acao()` executes the retrieval cascade and returns
`list[RetrievedChunk]`. Retrieval uses a two-path cascade: when a document is identified by filename
or variant match, its full content becomes the evidence package; otherwise corpus-wide BM25 (one
query per Expected Product) runs in parallel with corpus-wide regex for exact identifiers. All
retrieval is deterministic — no LLM calls at retrieval time.

---

## User Stories

### Indexing (write path)

1. As a developer, I want to call `index(process_number, chunks)` with a `process_number` string
   and a `list[Chunk]` from the extraction module, so that the retrieval module stores those Chunks
   in SQLite and makes them searchable without requiring any knowledge of Case layout or storage
   conventions at the call site.

2. As a developer, I want `index()` to persist all Chunk fields to a base SQLite table along with
   the `process_number`, so that each indexed chunk is fully self-describing and carries its
   extraction provenance into storage.

3. As a developer, I want `index()` to populate the FTS5 virtual table from the base table's
   `text` column only, so that BM25 ranking is computed solely on chunk content and is not
   influenced by filenames, page numbers, or other metadata fields.

4. As a developer, I want `index()` to be idempotent using `(process_number, filename,
   page_number, chunk_index)` as the deduplication key, so that re-indexing a Document Artifact
   does not create duplicate entries.

5. As a developer, I want `index()` to accept an empty `list[Chunk]` without error, so that the
   caller does not need to guard against empty extraction results before indexing.

6. As a developer, I want SQLite to be opened in WAL mode, so that concurrent read access from
   other processes during retrieval does not block indexing writes.

### Retrieval cascade (read path)

7. As a developer, I want to call `retrieve_for_acao(acao_id, process_number)` and receive a
   `list[RetrievedChunk]`, so that downstream modules (LLM evaluation, Auditor interface) receive
   a single typed contract for retrieval results without needing to know how the cascade was
   executed.

8. As a developer, I want the retrieval cascade to first attempt filename matching — comparing each
   indexed Document Artifact filename for `process_number` against Rio Manual `document_names` for
   the Ação — so that exactly-named documents are identified before any BM25 search runs.

9. As a developer, I want the retrieval cascade to then attempt variant matching — comparing
   normalised Document Artifact content (title, headers) against Rio Manual `document_names` and
   their `regex_variants` for the Ação — so that documents that match Rio Manual conventions
   through content rather than filename are also identified.

10. As a developer, I want the cascade to treat token-overlap matching as a soft hint only — not
    establishing document identity and not restricting retrieval scope — so that partial lexical
    similarity never silently redirects or narrows the evidence set.

11. As a developer, I want the cascade to switch to document-focused retrieval when Step A
    (filename match) or Step B (variant match) identifies a candidate document: collect all indexed
    Chunks from that document and skip corpus-wide BM25, so that the full document content is
    always available as the evidence package when the document is positively identified.

12. As a developer, I want all Chunks from a document-focused retrieval result to carry
    `cascade_step` of `"filename_match"` or `"variant_match"` (matching the step that identified
    the document), so that the Auditor can trace exactly which identification mechanism produced
    the evidence package.

13. As a developer, I want the cascade to fall back to corpus-wide BM25 retrieval when neither
    Step A nor Step B identifies a candidate document, so that evidence is never abandoned simply
    because a document lacks a recognisable filename or header.

14. As a developer, I want corpus-wide BM25 retrieval to run one FTS5 query per letter-suffixed
    Expected Product for the Ação (e.g., 1a, 1b, 1c, 1d), with results merged and deduplicated
    by `(process_number, filename, page_number, chunk_index)`, so that each Expected Product has
    independent retrieval coverage and no single Expected Product dominates the evidence set by
    term frequency alone.

15. As a developer, I want the total corpus-wide BM25 result set to be bounded by
    `MAX_CHUNKS_PER_ACAO`, a named constant owned by the retrieval module, so that LLM prompt
    budget is controlled by the module with the most relevant knowledge of retrieval behaviour,
    not by the caller.

16. As a developer, I want corpus-wide regex retrieval (ADR-0007) to run in parallel with BM25
    when the corpus-wide path is active — searching all indexed Chunks for `process_number` using
    Python-registered regex functions for Rio Manual `regex_variants` (law numbers, regulation
    numbers, contract numbers) — so that exact identifier evidence is never dropped because it
    did not rank in the BM25 top-k.

17. As a developer, I want corpus-wide regex hits that are not already in the BM25 result set to
    be included in the final `list[RetrievedChunk]` with `cascade_step = "regex"`, so that exact
    identifier evidence is always surfaced regardless of BM25 ranking.

18. As a developer, I want regex retrieval on the document-focused path to scan only the candidate
    document's indexed Chunks, so that regex evidence is scoped to the identified document and
    consistent with the evidence-package approach.

### BM25 query construction

19. As a developer, I want BM25 query strings to be constructed by taking `produto.text` from
    each letter-suffixed Expected Product in `AcaoIPMP.produtos_esperados` as the base query
    text, so that retrieval queries are grounded directly in the IPMP's authoritative description
    of expected evidence.

20. As a developer, I want acronym expansion to be applied to each BM25 query string during
    construction, using `get_acronym_store()` to look up and expand known acronyms in the query
    text, so that BM25 matches chunks containing either the abbreviated or expanded form of a term.

21. As a developer, I want acronym expansion to transform only the query string — never the
    indexed chunk text — so that stored chunks remain verbatim representations of the source
    document and Auditor-displayed text always corresponds to the original document content.

22. As a developer, I want query construction to occur entirely within `query/`, with no LLM calls
    at retrieval time, so that retrieval is deterministic: the same `acao_id` and same index state
    always produce the same query strings and ranked results.

### `RetrievedChunk` contract

23. As a developer, I want `RetrievedChunk` to carry `process_number`, `filename`, `page_number`,
    `chunk_index`, `char_offset`, `page_total`, `ocr_used`, `source_type`, and `text` — the full
    provenance from `Chunk` minus the derivable `text_length` — so that downstream modules have
    complete provenance without needing to re-query the base table.

24. As a developer, I want `RetrievedChunk` to carry `cascade_step` as a
    `Literal["filename_match", "variant_match", "bm25", "regex"]`, so that the Auditor review
    interface can display which retrieval mechanism produced each piece of evidence.

25. As a developer, I want `RetrievedChunk` to carry `expected_product_id: str | None` — the
    letter-suffixed Expected Product id whose query produced this chunk — so that the Auditor can
    trace each retrieved chunk back to the specific Expected Product it was retrieved for.
    `expected_product_id` is null for `"filename_match"`, `"variant_match"`, and `"regex"` paths.

26. As a developer, I want `RetrievedChunk` to carry `bm25_score: float | None` and
    `rank: int | None` — null on non-BM25 paths — so that BM25 ranking metadata is available for
    diagnostics and retrieval evaluation without polluting document-focused or regex results.

27. As a developer, I want the retrieval module to return `list[RetrievedChunk]` directly — with
    no wrapper type — so that callers receive a flat, typed list compatible with standard Python
    iteration without additional unwrapping.

### Module interfaces

28. As a developer, I want `from retrieval import index, retrieve_for_acao, RetrievedChunk` to be
    the complete public surface of the module, so that downstream modules are isolated from
    internal sub-package layout changes.

29. As a developer, I want `interfaces/contracts.py` to define `RetrievedChunk` as a
    `pydantic.BaseModel`, so that field validation occurs at construction time and type errors
    are caught at the retrieval boundary rather than propagating to callers.

30. As a developer, I want `interfaces/protocols.py` to define a `ChunkRetriever` Protocol stub
    with a `search(query, acao_id, k)` method signature, so that the intended backend-agnostic
    contract is documented as architectural intent without enforcing dependency inversion in
    Phase 1.

### Error handling and edge cases

31. As a developer, I want `retrieve_for_acao()` to return an empty list when no indexed Chunks
    exist for `process_number`, so that the caller handles the no-evidence case explicitly rather
    than receiving an exception for a valid operating condition.

32. As a developer, I want `index()` to raise an explicit exception if the SQLite database or
    schema is not initialised, so that configuration failures are surfaced immediately rather than
    silently producing an empty index.

33. As a developer, I want schema initialisation to be idempotent (`CREATE TABLE IF NOT EXISTS`,
    `CREATE VIRTUAL TABLE IF NOT EXISTS`), so that the schema can be applied on every startup
    without error.

34. As a developer, I want `retrieve_for_acao()` to raise an explicit exception if `acao_id` is
    not present in the loaded `IPMPStore`, so that a missing Ação configuration is surfaced at
    retrieval time rather than returning empty results silently.

### Storage

35. As an operator, I want the SQLite database to be stored at a path configurable through the
    environment or module initialisation, so that test and production databases do not share the
    same file.

36. As a developer, I want the FTS5 tokeniser to be configured as `unicode61 remove_diacritics 2`
    (ADR-0003), so that BM25 retrieval handles accented Brazilian Portuguese characters through
    normalisation rather than exact byte matching.

---

## Implementation Decisions

### Module layout

```
src/retrieval/
    __init__.py          ← sole public surface: index, retrieve_for_acao, RetrievedChunk
    indexing/
        __init__.py
        writer.py        ← index() implementation: base table + FTS5 population
    query/
        __init__.py
        cascade.py       ← retrieve_for_acao(): cascade orchestration
        bm25.py          ← FTS5 query execution, result ranking, deduplication
        document.py      ← document-focused retrieval (filename_match, variant_match)
        regex_search.py  ← regex retrieval (ADR-0007)
        query_builder.py ← BM25 query string construction + acronym expansion
    schema/
        __init__.py
        ddl.py           ← CREATE TABLE / CREATE VIRTUAL TABLE statements, init function
    interfaces/
        __init__.py
        contracts.py     ← RetrievedChunk Pydantic model
        protocols.py     ← ChunkRetriever Protocol stub
```

### Public interface

```python
from retrieval import index, retrieve_for_acao, RetrievedChunk

index(process_number: str, chunks: list[Chunk]) -> None
retrieve_for_acao(acao_id: int, process_number: str) -> list[RetrievedChunk]
```

`Chunk` is imported from `src/extraction/`. No other symbols are re-exported. Downstream packages
must never import from `retrieval.indexing`, `retrieval.query`, or sub-modules directly.

### `RetrievedChunk` model

Fields decided in grill-me session (2026-05-30):

```python
class RetrievedChunk(BaseModel):
    process_number: str
    filename: str
    page_number: int
    chunk_index: int
    char_offset: int
    page_total: int
    ocr_used: StrictBool
    source_type: str
    text: str
    cascade_step: Literal["filename_match", "variant_match", "bm25", "regex"]
    expected_product_id: str | None
    bm25_score: float | None
    rank: int | None
```

### SQLite schema

Two-table design:

**Base table `chunks`:** all `Chunk` fields plus `process_number`. Integer primary key `id`.
Unique constraint on `(process_number, filename, page_number, chunk_index)` for idempotent indexing.

**FTS5 virtual table `chunks_fts`:** external content (`content='chunks'`), indexes `text` column
only. Tokeniser: `unicode61 remove_diacritics 2`. On retrieval, FTS5 returns docids; a join on
`chunks.id` fetches full metadata. `filename` is not indexed in FTS5 — document identity matching
uses SQL `WHERE` clauses on the base table.

Schema initialisation is idempotent (`IF NOT EXISTS`). SQLite in WAL mode.

### Retrieval cascade

**Step A — filename match:** `WHERE filename IN (doc_names_for_acao)` on base table filtered by
`process_number`. Returns matching documents.

**Step B — variant match:** Python-registered regex function applied to Document Artifact content
fields (title/headers stored separately or extracted from the first chunk). Uses `regex_variants`
from `AcaoRioManual`.

**If A or B succeeds:** collect all chunks from the identified document for `process_number`.
`cascade_step = "filename_match"` or `"variant_match"`.

**If neither succeeds:** run corpus-wide BM25 + regex in parallel (below).

**Corpus-wide BM25:** one FTS5 query per letter-suffixed Expected Product text (with acronym
expansion). Top-k results per query merged and deduplicated; total bounded by `MAX_CHUNKS_PER_ACAO`.
`cascade_step = "bm25"`, `expected_product_id` set to the driving Expected Product id.

**Corpus-wide regex (ADR-0007):** Python-registered regex function in SQLite scans all chunks for
`process_number`. Hits not already in the BM25 set are appended. `cascade_step = "regex"`,
`expected_product_id = None`.

### Query construction

`query_builder.py` constructs one query string per letter-suffixed Expected Product:
1. Take `produto.text` from `AcaoIPMP.produtos_esperados` for each letter-suffixed product.
2. Apply acronym expansion: for each token, if it appears in `get_acronym_store()`, append
   the expanded form. Both abbreviated and expanded forms are present in the query string.
3. Return the query string to `bm25.py` for FTS5 execution.

No LLM calls. No offline preparation step. Deterministic: same IPMP artifact + same acronym store
→ same query string.

### Chunk budget

`MAX_CHUNKS_PER_ACAO` is a named constant in `query/bm25.py` (or a module-level config constant).
It bounds the total BM25 result set after merge and deduplication. Regex hits are additive —
they are not counted against `MAX_CHUNKS_PER_ACAO`.

### Module boundaries

**Owns:** SQLite schema, FTS5 index lifecycle, base chunk persistence, cascade execution, BM25
query construction, acronym expansion, regex search integration, `RetrievedChunk` construction.

**Does not own:** PDF extraction, `Chunk` schema definition, IPMP/Rio Manual loading, LLM prompt
assembly, Auditor interface rendering, vector embeddings, dense vector search.

**Consumes from other modules:**
- `from extraction import Chunk` — input type for `index()`
- `from ingestion import get_ipmp_store, get_rio_manual_store, get_acronym_store` — domain
  structures used at retrieval time (query construction, cascade step A/B, regex patterns)

---

## Testing Decisions

**What makes a good test for this module:** tests must verify external behaviour observable through
the public interface (`index()`, `retrieve_for_acao()`, and `RetrievedChunk` fields). Tests must
not assert FTS5 query strings, internal ranking internals, or which internal function was called.
A test must verify that the correct chunks are returned with the correct `cascade_step`, not that
a specific SQL statement was issued.

**What is tested:**

- **Unit tests — `RetrievedChunk` model:** Pydantic validation for each field; construction with
  valid inputs; construction failure on invalid `cascade_step` values; null/non-null invariants
  for `bm25_score`, `rank`, `expected_product_id` per `cascade_step`. Fast, no SQLite required.

- **Integration tests — `index()` + `retrieve_for_acao()`:** Use an in-memory or tmp-file SQLite
  database. Index a small synthetic set of Chunks for a known `process_number`. Assert:
  - `retrieve_for_acao()` returns non-empty results for a known `acao_id`;
  - `cascade_step` values on returned chunks match the retrieval path taken;
  - `expected_product_id` is set correctly for BM25 results and null for document-focused results;
  - idempotent re-indexing does not duplicate results;
  - empty return when `process_number` has no indexed chunks.

- **Cascade path tests:** One test exercises the document-focused path (index a chunk from a file
  whose name matches a Rio Manual `document_name`; verify `cascade_step = "filename_match"`). One
  test exercises the BM25 path (index chunks with no matching filename; verify `cascade_step =
  "bm25"`). One test exercises the regex path (index a chunk containing a law number matching a
  `regex_variant`; verify it appears with `cascade_step = "regex"`).

- **Query construction unit test:** Given a known `AcaoIPMP` and known `acronyms`, assert that
  the constructed query string contains both the original term and its expanded form.

**Prior art:** `tests/test_chunk.py` (Module 2) established the Pydantic model validation test
pattern. `tests/test_extract_digital.py` established the integration test pattern using real
fixture files. Retrieval integration tests follow the same structure but use a SQLite tmp database
instead of PDF fixture files.

**No slow marker needed** for Phase 1 retrieval tests — SQLite in-memory databases are fast.

---

## Out of Scope

- Dense vector (LanceDB) retrieval — deferred to Module 6 (Phase 2)
- Offline LLM-assisted query-artifact generation — deferred to Phase 2 (DAN-0002)
- Document-level context expansion (adjacent-page, multi-page reconstruction) — deferred
- Token-budget-driven chunk sizing — evaluation concern, not retrieval concern
- Semantic chunking or heading-aware splitting — Module 2 / DAN-0001
- Vector embeddings or sentence-transformers — Phase 2
- Cross-Ação or multi-Case retrieval in a single call
- Retrieval evaluation framework (precision/recall metrics) — future phase
- `RetrievalResult` wrapper type — not introduced until a concrete requirement emerges
- Any write to `data/ipmp/`, `data/rio_manual/`, or `data/acronyms/`

---

## Further Notes

- **GitHub issues:** Next issues start at #11.

- **`MAX_CHUNKS_PER_ACAO` initial value:** The implementer selects an initial value (20 is a
  reasonable starting point) and documents the choice in code. This constant is the correct
  place to iterate once retrieval is evaluated against real Case data.

- **Regex hits are additive:** Regex results from the corpus-wide path supplement the BM25 result
  set rather than replacing or capping it. The total returned list may exceed `MAX_CHUNKS_PER_ACAO`
  when regex adds extra chunks.

- **`ChunkRetriever` Protocol is not enforced at runtime:** It is architectural intent only.
  The concrete SQLite + FTS5 implementation is instantiated directly. The protocol becomes the
  transition point if a second retrieval backend (e.g., LanceDB) is introduced in Phase 2.

- **Schema initialisation responsibility:** The `schema/ddl.py` `init_db()` function is called
  once at application startup (or in tests via fixture). It is not called inside `index()` or
  `retrieve_for_acao()` — callers are responsible for ensuring the schema exists before calling
  these functions.

- **Document Artifact title/header content for variant match (Step B):** The exact mechanism for
  extracting document title or header content for variant matching is an implementation detail.
  One approach: use the text of the first one or two Chunks from a document as the content to
  match against `regex_variants`. The implementer documents the chosen approach.

- **Deduplication key:** `(process_number, filename, page_number, chunk_index)` is the stable
  chunk identity both in the base table unique constraint and in the in-memory merge deduplication
  during cascade result assembly.

- **Assumptions downstream modules must preserve:**
  1. `retrieve_for_acao()` is the only retrieval entry point — no direct access to `retrieval.query`
     sub-modules.
  2. `list[RetrievedChunk]` may be empty — downstream must handle the no-evidence case.
  3. `cascade_step` is authoritative for which retrieval mechanism produced a chunk.
  4. `bm25_score` and `rank` are null on non-BM25 paths — downstream must not assume they are set.
  5. `expected_product_id` is the canonical link between a retrieved chunk and the Expected Product
     query that surfaced it; null on document-focused and regex paths.
