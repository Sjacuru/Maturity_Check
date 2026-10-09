# Gate verdicts are frozen in a ledger keyed by the prompt hash, and the auditor can overturn them

**Status:** accepted — implemented 2026-10-03 (`src/evaluation/gate_ledger.py`); wired in `main.py` only, switched off in the measurement harness
**Date:** 2026-10-03

The first verdict the gate model gives for a (model, reasoning effort, system
prompt, user prompt) tuple is recorded in a `gate_verdicts` table of the shared
app DB, and every later identical call is answered from that record instead of
being re-asked. The auditor can overturn a recorded verdict through
`POST /api/cases/{process}/evaluations/{acao}/gate-overrides` (justification
required); the row then answers with `source="auditor"`. Failed calls are never
recorded.

## Why a ledger, and why only now

After ADR-0058 (score counted in code), ADR-0059/0060 (no silent fallback, no
silent failure), ADR-0064 (sibling contrast) and ADR-0065 (serial gate at
`reasoning_effort=low`), what remains of the run-to-run variation is a handful
of borderline chunks whose verdict depends on what the server computed just
before them — stable in isolation (`FFFFFF`), not inside a run (Ação 3's p.161,
Ação 22's p.145). The engine settings that would remove that residue are server
internals (prompt cache, slot pinning), which this project does not use
(CLAUDE.md Decision 6), and the measured alternatives were rejected with data:
best-of-N voting (ADR-0061/0063), cache off (the worst cell of the grid), generic
strictness (ADR-0064).

The ledger removes the residue at the application layer, by construction: the
same input is answered the same way because it is not asked twice. That is the
reproducibility the project owes its reviewers (Decision 7: same input → same
score).

It comes last on purpose. The user's own condition was "depois de 1–5 reduzirem
a parte estocástica … antes disso, congelaria erros de hoje": a ledger freezes
whatever verdict comes first, right or wrong, so it is only acceptable once the
first verdict is right most of the time. Every canonical correction made before
it (3a, 14e, the sibling-id rewrites, the metadata moves, V4, P1 if adopted)
changes the prompts it affects and therefore misses the ledger for exactly those
calls — nothing stale survives a correction.

## The key

`sha256(model ␟ reasoning_effort ␟ system_prompt ␟ user_prompt)`. `model` is
the label the gate client is CONFIGURED with (`gpt-oss-20b-F16.gguf`), not the
name the server reports in its responses (`Meme-GPT`, the GGUF's metadata
name): the served name is unknown until the process's first response, so a
key built from `last_model_used` changed after the first call and the first
prompt of every process missed once and was re-asked (found 2026-10-03 in
the first live measurement, 586 rows all stamped `Meme-GPT` while their first
key had been hashed with the label; fixed the same day, `_ledger_model()`).
The row's `model` column stores the same string the key was hashed with, so
a key can be recomputed from the row and the two prompts. The system prompt
carries the Ação's identity block, the product's criterion, concepts,
negative patterns and sibling list; the user prompt carries the chunk text.
Hence:

- a profile correction re-judges the products it changes and nothing else
  (the sibling list makes a change to one product's IPMP text re-judge its
  siblings too — correct, their prompts changed);
- a prompt-builder change re-judges everything;
- a model or effort change re-judges everything;
- a re-extraction that alters a chunk's text re-judges that chunk.

The process number is deliberately not part of the key: the same criterion on
the same text is the same question in whichever case it appears, and an
auditor's override is a judgement about that content.

## What the auditor sees

`RetrievedChunk.gate_source` / `RejectedChunk.gate_source` say whether a verdict
came from the model in this run, from the ledger, or from an auditor override;
`gate_prompt_hash` is the key the override route takes; `gate_reasoning` (kept
since 2026-10-03) shows why. `ProductGateReport.n_ledger_hits` counts the calls a
product did not need to make. An override does not rewrite the stored
evaluation: it applies when the case is assessed again, and the UI says so.

## What it does not do

- It does not make the FIRST run of a new prompt deterministic; that is the
  engine's residue and the reason items 1–6 came first.
- It is off in `scripts/diagnostics/reproducibility.py`: with it on, a repeated
  run would agree with itself trivially and measure nothing about the engine.
- It does not expire. A verdict stays until its key changes or the auditor
  overturns it; the table is small (one row per distinct gate question).

## Consequences

- The evaluation module now owns one table in the shared DB (`gate_verdicts`),
  created by `GateLedger(db_path)`; ADR-0024's per-module ownership holds.
- `_gate_chunk()` takes the chunk and process number only to annotate the row;
  the key never depends on them.
- Tests pin: identical call answered without a model call, changed prompt
  re-judged, override wins, failures not recorded, no ledger → model every time,
  route 503/404/422/200.
