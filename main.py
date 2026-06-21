from __future__ import annotations

from pathlib import Path

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment.api.app import create_app
from evaluation import configure_llm
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


_bootstrap()
app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
