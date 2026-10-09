# Majority voting does not stabilise the relevance gate

**Status:** rejected — implemented 2026-09-28, measured over a full sweep, reverted 2026-09-29
**Date:** 2026-09-29

Best-of-3 voting was added to `_gate_chunk()` on the theory that repeating the
same prompt and taking the majority would absorb the gate's per-call verdict
noise. It was measured and reverted: the cost was 2.05x the gate calls (a full
46-Ação sweep went 45.8 -> 76.5 min) and the measured stability gain was zero.

## Why it fails, which is not obvious

The arithmetic that motivated it uses a single average noise rate. Two
same-condition controls had put per-call agreement at 90.9% and 94.9%, and
best-of-3 turns a minority rate p into 3p²(1−p) + p³ — a ~9.5x reduction at
p ≈ 3.6%. That reasoning is sound only if every chunk carries the same p.

It does not. For a chunk whose true accept-probability is q, best-of-3 yields
q³ + 3q²(1−q):

    q=0.50 -> 0.500     q=0.80 -> 0.896
    q=0.60 -> 0.648     q=0.90 -> 0.972
    q=0.70 -> 0.784     q=0.99 -> 1.000

**At q = 0.5 voting changes nothing** — the majority of three fair coins is a
fair coin. And the chunks that actually flip between runs are precisely the
ambiguous ones clustered near the middle, not the confident ones. Voting spends
its money on the chunks that never needed it.

## What was measured

`scripts/diagnostics/measure_run_to_run.py`, 7 Ações x 2 passes on ONE fixed
configuration, 592 chunks judged:

- **Voting worked mechanically.** 1,213 calls for 592 chunks = 2.05x, matching
  the predicted cost of stopping at a 2-0 lead.
- **The votes are not correlated.** 29 splits / 592 chunks = 4.9%, which implies
  a per-call minority rate of p ≈ 2.5% (a split needs the first two calls to
  disagree: 2p(1−p) = 0.049). An earlier hypothesis — that repeating an
  identical prompt would return an identical answer, per the 2026-08-27
  forensics where homogeneous concurrency was 0/184 — is therefore wrong.
- **And it bought nothing.** 7 evidence chunks of ~296 per pass diverged between
  the two passes = 2.4%, against the ~2.5% per-call rate it was meant to reduce.
  The 29 splits plus the 7 divergences place the ambiguous subset at q ≈ 0.7-0.8,
  exactly where the table above shows best-of-3 to be weak.

Those 7 chunks changed the accepted evidence on 5 of the 7 Ações and the outcome
on 2, because the evidence is thin — Ação 28 moved 1 -> 3 chunks, Ação 31 moved
1 -> 0. One chunk decides a score.

## Consequences

`_gate_chunk()` is one call again, and `ProductGateReport` loses `n_gate_calls`
and `n_vote_splits` (both were voting-only; defaults meant no stored row was
affected either way).

The measurement stands even though the change did not: the residual instability
is concentrated in a small set of genuinely ambiguous chunks, and no amount of
resampling a stochastic judge will settle them. Stability has to come from
removing the ambiguity (retrieval-profile work: sharper `evidence_intent`,
`negative_evidence_patterns`) or from removing the stochasticity (reusing a
verdict already decided for identical content, rather than asking again).

A methodological note this exposed, worth more than the change itself: sweep-to-
sweep agreement figures (R6->R7 84.8%, R7->R8 80.4%, R8->R9 78.3%) each straddle
a configuration change and therefore cannot measure stability at all. Only
repeated passes of ONE configuration can, which is what
`measure_run_to_run.py` exists to do.
