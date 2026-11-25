from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment.api.app import create_app
from evaluation import (
    GATE_MAX_IN_FLIGHT,
    GateLedger,
    configure_gate_ledger,
    configure_gate_llm_client,
    configure_llm_client,
)
from evaluation.llm.llamacpp import LlamaCppClient
from retrieval import configure as retrieval_configure
from retrieval.schema.ddl import init_db as retrieval_init_db

_DB_PATH = Path("data") / "app.db"

# The user's personal llama.cpp server, hosted outside the corporate network,
# serves BOTH the scorer and the gate. It is the ONLY provider — see
# _bootstrap() for why the ADR-0054 fallback was removed.
# The default is the SSH tunnel on the client (local port 18083 to the
# server's port 8083, opened over port 443): the server's port 8080 serves
# another service and is blocked on the client network (2026-10-10).
# LLAMACPP_BASE_URL (environment or .env) overrides the address; the provider
# never changes (ADR-0059).
_LLAMACPP_BASE_URL = os.environ.get(
    "LLAMACPP_BASE_URL", "http://127.0.0.1:18083"
).rstrip("/")
_LLAMACPP_MODEL = "gpt-oss-20b-F16.gguf"
# gpt-oss reasoning level for the relevance gate only (ADR-0065); the scorer
# keeps the model default.
_GATE_REASONING_EFFORT = "low"


def _bootstrap() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    retrieval_configure(_DB_PATH)
    retrieval_init_db(_DB_PATH)

    assessment_configure(_DB_PATH)
    assessment_init_db(_DB_PATH)

    # ─────────────────────────────────────────────────────────────────────
    # LLM wiring: the personal GPU server ONLY, fail-fast, no fallback.
    #
    # ADR-0054 wired a FallbackLLMClient circuit breaker here: Groq
    # (openai/gpt-oss-20b) behind the scorer, local Ollama (qwen2.5:7b) behind
    # the gate, with a 10s cooldown. That wiring was REMOVED 2026-09-27, for
    # two reasons found in the reproducibility diagnosis:
    #
    #   1. It substituted a different model silently. A single timeout put the
    #      primary in cooldown, and the next gate calls — up to 9 products
    #      gated concurrently — were answered by qwen2.5:7b instead of
    #      gpt-oss-20b. Nothing recorded which model decided what:
    #      RejectedChunk had no provider field and EvaluationResult.provider is
    #      the SCORER's. Two models with different strictness produce different
    #      accepted sets, which is indistinguishable from GPU non-determinism
    #      in the stored audit trail. The 2026-08-27 gate forensics (704 calls)
    #      deliberately bypassed FallbackLLMClient and so never measured this
    #      path at all, even though production always takes it.
    #   2. The fallback path is far slower and costlier than the GPU, so a run
    #      that silently degrades into it takes many hours.
    #
    # Decision: the GPU is the only provider. If it is down, nothing runs and
    # the failure is explicit. The fallback, Groq and Ollama clients were kept
    # unwired until 2026-11-15 and then deleted at the owner's request (both
    # providers had proved inefficient); ADR-0054 and git history record them.
    #
    # Both roles share one server, so both get their own client instance: the
    # gate needs a tighter token cap and a longer read timeout than the scorer.
    # ─────────────────────────────────────────────────────────────────────

    scorer_client = LlamaCppClient(_LLAMACPP_BASE_URL, _LLAMACPP_MODEL)
    configure_llm_client(
        scorer_client, provider="llamacpp", model=_LLAMACPP_MODEL
    )

    # read_timeout=120s, single attempt: empirically the only value tested
    # 2026-08-14 that produced zero timeouts on the reference case (15s and 45s
    # were ruled out). max_tokens=768 is a second, independent guardrail from
    # the same day: token-usage logging caught a gate call whose final answer
    # was 19 chars but which generated 7685 completion tokens of hidden
    # reasoning (~55s at this server's ~140 tok/s).
    #
    # Those two guardrails interact badly. gpt-oss emits the schema-constrained
    # JSON on a final channel AFTER an unconstrained reasoning channel, so a cap
    # that fires mid-reasoning returns empty content — which used to become
    # relevant=False, a silent rejection. Since 2026-09-27 LlamaCppClient raises
    # LlamaCppTruncated on finish_reason="length" and the gate counts it as a
    # FAILURE, not a rejection (ADR-0060), which is what made the cap's real cost
    # visible: the first instrumented run caught a gate call burning all 768
    # tokens on reasoning and emitting zero content characters.
    #
    # 768 -> 2048 -> 8192 (both steps 2026-09-28), sized from measurement.
    #
    # A cap is a ceiling, not an allocation: across 216 real gate calls the
    # median spends 180 tokens and p90 is 292
    # (scripts/diagnostics/measure_degenerate_chunks.py), so raising it costs
    # nothing on the calls that already finish. Only the pathological ones
    # behave differently — and today those are discarded unjudged (ADR-0060),
    # which varies the evidence set between runs and so varies the score.
    #
    # 2048 was not enough. The one deterministically truncating prompt
    # (Ação 40 / 40d, a 122-char orphaned clause left after
    # strip_extraction_noise) burns the cap whatever it is set to, until it
    # has room to finish: 2048 -> truncated, 4096 -> truncated, 8192 -> stop
    # with a correct False (scripts/diagnostics/inspect_truncating_gate_prompt.py).
    # It is deliberation, not a loop. Note the generation length for that one
    # identical prompt at temperature=0 has been measured at 1675, 1893, 4745
    # and 7871 tokens — a 4.7x spread, the same non-determinism documented
    # 2026-08-27, which is why the headroom is deliberately generous.
    #
    # read_timeout 120 -> 240s, and this is not optional: production gates 4
    # products concurrently, and under that contention per-slot throughput
    # drops from ~138 to ~75 tok/s (measured). 8192 tokens at 75 tok/s is
    # ~109s, which would have sailed straight past a 120s read timeout — the
    # cap would have stopped truncating calls only to start timing them out.
    #
    # REJECTED alternative 1: chat_template_kwargs={"reasoning_effort": "low"}.
    # This build honours it and it is dramatically cheaper (median 276 -> 64
    # tokens, max 80), but it is NOT verdict-neutral: measured against a
    # same-condition control run, agreement with the production gate was 54.5%
    # vs a 90.9% noise floor, with Ação 40/40a flipping False -> True on 8 of 8
    # prompts. It buys latency by making the gate systematically more
    # permissive, which is the opposite of what this work is for.
    #
    # REJECTED alternative 2: adding a "reasoning" field to GATE_SCHEMA, on the
    # theory that a declared place for reasoning would pull it out of gpt-oss's
    # unconstrained channel. Measured on the 40 real prompts from the products
    # that failed in Runs 1 and 2
    # (scripts/diagnostics/measure_gate_reasoning_field.py): truncation was
    # unchanged (1/40, the same prompt), median cost rose 180 -> 254 tokens
    # (+41% on every call), and verdict agreement was 92.3% against a 94.9%
    # same-condition control. It writes to both channels rather than moving
    # between them.
    #
    # max_timeout_retries 1 -> 2 (2026-09-28). A read timeout is deliberately
    # not caught by _gate_chunk — with no fallback wired, a transport failure
    # must abort loudly (ADR-0060) — so with a single attempt one transient
    # stall aborts the whole Ação and the service records it as failed. That
    # silently turns a scored Ação into an unscored one, which is an outcome
    # flip between runs in its own right: measure_gate_concurrency.py's first
    # attempt died exactly this way on Ação 31, on a server whose four slots
    # were confirmed idle immediately afterwards. The two causes behind a
    # timeout are not distinguishable client-side (see LlamaCppTimeout), and a
    # retry is cheap insurance either way — a dropped connection recovers, a
    # genuine runaway fails as before, 243s later. It costs nothing on a run
    # with no stalls (Run 3 had zero), so the sweep's normal duration is
    # unchanged. Worst case per pathological call becomes 240 + 3 + 240s.
    #
    # DEFERRED alternative, stronger but slower: majority-of-3 gate voting. Two
    # same-condition controls put per-call agreement at 90.9% and 94.9%, i.e. a
    # ~3.6% minority rate per call, which best-of-3 would cut ~9.5x to ~0.38%.
    # It triples gate calls (~45min -> ~2h15 per sweep), so it is held until the
    # changes that cost no sweep time are exhausted.
    #
    # NOT the cause, measured and excluded: request concurrency. The gate's pool
    # is `max_workers=len(candidates)` (9 for Ação 31), but complete() acquires a
    # semaphore of max_concurrent_requests=4, so the server never sees more than
    # 4 in flight and the pool's width above 4 is inert. Dropping in-flight calls
    # from 4 to 3 over Ações 31/35/15/25, two passes each, changed neither the
    # noise (21 vs 20 divergent chunks) nor the wall time (845 vs 843s) —
    # scripts/diagnostics/measure_gate_concurrency.py.
    #
    # 2026-10-02/03, ADR-0065 — the two settings that actually removed the
    # verdict noise, measured on the same server with the production prompts:
    # ONE call in flight (GATE_MAX_IN_FLIGHT, which also fixes the call order)
    # and the gate model at reasoning_effort=low. Grid on Ação 14 (40 chunks x
    # 8 passes): 4-in-flight/medium 2 unstable chunks, 1-in-flight/medium 3,
    # 1-in-flight/low 0; Ação 22 at 1-in-flight/low 0/32 with the genuine risk
    # matrix (p.774) and insurance clauses (p.921) still accepted; Ação 3 0/8.
    # Low also cuts completion tokens ~2.5x (median 54 vs 136-210), so the
    # serial gate costs about what the 4-concurrent one did. The scorer keeps
    # the model default (medium): its judgement is the nuanced one and it was
    # not measured at low.
    gate_client = LlamaCppClient(
        _LLAMACPP_BASE_URL, _LLAMACPP_MODEL,
        read_timeout=240.0, max_timeout_retries=2, max_tokens=8192,
        max_concurrent_requests=GATE_MAX_IN_FLIGHT,
        reasoning_effort=_GATE_REASONING_EFFORT,
    )
    configure_gate_llm_client(gate_client)
    # Gate verdict ledger (ADR-0067): the first verdict for a (model, effort,
    # system prompt, user prompt) tuple is frozen in the shared DB and answers
    # every later identical call; the auditor can overturn it through
    # POST .../gate-overrides. Measurement runs (reproducibility.py) switch it
    # off, otherwise a repeated run would agree with itself by construction.
    configure_gate_ledger(GateLedger(_DB_PATH))


_bootstrap()
app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
