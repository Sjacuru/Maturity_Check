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

## Coverage measured over six independent processes (2026-10-10)

The six processes are full runs of the case with the ledger off: the three
A+B+C processes of ADR-0072 and the three `rotulado` processes of ADR-0071.

The A+B+C processes predate the harness recording the margin. For them the
margin was recomputed with `compute_score_margin` from the stored scorer
verdicts and delivered batches. On the other three processes the recomputation
matches the recorded margin in 137/137 Ação × process.

The measurement covers the 41 Ações that did not change between the two arms.
Counting `sem evidência` as 0, an Ação's outcome crossed a band in 19 Ação ×
arm cases.

- **In 18 of them the signal fired in at least one process.** Every time it
  fired on the Ação's highest outcome, in the process where that score hung on
  a product held by a single chunk.
- **The one miss is Ação 36 (A+B+C).** It went `sem evidência` in one process
  because product 36a lost all of the 2–5 accepts that held it in the other
  two. A margin of one cannot see a correlated drop like that.
- **Six variations are silent by design.** These are the `sem evidência` ↔ 0
  alternations, three per arm (A+B+C: 27, 40, 43; labelled: 21, 31, 33). A
  score of 0 has no evidenced product that could be fragile, and the margin
  makes no upward claim.

The signal works per process. When the lower outcome comes up in a process,
nothing in that process says the score could have been higher. Ação 4 under
the label shows this: 3, then 3 (flagged), then 1.

Signals on Ações whose outcome did not vary over three processes are not false
alarms. They mark scores that hung on one chunk that happened to hold: 15 of 93
Ação × process in A+B+C, 4 of 78 under the label. Ação 45's 3 was flagged in
all three A+B+C processes and fell to `sem evidência` in one labelled process.
Ação 24's 1 was flagged in all three and did the same.

Widening the signal is the user's decision. The data points to two levers:

1. Flag a 0 whose whole delivered batch rests on single accepts; its floor
   would then be `sem evidência`. This covers the six silent alternations, and
   only matters if `sem evidência` and 0 are to count as different outputs.
2. Add a correlated-drop check. That is not deterministic, so it is outside
   this ADR.

## The acceptance criterion read in points; the signal stays as is (2026-10-10)

The user accepted both suggestions of 2026-10-10.

- **`sem evidência` counts as 0 points for the acceptance criterion only.** The
  user's criterion — after 10 runs, 90 % of the runs give the same output — is
  read on the points an Ação earns, so `sem evidência` and score 0 are the same
  output for it. The label is kept everywhere else: the auditor still sees
  whether the gate delivered nothing or the scorer judged what it received
  insufficient (ADR-0058's distinction), and this ADR's floor still separates
  `None` from 0. Analyses report both readings, labels and points.
- **The signal is not widened.** Lever 1 above only mattered if `sem evidência`
  and 0 were different outputs; read in points they are not, so the six silent
  alternations carry no point change. Lever 2 is not deterministic. The
  correlated drop it would target (Ação 36) cannot be seen from one process's
  margin, which is the only thing this ADR reports.
