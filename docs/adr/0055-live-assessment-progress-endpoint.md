# Live assessment progress: polling endpoint + in-thread execution

**Status:** accepted — narrow amendment to ADR-0027's synchronous execution decision

`POST /cases/{process_number}/assess` remains fully synchronous from the client's
perspective: it still blocks until the assessment completes and returns the same
response shape as before. What changes: the server no longer blocks its own event
loop while that call runs (`_service.run_assessment()` is now invoked via
`starlette.concurrency.run_in_threadpool`), and a new
`GET /cases/{process_number}/assess/progress?since=N` endpoint exposes short,
in-memory status messages emitted from inside the pipeline while it runs. The
frontend polls this endpoint every 1.5s during the wait and renders a live status
panel: current stage, whether the system is waiting/retrying, whether it has
switched to the local LLM fallback (ADR-0054) and why, and terminal
success/error states.

## Why this is a narrow amendment, not a reversal, of ADR-0027

ADR-0027 rejected "Asynchronous (202 + polling)" specifically because of what it
would have added: a job-state table, a background task runner, and polling
complexity for what was then a single LLM call in a single-user local workflow.
None of that materialized here:

- **No job-state table.** Progress events live in an in-memory dict
  (`assessment/progress.py`), keyed by `process_number`, cleared at the start of
  each run. Nothing is persisted; a server restart mid-run simply loses the log,
  which is fine — there is no assessment to resume, since the client's `POST` is
  still the single source of truth for the outcome.
- **No background task runner.** `run_in_threadpool` moves the *same* synchronous
  call onto a worker thread so the event loop can also serve the polling `GET`
  concurrently — it does not decouple assessment execution from the request
  lifecycle. The `POST` still owns the work end-to-end and still returns the
  final result directly.
- **The demonstrated need ADR-0027 asked for now exists.** Watching a live UI
  run on 2026-08-14, the assessment sat silent for several minutes while the
  primary LLM's read-timeout retry loop played out (ADR-0054) — from the
  browser, indistinguishable from "hung." A single LLM call in a single-user
  workflow was exactly ADR-0027's justification for not building this; a
  multi-provider call chain with retries and fallback is a different situation,
  and the silence is no longer tolerable.

## What the progress events show, and what they deliberately don't

Required by the feature request driving this ADR: current stage, the
decision route the algorithm is following (document-focused shortcut vs.
BM25+vector+gate — see `_retrieve_and_select()`), which prompt/role is being
built and which provider/model is handling it, explicit fallback
notification with a reason, and error/waiting/timeout/completion states —
all as short, human-readable Portuguese messages.

**Never included in an event message:** prompt content (system/user prompt
text), retrieved evidence text, API keys, or any other credential. Messages
are hand-written short templates (e.g. `"Chamando avaliador (Ação {id}) —
{provider}/{model}..."`), never an interpolated exception message or raw
response body — the one exception is the final orchestration-level error
event, which includes `str(exc)`, but that is the *type of failure* (e.g. "no
document_paths provided"), not response content, since exceptions raised in
this codepath are deliberately constructed with short, non-sensitive
messages.

## Emission mechanism: a global reporter, not a contextvar

`evaluation/progress.py` defines a module-level `report(stage, message,
level)` that calls into a single registered callback, set once per
`AssessmentService.run_assessment()` call and cleared in a `finally`. This is
a plain global, not a `contextvars.ContextVar`, because Phase 1 (ADR-0027)
runs exactly one assessment at a time — a contextvar would be the correct
choice under concurrent assessments, but would not even work correctly here
without extra propagation work: `evidence_selection.py`'s per-product
`ThreadPoolExecutor` workers do not automatically inherit a contextvar set by
the submitting thread (only asyncio's own executor integration does that
automatically; plain `concurrent.futures.ThreadPoolExecutor.submit()` does
not). A global avoids the problem entirely, correctly, for the current scope.
Revisit if concurrent assessments are ever supported.

## Considered options

- **Server-Sent Events / WebSocket push** — rejected: polling is simpler to
  reason about and test, degrades gracefully (a missed poll just shows slightly
  stale status, not a broken connection state machine), and 1.5s latency is
  fine for a process that itself takes minutes.
- **Persist progress events to SQLite** — rejected: nothing downstream needs
  them after the run completes (the final `EvaluationResult` is the record of
  truth); persisting would add a table and a cleanup policy for no benefit.
- **Per-candidate gate progress (one event per chunk gated)** — rejected: a
  single Ação examines dozens of candidates across products concurrently;
  per-candidate events would flood the panel. Product-level start/end summaries
  plus LLM-client-level retry/fallback events (the actual source of long
  silences) give real-time visibility without the noise.
- **contextvars-based reporter** — rejected for now; see mechanism section above.

## Consequences

- New `src/evaluation/progress.py` (generic `report()`, no `assessment` import)
  and `src/assessment/progress.py` (per-process_number event store + a
  `make_reporter()` bound closure).
- `evaluation/llm/llamacpp.py`, `evaluation/llm/fallback.py`,
  `evaluation/evaluator.py`, `evaluation/evidence_selection.py`, and
  `assessment/service.py` all call `report()`/`progress.emit()` at their
  respective decision points.
- `assessment/api/routes.py`: `/assess` now awaits
  `run_in_threadpool(_service.run_assessment, ...)`; new
  `GET /assess/progress` route.
- `AssessmentService.run_assessment()` is now a thin wrapper (`start_run` +
  bind reporter + call `_run_assessment` + emit a final `erro` event on any
  exception + always clear the reporter) around the previous method body,
  renamed `_run_assessment`.
- `frontend/src/views/UploadView.vue`: polls progress while `loading`, renders
  a live status panel (current stage, elapsed-since-last-update ticker, a
  persistent fallback banner, and a scrollable event log) instead of a bare
  spinner.
