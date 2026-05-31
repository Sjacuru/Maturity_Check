"""
Integration test — native text extraction (issue #7).

Uses the IPMP PDF in docs/ as the digital fixture. That PDF is committed to the repo,
has native embedded text on most pages, and covers the common PPP procurement document
structure: cover pages, dense text, tables, and section dividers.
"""
from pathlib import Path

import pytest

from extraction import Chunk, extract_document

_DOCS = Path(__file__).parent.parent / "docs"
_IPMP_PDF = _DOCS / "IPMP TCU2026 - Indicador_percepcao_maturidade.pdf"
_IPMP_PAGE_TOTAL = 246


@pytest.fixture(scope="module")
def ipmp_chunks():
    return extract_document(_IPMP_PDF)


def test_returns_nonempty_list(ipmp_chunks):
    assert len(ipmp_chunks) > 0


def test_all_chunks_are_chunk_instances(ipmp_chunks):
    assert all(isinstance(c, Chunk) for c in ipmp_chunks)


def test_filename_propagated(ipmp_chunks):
    expected = _IPMP_PDF.name
    assert all(c.filename == expected for c in ipmp_chunks)


def test_page_total_correct(ipmp_chunks):
    assert all(c.page_total == _IPMP_PAGE_TOTAL for c in ipmp_chunks)


def test_page_numbers_in_valid_range(ipmp_chunks):
    assert all(1 <= c.page_number <= _IPMP_PAGE_TOTAL for c in ipmp_chunks)


def test_page_numbers_are_ordered(ipmp_chunks):
    page_numbers = [c.page_number for c in ipmp_chunks]
    assert page_numbers == sorted(page_numbers)


def test_chunk_index_starts_at_zero_per_page(ipmp_chunks):
    from collections import defaultdict
    page_chunks: dict[int, list] = defaultdict(list)
    for c in ipmp_chunks:
        page_chunks[c.page_number].append(c)
    for chunks in page_chunks.values():
        assert min(c.chunk_index for c in chunks) == 0


def test_char_offset_zero_for_first_chunk(ipmp_chunks):
    from collections import defaultdict
    page_chunks: dict[int, list] = defaultdict(list)
    for c in ipmp_chunks:
        page_chunks[c.page_number].append(c)
    for chunks in page_chunks.values():
        first = min(chunks, key=lambda c: c.chunk_index)
        assert first.char_offset == 0


def test_ocr_used_false(ipmp_chunks):
    # Digital PDF — native text extraction only in this slice
    assert all(c.ocr_used is False for c in ipmp_chunks)


def test_source_type_text(ipmp_chunks):
    assert all(c.source_type == "text" for c in ipmp_chunks)


def test_text_length_matches_text(ipmp_chunks):
    assert all(c.text_length == len(c.text) for c in ipmp_chunks)


def test_text_nonempty(ipmp_chunks):
    assert all(len(c.text) > 0 for c in ipmp_chunks)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        extract_document(Path("does_not_exist.pdf"))


def test_invalid_pdf_raises(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"this is not a pdf")
    with pytest.raises(RuntimeError):
        extract_document(bad)
