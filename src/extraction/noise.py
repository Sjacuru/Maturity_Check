from __future__ import annotations

import re

# Deterministic stripping of mechanical PDF-extraction noise (repeated
# header/address block, digital-signature stamp, version tag, vertically-
# rotated watermark) — applied before the chunk text ever reaches the LLM
# gate. The gate itself no longer attempts any further cleaning (dropped
# 2026-06-29): regenerating a cleaned copy of the chunk cost 50-86s per accept
# vs. ~4s for a bare yes/no, and the cleaning was unreliable enough (silent
# early-stop, few-shot regurgitation — see ADR-0050 amendments) that its
# output was rarely usable anyway. This deterministic pass is the only
# cleaning that happens now.
#
# Lives in extraction since 2026-10-13 (ADR-0074): the genre classifier in
# retrieval reads the same cleaned text the gate reads, and retrieval cannot
# import from evaluation. evaluation.evidence_selection re-exports it.
_HEADER_RE = re.compile(
    r"PREFEITURA DA CIDADE DO RIO DE JANEIRO\s*\n"
    r"Secretaria Municipal de Coordena[cç][aã]o Governamental\s*\n"
    # "Cavalcanti" — PDF ligature extraction sometimes mangles "ti" into a
    # single substitute glyph (observed: "Ɵ") or a 2-char CJK look-alike
    # (observed: "琀椀"); match either the clean spelling or 1-2 stand-in chars.
    r"R\. Afonso Cavalcan(?:ti|\S{1,2}), 455 [–-] Cidade Nova\s*\n"
    r"Rio de Janeiro - RJ - CEP 20211-110\s*\n?",
    re.IGNORECASE,
)

# The stamp an electronic-process system prints on every page it signs or
# authenticates: "Assinado com senha por NOME - dd/mm/aaaa às hh:mm:ss." or
# "Autenticado digitalmente por NOME - ...", then "Documento Nº: N - consulta
# à autenticidade em <url>". It names the signer and the document number, so
# the gate and the scorer would read them as part of the passage. Covered
# since 2026-10-16: both verbs, the three ways of signing, a cargo between the
# name and the date, a date written out ("24 de Maio de 2024", the Diário
# Oficial's own stamp), a stamp cut anywhere after the date, the url wrapped
# onto the next line ("...?n=6220934-" / "6610"), and the system logo the OCR
# reads after it ("SIGA"). Only a capital "A" at the start of a line opens a
# stamp, and only with a date and time on that line or the next: an edital
# clause saying a document "deverá ser assinado digitalmente por" its signer
# is not a stamp.
_STAMP_HEAD = (
    r"A(?i:(?:ssinad|utenticad)[oa][ \t]+(?:com[ \t]+senha|digitalmente|eletronicamente)[ \t]+por)"
    r"[ \t]+"
)
_STAMP_DATE_TIME = (
    r"(?:\d{2}/\d{2}/\d{4}|\d{1,2}[ \t]+de[ \t]+(?i:janeiro|fevereiro|mar[çc]o|abril|maio|junho|"
    r"julho|agosto|setembro|outubro|novembro|dezembro)[ \t]+de[ \t]+\d{4})"
    r",?[ \t]+(?:[àa]s[ \t]+)?\d{1,2}:\d{2}(?::\d{2})?"
)
_STAMP_VALIDATION = (
    r"(?:\s*Documento[ \t]+N[ºo°][ \t]*:?[ \t]*[\w.\-/]*)?"
    r"(?:[ \t]*-(?:[ \t]*consulta(?:\s+[àa](?:\s+autenticidade(?:\s+em)?)?)?)?)?"
    r"(?:\s*https?:/{0,2}[^\n]*)?"
    r"(?:\s*\n[ \t]*\d{1,8}(?:[ \t]+[A-Z]{1,6})?[ \t]*(?=\n|\Z))?"
)
_SIGNATURE_STAMP_RE = re.compile(
    r"(?:^SMGPRO\d+V\d+[ \t]*\n(?:MINUTA[ \t]*\n)?)?"
    r"^[ \t]*" + _STAMP_HEAD + r"[^\n]*?(?:\n[^\n]*?)??" + _STAMP_DATE_TIME + r"[^\n]*"
    + _STAMP_VALIDATION + r"\s*",
    re.MULTILINE,
)

# A stamp the chunker cut before its date: the chunk ends inside the signer's
# name ("Autenticado digitalmente por VALMIR DE").
_SIGNATURE_STAMP_CUT_RE = re.compile(
    r"^[ \t]*" + _STAMP_HEAD + r"[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ .'\-]*\s*\Z",
    re.MULTILINE,
)

# The rest of a stamp the chunker cut, opening the next chunk: the url alone
# ("em" / "autenticidade em" / "consulta à autenticidade em" + url), or the end
# of the signer's name followed by the date and the document number.
_SIGNATURE_STAMP_TAIL_RE = re.compile(
    r"\A\s*(?:"
    r"(?:consulta\s+[àa]\s+)?autenticidade\s+em\s+https?:/{0,2}[^\n]*"
    r"|em\s+https?:/{0,2}\S*autentic[^\n]*"
    r"|[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ .'\-]*?(?:[ \t]+-[ \t]+[^\n]{1,60}?)?[ \t]+-[ \t]+" + _STAMP_DATE_TIME
    + r"[^\n]*(?=\s*Documento[ \t]+N[ºo°])" + _STAMP_VALIDATION
    + r")"
    r"(?:\s*\n[ \t]*\d{1,8}(?:[ \t]+[A-Z]{1,6})?[ \t]*(?=\n|\Z))?\s*"
)

# A validation url on a line of its own, with no stamp around it (a scanned
# page whose stamp the OCR read only in part).
_VALIDATION_URL_LINE_RE = re.compile(
    r"^[ \t]*(?:https?:/{0,2})?\S*/autenticar\?n=\S*(?:[ \t]+[A-Z]{1,6})?[ \t]*(?:\n|\Z)",
    re.MULTILINE,
)

_BARE_VERSION_TAG_RE = re.compile(r"^SMGPRO\d+V\d+\s*\n(MINUTA\s*\n)?", re.MULTILINE)

# Vertically-rotated margin watermark, extracted one glyph per line by the PDF
# layout parser ("processo.rio Secretaria Municipal de... / SMG###"). Any run
# of 10+ consecutive single-character (or blank) lines is this artifact, never
# real prose; the trailing short alphanumeric line is the page-number tail,
# which doesn't get split the same way as the rest of the stamp.
_WATERMARK_RUN_RE = re.compile(r"(?:^[^\n]?\n){10,}(?:^[A-Za-z0-9]{1,6}\n?)?", re.MULTILINE)


def strip_extraction_noise(text: str) -> str:
    text = _HEADER_RE.sub("", text)
    text = _SIGNATURE_STAMP_RE.sub("", text)
    text = _SIGNATURE_STAMP_TAIL_RE.sub("", text)
    text = _VALIDATION_URL_LINE_RE.sub("", text)
    text = _BARE_VERSION_TAG_RE.sub("", text)
    text = _WATERMARK_RUN_RE.sub("", text)
    text = text.strip()
    return _SIGNATURE_STAMP_CUT_RE.sub("", text).strip()
