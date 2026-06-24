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
    # bode-alpaca-pt-br (PT-BR finetuned) replaced base mistral: faster once
    # warm and consistently produces the literal RELEVANT: yes/no format
    # instead of rambling or translating the sentinel label.
    configure_gate_llm(provider="ollama", model="splitpierre/bode-alpaca-pt-br", num_predict=600)


_bootstrap()
app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
