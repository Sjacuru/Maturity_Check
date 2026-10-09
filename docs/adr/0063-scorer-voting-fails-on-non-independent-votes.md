# Majority voting does not stabilise the scorer either — the votes are not independent

**Status:** rejected — implemented 2026-09-29, measured over 20 full passes, reverted the same day
**Date:** 2026-09-29
**Related:** ADR-0061 (same rejection for the gate, different mechanism), ADR-0058 (score counted from per-product verdicts)

`_SCORER_VOTES` stays 1. Repeating the scorer call and taking a per-product
majority moved modal agreement not at all and cost up to 45% more wall time.

## The scorer is non-deterministic — that part was worth establishing

Every earlier probe in this investigation measured the gate. This was the first
measurement of the scorer in isolation, and it needed two attempts.

The first attempt froze one accepted-evidence set and scored it 8 times: 8 of 8
identical, for two different Ações. That looked like proof the scorer was
deterministic, and it was wrong as a conclusion — it had frozen whichever set
`_retrieve_and_select()` happened to return, and it issued the 8 calls
back-to-back.

The second attempt captured a digest of the `(system, user)` pair at the client
itself, wrapping `complete()` so the digest included `_cap_evidence()` truncation
and per-product block assembly, then ran 10 complete passes per Ação:

| | prompt seen repeatedly | outcomes from it |
|---|---|---|
| Ação 3 | `737879181830`, 7 times | `score=3` ×6, `score=0` ×1 |
| Ação 14 | `245424972cc2`, 2 times | `score=0`, `score=1` |
| Ação 14 | `395593dbfd32`, 3 times | `score=1`, `score=1`, `score=0` |

Byte-identical prompt, different verdict. Same engine-level behaviour already
documented for the gate on 2026-08-27: stable when a prompt is repeated
immediately, unstable when the same prompt is interleaved with other traffic.

An earlier framing in this session — that the gate had been stabilised and "the
bottleneck moved to the scorer" — rested on an evidence signature of sorted
`(filename, page, chunk_index)`. That omits `chunk.expected_product_ids`, which
decides the product block a chunk lands in, so two passes could share the
signature and still send different prompts. Corrected here.

## Why voting fails, and why the reason differs from ADR-0061

ADR-0061 rejected gate voting because the flipping chunks sat at q≈0.70–0.80,
where best-of-3 lifts agreement very little. The prior expectation here was
better: the scorer's flipping prompt sat at 6/7 ≈ 0.86, where `q³+3q²(1−q)`
predicts ~0.95, and the scorer is one call per Ação against roughly twenty gate
calls, so tripling it costs ~92 extra calls on a full sweep rather than ~2,000.

The prediction failed, and the measurement says why:

| | 1 voto | 3 votos |
|---|---|---|
| Ação 3, modal agreement | 90% | **90%** |
| Ação 3, seconds per pass | 41.9 | 60.6 (**+45%**) |
| Ação 14, modal agreement | 50% | **40%** |
| Ação 14, seconds per pass | 75.0 | 80.2 (+7%) |
| passes whose votes split | — | **2/10 (Ação 3), 0/10 (Ação 14)** |

That last row is the finding. **The votes are not independent samples.** They are
issued back-to-back on a byte-identical prompt, which is exactly the condition
under which this engine reproduces itself — the first attempt above measured 8 of
8 identical under it. So the three votes arrive as near-copies, agreeing with
each other in 8 of 10 passes on Ação 3 and in all 10 on Ação 14, and a majority
over near-copies cannot reduce variance. The flip happens *between* passes, not
within one.

There is no configuration that escapes this. Making the votes independent would
mean interleaving other traffic between them, and that interleaving is the very
condition that produces the divergence. Independent-and-individually-stable
samples are not available from this server.

## Consequences

- `_SCORER_VOTES = 1` in `evaluation/evaluator.py`. Raising it is the whole of
  re-running the experiment.
- `combine_votes()` in `evaluation/parsing/response.py` and its tests stay in the
  tree, unwired at that one line, with a `monkeypatch`ed test keeping the path
  exercised — the same treatment the unwired provider fallback gets under
  ADR-0059.
- `EvaluationResult.n_scorer_votes` and `n_verdict_splits` stay, defaulted. They
  cost nothing, need no migration (the read path is `json.loads(raw_json)`,
  ADR-0031), and a split is real auditor information whenever voting is on.
- **Where the instability actually is, per Ação.** Ação 3 reaches 90% modal
  agreement already, with or without voting, and its gate now yields few
  distinct evidence sets. Ação 14 sits at 40–50% and produced 5–7 *distinct
  prompts* in 10 passes, three of them with no accepted evidence at all: its
  variance is overwhelmingly the gate's evidence set, not the scorer's judgement.
  The next lever belongs upstream, on how the gate's accepted set varies between
  passes — not on repeating a call whose repetitions agree with each other.
