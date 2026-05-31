import pytest
from pydantic import ValidationError

from retrieval import RetrievedChunk


VALID_BM25 = dict(
    process_number="0023.001234/2024-01",
    filename="Estudo_de_Viabilidade.pdf",
    page_number=3,
    chunk_index=0,
    char_offset=0,
    page_total=42,
    ocr_used=False,
    source_type="text",
    text="Parceria Público-Privada para concessão de serviços de saneamento.",
    cascade_step="bm25",
    expected_product_id="1a",
    bm25_score=4.72,
    rank=1,
)

VALID_FILENAME_MATCH = dict(
    process_number="0023.001234/2024-01",
    filename="Estudo_de_Viabilidade.pdf",
    page_number=1,
    chunk_index=0,
    char_offset=0,
    page_total=42,
    ocr_used=False,
    source_type="text",
    text="Estudo de Viabilidade Técnica, Econômica e Ambiental.",
    cascade_step="filename_match",
    expected_product_id=None,
    bm25_score=None,
    rank=None,
)


# --- Valid construction ---

def test_bm25_chunk_valid():
    chunk = RetrievedChunk(**VALID_BM25)
    assert chunk.cascade_step == "bm25"
    assert chunk.expected_product_id == "1a"
    assert chunk.bm25_score == pytest.approx(4.72)
    assert chunk.rank == 1


def test_filename_match_chunk_valid():
    chunk = RetrievedChunk(**VALID_FILENAME_MATCH)
    assert chunk.cascade_step == "filename_match"
    assert chunk.expected_product_id is None
    assert chunk.bm25_score is None
    assert chunk.rank is None


def test_variant_match_chunk_valid():
    chunk = RetrievedChunk(**{**VALID_FILENAME_MATCH, "cascade_step": "variant_match"})
    assert chunk.cascade_step == "variant_match"


def test_regex_chunk_valid():
    chunk = RetrievedChunk(**{
        **VALID_BM25,
        "cascade_step": "regex",
        "expected_product_id": None,
        "bm25_score": None,
        "rank": None,
    })
    assert chunk.cascade_step == "regex"
    assert chunk.expected_product_id is None


# --- cascade_step validation ---

def test_invalid_cascade_step_rejected():
    with pytest.raises(ValidationError):
        RetrievedChunk(**{**VALID_BM25, "cascade_step": "invalid"})


def test_empty_cascade_step_rejected():
    with pytest.raises(ValidationError):
        RetrievedChunk(**{**VALID_BM25, "cascade_step": ""})


# --- Nullable fields ---

def test_bm25_score_none_accepted():
    chunk = RetrievedChunk(**{**VALID_BM25, "bm25_score": None, "rank": None})
    assert chunk.bm25_score is None
    assert chunk.rank is None


def test_expected_product_id_none_accepted():
    chunk = RetrievedChunk(**{**VALID_BM25, "expected_product_id": None})
    assert chunk.expected_product_id is None


# --- ocr_used is StrictBool ---

def test_ocr_used_true():
    chunk = RetrievedChunk(**{**VALID_BM25, "ocr_used": True, "source_type": "image"})
    assert chunk.ocr_used is True


def test_ocr_used_string_rejected():
    with pytest.raises(ValidationError):
        RetrievedChunk(**{**VALID_BM25, "ocr_used": "yes"})


def test_ocr_used_int_rejected():
    with pytest.raises(ValidationError):
        RetrievedChunk(**{**VALID_BM25, "ocr_used": 1})


# --- Required fields ---

@pytest.mark.parametrize("field", [
    "process_number", "filename", "page_number", "chunk_index",
    "char_offset", "page_total", "ocr_used", "source_type", "text", "cascade_step",
])
def test_missing_required_field_rejected(field):
    data = {k: v for k, v in VALID_BM25.items() if k != field}
    with pytest.raises(ValidationError):
        RetrievedChunk(**data)


# --- Type rejections ---

@pytest.mark.parametrize("field,bad_value", [
    ("page_number", "three"),
    ("chunk_index", 0.5),
    ("char_offset", None),
    ("page_total", []),
    ("rank", "first"),
    ("bm25_score", "high"),
])
def test_wrong_types_rejected(field, bad_value):
    with pytest.raises(ValidationError):
        RetrievedChunk(**{**VALID_BM25, field: bad_value})


# --- model_dump shape ---

def test_model_dump_contains_all_fields():
    chunk = RetrievedChunk(**VALID_BM25)
    keys = set(chunk.model_dump().keys())
    assert keys == {
        "process_number", "filename", "page_number", "chunk_index",
        "char_offset", "page_total", "ocr_used", "source_type", "text",
        "cascade_step", "expected_product_id", "bm25_score", "rank",
    }
