from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "rio_manual"


class Meta(BaseModel):
    schema_version: str
    last_updated: str
    sources: list[str]
    scope: str
    known_gaps: list[str]


class DocumentName(BaseModel):
    role: str
    canonical: str
    variants: list[str]
    maps_to_ipmp: list[str]
    minimum_required: bool
    source_volume: str
    notes: str


class LawReference(BaseModel):
    name: str
    regex_variants: list[str]
    law_number: str | None = None
    relevant_articles: list[str]
    maps_to_ipmp: list[str]
    source_volume: str
    notes: str | None = None


class PlanningItem(BaseModel):
    name: str
    variants: list[str]
    maps_to_ipmp: list[str]
    notes: str


class LocalPlanningInstruments(BaseModel):
    description: str
    items: list[PlanningItem]


class LegalPhraseItem(BaseModel):
    phrase: str
    maps_to_ipmp: list[str]
    source: str
    notes: str


class LegalPhrases(BaseModel):
    description: str
    items: list[LegalPhraseItem]


class MinimumRequiredFields(BaseModel):
    description: str
    source: str
    items: list[str]


class ProcessItem(BaseModel):
    name: str
    variants: list[str]
    notes: str


class ProcessContext(BaseModel):
    description: str
    items: list[ProcessItem]


class BM25SearchHints(BaseModel):
    primary_terms: list[str]
    secondary_terms: list[str]
    exact_match_names: list[str]


class AcaoRioManual(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    meta: Meta = Field(alias="_meta")
    acao_id: int
    document_names: list[DocumentName]
    law_references: list[LawReference]
    local_planning_instruments: LocalPlanningInstruments
    legal_phrases: LegalPhrases
    minimum_required_fields: MinimumRequiredFields
    process_context: ProcessContext
    bm25_search_hints: BM25SearchHints


class RioManualStore(BaseModel):
    acoes: dict[int, AcaoRioManual]


_store: RioManualStore | None = None


def get_rio_manual_store() -> RioManualStore:
    global _store
    if _store is None:
        _store = _load()
    return _store


def _load() -> RioManualStore:
    if not _DATA_DIR.exists():
        raise RuntimeError(f"Rio Manual data directory not found: {_DATA_DIR}")

    files = sorted(_DATA_DIR.glob("acao_*.json"))
    acoes: dict[int, AcaoRioManual] = {}
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
            acao = AcaoRioManual.model_validate(raw)
        except Exception as exc:
            logger.warning("Skipping %s — validation error: %s", path.name, exc)
            skipped.append(path.name)
            continue

        acoes[acao.acao_id] = acao

    total = len(acoes) + len(skipped)
    logger.info(
        "Loaded %d/%d Rio Manual action files. Skipped: %s",
        len(acoes),
        total,
        skipped or "0",
    )
    return RioManualStore(acoes=acoes)
