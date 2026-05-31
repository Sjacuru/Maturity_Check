from __future__ import annotations

from pydantic import BaseModel
from pydantic import StrictBool


class Chunk(BaseModel):
    filename: str
    page_number: int
    chunk_index: int
    char_offset: int
    text: str
    text_length: int
    page_total: int
    ocr_used: StrictBool
    source_type: str
