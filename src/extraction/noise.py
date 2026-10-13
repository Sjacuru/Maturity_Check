from __future__ import annotations

import re

# Deterministic stripping of mechanical PDF-extraction noise (repeated
# header/address block, digital-signature block, version tag, vertically-
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

_SIGNATURE_BLOCK_RE = re.compile(
    r"(SMGPRO\d+V\d+\s*\n(MINUTA\s*\n)?)?"
    r"Autenticado digitalmente por .+? [aà]s \d{2}:\d{2}:\d{2}\.\s+"
    r"Documento N[ºo°]:.+?consulta [aà] autenticidade em\s+"
    r"https?://\S+\s*",
    re.IGNORECASE | re.DOTALL,
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
    text = _SIGNATURE_BLOCK_RE.sub("", text)
    text = _BARE_VERSION_TAG_RE.sub("", text)
    text = _WATERMARK_RUN_RE.sub("", text)
    return text.strip()
