# The score carries a deterministic margin, computed in code and never shown to the scorer

**Status:** accepted — implemented 2026-10-05 (`src/evaluation/margin.py`)
**Date:** 2026-10-05
**Related:** ADR-0058 (score counted in code), ADR-0061/0063 (voting rejected), ADR-0067 (gate ledger)

Beside the counted score, every evaluation now reports how far that score sits
from a different one: how many accepted chunks hold each product's `evidenced`
bit (`ProductMargin`), how many bits must flip to leave the 0/1/3 band
(`band_margin`), and the resulting interval `[score_floor, score_ceiling]`.
All of it is arithmetic over data the pipeline already has — no model call, no
extra latency — so the same input yields the same score *and* the same margin.
Nothing computed here is fed back to the scorer.

## Why distance to a band change, rather than a flip count

Two independent cold runs of the same frozen configuration showed that the flip
count is the wrong metric. Verdicts were 96.3 % stable, but the stability was
concentrated in the rejections: `P(unstable | REJECTED)` = 1.7 % against
`P(unstable | ACCEPTED)` = 38.5 %, a 23× risk ratio, with only 48 % of the 173
ever-accepted chunks accepted by both runs. That propagated to the product bit
in 151/164 products (92.1 %) — and **8 of the 13 bit flips came from products
held by a single accept**. The 0/1/3 band then absorbed 5 of the 11 Ações whose
evidenced-product set differed.

So the question an auditor needs answered is not "how many verdicts moved" but
"how close is this score to a different one", and that is computable exactly.

## Why in code, and not as a model confidence

The alternative on the table was a per-verdict confidence from the gate model,
which needs either a prompt change or extra calls, and would itself be a sampled
quantity — the same instability it is meant to describe. The margin is instead a
property of the evidence set: deterministic, free, and auditable from the stored
row.

## Why the margin is not given to the scorer

This was the first proposal and it is deliberately rejected. ADR-0058 removed the
count from the model's judgement on purpose; a margin field would put a form of
it back. It would also change every scorer prompt byte, unfreezing the
configuration and invalidating the measurements taken against it — and the scorer
is itself the other residue source (9 score changes in 98 byte-identical cells).

## Definitions that are load-bearing

- **`fragile` at exactly one accept.** The only count for which the implication
  is deterministic: with that chunk gone, `build_user_prompt` emits an empty
  block and the header instruction defines an empty block as NOT evidenced. At
  two accepts, losing one is the scorer's call.
- **No upward claim.** `score_ceiling` is the proposed score. A product gaining
  an accept on a later pass could raise the score, but that depends on the
  scorer and is not calculable here.
- **`score_floor = None` is not `0`.** When no accepted chunk would remain the
  Ação comes out `sem evidência`, a different outcome from score 0, and must not
  be reported as one. The floor is therefore computed by *simulating the removal*
  of the chunks that are the sole support of a fragile product and recounting —
  not by subtracting a number, since `_deduplicate_across_products` merges
  attributions and one chunk may carry several bits.
- **The rubric has one implementation.** `score_for_counts()` in
  `parsing/response.py` is read by both `_score_from_verdicts` and the margin, so
  the margin cannot disagree with the score it qualifies.

## Consequences

`EvaluationResult.score_margin` is defaulted to `None`: the read path is
`json.loads(raw_json)` (ADR-0031) and does not re-validate, so rows persisted
before this ADR keep being served unchanged.

The auditor review this enables is **optional** — the interface signals the case
and explains what happened in the system's process, and the auditor decides
whether to touch the scorer's result. It is not an action on the gate.

Measured against the real cycle-1 data (read-only, no GPU): 4 Ações flagged
(23, 28, 32, 45), all inside the 12 that fell below 90 % modal agreement over 10
runs, none outside it. Recall is 4/12 by construction — the 8 missed are either
scorer-side flips on byte-identical prompts or Ações with zero evidenced bits,
where the movement is a new accept appearing, i.e. the upward side this ADR
declines to claim.
