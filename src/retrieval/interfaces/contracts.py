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
    expected_product_id: str | None  # null on document-focused, regex, and vector paths
    bm25_score: float | None         # null on document-focused, regex, and vector paths
    rank: int | None                 # null on document-focused, regex, and vector paths
    retrieval_mode: Literal["lexical", "vector_fallback"] = "lexical"
    retrieval_query: str | None = None
