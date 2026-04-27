from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


_heading_re = re.compile(r"^(#{1,6})\s+(.*)\s*$")


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

