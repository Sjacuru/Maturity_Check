from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "ipmp"
_ID_PATTERN = re.compile(r"^\d+[a-z]?$")


class Exemplo(BaseModel):
    nivel: str
    score: int
    texto: str


class ProdutoEsperado(BaseModel):
    id: str
    texto: str

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        if not _ID_PATTERN.match(v):
            raise ValueError(f"id '{v}' does not match r'^\\d+[a-z]?$'")
        return v


class AcaoIPMP(BaseModel):
    acao_id: int
    titulo: str
    dimensao: str
    por_que_importante: str
    descricao_acao: str
    o_que_esperar: str
    produtos_esperados: list[ProdutoEsperado]
    momento_ideal: str
    excecoes: list[str]
    exemplos: list[Exemplo]


class IPMPStore(BaseModel):
    acoes: dict[int, AcaoIPMP]


_store: IPMPStore | None = None


def get_ipmp_store() -> IPMPStore:
    global _store
    if _store is None:
        _store = _load()
    return _store


def _load() -> IPMPStore:
    if not _DATA_DIR.exists():
        raise RuntimeError(f"IPMP data directory not found: {_DATA_DIR}")

    files = sorted(_DATA_DIR.glob("acao_*.json"))
    acoes: dict[int, AcaoIPMP] = {}
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
            acao = AcaoIPMP.model_validate(raw)
        except Exception as exc:
            logger.warning("Skipping %s — validation error: %s", path.name, exc)
            skipped.append(path.name)
            continue

        acoes[acao.acao_id] = acao

    total = len(acoes) + len(skipped)
    logger.info(
        "Loaded %d/%d IPMP action files. Skipped: %s",
        len(acoes),
        total,
        skipped or "0",
    )
    return IPMPStore(acoes=acoes)
