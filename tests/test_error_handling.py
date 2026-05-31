"""
Tests for extraction error handling (issue #10).

Verifies: fatal errors terminate immediately; page-level failures are non-fatal
with structured log entries; partial and total page failures produce correct output.
"""
import logging
from pathlib import Path

import pytest

import extraction.pdf as pdf_module
from extraction import extract_document

_DOCS = Path(__file__).parent.parent / "docs"
_IPMP_PDF = _DOCS / "IPMP TCU2026 - Indicador_percepcao_maturidade.pdf"


# --- Fatal error: file not found ---

def test_file_not_found_raises_before_extraction():
    with pytest.raises(FileNotFoundError):
        extract_document(Path("nonexistent_file.pdf"))


# --- Fatal error: not a valid PDF ---

def test_invalid_pdf_raises(tmp_path):
    bad = tmp_path / "garbage.pdf"
    bad.write_bytes(b"this is definitely not a PDF file")
    with pytest.raises(RuntimeError):
        extract_document(bad)


# --- Non-fatal: all pages fail → empty list returned ---

def test_all_pages_fail_returns_empty_list(monkeypatch):
    def _always_fail(page, filename, page_number, page_total):
        raise RuntimeError("simulated page failure")

    monkeypatch.setattr(pdf_module, "_extract_page", _always_fail)
    result = extract_document(_IPMP_PDF)
    assert result == []


# --- Non-fatal: all page failures produce a structured log entry each ---

def test_page_failure_emits_structured_log(monkeypatch, caplog):
    def _always_fail(page, filename, page_number, page_total):
        raise RuntimeError("simulated page failure")

    monkeypatch.setattr(pdf_module, "_extract_page", _always_fail)

    with caplog.at_level(logging.WARNING, logger="extraction.pdf"):
        extract_document(_IPMP_PDF)

    assert len(caplog.records) > 0
    for record in caplog.records:
        assert "filename" in record.message
        assert "page_number" in record.message
        assert "error" in record.message


# --- Non-fatal: only some pages fail → extraction continues ---

def test_partial_page_failure_continues_extraction(monkeypatch):
    original_extract_page = pdf_module._extract_page
    call_count = {"n": 0}

    def _fail_first_page(page, filename, page_number, page_total):
        call_count["n"] += 1
        if page_number == 1:
            raise RuntimeError("simulated failure on page 1")
        return original_extract_page(page, filename, page_number, page_total)

    monkeypatch.setattr(pdf_module, "_extract_page", _fail_first_page)
    result = extract_document(_IPMP_PDF)

    # Extraction continued beyond page 1
    assert call_count["n"] > 1
    # Result contains chunks (from pages 2+)
    assert len(result) > 0
    # No chunk has page_number == 1
    assert all(c.page_number != 1 for c in result)


# --- No garbage Chunk from empty pages ---

class _FakeFitzPage:
    """Minimal fitz.Page stand-in: digital page (no images) with configurable text."""

    def __init__(self, text=""):
        self._text = text

    class _Rect:
        height = 842.0
        width = 595.0

    rect = _Rect()

    def get_text(self, mode="text"):
        if mode == "words":
            return []  # no words → _needs_ocr image check triggered, but no images
        return self._text

    def get_images(self, full=False):
        return []  # no images → _needs_ocr returns False (digital page)


def test_empty_page_produces_no_chunk():
    from extraction.pdf import _extract_page

    result = _extract_page(_FakeFitzPage(text=""), "doc.pdf", page_number=1, page_total=1)
    assert result == []


def test_whitespace_only_page_produces_no_chunk():
    from extraction.pdf import _extract_page

    result = _extract_page(_FakeFitzPage(text="   \n  \t  "), "doc.pdf", page_number=1, page_total=1)
    assert result == []


def test_minimal_content_page_produces_chunk():
    from extraction.pdf import _extract_page

    # A short but non-empty digital page (e.g., a section divider) produces a chunk.
    # There is no character-count filter in the native text path — that was replaced
    # by the word-count+image heuristic governing whether to OCR, not whether to output.
    result = _extract_page(_FakeFitzPage(text="Seção 3"), "doc.pdf", page_number=1, page_total=1)
    assert len(result) == 1
    assert result[0].ocr_used is False
