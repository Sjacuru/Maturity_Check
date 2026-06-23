# Retrieval Profile Validation Process — Ação N

Use this prompt when beginning a retrieval profile validation session for any Ação.
Provide Claude with this file plus the relevant sections of `data/retrieval_profiles/acao_NN.json` and `data/ipmp/acao_NN.json`.

---

## Context

The PPP Maturity Check system uses a retrieval profile (`data/retrieval_profiles/acao_NN.json`) to build BM25 queries for each Expected Product (1a, 1b, 1c, 1d…). The profile contains curated phrase and NEAR() terms organized by retrieval signal concept. The goal of a validation session is to understand what the system is actually retrieving, identify noise and gaps, and iterate on the profile terms until the chunks sent to the evaluator are genuinely relevant to each product's evidence intent.

---

## Step 1 — Understand what the product expects

Read `data/ipmp/acao_NN.json` for the target Ação. For each expected product:
- What physical artifact is the IPMP asking for?
- What section of the PPP process documents would contain that artifact?
- What language would that section use?

---

## Step 2 — Understand the current profile

Read `data/retrieval_profiles/acao_NN.json`. For the target product (e.g., 1a):
- What retrieval_signal_concepts are defined?
- How many active vs experimental query_terms exist?
- What is the evidence_intent for each product?

---

## Step 3 — Run the retrieval diagnostic

```powershell
cd "c:\Users\sanseri\Documents\Projetos\Maturity_Check"
$env:PYTHONIOENCODING="utf-8"
python inspect_retrieval.py
```

This produces `retrieval_diagnostic.txt` with five sections:

| Section | What it shows |
|---|---|
| QUERIES PER EXPECTED PRODUCT | Full FTS5 query string for each product + rio_hints |
| RAW HITS — before any dedup | All chunks each query returns (up to SQL LIMIT=80), with cross-product overlap flagged |
| CROSS-PRODUCT OVERLAP | Chunks matched by more than one product and which wins dedup |
| AFTER STEP 1 — per-product top-5 | Which 5 chunks each product nominates, and which are dropped |
| AFTER STEP 2 — cross-product dedup | Final 20 chunks sent to evaluator |
| FULL TEXT | Complete text of every BM25 chunk in evaluator order |

The diagnostic script is at the project root. If the process number or acao_id changes, update the `PROCESS_NUMBER` and `ACAO_ID` constants at the top.

---

## Step 4 — Analyse the diagnostic output

**Questions to answer per product:**

1. **Did the product get 5 chunks in the final top-20?**
   - If fewer than 5: either query returned weak scores, or cross-product dedup took its candidates.
   - Check STEP 1 — does the product nominate 5? If not, query coverage is thin.
   - Check STEP 2 — do any of the 5 get claimed by another product?

2. **Are the top-5 candidates substantively relevant?**
   Common failure modes:
   - **Header-only pages**: chunk text starts with "PREFEITURA DA CIDADE DO RIO DE JANEIRO Secretaria Municipal…" with no body content. This is a page header that was chunked together with a page that matches the query. The chunk itself has no evidence value.
   - **Wrong section of the right document**: the query terms match contractual penalty/termination clauses instead of the justification study. E.g., "vencimento contratual" in Clause 38 (what happens when a contract is terminated) vs. in the ETP introduction (why a new contract is needed).
   - **Concept contamination**: a term for one product (e.g., 1c's "objetivos estratégicos") appears in sections that belong to another product's evidence, inflating scores for the wrong product.

3. **What is the BM25 score spread?**
   - Scores of -17 to -19: strong, specific match.
   - Scores of -9 to -13: moderate match, likely keyword co-occurrence.
   - Scores below -5: weak, possibly header noise or incidental co-occurrence.
   - A product whose best chunk score is below -10 probably has few specific phrase matches in the corpus.

4. **Is the cross-product overlap large?**
   - If many chunks appear under multiple products, the queries are too broad or use overlapping vocabulary.
   - Overlap is not always bad: a chunk might genuinely contain evidence for two products (e.g., 1a and 1c).

---

## Step 5 — Identify profile improvements

For each problem chunk, determine the cause:

| Problem | Cause | Fix |
|---|---|---|
| Header-only pages retrieving | Query term matches body text on same page as repeated header | No fix needed at query level; this is a chunking limitation |
| Contract penalty clauses retrieved for 1a | Terms like "vencimento", "encerramento" appear in both ETP justification and contract penalty clauses | Add negative_evidence_patterns; or narrow terms with NEAR() closer distance |
| Another product's concepts dominating | rio_hints or 1b query is too broad, monopolising the top-20 | No action needed if per-product cap protects each product; verify cap is working |
| Product gets 0 chunks | Either query returned 0 hits OR all candidates were claimed by cross-product dedup | Check raw hits first; if 0, add broader terms; if claimed, narrow other products' queries |
| Good chunk not making top-5 per product | Correct chunk scores below the 5th-best | Either the chunk has weak BM25 score (term too rare or too common) or better candidates genuinely ranked higher |

---

## Step 6 — Edit the profile

Edit `data/retrieval_profiles/acao_NN.json`:

**Profile schema key points:**
- `encoding`: `"phrase"` for exact phrase, `"near"` for NEAR(token1 token2, distance)
- `status`: `"active"` (included in queries), `"experimental"` (included but under observation), `"deprecated"` (excluded)
- `provenance`: `"canonical"` (standard domain term), `"real_world"` (verbatim from observed documents)
- All string values must be in **Portuguese**
- `concept_ref` links the term to a `retrieval_signal_concept.key`

**Common edits:**
- Add a new phrase term: add to `query_terms` with `encoding: "phrase"`, `text: "nova frase"`, `status: "experimental"`
- Demote a noisy term: change `status` from `"active"` to `"experimental"` (still runs) or `"deprecated"` (excluded)
- Add a NEAR() term: use `encoding: "near"`, `tokens: ["token1", "token2"]`, `distance: 5`
- Tighten a NEAR() distance: reduce from 5 to 3 for more precise matching

**After editing**, the server singleton must be restarted to reload the profile. The singleton loads once on first access and caches for the server's lifetime.

---

## Step 7 — Restart server and re-run

```powershell
# Stop the uvicorn server (Ctrl+C if interactive, or kill process)
# Restart:
cd "c:\Users\sanseri\Documents\Projetos\Maturity_Check"
$env:PYTHONIOENCODING="utf-8"
$env:GROQ_API_KEY="<your key>"
python main.py
```

Re-run the assessment with the same files. Use `force=true` if you want to ensure a clean slate (wipes chunks + fingerprints + evaluations). Use `force=false` (default) if the chunks are already indexed correctly and you only changed the profile — the system will reuse existing chunks and re-run only the retrieval + evaluation.

```python
import requests
files = [
    ('files', ('doc1.pdf', open('path/to/doc1.pdf', 'rb'), 'application/pdf')),
]
r = requests.post('http://localhost:8000/api/cases/<process_number>/assess?force=true', files=files)
print(r.json())
```

Then re-run the diagnostic and compare Step 4 vs Step 5 to measure improvement.

---

## Step 8 — Evaluate chunk quality against IPMP criteria

After confirming the right chunks are being retrieved, run a full evaluation and inspect the result:

```python
import requests
r = requests.get('http://localhost:8000/api/cases/<process_number>/evaluations/1')
d = r.json()
print(d['proposed_score'], d['uncertainty_flag'])
print(d['reasoning'])
for c in d['retrieved_chunks']:
    print(c['expected_product_id'], c['cascade_step'], c['bm25_score'], c['text'][:200])
```

A chunk is "good" for the evaluator if:
- Its text directly addresses the evidence intent of its product (what the IPMP says that product should prove)
- It comes from the correct section of the document (ETP intro for 1a, economic study for 1b, risk matrix for 1c, legal instruments for 1d)
- The LLM reasoning references it explicitly

A chunk is "bad" (noise) if:
- The LLM reasoning ignores it entirely
- It contains only page headers or table-of-contents entries
- It matches the query keywords but from a different semantic context (contractual penalty clauses vs. project justification)

---

## Deduplication mechanics (reference)

The BM25 pipeline has three caps applied in sequence:

1. **SQL LIMIT per query** = `MAX_CHUNKS_PER_ACAO × 4` = 80. Each product's SQL query returns at most 80 rows.

2. **Per-product cap** (`_PER_PRODUCT_TARGET = 5`): After collecting all raw hits, each product independently selects its top 5 by BM25 score. A chunk ranked 6th or lower for a product is dropped at this stage even if it would be the best chunk overall. Maximum pool entering cross-product dedup = `n_products × 5`.

3. **Cross-product dedup** (`_merge()`): If the same physical chunk appears in multiple products' top-5 selections, only one copy survives — the one with the best (most negative) BM25 score. The "winning" product gets the attribution. A product can lose chunks here if another product matched the same chunk with a better score.

4. **Global cap** (`MAX_CHUNKS_PER_ACAO = 20`): The post-dedup pool is sorted by score and truncated to 20. Weak-scoring products (e.g., rio_hints with scores around -4 when 1d's floor is -9.7) may be cut here.

Final attribution note: a chunk appearing in multiple products' RAW query results is NOT necessarily a sign of a problem. It only matters when it appears in multiple products' post-cap top-5 selections, which forces a cross-product competition.

---

## Validation session checklist

- [ ] Profile loaded correctly (check server logs for "Loaded 1/1 retrieval profile files")
- [ ] `retrieval_diagnostic.txt` shows non-empty queries for all products
- [ ] Each product gets ≥ 3 chunks in the final top-20
- [ ] At least 1 chunk per product has score below -10 (strong match)
- [ ] The FULL TEXT section shows substantive content, not just headers
- [ ] No cross-product dedup is causing a product to lose all its candidates
- [ ] LLM reasoning references at least 1 specific chunk per scored product
- [ ] Proposed score and uncertainty_flag match expected outcome from ground truth
