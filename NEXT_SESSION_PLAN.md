# Next Session Plan

Two topics, tackle one at a time.

---

## Topic 1 — Architecture confirmation (quick)

**Question to resolve:** Is the chunk retrieval flow correct?

Current state:
- `data/framework.sqlite` → `reference_chunks` table holds: chunk_id, doc_id, ordinal,
  heading_path, text, text_hash (metadata + text, no vectors)
- `data/lancedb/reference/reference_m5d_chunks` → holds the same fields PLUS `vector`
- The two stores share the same `chunk_id` as the link key
- `heading_path` is stored in both (e.g. "Capítulo 3: ... > Ação 1: ...")

**Retrieval flow (intended, partially implemented):**

```
1. Query arrives (e.g. intencao text for sub-task 1.1)
2. Filter by heading_path → restrict to chunks from the right action/section
3. Rank filtered set by vector similarity → get top-K most relevant chunks
4. Return chunk text → feeds into LLM evaluation prompt
```

**What still needs to be wired:**
- `search_reference_lancedb` in `src/maturity_check/reference_search.py` currently does
  raw vector search with NO heading_path filter. Add a `heading_filter: str | None`
  parameter so callers can pass e.g. `"Ação 1:"` to restrict results to that section.
- File to edit: `src/maturity_check/reference_search.py` (function `search_reference_lancedb`)

---

## Topic 2 — Ingest Rio Manual and TCDF IN into the reference vector DB

**Goal:** When Ação 1 sub-task 1.1 is evaluated, the retrieval context pulls from all
three normative sources — M5D, Rio Manual, and TCDF IN — not just M5D.

**Pre-condition:** PDFs must be converted to Markdown and placed in `Plan/06_Models/`
before ingestion. Check what is already there:
```
ls Plan/06_Models/
```
Expected: M5D.md ✅  Rio Manual .md or .pdf  TCDF IN .md or .pdf

**If PDFs exist but no .md conversion yet:**
Convert them with a PDF-to-text tool (pdfplumber, pymupdf, or pdf2text) and save as:
- `Plan/06_Models/rio_manual.md`
- `Plan/06_Models/tcdf_in_01_2024.md`

**Ingestion steps:**

The `ingest-m5d` CLI command and `m5d_ingest.py` already work. Generalise or duplicate
for the two new sources. The `normalize_pdf_headings` pre-processor in
`src/maturity_check/ingest/chunking.py` is reusable — it handles the same PDF-conversion
heading format that Rio Manual and TCDF IN will have.

Two options:

**Option A — Generalise the CLI (recommended):**
Add `ingest-ref-doc` subcommand to `src/maturity_check/cli.py` with:
- `--source` (e.g. "RioManual", "TCDF_IN")
- `--doc-id` (e.g. "rio_manual_v1", "tcdf_in_01_2024_v1")
- `--path` to the markdown file
- Same `--embed`, `--model`, `--max-chars`, `--overlap-chars` flags as `ingest-m5d`

Then run:
```
maturity-check ingest-ref-doc --source RioManual --doc-id rio_manual_v1 \
  --path Plan/06_Models/rio_manual.md

maturity-check ingest-ref-doc --source TCDF_IN --doc-id tcdf_in_01_2024_v1 \
  --path Plan/06_Models/tcdf_in_01_2024.md
```

**Option B — Quick duplicate (faster to ship):**
Copy `m5d_ingest.py` → `ref_doc_ingest.py`, change `doc_id` / `source` / `title` constants,
wire into CLI. Less elegant but unblocks testing faster.

**After ingestion — verify:**
```python
import lancedb
db = lancedb.connect('data/lancedb/reference')
print(db.table_names())
# Should show 3 tables: reference_m5d_chunks, reference_rio_manual_chunks, reference_tcdf_in_chunks
# OR one shared table with doc_id as the filter field (decide which structure)
```

**Architecture decision to make during this session:**
- **One shared table** (all three sources in `reference_chunks` table, filtered by `doc_id`)
  → simpler queries, one vector index, easier cross-source search
- **Three separate tables** (one per source)
  → cleaner isolation, easier to re-ingest one source without touching others

Recommendation: **one shared table** with `doc_id` as the source discriminator.
This lets a single vector search return the best chunks across all three sources ranked together.

---

## Topic 3 (follows from Topic 2) — Three-way retrieval for sub-task evaluation

Once all three sources are in the vector DB, the retrieval for a sub-task needs to:

1. Load crosswalk for the sub-task (e.g. `action_1_subtask_1_1` JSON)
2. For each `intencao.by_source` entry, form a query string
3. Search the shared reference index with:
   - Query = intencao text
   - Optional heading filter = "Ação 1:" (to stay in the right section)
   - Return top-K chunks, flagging `doc_id` so the LLM knows which source each came from
4. Combine results into the evaluation prompt

This is the "expected output per action" step the user mentioned — the agent checks all
three sources to build a rich normative context before evaluating the case document.

**Files to create/modify:**
- `src/maturity_check/reference_search.py` — add heading_filter to `search_reference_lancedb`
- `src/maturity_check/retrieval/crosswalk_retrieval.py` (new) — orchestrates the three-source pull
  per sub-task using crosswalk intencao + heading filter

---

## Current repo state (as of this session)

| Item | Status |
|---|---|
| M5D ingested in LanceDB | ✅ 272 chunks, 97% with heading_path |
| Heading normaliser (`normalize_pdf_headings`) | ✅ in `src/maturity_check/ingest/chunking.py` |
| Rio Manual ingested | ❌ pending PDF conversion |
| TCDF IN ingested | ❌ pending PDF conversion |
| Heading filter on vector search | ❌ not yet added to `reference_search.py` |
| Case document pipeline | ❌ not yet built |
| LLM evaluator | ❌ not yet built |
| Case-type manifest | ✅ `Plan/06_Models/case_type_manifest/rio_ppp_v1.json` |
| Crosswalk templates Ação 1 | ✅ `Plan/06_Models/crosswalk/` |
| EPIC document | ✅ validated and corrected |
| **OQ-005 architectural decision** | ✅ **Revised 2026-05-06** — external LLM now allowed for reference docs (public); case docs remain local-first |

**LLM backend (revised):**
- Reference reasoning (M5D / Rio Manual / TCDF IN) → External API (Claude / Groq) — Phase 1
- Case evaluation (FR-009 / FR-010) → Ollama local — NFR-008
- Assurance pass (FR-021) → Ollama local, temp=0 — always local
