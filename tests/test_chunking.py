"""
Tests for hybrid chunking behaviour (issue #9).

Validates sub-page splitting, chunk ordering, char_offset correctness,
and text reconstruction for pages that exceed _PAGE_CHUNK_MAX_CHARS.
"""
from pathlib import Path

import pytest

from extraction import extract_document
from extraction.pdf import _split_page_text, _PAGE_CHUNK_MAX_CHARS

_DOCS = Path(__file__).parent.parent / "docs"
_IPMP_PDF = _DOCS / "IPMP TCU2026 - Indicador_percepcao_maturidade.pdf"


# --- Unit tests for _split_page_text ---

def test_short_text_produces_single_segment():
    text = "Short text."
    segments = _split_page_text(text)
    assert len(segments) == 1
    assert segments[0] == (0, text)


def test_exact_threshold_produces_single_segment():
    text = "x" * _PAGE_CHUNK_MAX_CHARS
    segments = _split_page_text(text)
    assert len(segments) == 1


def test_long_text_splits_into_multiple_segments():
    text = " ".join(["word"] * 2000)  # well over any threshold
    segments = _split_page_text(text)
    assert len(segments) > 1


def test_no_segment_exceeds_max_chars():
    text = " ".join(["word"] * 2000)
    for offset, segment in _split_page_text(text):
        assert len(segment) <= _PAGE_CHUNK_MAX_CHARS


def test_concatenation_reconstructs_original():
    text = " ".join(["word"] * 2000)
    segments = _split_page_text(text)
    reconstructed = "".join(seg for _, seg in segments)
    assert reconstructed == text


def test_offsets_are_correct():
    text = " ".join(["word"] * 2000)
    segments = _split_page_text(text)
    for offset, segment in segments:
        assert text[offset : offset + len(segment)] == segment


def test_offsets_are_non_decreasing():
    text = " ".join(["word"] * 2000)
    offsets = [off for off, _ in _split_page_text(text)]
    assert offsets == sorted(offsets)


def test_first_offset_is_zero():
    text = " ".join(["word"] * 2000)
    segments = _split_page_text(text)
    assert segments[0][0] == 0


def test_no_gaps_between_segments():
    text = " ".join(["word"] * 2000)
    segments = _split_page_text(text)
    reconstructed = "".join(seg for _, seg in segments)
    assert len(reconstructed) == len(text)


# --- Integration tests for split pages in the IPMP PDF ---

@pytest.fixture(scope="module")
def ipmp_chunks():
    return extract_document(_IPMP_PDF)


def test_chunk_index_contiguous_within_page(ipmp_chunks):
    from collections import defaultdict
    page_chunks: dict[int, list] = defaultdict(list)
    for c in ipmp_chunks:
        page_chunks[c.page_number].append(c)

    for page_number, chunks in page_chunks.items():
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_index)
        indices = [c.chunk_index for c in sorted_chunks]
        assert indices == list(range(len(indices))), (
            f"Non-contiguous chunk_index on page {page_number}: {indices}"
        )


def test_char_offsets_consistent_with_text(ipmp_chunks):
    from collections import defaultdict
    page_chunks: dict[int, list] = defaultdict(list)
    for c in ipmp_chunks:
        page_chunks[c.page_number].append(c)

    for page_number, chunks in page_chunks.items():
        if len(chunks) <= 1:
            continue
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_index)
        full_text = "".join(c.text for c in sorted_chunks)
        for c in sorted_chunks:
            assert full_text[c.char_offset : c.char_offset + len(c.text)] == c.text, (
                f"char_offset mismatch on page {page_number} chunk {c.chunk_index}"
            )


def test_split_pages_exist(ipmp_chunks):
    from collections import Counter
    page_counts = Counter(c.page_number for c in ipmp_chunks)
    multi_chunk_pages = {pg: cnt for pg, cnt in page_counts.items() if cnt > 1}
    assert len(multi_chunk_pages) > 0, (
        "Expected at least one page to be split; check _PAGE_CHUNK_MAX_CHARS"
    )


def test_single_chunk_pages_have_index_zero(ipmp_chunks):
    from collections import Counter
    page_counts = Counter(c.page_number for c in ipmp_chunks)
    single_chunk_pages = {pg for pg, cnt in page_counts.items() if cnt == 1}
    for c in ipmp_chunks:
        if c.page_number in single_chunk_pages:
            assert c.chunk_index == 0
            assert c.char_offset == 0
