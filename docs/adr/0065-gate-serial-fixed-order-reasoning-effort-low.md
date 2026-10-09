# The relevance gate runs one call at a time, in a fixed order, with gpt-oss at reasoning_effort=low

**Status:** accepted — measured 2026-10-02/03 on the project's own GPU server; outcome-level sweep R12 (2026-10-03): 29.7 min vs 41.0, 0 errors, accepted chunks 124 → 99
**Date:** 2026-10-03
**Supersedes:** the concurrency paragraph of ADR-0050's 2026-06-29 amendment (per-product gating in a `ThreadPoolExecutor`) for the GPU server; the thread pool stays in the code behind `GATE_MAX_IN_FLIGHT > 1`

The gate client is wired with `max_concurrent_requests=1` and
`reasoning_effort="low"` (`main.py`), and `select_evidence()` gates the products
one after the other in scored-product order, each product's candidates in RRF
rank order (`GATE_MAX_IN_FLIGHT = 1` in `evidence_selection.py`). The scorer is
untouched: it keeps the model default (medium) and its own client.

## Why

After ADR-0058–0064, retrieval was byte-identical across passes (164/164 products
× 5 stages × 3 passes), the gate prompt had its sibling contrast, and every
remaining run-to-run score change traced back to the same thing: the same gate
prompt getting different verdicts on different passes. The condition grid on
Ação 14 (40 (product, chunk) pairs × 8 passes each, production prompts, the
user's own server) and the follow-ups on the two Ações with genuine evidence:

| condition | Ação 14 | notes |
|---|---|---|
| 4 in flight, medium (production until now) | 2/40 oscillate, up to **8 distinct reasoning trajectories in 8 passes** for one prompt | |
| 1 in flight, medium | 3/40 | |
| 1 in flight, medium, prompt cache off | 2/40, exactly 2 states alternating by pass parity | server internal — not used |
| 4 in flight, prompt cache off | 3/40, 40/40 chunks with 4+ trajectories | the worst cell |
| 4 in flight, low | 3/40 | |
| **1 in flight, low, prompt cache off** | **0/40**, 39/40 single-state | |
| **1 in flight, low, cache default (this ADR)** | **0/40** (6 passes) | Ação 22: **0/32**, true positives p.774 (risk matrix) and p.921 (insurance) kept; Ação 3: 0/8 |

Two things carry the result. Concurrency: with several requests sharing the
server's slots, the batch composition differs on every pass, and gpt-oss's
reasoning channel amplifies any numerical difference into a different
trajectory. Reasoning length: at `low` the completion is ~2.5× shorter (median
54–59 tokens vs 128–210 at medium), so there is far less room for a borderline
trajectory to wander off — and the accepting trajectories were the long ones
(ADR-0064). Low did not lose a single measured true positive.

`reasoning_effort` is a model setting carried through the chat template
(`chat_template_kwargs`), not a server internal; `cache_prompt`, `id_slot` and
slot pinning are server internals and stay out of production and diagnostics
(CLAUDE.md Decision 6).

## Cost

A serial gate at low costs LESS than the 4-concurrent gate at medium did:
0.7–1.0 s per call in the production path (Ação 22, 40 calls, 35–57 s per
Ação), and the full 46-Ação sweep went from 41.0 min (R11, 4 in flight, medium)
to **29.7 min (R12, 2026-10-03, 0 errors)**. Low is also stricter: accepted
chunks 124 → 99, and six Ações whose only accepts at medium were one to four
borderline chunks (8, 9, 14, 20, 28, 40) now report no evidence.

## What it does not remove

- A few chunks remain order/state-dependent in the production path even though
  they are stable in isolation: Ação 3's p.161 (accepted in 1 of 2 production
  runs; `FFFF` isolated) and Ação 22's p.145 for 22.1 (accepted in 2 of 3
  production runs; `FFFFFF` isolated ×6 through the same client). The verdict
  of a borderline chunk depends on what the server computed just before it.
  This residue is what the gate verdict ledger (planned ADR-0067) freezes by
  construction, and what the canonical profile fixes shrink (3a, 14e).
- Ação 22's p.774 is absent from the final evidence although the gate accepts
  it `TTTTTT`: it is the same risk matrix as p.193 (`SMG-040_..._1.pdf`;
  document `_2` duplicates it; rapidfuzz ratio 88.0 after normalisation), p.193
  ranks #1 for 22.2 and the post-gate semantic dedup (threshold 0.70) keeps the
  first copy. The scorer sees the matrix once, via p.193. Not a defect — but a
  pair between 0.70 and the pre-gate threshold 0.92 costs two gate calls to
  keep one chunk.

## Consequences

- `GATE_MAX_IN_FLIGHT` is the single knob: `main.py` passes it to the gate
  client's semaphore, `select_evidence()` reads it to choose the serial loop
  (fixed order) or the pool. Tests pin the default to 1 and the call order.
- `LlamaCppClient(reasoning_effort=...)` sends `chat_template_kwargs` only when
  set; the default leaves the server default, so the scorer's client is
  unchanged.
- Diagnostics that measure the gate must use the same two settings
  (`audit_gate_flips.py --in-flight 1 --reasoning-effort low`), or they measure
  an engine production no longer runs.
- The "2.4× speedup" of concurrent gating (ADR-0050 amendment) was measured on
  CPU-only Ollama; it no longer applies to this server and is not a reason to
  turn the pool back on.
