# Interactive assessments process actions incrementally, not all 46 at once

**Status:** accepted — direct consequence of ADR-0050's 2026-06-29 latency amendment

A full 46-action assessment is not attempted as a single interactive request. Actions are assessed one at a time today (Phase 1 scope is already Ação 1 only — CLAUDE.md decision 8), and the system is expected to support a small batch (3-4 actions) per interactive sitting once Phase 1 expands, but never the full 46 in one run.

## Why this needs its own ADR

This is a scope/usage-pattern decision, not a gate-implementation detail — it constrains how the system is meant to be operated once it grows past Ação 1, and a future reader encountering a batch-size limit (or the absence of a "run everything" endpoint) would have no way to know it was a deliberate, measured decision rather than an oversight.

## Decision

**Confirmed usage pattern:** interactive — an auditor uploads documents and waits for results in one sitting (established directly with the project owner, 2026-06-29), not an overnight/batch job. This was the binding constraint the latency investigation (ADR-0050 amendment) was measured against.

**The math that drove this:** even after the full set of latency fixes in ADR-0050's amendment (examine-cap, dropped cleaning, per-product parallelism, and the `qwen2.5:7b` model swap), a single Ação 1 assessment takes ~20.6 minutes on the reference hardware (CPU-only, 6-core/12-thread, no GPU). Extrapolated to 46 actions: ~15.8 hours — roughly 10-16x over any reasonable interactive-session budget (the project owner's stated ceiling was 60-90 minutes for the *entire* 46-action set). No further low-cost lever closes a gap of that size:
- A smaller/faster local model (`LiquidAI/LFM2.5-350M`, 354M params, 3-5s/call) was tested directly and rejected — it answered "relevant" to every test case regardless of content, including cases that should have been rejected, even with few-shot examples added. Not a viable accuracy/speed trade at this size for this task.
- The hardware has no usable GPU (only an integrated Intel UHD 630 behind what appears to be a remote-display adapter) — ruled out via direct inspection, not assumed.
- Parallelism across products (already implemented) gives a real but bounded 2.4-7.3x speedup on 6 cores — nowhere near the 10-16x still needed.

**Resolution:** scope the unit of interactive work to what the corrected latency figure can actually support in one sitting — today, one Ação; once Phase 1 expands, a small batch (3-4 actions, ≈60-90 min at the measured per-Ação rate) — rather than force the full 46-action set into a single request and either blow through the latency budget or degrade gate quality further to chase an unrealistic target.

## Consequences

- No API or architectural change is required *today* — Phase 1 scope is already Ação 1 only (CLAUDE.md decision 8), so the system already operates within this constraint by construction.
- When Phase 1 expands beyond Ação 1, the assessment API (`POST /cases/{process_number}/assess`) should be designed (or explicitly re-evaluated) around a bounded action-batch parameter rather than an implicit "assess everything in scope" behavior, to keep any single request inside the measured per-batch latency budget.
- This is a standing constraint on future model/architecture choices for the relevance gate too: any future change to the gate (model swap, prompt redesign, etc.) should be evaluated against the same "interactive, small-batch" latency budget established here, not just per-call or per-Ação cost in isolation.
- Revisit this ADR if either: (a) the hardware changes (GPU becomes available, or deployment moves to better-provisioned infrastructure), or (b) the usage pattern itself changes (e.g., batch/overnight processing becomes acceptable), since both would reopen options that are closed today (see ADR-0050's amendment for the options considered and ruled out: smaller models, non-LLM pre-filtering, fine-tuning).

## Considered options

- **Force all 46 actions into one request regardless of latency** — rejected: ~15.8 hours is not an interactive experience by any reasonable definition; would effectively make the system unusable for its stated purpose.
- **Chase further latency reduction (non-LLM pre-filter, fine-tuned small model) before accepting any scope constraint** — deferred, not rejected: both remain open future directions (see ADR-0050's amendment), but neither is a same-session fix, and the project still needs a usable interactive workflow in the meantime.
- **Switch to batch/overnight processing as the primary usage pattern** — rejected: the project owner explicitly confirmed interactive, one-sitting usage is the real requirement; redesigning around batch processing would solve a different problem than the one stated.
