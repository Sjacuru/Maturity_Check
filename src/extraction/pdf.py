from __future__ import annotations

import io
import logging
from pathlib import Path

import os

import fitz  # pymupdf
import pytesseract
from PIL import Image

from extraction.chunk import Chunk

logger = logging.getLogger(__name__)

# Allow operators to point pytesseract at the Tesseract binary when it is not on
# the subprocess PATH (common on Windows conda environments).
# Set TESSERACT_CMD to the absolute path of tesseract.exe to override.
_tesseract_cmd = os.environ.get("TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd

# --- OCR triggering heuristic ---
#
# Uses word count in the content area (excluding margins) rather than raw character
# count. This handles the common pattern in PPP procurement documents where a document
# management system injects header/footer overlays (timestamps, protocol numbers,
# department codes) as native text onto pages that are otherwise scanned images.
#
# A page triggers OCR when BOTH conditions are true:
#   1. Fewer than _MIN_CONTENT_WORDS meaningful words in the non-margin area
#   2. At least one raster image covers >= _IMAGE_AREA_THRESHOLD of the page area
#
# The image-presence check prevents unnecessary OCR on digital title pages and
# section dividers that have minimal native text but no scanned content.
_MIN_CONTENT_WORDS = 15
_MARGIN_FRACTION = 0.15  # top/bottom fraction of page height treated as margin zone
_IMAGE_AREA_THRESHOLD = 0.25  # minimum image-to-page area ratio to consider OCR

# --- Chunking threshold ---
# Pages exceeding this character count are split into sub-page Chunks.
# Calibrated against the IPMP and Rio Manual PDFs: 99th-percentile page ~3380 chars.
_PAGE_CHUNK_MAX_CHARS = 3000

# --- OCR language ---
# Portuguese is the primary language of PPP procurement documents.
# "por+eng" covers mixed-language pages where English legal boilerplate appears.
_OCR_LANG = "por+eng"


def extract_document(path: Path) -> list[Chunk]:
    if not path.exists():
        raise FileNotFoundError(f"Document Artifact not found: {path}")

    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise RuntimeError(f"Cannot open '{path.name}': {exc}") from exc

    if doc.is_encrypted:
        doc.close()
        raise RuntimeError(f"Encrypted PDF not supported: '{path.name}'")

    page_total = doc.page_count
    filename = path.name
    chunks: list[Chunk] = []

    try:
        for page_idx in range(page_total):
            page_number = page_idx + 1
            try:
                page_chunks = _extract_page(
                    doc[page_idx], filename, page_number, page_total
                )
                chunks.extend(page_chunks)
            except Exception as exc:
                logger.warning(
                    "Page extraction failed — filename=%s page_number=%d error=%s",
                    filename,
                    page_number,
                    exc,
                )
    finally:
        doc.close()

    return chunks


def _extract_page(
    page: fitz.Page,
    filename: str,
    page_number: int,
    page_total: int,
) -> list[Chunk]:
    if not _needs_ocr(page):
        text = page.get_text().strip()
        if not text:
            return []
        return _build_chunks(
            text, filename, page_number, page_total,
            ocr_used=False, source_type="text",
        )

    logger.debug(
        "Applying OCR — filename=%s page_number=%d",
        filename,
        page_number,
    )
    ocr_text = _ocr_page(page)
    if not ocr_text.strip():
        logger.debug(
            "OCR produced empty text — filename=%s page_number=%d",
            filename,
            page_number,
        )
        return []

    has_any_native = bool(page.get_text().strip())
    source_type = "image+text" if has_any_native else "image"
    return _build_chunks(
        ocr_text, filename, page_number, page_total,
        ocr_used=True, source_type=source_type,
    )


def _needs_ocr(page: fitz.Page) -> bool:
    """Return True if this page's content should be recovered via OCR.

    Requires both: insufficient content words in the non-margin area, AND
    significant raster image coverage. This prevents unnecessary OCR on digital
    title pages and section dividers that are text-sparse but image-free.
    """
    h = page.rect.height
    margin = h * _MARGIN_FRACTION

    words = page.get_text("words")  # (x0, y0, x1, y1, word, block, line, word_no)
    content_words = [
        w for w in words
        if margin < w[1] < (h - margin)
        and len(w[4].strip()) > 2
        and any(c.isalpha() for c in w[4])
    ]
    if len(content_words) >= _MIN_CONTENT_WORDS:
        return False

    images = page.get_images(full=True)
    if not images:
        return False

    page_area = page.rect.width * h
    for img in images:
        for rect in page.get_image_rects(img[0]):
            if (rect.width * rect.height) / page_area >= _IMAGE_AREA_THRESHOLD:
                return True

    return False


def _ocr_page(page: fitz.Page) -> str:
    """Render the page at 2× resolution and run Tesseract OCR."""
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img, lang=_OCR_LANG).strip()


def _build_chunks(
    text: str,
    filename: str,
    page_number: int,
    page_total: int,
    ocr_used: bool,
    source_type: str,
) -> list[Chunk]:
    return [
        Chunk(
            filename=filename,
            page_number=page_number,
            chunk_index=idx,
            char_offset=offset,
            text=segment,
            text_length=len(segment),
            page_total=page_total,
            ocr_used=ocr_used,
            source_type=source_type,
        )
        for idx, (offset, segment) in enumerate(_split_page_text(text))
    ]


def _split_page_text(text: str) -> list[tuple[int, str]]:
    """Split page text into segments no longer than _PAGE_CHUNK_MAX_CHARS.

    Split points are chosen at whitespace boundaries to avoid mid-word cuts.
    Concatenating all returned segments in order reconstructs the original text exactly.
    Returns a list of (char_offset, segment) pairs.
    """
    if len(text) <= _PAGE_CHUNK_MAX_CHARS:
        return [(0, text)]

    segments: list[tuple[int, str]] = []
    start = 0

    while start < len(text):
        end = start + _PAGE_CHUNK_MAX_CHARS
        if end >= len(text):
            segments.append((start, text[start:]))
            break

        split_at = text.rfind(" ", start, end + 1)
        if split_at <= start:
            split_at = end

        segments.append((start, text[start:split_at]))
        start = split_at

    return segments
