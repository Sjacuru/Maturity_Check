# Handoff: Module 4 Grill-Me — LLM Evaluation

**Date opened:** 2026-05-30
**Status:** OPEN — ready to begin grill-me session
**Next agent task:** Run grill-me for Module 4 (LLM Evaluation), write ADRs and to-PRD

---

## What This Handoff Is

Module 3 (BM25 retrieval) is complete. This document gives a fresh session enough context to run
the grill-me for Module 4 — the LLM evaluation layer that receives `list[RetrievedChunk]` and
produces a proposed Maturity Score (0/1/3) with full audit trail for human review.

---

## Suggested Skills

- **grill-me** — `docs/prompts/01_grill-me.md` — governs how to run the session
- **to-PRD** — `docs/prompts/02_To-PRD.md` — downstream step after grill-me completes

---

## Project Snapshot

**Repo:** https://github.com/Sjacuru/Maturity_Check
**Working dir:** `c:\Users\sanseri\Documents\Projetos\Maturity_Check`
**Conda env:** `rel_voto` (Python 3.11)
**Language:** Bilingual PT + EN

**Completed modules:**
| Module | Package | Tests |
|--------|---------|-------|
| 1 — Ingestion | `src/ingestion/` | ✅ |
| 2 — Extraction | `src/extraction/` | ✅ |
| 3 — Retrieval | `src/retrieval/` | ✅ 147/147 fast |

**Module 4 scope:** `src/evaluation/` — LLM evaluation (temperature=0, one call per Ação)

---

## What Module 3 Produces (Module 4's input)

Module 3's public surface:

```python
from retrieval import index, retrieve_for_acao, RetrievedChunk

# Write path
index(process_number: str, chunks: list[Chunk]) -> None

# Read path — full cascade A→B→C+D
retrieve_for_acao(acao_id: int, process_number: str) -> list[RetrievedChunk]
```

`RetrievedChunk` fields:
```python
process_number: str
filename: str
page_number: int
chunk_index: int
char_offset: int
page_total: int
ocr_used: bool
source_type: str
text: str
cascade_step: Literal["filename_match", "variant_match", "bm25", "regex"]
expected_product_id: str | None   # null on doc-focused and regex paths
bm25_score: float | None          # null on non-BM25 paths
rank: int | None                  # null on non-BM25 paths
```

The list may be empty (no evidence found). Module 4 must handle this case explicitly.

---

## Auditor Review Interface (7 elements — from CLAUDE.md)

For each scored Ação, the system presents to the Auditor:

1. IPMP criteria for the action
2. Retrieval query used
3. Retrieved chunks (with source document + page number)
4. Exact LLM prompt sent
5. LLM reasoning
6. Uncertainty flag
7. Proposed score (0 / 1 / 3)

Module 4 must produce enough data for Module 5 to render all 7 elements. The boundary question
(what does Module 4 own vs Module 5?) is an open grill-me question.

---

## Settled Constraints (from CLAUDE.md strategic decisions)

| Constraint | Source |
|-----------|--------|
| **temperature=0** | ADR-0004 — reproducibility requirement |
| **Fixed prompt per Ação** | ADR-0009 — single LLM call per Ação |
| **IPMP criteria + scored examples in prompt** | ADR-0001, ADR-0004 |
| **Human Auditor validates every score** | ADR-0005 |
| **Score: 0 / 1 / 3 integers only** | ADR-0008 — action-level scoring |
| **Phase 1: Ação 1 only** | CLAUDE.md strategic decision 8 |
| **Ollama/Mistral default (local), Groq option** | CLAUDE.md tools table |
| **Reproducibility** is the core academic constraint | CLAUDE.md |

---

## Key IPMP Data for Ação 1

`data/ipmp/acao_01.json` contains the full LLM prompt substrate:

- `titulo` — Ação title
- `descricao_acao` — what the Ação evaluates
- `o_que_esperar` — what a good response looks like
- `produtos_esperados` — 5 entries (id `"1"` parent + `"1a"`–`"1d"` sub-items)
- `exemplos` — 3 scored examples: `"Atendido"` (3), `"Parcialmente Atendido"` (1), `"Não Atendido"` (0)
- `excecoes` — exceptions that affect scoring
- `momento_ideal` — expected phase

The scored examples are the key: each has `nivel`, `score`, and `texto` (a concrete paragraph
describing a project that received that score). These ground the LLM in what each score level looks
like in practice.

---

## Open Design Questions (grill-me material)

These are the questions the grill-me session must resolve before to-PRD can run. They are ordered
roughly by dependency — resolve earlier ones before later ones.

### Q1 — Module 4 API boundary

What does Module 4 expose? Options:

A. `evaluate(acao_id, process_number) -> EvaluationResult` — Module 4 calls `retrieve_for_acao` internally  
B. `evaluate(acao_id, process_number, chunks: list[RetrievedChunk]) -> EvaluationResult` — caller supplies chunks  
C. Two separate functions: `build_prompt(...)` + `run_evaluation(...)`

**Why it matters:** If A, Module 4 owns the full flow and is easy to call. If B, separation of
concerns is cleaner and Module 4 is testable without a live DB. If C, prompt building becomes
separately testable.

### Q2 — EvaluationResult shape

What fields does `EvaluationResult` carry? Minimum needed for the 7-element auditor interface:

- `proposed_score: int` — 0, 1, or 3
- `reasoning: str` — LLM's explanation
- `uncertainty_flag: bool` — did the LLM flag uncertainty?
- `prompt_sent: str` — exact prompt sent to LLM
- `acao_id: int`
- `process_number: str`
- `retrieved_chunks: list[RetrievedChunk]` — evidence used

Questions: Is `EvaluationResult` a Pydantic model? Does it live in `src/evaluation/` or
`src/interfaces/`? Does it carry the raw LLM response alongside the parsed score?

### Q3 — Prompt structure

How is the prompt assembled? Candidates:

A. Single system prompt embedding full IPMP section + all chunks  
B. System prompt = IPMP criteria; user prompt = retrieved chunks  
C. Structured into subsections (criteria, examples, evidence, instruction)

The IPMP source includes: `descricao_acao`, `o_que_esperar`, `produtos_esperados`, `exemplos` (3
scored paragraphs), `excecoes`. All of this must be embedded to match ADR-0004.

**Key question:** In what order? The scored examples are the ground truth anchors — the LLM should
compare the retrieved evidence against them.

### Q4 — Score parsing strategy

LLM output must yield exactly 0, 1, or 3. Options:

A. Prompt instructs LLM to end with `SCORE: 0`, `SCORE: 1`, or `SCORE: 3` — parse with regex  
B. Use provider JSON mode / structured output to get `{"score": 1, "reasoning": "..."}` directly  
C. Ask LLM to pick from `["Não Atendido", "Parcialmente Atendido", "Atendido"]` and map internally

**What if parsing fails?** Need a defined failure mode — raise? Return score=None? Return with
uncertainty_flag=True?

### Q5 — Uncertainty flag definition

What constitutes an uncertainty flag? Options:

A. LLM explicitly says "insufficient evidence" or similar → flag set programmatically  
B. LLM is instructed to include a confidence signal in structured output  
C. Flag is set when retrieved chunks are empty or below a minimum count  

**Why it matters:** The Auditor interface shows it — needs a deterministic definition.

### Q6 — LLM provider abstraction

How do Ollama and Groq co-exist? Options:

A. Environment variable `LLM_PROVIDER=ollama|groq` selects at startup  
B. `configure_llm(provider, model, base_url)` call mirrors `configure(db_path)` in retrieval  
C. Thin wrapper protocol: `LLMClient.complete(prompt) -> str`

**ADR-0009** says single LLM call per Ação — this implies one round-trip, not streaming.

### Q7 — Context window management

How many `RetrievedChunk.text` strings can fit in a single prompt? With MAX_CHUNKS_PER_ACAO=20
and potentially multi-page chunks, the evidence section could be large.

Is there a character limit for the evidence section? Who owns the truncation decision?
(Retrieval module already bounds result count; does evaluation module further trim?)

### Q8 — Module boundaries

What does Module 4 own vs borrow?

- Module 4 owns: prompt assembly, LLM call, response parsing, `EvaluationResult` construction
- Module 4 consumes: `list[RetrievedChunk]` from Module 3, IPMP data via `get_ipmp_store()`
- Module 4 does NOT own: retrieval logic, DB access, Auditor rendering, score persistence

---

## Reference Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Full project state, strategic decisions |
| `CONTEXT.md` | Domain glossary — check before using any term |
| `data/ipmp/acao_01.json` | Ação 1 full IPMP data (criteria, examples, products) |
| `docs/adr/0004-llm-temperature-zero-evaluation.md` | temperature=0 rationale |
| `docs/adr/0005-human-in-the-loop-scoring.md` | Auditor role |
| `docs/adr/0008-action-level-scoring.md` | 0/1/3 scoring model |
| `docs/adr/0009-single-llm-call-per-action.md` | one call per Ação |
| `src/retrieval/interfaces/contracts.py` | `RetrievedChunk` model |
| `src/retrieval/__init__.py` | Module 3 public surface |

---

## How to Continue

1. Open `docs/prompts/01_grill-me.md` and follow the session protocol
2. Work through Q1–Q8 above (one at a time, waiting for feedback)
3. For each resolved decision: update `CONTEXT.md` if a new term is defined, write an ADR if all three criteria apply
4. When all questions are settled, run `docs/prompts/02_To-PRD.md` to produce the Module 4 PRD
5. Then create GitHub issues from the PRD and implement

**Next ADR number:** `0019-`
**Next DAN number:** `0003-`
