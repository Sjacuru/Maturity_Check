"""Genre of procurement text and the canonical document index (ADR-0074)."""

from __future__ import annotations

from retrieval.genre.classifier import INSTRUMENT, OTHER, classify_chunks
from retrieval.genre.index import (
    GENRE_RULES_VERSION,
    DocumentSegment,
    build_document_index,
    ensure_document_index,
    get_chunk_genres,
    get_document_index,
    get_narrative_sections,
    invalidate_document_index,
)

__all__ = [
    "INSTRUMENT",
    "OTHER",
    "GENRE_RULES_VERSION",
    "DocumentSegment",
    "classify_chunks",
    "build_document_index",
    "ensure_document_index",
    "get_chunk_genres",
    "get_document_index",
    "get_narrative_sections",
    "invalidate_document_index",
]
