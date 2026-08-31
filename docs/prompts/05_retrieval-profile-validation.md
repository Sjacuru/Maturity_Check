# Retrieval Profile Validation Process — Ação N

Use this prompt when beginning a retrieval profile validation session for any Ação.
Provide Claude with this file plus the relevant sections of `data/retrieval_profiles/acao_NN.json` and `data/ipmp/acao_NN.json`.

If `data/retrieval_profiles/acao_NN.json` doesn't exist yet for the target Ação, run `04_retrieval-profile-synthesis.md` first to generate a seed profile — this process validates and tunes against a real case document; it does not create a profile from nothing.

**Revision history:** substantially rewritten 2026-08-27 after validating Ação 2 against the real SMG-040 corpus and closing a long-open gate/GPU instability investigation. The previous version predated the LLM relevance gate (ADR-0050) and hybrid BM25+vector retrieval (ADR-0049) entirely — it described a pure-BM25 dedup pipeline that no longer exists and pointed at a script (`inspect_retrieval.py`) that has since been superseded. If you're reading an older cached copy of this file, re-fetch it.

---

## Context

The PPP Maturity Check system builds evidence for each Expected Product (1a, 1b, 1c, 1d…) in three stages: (1) a per-product BM25+vector hybrid search fused via RRF (`retrieval/query/cascade.py`, ADR-0049), (2) an LLM relevance gate that accepts/rejects each candidate and expands accepted anchors to their document neighbors (`evaluation/evidence_selection.py`, ADR-0050), (3) a final scoring call over whatever survived the gate. A validation session tunes the **retrieval profile** (`data/retrieval_profiles/acao_NN.json`) — Query Terms that drive stage 1, and `negative_evidence_patterns` that steer stage 2 — until the evidence reaching the scorer is genuinely relevant to each product's evidence intent. It ends by updating the profile's own status metadata (`profile_maturity`, per-term `status`) to reflect what was actually learned, not just the query text.

---

## Step 1 — Understand what the product expects

Read `data/ipmp/acao_NN.json` for the target Ação. For each expected product:
- What physical artifact is the IPMP asking for?
- What section of the PPP process documents would contain that artifact?
- What language would that section use?

---

## Step 2 — Understand the current profile

Read `data/retrieval_profiles/acao_NN.json`. For the target product (e.g., 1a):
- What `retrieval_signal_concepts` are defined?
- How many `active` vs `experimental` query_terms exist per concept?
- What is the `evidence_intent`? What `negative_evidence_patterns` already exist, if any?

---

## Step 3 — Build (or reuse) dedicated inspection scripts for this Ação

Create `scripts/a3_inspect_retrieval_acaoNN.py` and `scripts/a4_inspect_evaluation_acaoNN.py`, using the Ação 2 pair (`scripts/a3_inspect_retrieval_acao2.py`, `scripts/a4_inspect_evaluation_acao2.py`) as the structural template — **do not** copy the old Ação 1 scripts' pattern (`retrieve_for_acao` → `evaluate()` directly): those predate the gate and are kept unmodified on purpose as a record of the old architecture, not as something to imitate. The current-architecture pattern:

- `a3` (retrieval only): print the BM25/vector query per product, run Step A/B document-focused match, then `retrieve_hybrid_candidates_for_acao()` to see the RRF-fused candidate pool with scores — no gate involved yet.
- `a4` (full pipeline): `import main` first (triggers real `_bootstrap()`, so LLM wiring matches production per ADR-0054), mirror `assessment.service._retrieve_and_select()` (Step A/B short-circuit, else Step C hybrid + `select_evidence()`), and print accepted vs. rejected per product — flag any rejected chunk with a non-empty `matched_concepts` as a possible gate false negative worth a closer look — then call `evaluate()` for the real final result.

Run both against the real case document(s) already indexed for this Ação (or index one first if none exists yet).

---

## Step 4 — Analyse retrieval (a3)

**Questions to answer per product:**

1. **Does the product get candidates at all, and from which lane?** Every `RetrievedChunk` carries `cascade_step` (`"bm25"`/`"vector"`) and `retrieval_mode` (`"lexical"`/`"vector_fallback"`). A product whose accepted evidence is *always* `cascade_step: "vector"` across several runs, never `"bm25"`, means its Query Terms are not the thing actually finding evidence — see Step 8, this changes what you can claim about Term Status.
2. **Are the top candidates substantively relevant, or off-topic-but-lexically-matching?** Common failure modes: header-only chunks (chunking artifact, not a query problem — no profile fix applies); the right document's *wrong section* (e.g. a term like "vencimento" matching a contract-termination penalty clause instead of the needs-justification section); a term belonging to one product's vocabulary contaminating another product's results.
3. **BM25 score spread**: roughly, below ‑10 is a weak/incidental match; ‑10 to ‑15 is moderate; above ‑15 is a strong, specific match. A product whose best score never clears ‑10 across the query terms available probably needs more Track 1 canonical phrasing (see `04`), not a structural fix.

---

## Step 5 — Analyse the gate (a4) — accept/reject, not just retrieval

The candidate pool from Step 4 is not what the scorer sees — the gate (`select_evidence()`) filters it first. For each product, look at both sides:

- **Rejected candidates with a non-empty `matched_concepts`**: the deterministic concept-attribution pass (`_attribute_concepts`) found query-term vocabulary in the text, but the LLM gate still said no. This is either a correct rejection (the vocabulary appears, but not in the sense the criterion needs — the exact pattern this session's `negative_evidence_patterns` work targets) or a genuine gate false negative. Read the actual chunk text before assuming either.
- **Accepted candidates**: does the reasoning (available via a direct gate call, or from a live run's stored result) actually reference the criterion, or does it hedge and flip-flop between "However / But / So I think it's relevant"? A candidate whose acceptance reasoning reads as genuinely torn is a signal worth acting on even if this particular run accepted it correctly — see Step 7.

---

## Step 6 — Distinguish a genuine content gap from a retrieval defect

Before tuning anything, rule out the cheapest wrong conclusion: assuming weak/no retrieval for a product means the query is broken, when the case document may simply not contain that content. Run an independent full-corpus `SQL LIKE` search (no BM25, no RRF, no gate) for the product's expected vocabulary directly against `chunks.text` in `data/app.db`. If it comes back empty, that's a genuine document gap (Ação 2's 2a/2b against SMG-040, 2026-08-26, was exactly this — the case document has no EVTEA-style objectives section at all) — document it in `_meta` or a session note and move on. Do **not** keep adding query terms or negative patterns to chase a product that has nothing to find in the one document available; that just adds untested surface area. This isn't closeable by profile work — it needs a different case document, or an accepted gap.

---

## Step 7 — Tune `negative_evidence_patterns` — and check it's worth doing before you do it

When a candidate is rejected inconsistently (accepted on some runs, rejected on others) or accepted when it shouldn't be, first determine **why** before writing a fix:

1. **Read the actual gate reasoning**, not just the verdict. Capture `reasoning_content` on a few calls (direct HTTP to the primary LLM, `cache_prompt` left at default) rather than relying on the wrapped client, which doesn't expose it.
2. **Isolate infrastructure noise from content ambiguity.** Run the same prompt sequentially and under 2-way/4-way concurrency, *with itself* (homogeneous) — if it's rock-stable there, but flips only when run concurrently *with the other real products' prompts* (heterogeneous, matching `select_evidence()`'s actual `ThreadPoolExecutor` shape), that's the discriminator: pure GPU/kernel non-determinism reproduces under any concurrency; genuine content ambiguity typically only surfaces under the heterogeneous condition, because it takes a small numeric perturbation to tip an already-close decision. (Background: no deterministic-kernel flag exists in the current llama.cpp build — PR #16016 is unmerged/draft — and `cache_prompt: false`, a maintainer-suggested workaround, only partially helps and isn't reliable alone.)
3. **If the flip recurs across several calls on the same exact phrase**, that's content ambiguity, not noise — write a `negative_evidence_patterns` entry naming the specific confusion (e.g., "this describes contractual risk allocation, not an operational-deficiency diagnosis"), in the same register as the product's existing patterns.
4. **Before applying it, run the scalability check** (explicit project rule, 2026-08-27): would this fix help only this one Ação, or is it hard to reproduce for the other Ações? If either is true, discard it — a prompt correction that only pays off once isn't worth the maintenance surface. If the same confound has already shown up elsewhere (risk-allocation/responsibility-matrix boilerplate colliding with a "diagnosis of current state" criterion has now recurred 3 times across 2 different Ações in one session), that's evidence it's a structural domain confound worth fixing wherever it appears, not a one-off.
5. **Validate before *and* after** at matched sample size — a battery of 10 isolated sequential calls, then the same battery of ≥10 under real heterogeneous concurrency (see Step 3 of this list); compare accept/reject counts directly, not by feel. n=10 is enough to spot a clear signal; treat anything close (e.g. 2/40 vs 1/40) as inconclusive, not confirmed, unless you have the sample size to back it.

---

## Step 8 — Update Term Status with evidence, not intent

Every Query Term sits at `active` ("in use, untested"), `experimental` (excluded from BM25 until promoted), `validated` (confirmed to contribute useful recall), or `deprecated` (proven noise, kept for audit). Promoting/demoting is a status-metadata edit with real consequences for `experimental`↔`active` and `active`↔`deprecated` (both change what's actually searched — `build_query_from_terms` only includes `active`/`validated`), but not for `active`↔`validated` (cosmetic only, both already searched).

Do this check with a real batch of runs, not a single one — a term that happened to fire once isn't validated:
- **For an `experimental` term**: pull the actual accepted-evidence chunk text (`RetrievedChunk.text`) across a batch of ≥5–10 runs and grep for the literal phrase/tokens. If it's genuinely present in real accepted content, promote to `active` — that's empirical grounding, even though the term itself wasn't the one that found the chunk (it was excluded from the query). If it never appears, leave it — absence isn't proof of noise, just no evidence yet.
- **For an `active` term that a `negative_evidence_pattern` now specifically excludes** (i.e., the term reliably pulls in candidates the gate then has to reject) — that's a real signal the term is net-negative for this product; demote to `deprecated`, don't delete it (the field exists specifically so the reasoning stays auditable).
- Per Step 4's `cascade_step` check: if a whole product's accepted evidence across a batch never shows `cascade_step: "bm25"`, don't promote any of that product's `active`/`experimental` BM25 terms to `validated` yet regardless of how good the aggregate outcome looks — the aggregate improvement may be coming from the vector lane, not the terms you're evaluating. This is exactly the trap Ação 2's Component 3 batch fell into: real, measured score improvement, but the accepted evidence itself showed zero BM25 attribution across 10/10 runs.

---

## Step 9 — Advance `profile_maturity`

Per CONTEXT.md's own definition, `profile_maturity` advances `seed` → `observed` the first time a real case document has actually been used in a population/validation session — which is exactly what Steps 3–8 above are. **Do this explicitly; it does not happen automatically and is easy to forget** (Ação 2 sat at `seed` for a full session after real-document validation had already happened, until caught in a later review). `observed` → `mature` needs validation across multiple cases/sectors, not just one — don't advance past `observed` on a single case document.

---

## Step 10 — Statistical confirmation, not a single run

A single before/after run proves nothing given the gate's own non-determinism (Step 7). Run a live battery (≥10 sequential calls through the real `/assess` API, not scratchpad-only function calls) before a change and the same battery after, and compare distributions directly: `score` distribution, `no_evidence_found` rate, `retrieved`/`rejected` counts, `uncertainty_flag` rate. Treat a difference as confirmed only if it holds at this sample size — see Step 7.5 for the same caution applied to a single candidate.

---

## Deduplication and evidence-selection mechanics (reference, current as of ADR-0050)

1. **RRF-fused candidate pool** (`retrieve_hybrid_candidates_for_acao`, ADR-0049): BM25 and vector rankings fused per product via Reciprocal Rank Fusion (k=60) — vector is co-equal and always-on, not a fallback.
2. **Pre-gate near-duplicate filter** (`_prefilter_near_duplicates`, threshold 0.92): drops near-identical candidates before spending a gate call on them.
3. **Gate + anchor selection** (`_select_for_product`): examines up to `_MAX_EXAMINED = 8` ranked candidates per product, keeps up to `_ANCHOR_TARGET = 5` accepted ones as anchors. Each candidate is gated against `evidence_intent` + `retrieval_signal_concepts` + `negative_evidence_patterns` (all three, scoped strictly to this Ação/product — no shared/canonical list).
4. **Neighbor expansion** (`_expand_anchors`): for each accepted anchor, its immediate document neighbors are fetched and gated too, up to `_EXPANSION_TARGET = 5` accepted expansions per product.
5. **Cross-product dedup + budget trim + semantic dedup**: the same physical chunk accepted by multiple products collapses to one copy with merged `expected_product_ids`; expansions are trimmed first (weakest-scoring product first) if the combined evidence exceeds the character budget; a final semantic-similarity pass (threshold 0.70) drops near-duplicate text across the whole accepted set.

The public `EvaluationResult`/`RetrievedChunk` model has no field distinguishing "anchor" from "expansion" — that distinction only exists transiently inside `select_evidence()`'s private helpers; if you need it for diagnostics, instrument the function directly rather than trying to infer it from the API response.

---

## Validation session checklist

- [ ] Dedicated `a3`/`a4` inspection scripts exist for this Ação (Step 3), following the current-architecture pattern, not the pre-gate Ação 1 template
- [ ] Retrieval analysed per product: candidate presence, lane (`cascade_step`), score spread, off-topic-but-matching cases (Step 4)
- [ ] Gate accept/reject analysed per product, not just retrieval (Step 5)
- [ ] Any product with weak/no evidence checked against a full-corpus `SQL LIKE` search before being treated as a query defect (Step 6)
- [ ] Any `negative_evidence_patterns` addition passed the scalability check before being applied (Step 7.4) — and was validated at matched sample size before/after (Step 7.5), with infra noise ruled out first (Step 7.2) if the symptom was a flip under concurrency
- [ ] Term Status reviewed with actual batch evidence, not left at its generation-time default (Step 8) — check `cascade_step` attribution before promoting any BM25 term to `validated`
- [ ] `profile_maturity` advanced if this session used a real case document and the field was still at `seed` (Step 9)
- [ ] Improvement claims backed by a ≥10-run live battery before vs. after, not a single run (Step 10)
- [ ] Proposed score and uncertainty_flag reviewed against expected outcome / ground truth where available
