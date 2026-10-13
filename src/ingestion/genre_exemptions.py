"""Produtos isentos do filtro de gênero (data/ipmp/isencoes_genero.json, ADR-0074).

Para um Produto Esperado cujo critério do IPMP é o próprio instrumento de
contratação (contrato ou minuta, edital, termo de referência, matriz de
riscos), o texto de instrumento é a evidência pedida: o filtro de gênero não
o retira antes do gate. Para todos os outros produtos, ele retira.

Cada isenção carrega a frase do IPMP que a justifica, copiada literalmente do
produto em data/ipmp/acao_NN.json. O carregador confere a frase contra o IPMP
carregado, de modo que uma edição do IPMP que mude o produto obriga a revisar
a isenção em vez de mantê-la em silêncio.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from ingestion.ipmp import get_ipmp_store

_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "ipmp" / "isencoes_genero.json"


class IsencaoGenero(BaseModel):
    acao: int
    produto: str
    frase: str
    motivo: str


class GenreExemptionStore(BaseModel):
    isencoes: list[IsencaoGenero]

    def produtos(self, acao_id: int | None = None) -> frozenset[str]:
        """Ids dos produtos isentos, de uma Ação ou de todas."""
        return frozenset(
            i.produto for i in self.isencoes if acao_id is None or i.acao == acao_id
        )


_store: GenreExemptionStore | None = None


def get_genre_exemption_store() -> GenreExemptionStore:
    global _store
    if _store is None:
        _store = load_genre_exemptions(_DATA_FILE)
    return _store


def load_genre_exemptions(path: Path) -> GenreExemptionStore:
    if not path.exists():
        raise RuntimeError(f"Genre exemption file not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Cannot read {path.name}: {exc}") from exc

    store = GenreExemptionStore(isencoes=raw.get("isencoes", []))
    ipmp = get_ipmp_store().acoes
    vistos: set[str] = set()
    for i in store.isencoes:
        if i.produto in vistos:
            raise RuntimeError(f"{path.name}: produto {i.produto} isento duas vezes")
        vistos.add(i.produto)
        acao = ipmp.get(i.acao)
        if acao is None:
            raise RuntimeError(f"{path.name}: Ação {i.acao} não existe no IPMP carregado")
        produto = next((p for p in acao.produtos_esperados if p.id == i.produto), None)
        if produto is None or not produto.scored:
            raise RuntimeError(
                f"{path.name}: {i.produto} não é um Produto Esperado pontuado da Ação {i.acao}"
            )
        if i.frase != produto.texto:
            raise RuntimeError(
                f"{path.name}: a frase da isenção de {i.produto} não é mais a do IPMP; "
                "revise a isenção contra o texto atual do produto"
            )
    return store
