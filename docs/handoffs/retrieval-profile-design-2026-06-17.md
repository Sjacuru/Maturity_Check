# Retrieval Profile Design Session — Handoff
**Date:** 2026-06-17
**Session type:** Grill-me / architectural interview (one question at a time, one decision at a time)
**Scope:** Improving BM25 retrieval for IPMP Expected Products 1a–1d

---

## Starting Problem

`build_bm25_query()` tokenizes `produto.texto` into a bag of single words (≥5 chars, lowercased, deduped, OR-joined). For Expected Product 1d this produces a 40-term OR query of which only 7 terms (17.5%) are genuine signal words. The remaining 33 are IPMP's own governance framing language, "levels" boilerplate, and connectors that match unrelated content.

Root cause: two problems interact.
1. **Mechanism**: multi-word phrases in the source text (e.g., "Plano Nacional de Hidrovias") are destroyed before FTS5 ever receives the query — tokenized into independent single-word OR-clauses.
2. **Vocabulary**: `produto.texto` is criterion language (IPMP's description of what the evidence should contain), not evidence-anchor language (the actual words a case document would use to satisfy the criterion).

Both problems must be fixed. Neither alone is sufficient.

---

## Two Code Paths Already in Production

The existing codebase has two query-construction mechanisms with opposite phrase behaviour:

**Mechanism 1 — `rio_hints` (`cascade.py:36`):**
```python
queries["rio_hints"] = " OR ".join(f'"{t}"' for t in all_hints)
```
Each hint is wrapped *whole* in quotes and passed verbatim to `chunks_fts MATCH ?`. FTS5 treats quoted multi-word strings as phrase queries (exact token sequence). **Phrase semantics survive end-to-end.** Validated by Phase A (3/4 retrieved pages for Score3 doc came via `rio_hints`).

**Mechanism 2 — `build_bm25_query()` (`query_builder.py:26–35`):**
```python
for text in texts:
    for w in _PUNCT_RE.sub(" ", text).split():
        if len(w) >= _MIN_WORD_LEN:
            words.add(w.lower())
return " OR ".join(f'"{w}"' for w in sorted(words))
```
`product.texto` is split into single words *before* quoting. A phrase like "Plano Nacional de Hidrovias" becomes `"plano" OR "nacional" OR "hidrovias"` — three independent single-token clauses with no sequence constraint. The destruction happens in Python, before FTS5 is involved.

**Consequence:** if curated multi-word anchors were naively fed through `build_bm25_query()`, they would be shredded just as `produto.texto` is. Layer 1's mechanism fix is a prerequisite for any vocabulary improvement.

---

## Evidence Ontology Framework

The session produced a layered evidence framework that replaces the flat "anchor" concept.

### Evidence Type Taxonomy (A/B/C/D — what kind of evidence it is)

| Type | Description | FTS5 encoding | Notes |
|---|---|---|---|
| **A** | Named entities (PNH, PLANSAB, specific plan/document names) | Strict phrase | Low variability, high precision, limited generalization across sectors |
| **B** | Domain concepts (saneamento básico, logística portuária, mobilidade urbana) | Case-by-case (phrase or NEAR) | Moderate generalization |
| **C** | Evidence/process patterns (diagnóstico setorial, análise de alternativas, priorização de investimentos) | NEAR() as primary encoding | Relationship-oriented, not phrase-oriented; high paraphrase variability |
| **D** | Intervention logic (Problem → Need → Intervention → Outcome chains) | NOT a retrieval term | Evaluation/reranking layer only |

**Key insight on Type C:** NEAR() is not a relaxed fallback — it is the more faithful encoding of the underlying evidence model for Type C. "diagnóstico + problema" can be expressed in many syntactic forms while still representing the same evidence pattern. Phrase matching would impose artificial rigidity.

**Key insight on Type D:** FTS5 cannot detect causal chains across paragraphs. Type D patterns govern how the evaluation and reranking layers assess evidence *strength*, not how the retrieval layer generates candidates.

### Ontology Layer Framework (A/B/C/D — what role it plays in the pipeline)

| Layer | Question it answers | Role | Becomes FTS5 input? |
|---|---|---|---|
| **Layer A** | What kind of evidence am I looking for? | Evidence intent — conceptual | No |
| **Layer B** | What concepts indicate this evidence? | Retrieval signal — conceptual bridge | No |
| **Layer C** | How does this concept appear in reality? | Query terms — derived from real documents + canonical sources | Yes |
| **Layer D** | What logic pattern constitutes strong evidence? | Evidence strength — relational | No — evaluation/reranking only |

**Workflow:**
```
Expected Product
→ Evidence Intent (Layer A: never a query)
→ Retrieval Signal Concept (Layer B: conceptual bridge, never a query)
→ Query Terms (Layer C: FTS5 artifact, derived from Observed Expressions + canonical sources)
→ FTS5 MATCH
```

**Critical distinction:** "Retrieval Signals" in the original ontology document are Layer B (conceptual — e.g., "necessidade de intervenção"), while "Observed Real-World Expressions" are Layer C source material (verbatim phrases from real documents — e.g., "qualidade de vida", "conforto à população"). Query terms are derived *from* Layer C source material, not directly from Layer B signal concepts.

**"Instance → concept" principle:** BRT and Bike Rio are instances of "integração com iniciativas municipais de mobilidade urbana." Query terms should be at the concept level for generalization across cases, not at the specific-object level. NEAR() supports this ("integração" NEAR "municipal") without requiring enumeration of every possible instance.

---

## Resolved Architectural Decisions

### Layer 1 (mechanism fix — prerequisite)

1. Extract the phrase-preserving join pattern from `cascade.py`'s `rio_hints` construction into a shared function used by both `rio_hints` and the 1a-1d path.
2. Acronym expansions become **atomic phrase-terms** rather than being shredded into the word-set. Trigger rule (`if acronym in product_text`) is unchanged — only the representation changes. For 1d specifically, this upgrades 5 of 7 signal terms (logística, decenal, saneamento, portuária, hidrovias) from isolated word-clauses to precise 3–4-token phrase clauses — for free, with zero vocabulary judgment.
3. `produto.texto`'s own word-extraction (≥5-char single words) is **unchanged** in Layer 1 — that is Layer 2's territory.
4. NEAR() encoding included in Layer 1 scope (not a later enhancement). The schema needs to distinguish phrase-type vs NEAR()-type terms from the start to avoid a later schema migration.

**Gap Layer 1 cannot close:** "aeroviário" (one of 1d's 7 signal terms) comes from "Plano Aeroviário Nacional" — no acronym entry in `acronyms.json`, so Layer 1's mechanism doesn't touch it. Layer 2 curation must add this explicitly.

### Encoding defaults (Layer 1 scope)

- **Type A** → strict phrase queries (`"Plano Nacional de Hidrovias"`)
- **Type B** → case-by-case depending on the concept
- **Type C** → NEAR() as primary encoding (`NEAR("diagnóstico" "problema", 5)`)
- **Type D** → evaluation/reranking layer only; never enters FTS5

### Data artifact — `data/retrieval_profiles/acao_01.json`

New artifact category, separate from `data/ipmp/`, `data/rio_manual/`, `data/acronyms/`. Rationale: retrieval profiles are **derived knowledge artifacts** (synthesized from IPMP text + Rio Manual + real-document observation + acronym tables) that evolve as corpus knowledge accumulates. IPMP, Rio Manual, and Acronyms are **canonical primary sources** that should remain immutable. Conflating them would violate this separation.

**Schema (approved):**
```json
{
  "acao_id": 1,
  "expected_products": {
    "1a": {
      "evidence_intent": "Justificativa do projeto — motivos pelos quais o projeto é necessário",
      "retrieval_signal_concepts": [
        { "key": "necessidade_intervencao", "text": "necessidade de intervenção identificada" },
        { "key": "diagnostico_problema",   "text": "diagnóstico do estado atual do problema" }
      ],
      "query_terms": [
        { "encoding": "phrase", "text": "qualidade de vida",
          "type": "C", "provenance": "real_world",  "concept_ref": "necessidade_intervencao" },
        { "encoding": "phrase", "text": "conforto à população",
          "type": "C", "provenance": "real_world",  "concept_ref": "necessidade_intervencao" },
        { "encoding": "phrase", "text": "conveniência e oportunidade",
          "type": "C", "provenance": "canonical",   "concept_ref": "necessidade_intervencao" },
        { "encoding": "near",  "tokens": ["diagnóstico", "problema"], "distance": 5,
          "type": "C", "provenance": "canonical",   "concept_ref": "diagnostico_problema" }
      ],
      "evidence_logic_patterns":    ["Problema → Necessidade → Intervenção"],
      "negative_evidence_patterns": ["Solução proposta sem diagnóstico identificável do problema"]
    }
  }
}
```

Notes:
- `concept_ref` is optional per query term; enables future analysis of which retrieval signal concepts generate useful results vs. noise
- All query-facing strings (text, tokens) are in Portuguese; structural field names in English
- `retrieval_signal_concepts` uses keyed map (slug → text) for stable `concept_ref` values as the list grows

The ingestion module gains `get_retrieval_profile_store()` (mirroring `get_ipmp_store()`). `cascade.py`'s `retrieve_bm25_for_acao()` calls this store to build 1a-1d queries, replacing `build_bm25_query(product.texto, acronym_map)`.

---

## Documentation Methodology (agreed)

### Two ADRs, not three to five

Consolidate tightly-coupled decisions to avoid forcing future readers to cross-reference multiple ADRs for a single coherent design.

**ADR-A — Retrieval Profile Architecture:**
- Evidence ontology layers A/B/C/D
- Retrieval profile as a new derived artifact category (`data/retrieval_profiles/`)
- Evidence model (Types A/B/C/D)
- Layer A/B/C/D role separation

**ADR-B — Query Construction and Encoding:**
- Phrase preservation mechanism (Layer 1 fix)
- Acronym expansion as atomic phrase-terms
- Encoding defaults by evidence type (Type A: phrase, Type C: NEAR, Type D: evaluation only)
- NEAR() support in query construction

### DAN-0002 update — not a new DAN

DAN-0002's original question: "How should BM25 queries be generated?" This session answers that question at a deeper level. It is not a new design space — it is the evolution of the same one. Add a section to DAN-0002: **"Evolution of Query Generation Strategy"** documenting how Position A evolved into the retrieval profile + ontology framework. Do not open DAN-0003 for this topic.

### CONTEXT.md updates needed

New terms to add:
- **Retrieval Profile** — derived knowledge artifact per Ação containing Layer A/B/C/D content for evidence identification and query generation
- **Evidence Ontology** — framework classifying evidence by type (A/B/C/D) and by pipeline layer (A/B/C/D)
- **Query Term** — a Layer C artifact with encoding type (phrase/NEAR), evidence type, provenance, and concept reference; the actual FTS5 input
- **Evidence Intent** — Layer A; describes what the Expected Product is verifying; never a query term
- **Retrieval Signal Concept** — Layer B; conceptual bridge between evidence intent and observable language; never a query term

---

## Open Questions (not yet decided)

### 1. Retrieval Profile Population Methodology — BLOCKED, needs explicit decision

Q2 approved the artifact structure but NOT the generation process. Three options identified:
1. Manual curation per Ação by the domain expert
2. Claude-guided curation per Ação (structured interview with domain expert)
3. Separate evidence-discovery workflow driven by real-document analysis (the user's preferred direction)

User view: this may deserve its own workstream/mini-project because the methodology for creating high-quality Layer A/B/C/D content is substantial in its own right. **No decision made yet — explicit decision required before implementation begins.**

### 2. Process/Ownership (Q5)

Who maintains retrieval profiles over time? How does the corpus-observation cycle (read real doc → add real-world expressions → test → update profile) work operationally? How are provenance records maintained as new corpus knowledge is added?

### 3. Empirical Validation Plan (pending)

A/B comparison: Strategy A (curated Layer C terms only) vs Strategy B (curated Layer C terms + current algorithmic extraction from `produto.texto`). The question "do algorithmic terms occasionally recover evidence curated vocabulary misses?" needs data, not reasoning — OR-semantics mean B's candidate pool ⊇ A's, but ranking effects are empirical.

Infrastructure already in place:
- `data/test_corpus/Caso_Teste_Acao1_Score3.pdf` and `Score1.pdf` with known ground truth (Score3=3, Score1=1 per Phase A validation)
- `RetrievedChunk.expected_product_id` already provides per-Expected-Product attribution
- Real document: `docs/SMG-040_101607_2024_*.pdf` (3 volumes, gitignored — "Acesso: Limitado ao Órgão") — Rio de Janeiro PPP, "mobiliário urbano", process SMG-PRO-2024/00020. Different sector from all of IPMP 1d's example national plans → ideal stress test for Type C generalization

### 4. Chunk Context Expansion (Q6) — DEFERRED

Explicitly deferred per Module 3 handoff ("Revisit when retrieval effectiveness and document-size characteristics are better understood from real-case evaluation"). Revisit after A/B validation.

### 5. Layer 5 Reranking / Evidence-Selection Agents (Q7) — DEFERRED

Deferred to Layer 5, contingent on A/B results and ADR-0009 revisit (one-LLM-call-per-Ação). User's view: ADRs 0009 and no-reranking were created under assumptions that may need revalidation once retrieval quality is measured empirically. Not discarded — revalidated using evidence from empirical results.

---

## Real Document — Key Observations

`docs/SMG-040_101607_2024_*.pdf` (3 volumes, restricted access):
- Process: SMG-PRO-2024/00020, Prefeitura do Rio de Janeiro / SMCG
- Subject: urban furniture concession (bus shelters, digital clocks, MUPIs/totems, public restrooms)
- Pages 1–2 confirmed the following Observed Real-World Expressions (already used in 1a/1d curation):
  - 1a: "qualidade de vida e bem-estar à população", "promovendo maior conforto, segurança e saúde", "apoio ao uso dos serviços públicos" (exactly matching the 1a row in the evidence ontology)
  - 1d: "BRTs", "pontos de Bike Rio" (supporting "revitalização do sistema BRT, integração com Bike Rio")
- This document is from a sector NOT covered by any IPMP 1d example plans (PNH/PNL/Plansab/etc.) → a Type C–heavy retrieval challenge, confirming the hypothesis that named-entity Type A terms have poor recall in sectors IPMP's examples don't anticipate

---

## Key Files

| File | Role |
|---|---|
| `src/retrieval/query/query_builder.py` | Current `build_bm25_query()` — phrase-destroying mechanism to be replaced/extended |
| `src/retrieval/query/cascade.py` | `retrieve_bm25_for_acao()` — builds queries dict; rio_hints construction at line 36 |
| `src/retrieval/query/bm25.py` | `search_bm25()` — query string passed verbatim to `MATCH ?` at lines 97–99 |
| `data/ipmp/acao_01.json` | IPMP source (produtos_esperados 1a–1d texts + exemplos) |
| `data/rio_manual/acao_01.json` | Rio Manual (bm25_search_hints, legal_phrases, document_names) |
| `data/acronyms/acronyms.json` | Acronym map (PNL, PDE, Plansab, PNLP, PNH, PPA, EVTEA, PPP, IPMP, TCU, TCDF) |
| `docs/dan/0002-bm25-query-generation-strategy.md` | DAN to update with Evolution section |
| `docs/SMG-040_101607_2024_*.pdf` | Real case document (3 volumes, gitignored — restricted access) |
| `Learning/` | BM25 learning workspace (MISSION.md, NOTES.md, lessons/, reference/) |
