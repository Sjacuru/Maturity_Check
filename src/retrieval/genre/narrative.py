"""Narrative sections of instrument documents (ADR-0077).

An edital, a termo de referência or a contract usually opens with sections
that describe instead of prescribe: the introduction, the context and history
of the project, its justification. Those passages carry the project's own
account of its objectives and motivation, which several IPMP products ask for,
and they are not the normative text the genre filter (ADR-0074) keeps away
from the gate. This module finds them, so the filter can let them through.

A section is narrative when its TITLE is one of these general conventions of
Brazilian procurement drafting (none was taken from a page of a case,
ADR-0073):

  INTRODUÇÃO, APRESENTAÇÃO, CONTEXTO, CONTEXTUALIZAÇÃO, HISTÓRICO,
  ANTECEDENTES, JUSTIFICATIVA, MOTIVAÇÃO, DIAGNÓSTICO, SITUAÇÃO ATUAL,
  BREVE ANÁLISE, ANÁLISE PRELIMINAR, CONSIDERAÇÕES INICIAIS/FINAIS, CONCLUSÃO

CRONOGRAMA is deliberately absent: a schedule annex of an instrument says
what will happen, not that it happened, and in test cycle 11 its only effect
was a confusion (ADR-0077).

The title opens the section; it ends at the next title of the same level or
higher ("2." closes "1."; "1.4" does not). When the extraction puts a section
number alone on its line ("1." then "INTRODUÇÃO"), the title takes that
number's level. A section opened by an unnumbered title ends at the next
unnumbered title standing alone on its line. A document whose own title is
narrative (an annex named after one of the titles above) is narrative as a
whole. A chunk belongs to a narrative section when half or more of its
noise-stripped text lies inside one. Table-of-contents lines (dot leaders or a
page number at the end) are not titles. The "considerandos" of a minuta are
not a section and never count.
"""

from __future__ import annotations

import re
import unicodedata

from extraction.noise import strip_extraction_noise

_NARRATIVE_TITLE = re.compile(
    r"^(?:INTRODUCAO|APRESENTACAO|CONTEXTO|CONTEXTUALIZACAO|HISTORICO|ANTECEDENTES|"
    r"JUSTIFICATIVAS?|MOTIVACAO|DIAGNOSTICO|SITUACAO ATUAL|BREVE ANALISE|ANALISE PRELIMINAR|"
    r"CONSIDERACOES (?:INICIAIS|FINAIS)|CONCLUS(?:AO|OES))\b"
)
_NUMBERED = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s*[-–—)]?\s+(\S.*)$")
_NUMBER_ONLY = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.\s*$")
_ANNEX_PREFIX = re.compile(r"^ANEXO\s+[IVXLC]+(?:\s*-\s*[A-Z])?\s*[-–—:]\s*")
_ANNEX_TITLE = re.compile(r"\bANEXO\s+[IVXLC]+(?:\s*-\s*[A-Z])?\s*-\s*([A-Z][A-Z ,/]{3,60})")
_TABLE_OF_CONTENTS = re.compile(r"\.{4,}|\s\d{1,3}\s*$")
_SENTENCE_END = re.compile(r"[.;:!?]\s*$")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.replace("–", "-").replace("—", "-")).strip().upper()


def _uppercase_share(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum(c.isupper() for c in letters) / len(letters) if letters else 0.0


def _short_title(text: str) -> bool:
    return (0 < len(text.split()) <= 10 and not re.search(r"[.;,]\s*$", text)
            and not _TABLE_OF_CONTENTS.search(text))


def heading(line: str, previous: str) -> tuple[int, str] | None:
    """(level, normalized title) when the line is a section title; level 0 =
    an unnumbered title. `previous` is the last non-blank line before it."""
    text = line.strip()
    if not text:
        return None
    alone = _NUMBER_ONLY.match(previous.strip())
    if alone and not _NUMBERED.match(text):
        text = f"{alone.group(1)}. {text}"
    numbered = _NUMBERED.match(text)
    if numbered:
        level, title = numbered.group(1).count(".") + 1, numbered.group(2).strip()
        if _short_title(title) and (_uppercase_share(title) >= 0.7
                                    or (level == 1 and len(title.split()) <= 6)):
            return level, _norm(title)
        return None
    standalone = (not previous.strip() or previous.strip().isdigit()
                  or _SENTENCE_END.search(previous))
    if _short_title(text) and _uppercase_share(text) >= 0.9 and len(text.split()) <= 8 and standalone:
        return 0, _norm(text)
    return None


def is_narrative_title(title: str) -> bool:
    return bool(_NARRATIVE_TITLE.match(_ANNEX_PREFIX.sub("", _norm(title))))


def narrative_sections(
    chunks: list[tuple[int, int, str]],
    document_title: str | None,
) -> dict[tuple[int, int], str]:
    """{(page, chunk_index): narrative section title} for one instrument document.

    `chunks` are (page, chunk_index, text) of the document, in any order.
    """
    chunks = sorted(chunks)
    if not chunks:
        return {}
    first_page = chunks[0][0]
    top = " ".join(_norm(line) for p, _c, t in chunks if p == first_page
                   for line in strip_extraction_noise(t or "").splitlines())
    annex = _ANNEX_TITLE.search(top)
    if document_title and is_narrative_title(document_title):
        return {(p, c): _norm(document_title) for p, c, _t in chunks}
    if annex and is_narrative_title(annex.group(1)):
        return {(p, c): _norm(annex.group(0)) for p, c, _t in chunks}

    out: dict[tuple[int, int], str] = {}
    open_section: tuple[int, str] | None = None  # (level that opened it, title)
    for page, chunk_index, text in chunks:
        inside = outside = 0
        seen = open_section[1] if open_section else None
        previous = "."
        for line in strip_extraction_noise(text or "").splitlines():
            found = heading(line, previous)
            if found:
                level, title = found
                if open_section is not None:
                    opened = open_section[0]
                    if (level != 0 and opened != 0 and level <= opened) or (level == 0 and opened == 0):
                        open_section = None
                if open_section is None and is_narrative_title(title):
                    open_section = (level, title)
                    seen = seen or title
            size = len(line.strip())
            if open_section is not None:
                inside += size
            else:
                outside += size
            if line.strip():
                previous = line
        if inside and inside >= outside:
            out[(page, chunk_index)] = seen
    return out
