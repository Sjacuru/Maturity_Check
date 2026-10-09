from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import StrictBool


class RetrievedChunk(BaseModel):
    # Provenance — mirrors Chunk fields minus text_length (derivable)
    process_number: str
    filename: str
    page_number: int
    chunk_index: int
    char_offset: int
    page_total: int
    ocr_used: StrictBool
    source_type: str
    text: str
    # Retrieval metadata
    cascade_step: Literal["filename_match", "variant_match", "bm25", "regex", "vector"]
    expected_product_ids: list[str] = []  # products this chunk was retrieved for; empty on document-focused, regex, vector paths; merged across products by _deduplicate_across_products
    bm25_score: float | None         # null on document-focused, regex, and vector paths
    rank: int | None                 # null on document-focused, regex, and vector paths
    retrieval_mode: Literal["lexical", "vector_fallback"] = "lexical"
    retrieval_query: str | None = None
    # Concept keys from the retrieval profile whose query terms were found in
    # the accepted chunk's text — populated deterministically post-gate for
    # auditor traceability (ADR-0052). Empty for ungated paths (regex, doc-focused).
    matched_concepts: list[str] = []
    # The relevance gate's reasoning channel for the call that accepted this
    # chunk, keyed by Expected Product id (a chunk accepted for several products
    # carries one entry per product; _deduplicate_across_products merges them).
    # Empty for ungated paths and for rows persisted before 2026-10-03.
    gate_reasoning: dict[str, str] = {}
    # Where each product's accepting verdict came from — "model" (asked this
    # run), "ledger" (frozen earlier verdict) or "auditor" (overridden) — and
    # the ledger key, which the override route takes (ADR-0067). Keyed by
    # product id like gate_reasoning; empty on ungated paths and older rows.
    gate_source: dict[str, str] = {}
    gate_prompt_hash: dict[str, str] = {}
