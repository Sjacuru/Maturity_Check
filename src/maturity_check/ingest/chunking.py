from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


_heading_re = re.compile(r"^(#{1,6})\s+(.*)\s*$")

# -- Heading normaliser for reconstructed-markdown M5D format -----------------

# Separates front matter from main M5D content.
_CONTENT_ANCHOR_RE = re.compile(r"^#\s+Orientações\s+Detalhadas\s*$", re.IGNORECASE)

# Known M5D stage names (exact match against extracted heading title).
_M5D_STAGES = frozenset({
    "Proposta Inicial de Investimento",
    "Proposta Intermediária de Investimento",
    "Proposta Completa de Investimento",
})

# Known M5D dimension names mapped to their canonical form.
# The document uses "Pontos de Transição" (plural) while metadata uses the singular.
_M5D_DIMENSIONS: dict[str, str] = {
    "Dimensão Estratégica":    "Dimensão Estratégica",
    "Dimensão Econômica":      "Dimensão Econômica",
    "Dimensão Comercial":      "Dimensão Comercial",
    "Dimensão Financeira":     "Dimensão Financeira",
    "Dimensão Gerencial":      "Dimensão Gerencial",
    "Ponto de Transição":      "Ponto de Transição",
    "Pontos de Transição":     "Ponto de Transição",   # plural form used in PDF
}

# Ação heading body: "Ação N: title text..."
_ACTION_HEADING_RE = re.compile(r"^Ação\s+(\d+)\s*:(.*)")

# Annex headings — break the Ação stack so Annex content is not attributed to Ação 46.
_ANNEX_HEADING_RE = re.compile(r"^Anexo\s+\d+", re.IGNORECASE)

# Trailing noise fused onto Ação titles by the PDF converter.
_ACTION_TITLE_NOISE_RE = re.compile(
    r"(\s+Quem deve trabalhar nisto\??|\s+O que você deve fazer\??|\s+\d{1,3})\s*$",
    re.IGNORECASE,
)

# Internal section labels appearing as headings within each Ação.
_INTERNAL_LABEL_RE = re.compile(
    r"^(Quem deve trabalhar nisto\??|O que você deve fazer\??)$",
    re.IGNORECASE,
)

# Subtask items within Ação body — roman numeral list markers.
# Covers i–iii, iv, v–viii, ix, x–xiii, xiv, xv (sufficient for M5D).
# Matches both "iii. text" and standalone "iii." (PDF converters often split them).
_PDF_SUBTASK_RE = re.compile(
    r"^(i{1,3}|iv|vi{0,3}|ix|xi{0,3}|xiv|xv)\.(?:[ \t]|$)",
    re.IGNORECASE,
)


def normalize_pdf_headings(text: str) -> str:
    """
    Normalise reconstructed-markdown M5D output for ingestion.

    Expects input from a PDF-to-markdown converter that marks all headings
    as level-5 (#####). Produces a clean four-level hierarchy:

      ## Stage name                 (Proposta Inicial / Intermediária / Completa)
      ### Dimension name            (Estratégica, Econômica, Comercial, etc.)
      #### Ação N: clean title      (46 actions — trailing noise stripped from title)
      ##### i. subtask item         (roman-numeral subtask items)

    Front matter (before "# Orientações Detalhadas") is kept with its ##
    headings intact for general retrieval but excluded from the stage/action
    hierarchy. Consecutive duplicate headings and plain-text echoes of
    promoted headings are suppressed.
    """
    lines = text.split("\n")
    result: list[str] = []
    in_content = False

    seen_stages: set[str] = set()
    current_stage: str | None = None
    seen_stage_dim_pairs: set[tuple[str, str]] = set()

    # Tracks the title of the last heading processed so that (a) consecutive
    # duplicate headings and (b) plain-text echoes of promoted headings are skipped.
    last_heading_title: str | None = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Content section anchor ─────────────────────────────────────
        if _CONTENT_ANCHOR_RE.match(stripped):
            in_content = True
            i += 1
            continue

        # ── Front matter (before anchor) ──────────────────────────────
        if not in_content:
            m = _heading_re.match(stripped)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                if title == last_heading_title:
                    i += 1
                    continue
                last_heading_title = title
                result.append(f"## {title}" if level <= 2 else title)
            else:
                if stripped and stripped == last_heading_title:
                    last_heading_title = None
                    i += 1
                    continue
                if stripped:
                    last_heading_title = None
                result.append(line)
            i += 1
            continue

        # ── Content section (after anchor) ────────────────────────────
        m = _heading_re.match(stripped)
        if m:
            title = m.group(2).strip()
            if not title:
                i += 1
                continue

            # Suppress consecutive duplicate headings
            if title == last_heading_title:
                i += 1
                continue
            last_heading_title = title

            # Internal section labels → plain text inside their Ação
            if _INTERNAL_LABEL_RE.match(title):
                result.append(title)
                i += 1
                continue

            # Ação heading → #### Ação N: clean title
            action_m = _ACTION_HEADING_RE.match(title)
            if action_m:
                num = action_m.group(1)
                rest = _ACTION_TITLE_NOISE_RE.sub("", action_m.group(2)).strip()
                result.append(f"#### Ação {num}: {rest}")
                i += 1
                continue

            # Stage heading → ## (first occurrence per stage only)
            if title in _M5D_STAGES:
                if title not in seen_stages:
                    seen_stages.add(title)
                    current_stage = title
                    result.append(f"## {title}")
                i += 1
                continue

            # Dimension → ### heading, once per (stage, canonical dimension) pair
            canonical_dim = _M5D_DIMENSIONS.get(title)
            if canonical_dim is not None:
                key = (current_stage or "", canonical_dim)
                if key not in seen_stage_dim_pairs:
                    seen_stage_dim_pairs.add(key)
                    result.append(f"### {canonical_dim}")
                i += 1
                continue

            # Annex headings → ## so they break the Ação stack cleanly
            if _ANNEX_HEADING_RE.match(title):
                result.append(f"## {title}")
                i += 1
                continue

            # Subtask items arriving as headings (converter already marked them)
            # → keep as ##### and emit body repeat for single-line subtasks.
            if _PDF_SUBTASK_RE.match(title):
                result.append(f"##### {title}")
                result.append(title)
                i += 1
                continue

            # All other headings (captions, section scaffolding, etc.) → plain text
            result.append(title)
            i += 1
            continue

        # ── Non-heading line ───────────────────────────────────────────
        # Subtask items in plain text → ##### heading + body repeat so
        # single-line subtasks still produce a non-empty chunk.
        if _PDF_SUBTASK_RE.match(stripped):
            result.append(f"##### {stripped}")
            result.append(stripped)
            last_heading_title = None
            i += 1
            continue

        # Skip plain-text echo of last promoted heading
        if stripped and stripped == last_heading_title:
            last_heading_title = None
            i += 1
            continue

        if stripped:
            last_heading_title = None
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

