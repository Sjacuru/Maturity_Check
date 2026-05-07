from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


_heading_re = re.compile(r"^(#{1,6})\s+(.*)\s*$")

# -- PDF heading normaliser ---------------------------------------------------
# Matches the M5D (and similarly converted) running book-title header line:
# "Estruturação de Propostas de Investimento em Infraestrutura - Modelo de 5 Dimensões 4"
_PDF_BOOK_TITLE_RE = re.compile(
    r"^Estruturação de Propostas de Investimento em Infraestrutura"
    r" - Modelo de 5 Dimensões\s+[ivxlcdmIVXLCDM\d]+\s*$"
)
# Matches chapter / section running-header lines:
# "Capítulo 3: Proposta Inicial de Investimento – Dimensão Estratégica"
_PDF_CHAPTER_RE = re.compile(r"^Capítulo\s+\d+:")
# Matches action body-heading lines (body = no ToC underscore padding):
# "Ação 1: Descreva o projeto, seu contexto estratégico e objetivos estratégicos"
_PDF_ACTION_RE = re.compile(r"^Ação\s+\d+:")
# Matches annex heading lines — requires space/dash/end after the number to avoid
# matching inline references like "Anexo 9." in body text.
# "Anexo 1 – Glossário"  "Anexo 10 – Finanças Sustentáveis e o Modelo de Cinco Dimensões"
_PDF_ANNEX_RE = re.compile(r"^Anexo\s+\d+(?:\s|–|$)")
# ToC lines for actions end with underscores and/or a bare page number.
# e.g. "Ação 4: ... __ 46"  "Ação 17: ... 107"  "Ação 15: ...risco75"
_PDF_TOC_TRAILING_RE = re.compile(r"_*\s*\d+\s*$")
# ToC lines for annexes always have double underscores before the page number.
# Using a stricter pattern to avoid false-positives like "Princípios do G20".
# e.g. "Anexo 1 – Glossário ____ 199"
_PDF_TOC_ANNEX_RE = re.compile(r"_{2,}\s*\d+\s*$")


def normalize_pdf_headings(text: str) -> str:
    """
    Pre-process PDF-converted markdown to insert # heading markers.

    Designed for M5D-style documents where the PDF conversion produces:
    - Repeated book-title running headers  → stripped entirely
    - Chapter/section running headers      → de-duplicated; first occurrence
                                             becomes a ## heading, the rest
                                             are dropped (they are page headers)
    - Action headings (Ação N:) in body   → ### heading (ToC entries are
                                             identified by trailing underscores
                                             and left unchanged)
    - Annex headings (Anexo N) in body    → ## heading, de-duplicated like
                                             chapters; wrapped titles (trailing
                                             space) are joined with next line

    Reusable for Rio Manual and TCDF IN when converted from PDF with a similar
    layout. Pass the result directly to iter_markdown_blocks.
    """
    lines = text.split("\n")
    result: list[str] = []
    seen_chapter_headings: set[str] = set()
    seen_annex_headings: set[str] = set()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Strip book-title running headers
        if _PDF_BOOK_TITLE_RE.match(stripped):
            i += 1
            continue

        # Chapter/section running headers: first occurrence → ## heading; rest dropped
        if _PDF_CHAPTER_RE.match(stripped):
            if stripped not in seen_chapter_headings:
                seen_chapter_headings.add(stripped)
                result.append(f"## {stripped}")
            i += 1
            continue

        # Action body headings — ToC entries end with underscores and/or a page number
        if _PDF_ACTION_RE.match(stripped):
            if not _PDF_TOC_TRAILING_RE.search(stripped):
                result.append(f"### {stripped}")
            i += 1
            continue

        # Annex headings — deduplicated like chapters.
        # Strategy: the full title always appears first (body section start).
        # Running-header occurrences may be wrapped over 2-3 lines without trailing
        # spaces; detect them by checking if stripped is a prefix of a known title.
        if _PDF_ANNEX_RE.match(stripped):
            # Annex ToC entries always have double underscores before page number
            if _PDF_TOC_ANNEX_RE.search(stripped):
                i += 1
                continue

            # Wrapped running header: this line is a strict prefix of a known title
            if any(known.startswith(stripped) and known != stripped
                   for known in seen_annex_headings):
                i += 1
                continue

            # Exact match: deduplicate
            if stripped in seen_annex_headings:
                i += 1
                continue

            # New heading — join wrapped continuation lines (trailing space heuristic)
            full_title = stripped
            while line.rstrip("\n").endswith(" ") and i + 1 < len(lines):
                next_line = lines[i + 1]
                next_stripped = next_line.strip()
                if (not next_stripped
                        or _PDF_BOOK_TITLE_RE.match(next_stripped)
                        or _PDF_CHAPTER_RE.match(next_stripped)
                        or _PDF_ACTION_RE.match(next_stripped)
                        or _PDF_ANNEX_RE.match(next_stripped)):
                    break
                full_title = full_title + " " + next_stripped
                i += 1
                line = next_line  # advance so next iteration checks new line's trailing space

            seen_annex_headings.add(full_title)
            result.append(f"## {full_title}")
            i += 1
            continue

        result.append(line)
        i += 1

    return "\n".join(result)


@dataclass(frozen=True)
class Heading:
    level: int
    text: str


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    heading_path: str | None
    start_char: int
    end_char: int
    text: str


def iter_markdown_blocks(md: str) -> Iterable[tuple[int, str | None, str]]:
    """
    Yield (start_offset, heading_path, block_text) where block_text is the text under
    the current heading path until the next heading of same-or-higher level.
    """
    lines = md.splitlines(keepends=True)
    stack: list[Heading] = []

    buf: list[str] = []
    buf_start = 0
    cur_heading_path: str | None = None
    offset = 0

    def flush() -> tuple[int, str | None, str] | None:
        nonlocal buf, buf_start
        if not buf:
            return None
        text = "".join(buf).strip()
        buf = []
        if not text:
            return None
        return (buf_start, cur_heading_path, text)

    for line in lines:
        m = _heading_re.match(line)
        if m:
            flushed = flush()
            if flushed:
                yield flushed

            level = len(m.group(1))
            title = m.group(2).strip()

            while stack and stack[-1].level >= level:
                stack.pop()
            stack.append(Heading(level=level, text=title))
            cur_heading_path = " > ".join(h.text for h in stack)

            buf_start = offset + len(line)
        else:
            if not buf:
                buf_start = offset
            buf.append(line)
        offset += len(line)

    flushed = flush()
    if flushed:
        yield flushed


def chunk_text(
    text: str,
    *,
    max_chars: int,
    overlap_chars: int,
) -> list[tuple[int, int, str]]:
    """
    Chunk text by character window, preferring paragraph boundaries.

    Returns list of (start, end, chunk_text) relative to `text`.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be >= 0")
    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be < max_chars")

    # Normalize newlines but keep content stable enough for hashing
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    if len(t) <= max_chars:
        return [(0, len(t), t)]

    paragraphs = []
    cursor = 0
    for p in re.split(r"\n{2,}", t):
        p = p.strip()
        if not p:
            cursor += 2
            continue
        start = t.find(p, cursor)
        end = start + len(p)
        paragraphs.append((start, end, p))
        cursor = end

    chunks: list[tuple[int, int, str]] = []
    if not paragraphs:
        paragraphs = [(0, len(t), t)]

    i = 0
    while i < len(paragraphs):
        start = paragraphs[i][0]
        end = start
        parts: list[str] = []
        j = i
        while j < len(paragraphs) and (paragraphs[j][1] - start) <= max_chars:
            parts.append(paragraphs[j][2])
            end = paragraphs[j][1]
            j += 1
        if j == i:
            # single huge paragraph; hard cut
            end = min(start + max_chars, len(t))
            chunk = t[start:end]
            chunks.append((start, end, chunk))
            i += 1
        else:
            chunk = "\n\n".join(parts)
            chunks.append((start, end, chunk))
            i = j

        # overlap step
        if overlap_chars > 0 and chunks:
            next_start = max(0, end - overlap_chars)
            # advance i to paragraph containing next_start
            while i < len(paragraphs) and paragraphs[i][1] <= next_start:
                i += 1

    # de-dup identical windows
    out: list[tuple[int, int, str]] = []
    seen = set()
    for s, e, c in chunks:
        key = (s, e)
        if key in seen:
            continue
        seen.add(key)
        out.append((s, e, c.strip()))
    return out

