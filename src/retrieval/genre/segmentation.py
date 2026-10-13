"""Where each document starts and ends inside a PDF file (ADR-0074).

A procurement process is uploaded as a few large PDFs, each a bundle of many
documents: an edital, its minutas, termos de referência, studies, risk
matrices, opinions, acts. The chunk table records pages, not documents. This
module recovers the documents from signals that are general conventions of
Brazilian administrative and procurement documents — none was taken from a
page of a case:

  title    a title line opening with a known document type (EDITAL, MINUTA,
           CONTRATO, TERMO DE REFERÊNCIA, MATRIZ DE RISCO, ESTUDO, PARECER,
           DESPACHO...), found after the printed page number and the letterhead,
           or on any line of a cover page; in CAPS with no final punctuation, or
           in mixed case followed by an identifier ("Parecer nº 12/2024")
  cover    a short page followed by a SUMÁRIO/ÍNDICE or by printed page 2
  restart  the printed page number at the top of the page goes back to 1
           away from the start of a document

A printed page number that continues the previous one (n = previous + 1, or 2
right after a document opened on the previous page) never opens a document,
and a title equal to the current document's title is a running header.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field

from extraction.noise import strip_extraction_noise

from retrieval.genre.classifier import INSTRUMENT, OTHER

# (pattern on the normalised line, document type, genre). Order matters only
# for common prefixes -- the first pattern that matches at the START of the
# line wins: TERMO DE ATESTAÇÃO before TERMO DE REFERÊNCIA, ESTUDO TÉCNICO
# PRELIMINAR before ESTUDO. Generic headings (DECLARAÇÃO, CRONOGRAMA, MANUAL,
# PLANO, DIRETRIZES) are deliberately untyped: such a document is decided by
# the majority of its chunk labels, so a declaration of the ordenador de
# despesas is not filtered out because a contract annex may also be headed
# DECLARAÇÃO.
DOCUMENT_TYPES: tuple[tuple[str, str, str], ...] = (
    (r"TERMOS? DE ATESTACAO", "termo_atestacao", OTHER),
    (r"TERMOS? DE JUSTIFICATIVA", "justificativa", OTHER),
    (r"TERMOS? DE REFERENCIA", "termo_referencia", INSTRUMENT),
    (r"TERMOS? (?:DE CONCESSAO|DE PERMISSAO|ADITIVO|DE CONTRATO|DE PARCERIA)", "contrato", INSTRUMENT),
    (r"ESTUDOS? TECNICOS? PRELIMINAR", "etp", OTHER),
    (r"ESTUDOS?\b", "estudo", OTHER),
    (r"EVTEA\b", "estudo", OTHER),
    (r"EDITA(?:L|IS)\b", "edital", INSTRUMENT),
    (r"INSTRUMENTO CONVOCATORIO", "edital", INSTRUMENT),
    (r"MINUTAS?\b", "minuta", INSTRUMENT),
    (r"CONTRATOS?\b", "contrato", INSTRUMENT),
    (r"PROJETO BASICO", "projeto_basico", INSTRUMENT),
    (r"ANTEPROJETO", "anteprojeto", INSTRUMENT),
    (r"CADERNO DE (?:ENCARGOS|ESPECIFICACOES)", "caderno_encargos", INSTRUMENT),
    (r"ESPECIFICACO(?:ES|AO) TECNICAS?", "especificacao", INSTRUMENT),
    (r"MEMORIAL DESCRITIVO", "especificacao", INSTRUMENT),
    (r"MATRIZ(?:ES)? DE (?:ALOCACAO DE )?RISCOS?", "matriz_riscos", INSTRUMENT),
    (r"MODELOS?\b", "modelo", INSTRUMENT),
    (r"(?:SISTEMA DE )?(?:MENSURACAO|AVALIACAO) DE DESEMPENHO", "indicadores", INSTRUMENT),
    (r"(?:QUADRO DE )?INDICADORES DE DESEMPENHO", "indicadores", INSTRUMENT),
    (r"MECANISMO DE PAGAMENTO", "mecanismo_pagamento", INSTRUMENT),
    (r"MAPA DE RISCOS?", "mapa_riscos", OTHER),
    (r"JUSTIFICATIVA", "justificativa", OTHER),
    (r"DOCUMENTO DE FORMALIZACAO", "formalizacao_demanda", OTHER),
    (r"PARECER", "parecer", OTHER),
    (r"NOTA (?:TECNICA|JURIDICA|INFORMATIVA)", "nota", OTHER),
    (r"MANIFESTACAO", "manifestacao", OTHER),
    (r"RELATORIO", "relatorio", OTHER),
    (r"INFORMACAO (?:TECNICA|N\b)", "informacao", OTHER),
    (r"DESPACHO", "despacho", OTHER),
    (r"OFICIO", "oficio", OTHER),
    (r"MEMORANDO", "memorando", OTHER),
    (r"CERTIDAO", "certidao", OTHER),
    (r"ATA\b", "ata", OTHER),
    (r"AVISO\b", "aviso", OTHER),
    (r"EXTRATO\b", "extrato", OTHER),
    (r"PORTARIA", "portaria", OTHER),
    (r"COMUNICACAO INTERNA", "comunicacao", OTHER),
)
_TYPES = tuple((re.compile(p), t, g) for p, t, g in DOCUMENT_TYPES)

# An annex prefix before the type: "ANEXO I-A -", "ANEXO III:", "ANEXO AO RIPM -".
_ANNEX_PREFIX = re.compile(r"^ANEXO\b[^:]{0,30}?(?:\s-|\s?:)\s*")
_ANNEX_ALONE = re.compile(r"^ANEXO\b[^:]{0,30}?(?:\s-|\s?:)?\s*$")
# The identifier of an act after its type, for mixed-case titles.
_IDENTIFIER = re.compile(r"\b(?:N|NO|NR|NUMERO)\s*\.?\s*\d|\b[A-Z]{2,}(?:/[A-Z0-9-]+){1,}|\b\d{1,5}/\d{2,4}\b")
# Letterhead: short lines naming the body, the process or the sheet.
_LETTERHEAD = re.compile(
    r"^(?:PREFEITURA|GOVERNO|ESTADO D|MUNICIPIO|SECRETARIA|SUBSECRETARIA|PROCURADORIA|GABINETE|COMPANHIA|"
    r"CONTROLADORIA|TRIBUNAL|COMITE|COORDENADORIA|DIRETORIA|ASSESSORIA|CLASSIF|PROCESSO|DATA\s*:|FLS?\b|"
    r"RUBRICA|TELEFONE|TEL\b|E-?MAIL|CEP\b|RUA\b|AV\b|AVENIDA|CONCORRENCIA|LICITACAO\s+N|\d{2}\.\d{2}\.\d{2})"
)
_LETTERHEAD_MAX_WORDS = 14
_PAGE_NUMBER = re.compile(r"^\d{1,3}$")
_TABLE_OF_CONTENTS = re.compile(r"^(?:SUMARIO|INDICE)\b")
_TITLE_MAX_CHARS = 160
_TITLE_MIN_LETTERS = 4
_TITLE_CAPS_SHARE = 0.85
_MIXED_CASE_TITLE_LINES = 12
COVER_MAX_WORDS = 170


def normalise(line: str) -> str:
    """Upper case, accents and dash variants removed, whitespace collapsed."""
    s = unicodedata.normalize("NFKD", line)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("–", "-").replace("—", "-").replace("•", " ")
    return " ".join(s.upper().split())


def content_lines(text: str) -> list[str]:
    return [x.strip() for x in strip_extraction_noise(text).split("\n") if x.strip()]


def title_type(line: str, mixed_case: bool = False) -> tuple[str, str] | None:
    """(document type, genre) when the line is a document title, else None."""
    if len(line) > _TITLE_MAX_CHARS or line[-1] in ".;,":
        return None
    letters = [c for c in line if c.isalpha()]
    if len(letters) < _TITLE_MIN_LETTERS:
        return None
    norm = _ANNEX_PREFIX.sub("", normalise(line))
    caps = sum(c.isupper() for c in letters) / len(letters)
    for rx, doc_type, genre in _TYPES:
        m = rx.match(norm)
        if not m:
            continue
        if caps >= _TITLE_CAPS_SHARE:
            return doc_type, genre
        if mixed_case and _IDENTIFIER.search(norm[m.end():m.end() + 60]):
            return doc_type, genre
        return None
    return None


def page_title(lines: list[str], cover: bool) -> tuple[str, str, str] | None:
    """(type, genre, title text) of the page's title line, if any.

    On a cover page any line may be the title; elsewhere it is the first
    content line after the letterhead (an "ANEXO X -" line on its own joins
    the next one), or a mixed-case line with an identifier among the first
    lines.
    """
    if cover:
        for i, line in enumerate(lines):
            found = title_type(line)
            if found:
                return found + (line,)
            if _ANNEX_ALONE.match(normalise(line)) and i + 1 < len(lines):
                found = title_type(lines[i + 1])
                if found:
                    return found + (line + " " + lines[i + 1],)
        return None
    i = 0
    while (
        i < len(lines)
        and _LETTERHEAD.match(normalise(lines[i]))
        and len(lines[i].split()) <= _LETTERHEAD_MAX_WORDS
    ):
        i += 1
    if i < len(lines):
        line = lines[i]
        if _ANNEX_ALONE.match(normalise(line)) and i + 1 < len(lines):
            found = title_type(lines[i + 1])
            if found:
                return found + (line + " " + lines[i + 1],)
        found = title_type(line)
        if found:
            return found + (line,)
    for line in lines[:_MIXED_CASE_TITLE_LINES]:
        found = title_type(line, mixed_case=True)
        letters = sum(c.isalpha() for c in line)
        if found and not sum(c.isupper() for c in line if c.isalpha()) >= _TITLE_CAPS_SHARE * letters:
            return found + (line,)
    return None


@dataclass
class Page:
    page_number: int
    printed_number: int | None
    words: int
    lines: list[str]
    table_of_contents: bool
    chunk_indexes: list[int]


@dataclass
class Segment:
    """One document inside a file: its page range and how it was recognised."""

    page_start: int
    page_end: int
    start_reason: str            # file_start | cover | title | restart
    doc_type: str | None = None
    genre: str | None = None     # from the title's type; None = decided by chunk labels
    title: str | None = None
    pages: list[int] = field(default_factory=list)


def pages_by_file(rows: Iterable[tuple[str, int, int, str]]) -> dict[str, list[Page]]:
    """rows (filename, page, chunk_index, text) -> {filename: [Page] in page order}.

    The page's lines are those of its first chunk (where a title sits); its
    word count is over all its chunks.
    """
    by_file: dict[str, dict[int, list[tuple[int, str]]]] = {}
    for filename, page, chunk_index, text in rows:
        by_file.setdefault(filename, {}).setdefault(page, []).append((chunk_index, text))
    out: dict[str, list[Page]] = {}
    for filename, by_page in by_file.items():
        pages = []
        for page in sorted(by_page):
            chunks = sorted(by_page[page])
            lines = content_lines(chunks[0][1])
            printed = None
            if lines and _PAGE_NUMBER.match(lines[0]):
                printed = int(lines[0])
                lines = lines[1:]
            pages.append(Page(
                page_number=page,
                printed_number=printed,
                words=sum(len(text.split()) for _c, text in chunks),
                lines=lines,
                table_of_contents=any(_TABLE_OF_CONTENTS.match(normalise(x)) for x in lines[:3]),
                chunk_indexes=[c for c, _t in chunks],
            ))
        out[filename] = pages
    return out


def segment_file(pages: list[Page]) -> list[Segment]:
    """The documents of one file, in page order."""
    segments: list[Segment] = []
    previous_printed: int | None = None
    for i, page in enumerate(pages):
        following = pages[i + 1] if i + 1 < len(pages) else None
        printed = page.printed_number
        current = segments[-1] if segments else None
        # The printed numbering continues: n = previous + 1, or page 2 right
        # after a document whose first page (a cover) carries no number.
        continues = printed is not None and printed >= 2 and (
            (previous_printed is not None and printed == previous_printed + 1)
            or (printed == 2 and current is not None and current.page_start == page.page_number - 1)
        )
        cover = (
            page.words <= COVER_MAX_WORDS and not continues and following is not None
            and (following.table_of_contents or following.printed_number == 2)
        )
        title = page_title(page.lines, cover or page.words <= COVER_MAX_WORDS)
        reason = None
        # The first page after a cover repeats the cover's type: same document.
        after_cover = (
            current is not None and current.start_reason == "cover"
            and current.page_start == page.page_number - 1
            and title is not None and current.doc_type == title[0]
        )
        untyped_cover_before = (
            current is not None and current.start_reason == "cover" and current.doc_type is None
            and page.page_number - current.page_start == 1
        )
        if not continues and not after_cover:
            if cover:
                reason = "cover"
            elif title and not (
                current and current.title and normalise(current.title) == normalise(title[2])
            ):
                if untyped_cover_before:
                    current.doc_type, current.genre, current.title = title
                else:
                    reason = "title"
            elif printed == 1 and current is not None and page.page_number - current.page_start > 2:
                reason = "restart"
        elif title and untyped_cover_before:
            current.doc_type, current.genre, current.title = title
        if reason or current is None:
            segment = Segment(
                page_start=page.page_number,
                page_end=page.page_number,
                start_reason=reason or "file_start",
            )
            if title:
                segment.doc_type, segment.genre, segment.title = title
            segment.pages.append(page.page_number)
            segments.append(segment)
        else:
            current.page_end = page.page_number
            current.pages.append(page.page_number)
        previous_printed = printed
    return segments
