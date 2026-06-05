from __future__ import annotations

from retrieval._config import configure
from retrieval.interfaces.contracts import RetrievedChunk
from retrieval.indexing.writer import index
from retrieval.query.cascade import retrieve_for_acao
from retrieval.query.vector import invalidate_vector_index

__all__ = [
    "configure",
    "index",
    "retrieve_for_acao",
    "RetrievedChunk",
    "invalidate_vector_index",
]
