"""
Integration test — OCR fallback for scanned pages (issue #8).

Uses a synthetic scanned-page fixture (tests/fixtures/scanned_fixture.pdf):
  Page 1: image-only (no native text, one full-page raster image)
  Page 2: digital text (native extraction, control page)

Marked @pytest.mark.slow — excluded from the default test run. Run explicitly with:
  pytest -m slow
"""
from pathlib import Path

import pytest

from extraction import Chunk, extract_document

_FIXTURE = Path(__file__).parent / "fixtures" / "scanned_fixture.pdf"


@pytest.fixture(scope="module")
def scanned_chunks():
    return extract_document(_FIXTURE)


@pytest.mark.slow
def test_returns_nonempty_list(scanned_chunks):
    assert len(scanned_chunks) > 0


@pytest.mark.slow
def test_all_chunks_are_chunk_instances(scanned_chunks):
    assert all(isinstance(c, Chunk) for c in scanned_chunks)


@pytest.mark.slow
def test_filename_propagated(scanned_chunks):
    assert all(c.filename == _FIXTURE.name for c in scanned_chunks)


@pytest.mark.slow
def test_page_total_correct(scanned_chunks):
    assert all(c.page_total == 2 for c in scanned_chunks)


@pytest.mark.slow
def test_scanned_page_uses_ocr(scanned_chunks):
    page1_chunks = [c for c in scanned_chunks if c.page_number == 1]
    assert len(page1_chunks) > 0, "Expected at least one Chunk from the scanned page"
    assert all(c.ocr_used is True for c in page1_chunks)


@pytest.mark.slow
def test_digital_page_does_not_use_ocr(scanned_chunks):
    page2_chunks = [c for c in scanned_chunks if c.page_number == 2]
    assert len(page2_chunks) > 0, "Expected at least one Chunk from the digital page"
    assert all(c.ocr_used is False for c in page2_chunks)


@pytest.mark.slow
def test_scanned_page_source_type(scanned_chunks):
    page1_chunks = [c for c in scanned_chunks if c.page_number == 1]
    assert all(c.source_type == "image" for c in page1_chunks)


@pytest.mark.slow
def test_digital_page_source_type(scanned_chunks):
    page2_chunks = [c for c in scanned_chunks if c.page_number == 2]
    assert all(c.source_type == "text" for c in page2_chunks)


@pytest.mark.slow
def test_scanned_page_text_nonempty(scanned_chunks):
    page1_chunks = [c for c in scanned_chunks if c.page_number == 1]
    assert all(len(c.text) > 0 for c in page1_chunks)


@pytest.mark.slow
def test_text_length_matches_text(scanned_chunks):
    assert all(c.text_length == len(c.text) for c in scanned_chunks)


@pytest.mark.slow
def test_chunk_index_starts_at_zero_per_page(scanned_chunks):
    from collections import defaultdict
    page_chunks: dict[int, list] = defaultdict(list)
    for c in scanned_chunks:
        page_chunks[c.page_number].append(c)
    for chunks in page_chunks.values():
        assert min(c.chunk_index for c in chunks) == 0


@pytest.mark.slow
def test_page_numbers_in_valid_range(scanned_chunks):
    assert all(1 <= c.page_number <= 2 for c in scanned_chunks)
