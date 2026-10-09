# A full 46-action run is the working unit, not a 3-4 action batch

**Status:** accepted — supersedes ADR-0051
**Date:** 2026-09-29

A whole-case assessment runs all 46 Ações in one go. ADR-0051 forbade that on
latency grounds; every number it rested on has since been replaced by a
measurement from the GPU server, and the constraint no longer exists.

## What changed

ADR-0051 was written against CPU-only hardware with an unusable GPU, a
`qwen2.5:7b` gate on Ollama, and a measured ~20.6 min for a single Ação. Its
central figure — ~15.8 hours extrapolated for 46 Ações — was an extrapolation,
never an observation.

The full run is now measured, repeatedly, end to end:

| run | configuration | 46 Ações |
|-----|---------------|----------|
| R6  | evidence cap 40k          | 44.0 min |
| R7  | gate cap 8192             | 44.8 min |
| R8  | gate retries 2            | 45.8 min |
| R9  | best-of-3 voting (reverted, ADR-0061) | 76.5 min |

ADR-0051 records the project owner's own ceiling as 60-90 minutes for the entire
46-action set. At ~45 min the requirement is met with room to spare — and met
even by the voting configuration that was rejected for other reasons.

Two further measurements close the option space that ADR-0051 left open:

- **The GPU is not slot-bound.** Dropping concurrent gate calls from 4 to 3
  changed wall time not at all (845s vs 843s); dropping from 4 to 1 costs ~41%
  (356s vs ~503s per pass over four Ações), which extrapolates to ~65 min for a
  full sweep — still inside the stated budget. So even fully serialised gating,
  if it were ever wanted for stability, stays affordable.
- **Latency is no longer the binding constraint on gate design.** ADR-0051's
  standing instruction was to evaluate any gate change against an
  interactive small-batch budget. The binding constraint today is run-to-run
  reproducibility, not wall time: ADR-0061 rejected a change that was affordable
  in time and useless for stability.

## Consequences

- `AssessmentService.run_assessment()` already iterates the whole IPMP store
  (ADR-0030) and needs no change; what changes is that doing so is now the
  intended behaviour rather than something to be avoided.
- The bounded action-batch parameter ADR-0051 asked the assessment API to grow
  is not needed. If one is ever added it should be for auditor convenience
  (re-running a single Ação after editing its retrieval profile), not as a
  latency guard.
- ADR-0051's non-latency findings stay valid and are not revisited here: a
  354M-parameter gate model (`LiquidAI/LFM2.5-350M`) accepted everything
  regardless of content, and per-product parallelism gives a bounded speedup.
  Both are recorded in ADR-0050's amendment.
- Gate changes should still be measured, but against reproducibility first and
  wall time second. A change that doubles gate calls is now a question about
  what it buys, not a question about whether the run finishes.
