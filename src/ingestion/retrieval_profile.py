from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, model_validator

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "retrieval_profiles"

# ---------------------------------------------------------------------------
# Query Term models — discriminated by encoding field
# ---------------------------------------------------------------------------

class PhraseQueryTerm(BaseModel):
    encoding: Literal["phrase"]
    text: str
    type: Literal["A", "B", "C"]
    provenance: Literal["real_world", "canonical", "synthetic"]
    status: Literal["active", "experimental", "validated", "deprecated"] = "active"
    concept_ref: str | None = None
    sector_hint: str | None = None
    shared_with_acao: list[int] = []
    shared_with_acao_note: str | None = None


class NearQueryTerm(BaseModel):
    encoding: Literal["near"]
    tokens: list[str]
    distance: int
    type: Literal["A", "B", "C"]
    provenance: Literal["real_world", "canonical", "synthetic"]
    status: Literal["active", "experimental", "validated", "deprecated"] = "active"
    concept_ref: str | None = None
    sector_hint: str | None = None
    shared_with_acao: list[int] = []
    shared_with_acao_note: str | None = None

    @model_validator(mode="after")
    def _validate_tokens(self) -> NearQueryTerm:
        if len(self.tokens) < 2:
            raise ValueError("NEAR() terms require at least 2 tokens")
        if self.distance < 1:
            raise ValueError("NEAR() distance must be >= 1")
        return self


# ---------------------------------------------------------------------------
# Profile structure models
# ---------------------------------------------------------------------------

class RetrievalSignalConcept(BaseModel):
    key: str
    text: str


class ExpectedProductProfile(BaseModel):
    evidence_intent: str
    retrieval_signal_concepts: list[RetrievalSignalConcept]
    query_terms: list[PhraseQueryTerm | NearQueryTerm]
    evidence_logic_patterns: list[str] = []
    negative_evidence_patterns: list[str] = []


class AcaoRetrievalProfile(BaseModel):
    acao_id: int
    profile_maturity: Literal["seed", "observed", "mature"]
    expected_products: dict[str, ExpectedProductProfile]


class RetrievalProfileStore(BaseModel):
    acoes: dict[int, AcaoRetrievalProfile]


# ---------------------------------------------------------------------------
# Store singleton
# ---------------------------------------------------------------------------

_store: RetrievalProfileStore | None = None


def get_retrieval_profile_store() -> RetrievalProfileStore:
    global _store
    if _store is None:
        _store = _load()
    return _store


def _load() -> RetrievalProfileStore:
    if not _DATA_DIR.exists():
        logger.info("Retrieval profiles directory not found — returning empty store")
        return RetrievalProfileStore(acoes={})

    files = sorted(_DATA_DIR.glob("acao_*.json"))
    if not files:
        logger.info("No retrieval profile files found — returning empty store")
        return RetrievalProfileStore(acoes={})

    acoes: dict[int, AcaoRetrievalProfile] = {}
    skipped: list[str] = []

    for path in files:
        suffix = path.stem.removeprefix("acao_")
        if not suffix.isdigit():
            raise RuntimeError(f"Unexpected filename format: {path.name}")
        expected_id = int(suffix)

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"Cannot read {path.name}: {exc}") from exc

        actual_id = raw.get("acao_id")
        if actual_id != expected_id:
            raise RuntimeError(
                f"Filename/id mismatch in {path.name}: "
                f"filename implies {expected_id}, file contains {actual_id!r}"
            )

        try:
            profile = AcaoRetrievalProfile.model_validate(raw)
        except Exception as exc:
            logger.warning("Skipping %s — validation error: %s", path.name, exc)
            skipped.append(path.name)
            continue

        acoes[profile.acao_id] = profile

    total = len(acoes) + len(skipped)
    logger.info(
        "Loaded %d/%d retrieval profile files. Skipped: %s",
        len(acoes),
        total,
        skipped or "0",
    )
    return RetrievalProfileStore(acoes=acoes)
