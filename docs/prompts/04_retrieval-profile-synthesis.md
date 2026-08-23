# Retrieval Profile Synthesis Process — Ação N

Use this prompt to generate a **seed** retrieval profile (`data/retrieval_profiles/acao_NN.json`) for an Ação that doesn't have one yet, or to extend an existing one with synthetic sector vocabulary — without ever reading a real case document.

Provide Claude with this file and the target `acao_id`. `data/ipmp/acao_NN.json`, `data/sector_taxonomy.json`, and any existing `data/retrieval_profiles/acao_*.json` files are read directly from the project — no need to paste them.

**Prerequisite:** `data/ipmp/acao_NN.json` must already exist (IPMP ingestion is manual — this process does not create it). If it doesn't, stop and ask for the transcribed IPMP text first.

**Hard rule — do not violate:** this process never opens a real case document (no `test_corpus/`, no uploaded PDFs, nothing under `docs/*_*.pdf`). Everything it produces is derived from `data/ipmp/acao_NN.json`, `data/sector_taxonomy.json`, and general domain knowledge of Brazilian public procurement. Real-document grounding is a separate, later process — see `05_retrieval-profile-validation.md`.

---

## Why this exists

`data/retrieval_profiles/` only has `acao_01.json`, built by hand against a real case (SMG-040). Scaling to 46 Ações by repeating that manual, per-case process for every one is exactly what the project decided not to do (see CONTEXT.md — Profile Maturity, Provenance). This process produces a `profile_maturity: "seed"` profile instead: safe to generate ahead of any real document, because every term it adds under `provenance: "synthetic"` starts at `status: "experimental"` and is therefore excluded from the active BM25 query until a human (or a later `05` validation session) promotes it. A seed profile is a hypothesis, not a certified retrieval configuration.

---

## Step 1 — Read the Ação's IPMP source and orient by Dimensão/Fase

Read `data/ipmp/acao_NN.json` in full. For each Expected Product (e.g., `2a`, `2b`, `2c`, `2d`):
- What physical artifact is the IPMP asking for?
- What is the one-sentence Evidence Intent (Layer A) — the evaluation objective, not a query term?

Also note the Ação's `dimensao` and `fase` fields. Use them to calibrate register, not content:
- **Estratégica** Ações lean on planning/alignment vocabulary (objetivos, alinhamento, políticas públicas, diagnóstico).
- **Gerencial** Ações lean on execution/governance vocabulary (plano de gestão, equipe de projeto, cronograma, riscos).
- **Econômica/Financeira/Comercial** Ações lean on their respective technical vocabularies (viabilidade econômica, custeio, modelo de contratação).
- **Fase Inicial** Ações describe a scenario without the project yet (diagnóstico, situação atual). **Fase Final** Ações describe review/consolidation (atualização, revisão, confirmação).

This shapes word choice in Steps 2–3; it is not a filter that excludes any Dimensão/Fase from generation.

---

## Step 2 — Draft Retrieval Signal Concepts (Layer B)

For each Expected Product, draft one or more `retrieval_signal_concepts` — conceptual bridges between the Evidence Intent and language a real document would plausibly use. Derive these from the IPMP text plus general procurement domain knowledge (Stage A reasoning). No provenance tracking is needed at this layer (see "Scope note" below).

---

## Step 3 — Draft Query Terms (Layer C) — the only layer that drives retrieval

Two tracks, both required:

**Track 1 — canonical terms.** Phrase or NEAR() terms drawn directly from the IPMP's own wording for that product (`type: "A"`, `provenance: "canonical"`, `status: "active"`). These are safe by construction — they're the IPMP's own language.

**Track 2 — synthetic sector terms.** For each Expected Product, judge whether cross-sector vocabulary variation is actually plausible for that specific product's evidence — not every product needs it (see "Don't force it" below). Where it is plausible:
- Consult `data/sector_taxonomy.json`. Use its `key` values verbatim as `sector_hint`. Never invent a new sector label inline — if a genuinely new sector is needed, stop and propose adding it to `data/sector_taxonomy.json` first, as its own deliberate edit.
- Select only the sectors where the term would plausibly appear in that product's evidence — not all 15.
- Set `provenance: "synthetic"`, `status: "experimental"`, `sector_hint: "<key>"` on every term from this track.
- **Prefer `NEAR()` over enumerating phrase variants.** If a concept has several plausible sector-specific phrasings (e.g., "postes de iluminação", "rede de iluminação pública", "sistema de iluminação"), encode it as one `NEAR()` term around the shared tokens rather than three separate `phrase` terms.
- **Auto-demote colliding generic terms.** If a candidate term's dominant word already appears in 2+ other Query Terms within the same Ação, set `status: "experimental"` regardless of provenance — it's a collision risk for the BM25 OR query, not just a synthetic-vocabulary risk.

**Don't force it.** A product whose Evidence Intent is procedural/structural (e.g., "describe the gap between current state and objectives") often doesn't vary by sector at all. Adding sector terms to it anyway is exactly the over-breadth this process must avoid — skip Track 2 for that product rather than padding it.

---

## Step 4 — Check for cross-Ação overlap

Before finalizing, compare every new Concept/Query Term (both tracks) against the content of every other existing `data/retrieval_profiles/acao_*.json`. If a candidate is textually or semantically close to something already in another Ação's profile:
- If the overlap is genuinely pertinent to both Ações (the same underlying fact supports two different evaluative conclusions), keep it and add `shared_with_acao: [<other acao_id>]` plus a short justification.
- If the overlap looks like an accident of generic phrasing with no distinct new meaning for this Ação, prefer a more specific formulation instead.

This is a one-time comparison at generation time, not a runtime chunk-tracking mechanism — no chunk, real or otherwise, is involved.

---

## Step 5 — Draft Evidence Logic Patterns (Layer D)

Draft `evidence_logic_patterns` and, where relevant, `negative_evidence_patterns` for each product, at Stage-A quality — generic relational/structural patterns derivable from the IPMP text and domain knowledge, not case-specific corrective notes (a corrective note like Ação 1 1d's "for mobiliário urbano, national sector plans don't apply" can only come from reading a real document — that's Stage B's job, in `05_retrieval-profile-validation.md`, not this process).

**Scope note:** Layers B and D get no per-item provenance tracking in this pass. Only Layer C (Query Terms) drives BM25 retrieval, so that's where the experimental/active safety mechanism needs to live. Retrofitting provenance onto B/D would require converting `evidence_logic_patterns`/`retrieval_signal_concepts` from plain-string lists into structured objects — a breaking change to Ação 1's existing data, disproportionate to a layer that doesn't affect what gets retrieved.

---

## Step 6 — Write the profile

Target: `data/retrieval_profiles/acao_NN.json`.

**If the file doesn't exist:** create it fresh. `profile_maturity: "seed"`. `_meta.population_stages_completed: ["A"]`. `_meta.stage_b_sources: []`. `_meta.scope`: free-text note that this profile was generated by the synthesis process, without real-document grounding, including which sectors from `data/sector_taxonomy.json` were drawn on.

**If the file already exists:** additive merge only.
- Never modify or remove an existing item whose `status` is `"validated"` or `"deprecated"` — those reflect human judgment.
- Only add new items (as `"experimental"`, per the rules above).
- You may read another Ação's already-`"validated"` terms as a style/register reference for phrasing — but never copy their content into this Ação without going through Steps 3–4 on their own merits.
- Do not change `profile_maturity` — only a real-document population session (`05`) advances it.

---

## Step 7 — Self-validate

Reload the file through the actual loader before declaring the profile done:

```powershell
cd "c:\Users\sanseri\Documents\Projetos\Maturity_Check"
$env:PYTHONIOENCODING="utf-8"
python -c "from src.ingestion.retrieval_profile import get_retrieval_profile_store; s = get_retrieval_profile_store(); print(s.acoes[<acao_id>].profile_maturity, list(s.acoes[<acao_id>].expected_products.keys()))"
```

If this raises a validation error, fix the JSON before finishing — do not leave a profile that fails to load.

---

## Synthesis session checklist

- [ ] `data/ipmp/acao_NN.json` read in full; no real case document opened at any point
- [ ] Every Expected Product has an `evidence_intent` and at least one `retrieval_signal_concept`
- [ ] Every product has at least one canonical (`provenance: "canonical"`) Query Term drawn from the IPMP's own wording
- [ ] Sector terms only added where plausibly relevant to that specific product — not blanket-applied
- [ ] Every sector term uses a `sector_hint` key that exists in `data/sector_taxonomy.json`
- [ ] Every `provenance: "synthetic"` term has `status: "experimental"`
- [ ] Repeated sector phrasing encoded as `NEAR()`, not enumerated `phrase` variants
- [ ] Terms colliding with 2+ existing terms in the same Ação demoted to `"experimental"`
- [ ] New Concepts/Terms checked against every other existing Ação's profile for overlap; genuine overlaps carry `shared_with_acao` + justification
- [ ] If the profile already existed: no `"validated"`/`"deprecated"` item touched; `profile_maturity` unchanged
- [ ] `_meta.scope` documents that this was a synthesis pass, not a real-document population session
- [ ] File reloads through `get_retrieval_profile_store()` without a validation error
