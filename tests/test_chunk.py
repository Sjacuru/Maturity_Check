import pytest
from pydantic import ValidationError

from extraction import Chunk


VALID = dict(
    filename="doc.pdf",
    page_number=1,
    chunk_index=0,
    char_offset=0,
    text="Sample text from a PPP procurement document.",
    text_length=44,
    page_total=10,
    ocr_used=False,
    source_type="text",
)


def test_chunk_valid_construction():
    chunk = Chunk(**VALID)
    assert chunk.filename == "doc.pdf"
    assert chunk.page_number == 1
    assert chunk.chunk_index == 0
    assert chunk.char_offset == 0
    assert chunk.text == "Sample text from a PPP procurement document."
    assert chunk.text_length == 44
    assert chunk.page_total == 10
    assert chunk.ocr_used is False
    assert chunk.source_type == "text"


def test_chunk_model_dump_shape():
    chunk = Chunk(**VALID)
    d = chunk.model_dump()
    assert set(d.keys()) == {
        "filename",
        "page_number",
        "chunk_index",
        "char_offset",
        "text",
        "text_length",
        "page_total",
        "ocr_used",
        "source_type",
    }


def test_chunk_model_dump_values():
    chunk = Chunk(**VALID)
    d = chunk.model_dump()
    assert d["filename"] == "doc.pdf"
    assert d["ocr_used"] is False
    assert d["text_length"] == 44


def test_chunk_ocr_used_true():
    chunk = Chunk(**{**VALID, "ocr_used": True, "source_type": "image"})
    assert chunk.ocr_used is True
    assert chunk.source_type == "image"


def test_chunk_source_type_image_plus_text():
    chunk = Chunk(**{**VALID, "source_type": "image+text"})
    assert chunk.source_type == "image+text"


@pytest.mark.parametrize("field,bad_value", [
    ("page_number", "one"),
    ("chunk_index", 1.5),
    ("char_offset", None),
    ("text_length", "long"),
    ("page_total", []),
    ("ocr_used", "yes"),
])
def test_chunk_rejects_wrong_types(field, bad_value):
    with pytest.raises(ValidationError):
        Chunk(**{**VALID, field: bad_value})


def test_chunk_rejects_missing_filename():
    data = {k: v for k, v in VALID.items() if k != "filename"}
    with pytest.raises(ValidationError):
        Chunk(**data)


def test_chunk_no_business_identifiers():
    fields = set(Chunk.model_fields.keys())
    assert "process_number" not in fields
    assert "contract_number" not in fields
