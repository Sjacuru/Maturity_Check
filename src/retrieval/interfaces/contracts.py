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
    cascade_step: Literal["filename_match", "variant_match", "bm25", "regex"]
    expected_product_id: str | None  # null on document-focused and regex paths
    bm25_score: float | None         # null on document-focused and regex paths
    rank: int | None                 # null on document-focused and regex paths
