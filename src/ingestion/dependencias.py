"""Dependências entre Ações do IPMP (data/ipmp/dependencias.json).

Cada aresta diz que a Ação `citante` nomeia a Ação `citada` e com que sentido
(`tipo`). Só dois tipos têm efeito na avaliação (ADR-0070):

  pre       teto: a citante não recebe 3 se a citada ficou em 0 ou sem evidência
  artefato  sinal de revisão: a citante é uma versão posterior do mesmo documento

Os demais (`fraco`, `sucessora`, `contraste`, `delega`, `sequencia`, `lacuna`)
registram a leitura da frase para que a classificação seja auditável, e não
fazem nada. A frase do IPMP que justifica cada aresta viaja junto.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator

_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "ipmp" / "dependencias.json"

TipoDependencia = Literal[
    "pre", "artefato", "fraco", "sucessora", "contraste", "delega", "sequencia", "lacuna"
]

# Tipos cujo efeito depende de a citada ter sido avaliada ANTES da citante.
# A avaliação percorre as Ações em ordem crescente (AssessmentService), logo
# uma aresta destes tipos apontando para a frente nunca engataria — melhor
# recusar o arquivo do que deixar a regra silenciosamente inerte.
_TIPOS_COM_EFEITO: frozenset[str] = frozenset({"pre", "artefato"})


class Dependencia(BaseModel):
    citante: int
    citada: int
    tipo: TipoDependencia
    campo: str = ""
    frase: str = ""
    # Which of the citing Ação's products are the later version of the cited
    # Ação's artefact. Empty means the whole Ação. Only the `artefato` review
    # signal reads it (the cap needs every product evidenced, so scope is moot).
    produtos_citante: list[str] = []

    @field_validator("citante", "citada")
    @classmethod
    def _acao_valida(cls, v: int) -> int:
        if not 1 <= v <= 46:
            raise ValueError(f"Ação fora de 1..46: {v}")
        return v


class DependencyStore(BaseModel):
    dependencias: list[Dependencia]

    def com_efeito(self, citante: int) -> list[Dependencia]:
        """Arestas 'pre' e 'artefato' da Ação, na ordem do arquivo."""
        return [d for d in self.dependencias
                if d.citante == citante and d.tipo in _TIPOS_COM_EFEITO]

    def pre(self, citante: int) -> list[Dependencia]:
        return [d for d in self.dependencias if d.citante == citante and d.tipo == "pre"]

    def artefato(self, citante: int) -> list[Dependencia]:
        return [d for d in self.dependencias
                if d.citante == citante and d.tipo == "artefato"]

    def citantes_de(self, citada: int) -> list[Dependencia]:
        """Quem depende (com efeito) desta Ação — o leque de propagação."""
        return [d for d in self.dependencias
                if d.citada == citada and d.tipo in _TIPOS_COM_EFEITO]


_store: DependencyStore | None = None


def get_dependency_store() -> DependencyStore:
    global _store
    if _store is None:
        _store = load_dependencies(_DATA_FILE)
    return _store


def load_dependencies(path: Path) -> DependencyStore:
    if not path.exists():
        raise RuntimeError(f"Dependency file not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Cannot read {path.name}: {exc}") from exc

    store = DependencyStore(dependencias=raw.get("dependencias", []))

    vistos: set[tuple[int, int]] = set()
    for d in store.dependencias:
        if d.citante == d.citada:
            raise RuntimeError(f"{path.name}: Ação {d.citante} depende de si mesma")
        chave = (d.citante, d.citada)
        if chave in vistos:
            raise RuntimeError(f"{path.name}: aresta duplicada {d.citante} -> {d.citada}")
        vistos.add(chave)
        if d.tipo in _TIPOS_COM_EFEITO and d.citada >= d.citante:
            raise RuntimeError(
                f"{path.name}: aresta '{d.tipo}' {d.citante} -> {d.citada} aponta para a "
                "frente; a citada precisa ser avaliada antes da citante (ordem 1..46)"
            )
        for pid in d.produtos_citante:
            if not pid.startswith(str(d.citante)):
                raise RuntimeError(
                    f"{path.name}: aresta {d.citante} -> {d.citada} escopa o produto "
                    f"{pid!r}, que não pertence à Ação {d.citante}"
                )
    return store
