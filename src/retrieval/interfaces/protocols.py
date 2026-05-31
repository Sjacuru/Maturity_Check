from __future__ import annotations

from typing import Protocol

from retrieval.interfaces.contracts import RetrievedChunk


class ChunkRetriever(Protocol):
    def search(self, query: str, acao_id: int, k: int) -> list[RetrievedChunk]: ...
