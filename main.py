from __future__ import annotations

from pathlib import Path

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment.api.app import create_app
from evaluation import configure_gate_llm, configure_llm
from retrieval import configure as retrieval_configure
from retrieval.schema.ddl import init_db as retrieval_init_db

_DB_PATH = Path("data") / "app.db"


def _bootstrap() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    retrieval_configure(_DB_PATH)
    retrieval_init_db(_DB_PATH)

    assessment_configure(_DB_PATH)
    assessment_init_db(_DB_PATH)

    configure_llm(provider="groq", model="llama-3.3-70b-versatile")
    # Relevance gate (ADR-0050) always runs locally — Groq's account-level rate
    # limit can't absorb its call volume (see ADR-0019 amendment). num_predict
    # is capped low: classifying + lightly cleaning one chunk needs a few
    # hundred tokens at most, and with up to ~100 calls per assessment, an
    # uncapped generation that runs long even once balloons total latency.
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
    configure_gate_llm(
        provider="ollama",
        model="qwen2.5:7b",
        num_predict=600,
        num_ctx=32768,
        timeout=300.0,
    )


_bootstrap()
app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
