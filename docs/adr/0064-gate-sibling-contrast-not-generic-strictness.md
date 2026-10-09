# The gate prompt names the sibling products; generic strictness rules are rejected

**Status:** accepted — measured 2026-10-02 on Ações 14, 22 and 3; outcome-level sweep R11 same day (41.0 min vs 47.6, 39/46 outcomes unchanged vs R10, accepted chunks 144 → 124, 0 errors)
**Date:** 2026-10-02

The relevance gate's system prompt now lists every other scored Expected Product
of the Ação, with its IPMP text, as explicitly NOT under evaluation, and the user
prompt repeats the product id next to the chunk (`_sibling_contrast()` and
`build_relevance_user_prompt(..., product_id=)` in `relevance_builder.py`). Three
wordings that tried to make the gate stricter in general — a decision procedure,
a tiebreak rule ("em caso de dúvida, false"), and dropping/reframing the concept
list — were measured in the same session and rejected.

## What the captured reasoning showed

gpt-oss emits a reasoning channel before the schema-constrained verdict, and the
server returns it as `reasoning_content`. Reading it changes nothing about the
generation; 960 traces were captured on Ação 14 under several engine conditions.

- The abstract scope rule ("evidência que sirva a outro Produto Esperado... não
  conta") was engaged in **0.8 %** of traces. The model named the wrong sibling
  in **62 %** of them — while quoting the correct criterion text. The label
  leaks from sibling ids inside criteria ("identificado em 14a", 15 occurrences
  across the profiles) and from a lowercase letter suffix mentioned once, ~2 000
  chars before the chunk.
- Sibling criteria are not lexically alike (median `partial_ratio` 47, max 59
  over 279 pairs). The confusion is anchoring, not redundant criteria.
- The model already applies "mentions the topic ≠ contains the required
  element" in 79 % of traces, and that test rejects 495:13. **The accepting
  trajectories are the ones that abandon it** — and they are ~2× longer
  (median 1 200–2 000 chars vs 600–700; the accepting run is the longer one in
  12 of 15 same-prompt pairs). One trace accepted by quoting "Qualquer um dos
  elementos abaixo também conta" and reading the restated concept as a looser
  criterion; another by redefining "benefício" as "condição dos ativos".

## What was measured

All runs: the project's own GPU server, production configuration (4 calls in
flight, `reasoning_effort` medium, prompt cache default), N passes over every
(product, examined chunk) pair of the Ação. "Oscila" = verdict not identical
across passes.

| variant | Ação 14 (40 pairs, 8 passes) | Ação 22 (32 pairs, 6 passes) — genuine evidence |
|---|---|---|
| base | 2/40 oscillate, minority 1.9 %, 6 accepts (all false positives) | 4/32, p.774 risk matrix `TTTTTT`, p.921 `TTTTTT` |
| V1 procedure + tiebreak | 4/40, 2.8 % | — |
| V2 = V1 + drop restating concept list | 0/40, 0 % | **p.774 → `FTTFTF`**; Ação 3 loses p.161 (`TTTTTT` → `FFFFFF`) |
| V3 = V2 + sibling list | 0/40, 0 % | p.774 → `TTFTFF` |
| V4 = drop restating concept list only | 1/40, 0.3 % | unchanged by construction (touches the 23 degenerate products only) |
| **V5 = sibling list + id in user prompt** | **0/40, 0 %** | **2/32**, p.774 and p.921 `TTTTTT`, p.193 `FTTTFT` → `TTTTTT` |

V2/V3's zero on Ação 14 was partly the wrong kind of zero. "Obrigação
contratual genérica não é suficiente" is false for Dimensão Comercial products
whose evidence *is* a contract annex: it made the gate doubt the genuine 22.2
risk matrix. Generic strictness trades false positives on no-evidence Ações for
false negatives on real ones. V5 adds no strictness language; it supplies the
contrast the model was missing, and the two real-evidence Ações kept every
true positive.

## Costs

System prompt mean 1 954 → 2 417 chars (+24 %), max 3 974 → 4 489 (~1 120
tokens); reasoning +~20 % tokens on Ação 22. Single-product Ações get no list.

## What this does not do

It does not remove the engine's non-determinism: under 4 concurrent calls the
same prompt still has up to 8 distinct trajectories in 8 passes, and V5 left
2/32 oscillating chunks on Ação 22. That is the next item (serial gate +
`reasoning_effort=low`, measured 0/80 oscillations across three Ações in the
same session; see CLAUDE.md "Where to Resume"). V4 is a safe follow-up for the
23 products whose concept list restates the intent, and the reasoning study
produced two canonical profile corrections (3a: the IPMP's own Atendido example
is an itemised delineation and `o_que_esperar` includes costs; 14e: generic
periodic contract reporting ≠ reporting the progress of each benefit).

## What R11's inspection surfaced

Ação 26 went score=1 → sem_evidencia. Its only on-topic chunks — a Procuradoria
parecer stating the PPA/LDO/LOA compatibility declaration was *not* met (p.136)
and the structurer's reply that it does not apply to a concession (p.144) — are
now rejected 4/4 for 26a and 26d alike, with the same reasoning: the gate reads
"evidence for X" as evidence THAT X is satisfied. That polarity ambiguity predates
this ADR (the same chunk oscillated before); the sibling list stabilised it on the
side that hides documented non-fulfilment from the scorer and the auditor. The
candidate fix is one canonical sentence (a chunk that directly addresses the
criterion is relevant even when it attests non-fulfilment or inapplicability; the
fulfilment judgement is the scorer's) and, after V1's lesson, ships only after
measurement on 26 and on the Ações that must not move.

## Consequences

- `build_relevance_user_prompt` gained an optional `product_id`; the production
  call site passes it. Diagnostics that build gate prompts must pass it too, or
  they measure a prompt production no longer sends.
- `scripts/diagnostics/measure_gate_prompt_variants.py` keeps V1/V2/V4 as
  in-memory patches for future comparison; V3/V5 are retired there because the
  base now contains them.
- Sibling ids quoted inside criteria and the validation metadata still embedded
  in 10 `negative_evidence_patterns` (6 % of patterns, 15 % of their characters,
  with SMG-040 page references) are data defects this ADR does not fix.
