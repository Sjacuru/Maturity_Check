# A failed gate call is recorded as a failure, never as a rejection

**Status:** accepted

A relevance-gate call that breaks — truncated at `max_tokens`, unparseable JSON,
or refused by the server — no longer produces an indistinguishable
"not relevant" outcome. `RelevanceVerdict` carries a `failure_reason`
(`'parse' | 'truncated' | 'transport'`), `RejectedChunk` carries `gate_failed`,
`gate_failure_reason`, `gate_provider` and `gate_model`, and a new
`ProductGateReport` per Expected Product counts `n_candidates` / `n_examined` /
`n_accepted` / `n_rejected` / `n_gate_failures` separately. `LlamaCppClient`
raises `LlamaCppTruncated` when the server reports `finish_reason == "length"`
instead of returning the partial body.

## Why

This is the most likely single cause of the run-to-run score flipping. A gate
failure and a substantive rejection had identical effects: the chunk was dropped
and nothing anywhere recorded why. A failure rate that varies between runs —
which is what a token-limit or concurrency-related failure looks like — therefore
varies the evidence set, which varies the score, with no visible signal at all.
The 2026-08-27 forensics attributed borderline flips to content ambiguity under
concurrency; that conclusion could not have distinguished a broken call from a
confident rejection, because the data to tell them apart did not exist.

Truncation specifically is invisible without checking `finish_reason`: the
server returns HTTP 200 and a body, and a partial JSON object either fails to
parse (looks like a bad model) or — worse — parses into something wrong.

`LlamaCppTruncated` is deliberately **not** in `_PRIMARY_FAILURES`: it is a
prompt-sizing problem, not an availability problem, so it must not trigger a
provider switch (see ADR-0059).

## Transport failures deliberately propagate

`_gate_chunk` catches truncation and parse errors and records them, but does
**not** catch `LlamaCppUnavailable`/`Timeout`/`Busy`. Those abort the assessment
(ADR-0059). Swallowing them would let a GPU outage part-way through a run
produce a complete-looking result built on a handful of surviving chunks — the
exact failure mode this ADR exists to eliminate, in its worst form.

## Considered options

- **Retry a failed gate call** — rejected for now: it hides a systematic problem
  (a prompt that always truncates will always truncate) behind extra latency, and
  the instrumentation has to exist first to tell whether failures are systematic
  or sporadic. Revisit once measured.
- **Count failures as rejections but log them** — rejected: logs are not part of
  the auditor's seven review elements, and a score whose evidence set depends on
  a number not shown on screen is not reviewable.
- **Raise the gate's `max_tokens` pre-emptively** — rejected as a blind fix:
  without the `finish_reason` counter there is no evidence truncation is
  happening, and a larger cap costs latency on every one of the ~40 calls per
  Ação. Gated on measurement instead.

## Consequences

- `EvaluationResult.product_gate_reports` is populated per run; the auditor UI
  shows a per-product table and warns when `n_gate_failures > 0`, stating the
  score may be understated.
- `select_evidence()` logs a warning naming the total failure count.
- New `tests/test_gate_telemetry.py`; `tests/test_llamacpp_client.py` extended
  with `finish_reason`/`health_check` coverage.
