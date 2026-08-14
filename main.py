from __future__ import annotations

from pathlib import Path

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment.api.app import create_app
from evaluation import configure_gate_llm_client, configure_llm_client
from evaluation.llm.fallback import FallbackLLMClient
from evaluation.llm.groq import GroqClient
from evaluation.llm.llamacpp import LlamaCppClient
from evaluation.llm.ollama import OllamaClient
from retrieval import configure as retrieval_configure
from retrieval.schema.ddl import init_db as retrieval_init_db

_DB_PATH = Path("data") / "app.db"

# ADR-0054: the user's personal llama.cpp server, hosted outside the
# corporate network, is primary for BOTH the scorer and the gate.
# FallbackLLMClient's circuit breaker falls back to whatever previously
# served each role alone (Groq for scoring, local Ollama for the gate) on
# connection failure/timeout/busy, then retries the primary after a cooldown.
_LLAMACPP_BASE_URL = "http://189.60.217.20:8080"
_LLAMACPP_MODEL = "gpt-oss-20b-F16.gguf"
_FALLBACK_COOLDOWN_SECONDS = 10.0


def _bootstrap() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    retrieval_configure(_DB_PATH)
    retrieval_init_db(_DB_PATH)

    assessment_configure(_DB_PATH)
    assessment_init_db(_DB_PATH)

    # Scorer: primary = personal llama.cpp server (gpt-oss-20b); fallback =
    # Groq (openai/gpt-oss-20b — ADR-0053: llama-3.3-70b-versatile doesn't
    # support Groq's response_format=json_schema, only the weaker
    # json_object, so the fallback target must be a schema-capable model).
    scorer_primary = LlamaCppClient(_LLAMACPP_BASE_URL, _LLAMACPP_MODEL)
    scorer_fallback = GroqClient(model="openai/gpt-oss-20b")
    configure_llm_client(
        FallbackLLMClient(
            scorer_primary,
            scorer_fallback,
            primary_provider_label="llamacpp",
            fallback_provider_label="groq",
            cooldown_seconds=_FALLBACK_COOLDOWN_SECONDS,
        ),
        provider="llamacpp",
        model=_LLAMACPP_MODEL,
    )

    # Gate: primary = the same personal llama.cpp server; fallback = local
    # Ollama (ADR-0050's original sole gate provider — Groq's account-level
    # rate limit can't absorb the gate's call volume, see ADR-0019
    # amendment, so Groq was never a candidate fallback for this role).
    # qwen2.5:7b replaced bode-alpaca-pt-br (2026-06-28): direct A/B diagnostic
    # against 5 known-outcome chunks showed Bode unreliably either stopped
    # generating right after "RELEVANT: yes" (no CLEANED: block at all) or
    # regurgitated its few-shot example verbatim instead of editing the real
    # input — both confirmed via raw-response inspection, not inferred. qwen2.5
    # produced genuine, content-specific CLEANED extracts in every case tested
    # and never failed the format. num_ctx=32768 matches its real native
    # context window (confirmed via `ollama show qwen2.5:7b` -> "context
    # length 32768"), not assumed from Mistral's value.
    # timeout=300: Ollama unloads idle models, and reloading qwen2.5:7b's ~5GB
    # of weights plus allocating a 32768-token KV cache can exceed the
    # OllamaClient default of 180s on a cold daemon (observed: a live
    # assessment's first gate call timed out at 180s; once warm, calls take
    # 4-6s). This only matters for the first call after Ollama has evicted the
    # model — steady-state latency is unaffected.
    # read_timeout=120s, single attempt (no retry loop): empirically the only
    # timeout value tested 2026-08-14 that produced zero timeouts/fallbacks
    # on the reference case (15s and 45s were tried and ruled out — see that
    # date's diagnostic history in evaluation.llm.llamacpp). max_tokens=768
    # is a second, independent guardrail found the same day: token-usage
    # logging caught a gate call whose final answer was 19 chars but which
    # generated 7685 completion tokens of hidden reasoning (~55s at this
    # server's ~140 tok/s) — max_tokens hard-bounds that to ~5.5s regardless
    # of read_timeout. Kept both rather than treating either as a substitute
    # for the other. Gate concurrency stays at LlamaCppClient's default (4,
    # matching the gate's own ThreadPoolExecutor).
    gate_primary = LlamaCppClient(
        _LLAMACPP_BASE_URL, _LLAMACPP_MODEL,
        read_timeout=120.0, max_timeout_retries=1, max_tokens=768,
    )
    gate_fallback = OllamaClient(
        model="qwen2.5:7b",
        num_predict=600,
        num_ctx=32768,
        timeout=300.0,
    )
    configure_gate_llm_client(
        FallbackLLMClient(
            gate_primary,
            gate_fallback,
            primary_provider_label="llamacpp",
            fallback_provider_label="ollama",
            cooldown_seconds=_FALLBACK_COOLDOWN_SECONDS,
        )
    )


_bootstrap()
app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
