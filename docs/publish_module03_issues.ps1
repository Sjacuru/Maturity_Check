# publish_module03_issues.ps1
# Prerequisites: gh auth login (https://cli.github.com/)
# Run: pwsh -File docs\publish_module03_issues.ps1
# Issues created in dependency order so blockers reference real issue numbers.

$REPO = "Sjacuru/Maturity_Check"

function Ensure-Label($name, $color, $desc) {
    $existing = gh label list --repo $REPO --json name | ConvertFrom-Json | Where-Object { $_.name -eq $name }
    if (-not $existing) {
        gh label create $name --repo $REPO --color $color --description $desc
        Write-Host "Created label: $name"
    }
}
Ensure-Label "ready-for-agent"   "0075ca" "AFK slice — can be implemented without human interaction"
Ensure-Label "module:retrieval"  "1d76db" "Module 3 — BM25 retrieval layer"

# --- Issue 11: Package scaffold, schema, RetrievedChunk model ---
$issue11 = gh issue create `
  --repo $REPO `
  --title "Retrieval: package scaffold, SQLite schema, and RetrievedChunk model" `
  --label "ready-for-agent,module:retrieval" `
  --body @'
**What to build**

Create the `src/retrieval/` package structure and foundational contracts that all subsequent retrieval slices depend on. No retrieval logic is implemented here — this slice is the structural foundation: package layout, SQLite schema, the `RetrievedChunk` Pydantic model, and the `ChunkRetriever` Protocol stub.

Deliver:
- `src/retrieval/` importable package with `__init__.py` exporting `index`, `retrieve_for_acao`, `RetrievedChunk` as stubs (functions may raise `NotImplementedError` at this stage)
- `schema/ddl.py`: `init_db(db_path)` that creates `chunks` (base table) and `chunks_fts` (FTS5 virtual table, `content='chunks'`, `text` column only, tokeniser `unicode61 remove_diacritics 2`) — idempotent (`IF NOT EXISTS`), WAL mode
- `interfaces/contracts.py`: `RetrievedChunk` as a `pydantic.BaseModel` with all 13 fields:
  `process_number`, `filename`, `page_number`, `chunk_index`, `char_offset`, `page_total`, `ocr_used` (StrictBool), `source_type`, `text`, `cascade_step` (Literal["filename_match","variant_match","bm25","regex"]), `expected_product_id: str | None`, `bm25_score: float | None`, `rank: int | None`
- `interfaces/protocols.py`: `ChunkRetriever` Protocol stub with `search(query, acao_id, k)` — not exported from `__init__.py`
- Unit tests for `RetrievedChunk`: valid construction, invalid `cascade_step` rejected, null/non-null field invariants per `cascade_step`
- Unit test for `init_db`: calling twice does not raise; both tables exist after init

**Acceptance criteria — slice is done when:**

- [ ] `from retrieval import RetrievedChunk, index, retrieve_for_acao` works after `pip install -e .`
- [ ] `RetrievedChunk` with `cascade_step="bm25"` constructs without error
- [ ] `RetrievedChunk` with `cascade_step="invalid"` raises a Pydantic `ValidationError`
- [ ] `init_db(path)` called twice on the same path does not raise
- [ ] SQLite database opened by `init_db` is in WAL journal mode
- [ ] `chunks_fts` tokeniser is `unicode61 remove_diacritics 2` (verifiable via `PRAGMA compile_options` or FTS5 table info)
- [ ] All `RetrievedChunk` unit tests pass
- [ ] `retrieval.interfaces.protocols` is importable but `ChunkRetriever` is NOT in `from retrieval import *`

**Blocked by**

None — can start immediately
'@

$issue11_num = ($issue11 -split '/')[-1]
Write-Host "Created Issue #$issue11_num: Package scaffold"

# --- Issue 12: Indexing write path ---
$issue12 = gh issue create `
  --repo $REPO `
  --title "Retrieval: indexing write path (index)" `
  --label "ready-for-agent,module:retrieval" `
  --body @"
**What to build**

Implement `index(process_number: str, chunks: list[Chunk]) -> None` — the complete write path that persists Chunks from the extraction module into the `chunks` base table and populates the `chunks_fts` FTS5 index. Idempotent: re-indexing the same chunks must not create duplicates.

`Chunk` is imported from `src/extraction/`. The `process_number` is supplied by the caller (orchestration layer); extraction never knows it.

Deduplication key: `(process_number, filename, page_number, chunk_index)` — unique constraint on the base table.

**Acceptance criteria — slice is done when:**

- [ ] `index("P001", chunks)` with a non-empty list persists all chunks to `chunks` and `chunks_fts`
- [ ] Each persisted row carries `process_number` alongside all `Chunk` fields
- [ ] Calling `index()` twice with the same chunks leaves exactly one row per chunk (no duplicates)
- [ ] `index()` with an empty list returns without error and makes no writes
- [ ] `index()` raises an explicit exception if the schema is not initialised (i.e. `init_db` was not called)
- [ ] Integration test: index N chunks → `SELECT COUNT(*) FROM chunks` == N
- [ ] Integration test: index same chunks twice → count still == N
- [ ] Integration test: `index(process_number, [])` → count unchanged
- [ ] Integration test: calling `index()` without prior `init_db` raises an explicit exception

**Blocked by**

#$issue11_num
"@

$issue12_num = ($issue12 -split '/')[-1]
Write-Host "Created Issue #$issue12_num: Indexing write path"

# --- Issue 13: BM25 corpus-wide retrieval ---
$issue13 = gh issue create `
  --repo $REPO `
  --title "Retrieval: BM25 corpus-wide retrieval path (retrieve_for_acao — BM25 only)" `
  --label "ready-for-agent,module:retrieval" `
  --body @"
**What to build**

Implement `retrieve_for_acao(acao_id: int, process_number: str) -> list[RetrievedChunk]` delivering the BM25 corpus-wide retrieval path. The document-focused path (filename/variant match) is NOT part of this slice — it is added in the next slice. This slice delivers a working, testable end-to-end retrieval call via BM25 only.

Retrieval flow:
1. Load `AcaoIPMP` for `acao_id` from `get_ipmp_store()`
2. For each letter-suffixed Expected Product (e.g. 1a, 1b): construct a BM25 query string from `produto.text` with acronym expansion applied (using `get_acronym_store()`)
3. Execute one FTS5 query per Expected Product against all chunks for `process_number`
4. Merge and deduplicate results by `(process_number, filename, page_number, chunk_index)`
5. Bound total result set to `MAX_CHUNKS_PER_ACAO` (named constant, initial value: implementer's choice, document in code)
6. Return `list[RetrievedChunk]` with `cascade_step="bm25"`, `expected_product_id` set to the driving Expected Product id, `bm25_score` and `rank` set

**Acceptance criteria — slice is done when:**

- [ ] `retrieve_for_acao(1, "P001")` returns non-empty `list[RetrievedChunk]` for an indexed case with content matching Ação 1 Expected Products
- [ ] All returned chunks carry `cascade_step="bm25"` and non-null `expected_product_id`
- [ ] `bm25_score` (float) and `rank` (int) are non-null on all BM25 results
- [ ] Total results do not exceed `MAX_CHUNKS_PER_ACAO`
- [ ] A query containing an acronym returns chunks matching either the abbreviated or expanded form
- [ ] `retrieve_for_acao()` returns an empty list when no chunks are indexed for `process_number`
- [ ] `retrieve_for_acao()` raises an explicit exception when `acao_id` is not present in `IPMPStore`
- [ ] Integration test: BM25 retrieval returns expected chunks with correct `cascade_step`
- [ ] Integration test: acronym expansion — index chunk with expanded form, query with abbreviation → chunk returned
- [ ] Integration test: empty result for unknown `process_number`
- [ ] Integration test: unknown `acao_id` raises

**Blocked by**

#$issue12_num
"@

$issue13_num = ($issue13 -split '/')[-1]
Write-Host "Created Issue #$issue13_num: BM25 corpus-wide retrieval"

# --- Issue 14: Document-focused cascade path ---
$issue14 = gh issue create `
  --repo $REPO `
  --title "Retrieval: document-focused cascade path (filename_match and variant_match)" `
  --label "ready-for-agent,module:retrieval" `
  --body @"
**What to build**

Extend `retrieve_for_acao()` with cascade Steps A and B. Before running BM25, the cascade checks whether any indexed Document Artifact for `process_number` can be identified as a known Rio Manual document for the Ação.

Step A — filename match: compare each indexed `filename` for `process_number` against Rio Manual `document_names` for the Ação (SQL `WHERE` on the base table, no FTS5).

Step B — variant match: apply Python-registered SQLite regex functions from Rio Manual `regex_variants` against Document Artifact content (implementer may use first-chunk text as a proxy for title/header content; document the chosen approach).

If A or B succeeds: collect ALL indexed chunks from the identified document for `process_number` as the evidence package. Skip corpus-wide BM25. Set `cascade_step="filename_match"` or `"variant_match"`.

Step C (token-overlap): soft hint only. Must NOT redirect or restrict retrieval scope under any condition.

If neither A nor B succeeds: fall through to the corpus-wide BM25 path from the previous slice.

**Acceptance criteria — slice is done when:**

- [ ] A `process_number` with a file whose name exactly matches a Rio Manual `document_name` for Ação 1 → all that document's indexed chunks returned with `cascade_step="filename_match"`
- [ ] A `process_number` with a file whose content matches a `regex_variant` → all chunks returned with `cascade_step="variant_match"`
- [ ] `bm25_score` and `rank` are null on document-focused results
- [ ] `expected_product_id` is null on document-focused results
- [ ] A `process_number` with no filename or variant match → falls through to BM25 (slice 3 behaviour preserved)
- [ ] Step C matching never changes the retrieval path or restricts the result set
- [ ] All existing BM25 integration tests from slice 3 still pass
- [ ] Integration test: filename match path returns correct `cascade_step` and full document chunks
- [ ] Integration test: variant match path returns correct `cascade_step`
- [ ] Integration test: no match → BM25 path activates

**Blocked by**

#$issue13_num
"@

$issue14_num = ($issue14 -split '/')[-1]
Write-Host "Created Issue #$issue14_num: Document-focused cascade path"

# --- Issue 15: Regex retrieval integration ---
$issue15 = gh issue create `
  --repo $REPO `
  --title "Retrieval: regex retrieval integration (ADR-0007)" `
  --label "ready-for-agent,module:retrieval" `
  --body @"
**What to build**

Add regex-based exact-identifier retrieval (ADR-0007) to both cascade paths. Law numbers, regulation numbers, and contract numbers are exact identifiers stored in Rio Manual `regex_variants`. They must never depend on BM25 ranking to be discovered.

Corpus-wide BM25 path: register a Python regex function in SQLite; run it against all chunks for `process_number` in parallel with BM25 execution; append non-overlapping hits (not already in the BM25 result set) with `cascade_step="regex"`. Regex hits are additive — they do not replace or count against `MAX_CHUNKS_PER_ACAO`.

Document-focused path: run the same regex function scoped to only the identified document's chunks. Regex here labels hits within the evidence package but does not add chunks from outside the identified document.

**Acceptance criteria — slice is done when:**

- [ ] A chunk containing a law number matching a `regex_variant` but ranked outside the BM25 top-k appears in the result set with `cascade_step="regex"`
- [ ] Regex hits carry `expected_product_id=None`, `bm25_score=None`, `rank=None`
- [ ] On the document-focused path, regex does not return chunks from outside the identified document
- [ ] Regex results are additive — total result count may exceed `MAX_CHUNKS_PER_ACAO` when regex adds chunks
- [ ] A chunk already in the BM25 result set is not duplicated by the regex pass
- [ ] All existing BM25 and document-focused tests from slices 3 and 4 still pass
- [ ] Integration test: regex hit outside BM25 top-k is present with `cascade_step="regex"`
- [ ] Integration test: document-focused path — regex only returns chunks from identified document
- [ ] Integration test: chunk present in both BM25 and regex results appears exactly once

**Blocked by**

#$issue14_num
"@

$issue15_num = ($issue15 -split '/')[-1]
Write-Host "Created Issue #$issue15_num: Regex retrieval integration"

Write-Host ""
Write-Host "All 5 Module 3 issues created. Summary:"
Write-Host "  #$issue11_num — Package scaffold, schema, RetrievedChunk (AFK)"
Write-Host "  #$issue12_num — Indexing write path (AFK, blocked by #$issue11_num)"
Write-Host "  #$issue13_num — BM25 corpus-wide retrieval (AFK, blocked by #$issue12_num)"
Write-Host "  #$issue14_num — Document-focused cascade path (AFK, blocked by #$issue13_num)"
Write-Host "  #$issue15_num — Regex retrieval integration (AFK, blocked by #$issue14_num)"
