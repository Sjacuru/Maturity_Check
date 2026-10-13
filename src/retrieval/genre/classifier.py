"""Chunk-level genre: is this the text of a procurement INSTRUMENT, or OTHER text?

INSTRUMENTO is the text of a contracting instrument: a contract or its draft
(minuta), an edital, a termo de referência and their normative annexes (risk
matrix, forms, performance and payment mechanisms). OUTRO is everything else a
procurement process carries: studies, the ETP, opinions, notes, justifications,
administrative acts.

Every marker below is a general drafting convention of Brazilian procurement
instruments (Lei 14.133/2021, Lei 8.987/1995, Lei 11.079/2004); none was taken
from a page of a case (ADR-0073, ADR-0074):

  self_reference   "este CONTRATO", "do presente EDITAL", "neste ANEXO"
  deontic          a defined party in CAPS and a deontic verb in the same sentence,
                   or the party as subject of a future-tense verb ("O PODER
                   CONCEDENTE examinará")
  prescriptive     impersonal prescriptive voice: "serão aceitos", "fica vedado"
  enumerated       (i)/(a) items opening with an infinitive (a list of duties)
  numbered_dash    numbered clause followed by a dash: "16.5 - Os atestados"
  titled_clause    numbered clause with a short title: "30.5. Relatório Técnico. O"
  definition       a CAPS term between quotes (a definitions list)
  placeholder      form fields of a minuta or model: [LICITANTE], [•]
  matrix_row       a risk-matrix row (COMPARTILHADO, or a party followed by a dash)
                   or a risk allocated to a party ("riscos assumidos pela
                   CONCESSIONÁRIA"; Lei 11.079 art. 5 III, Lei 14.133 art. 6 XXVII)
  procedure        bidding-procedure terms (LICITANTE, ENVELOPE, SESSÃO PÚBLICA)
  sanction         sanction grades LEVE/MÉDIA/GRAVE/GRAVÍSSIMA, "por ocorrência"
  caps_share       share of CAPS words (defined terms, the lists and tables of a TR)
  clause_reference "nas Cláusulas 29 e 30", "subcláusula 12.3"
  semicolon_list   "...; (v) ...; (vi) ..." enumerations

Counter-markers: the voice of who analyses or reports (estimou-se,
considerou-se, parecer, premissas, fluxo de caixa, VPL...) and the voice of an
administrative act (DESPACHO, CERTIDÃO, AUTORIZO, Assunto:, a dateline
"<Cidade>, dd de <mês>").

Decision per chunk: INSTRUMENTO, OUTRO or INDECISO (a short chunk with little
signal either way). An INDECISO chunk takes the label of chunk 0 of its page,
else the strict majority of the firm chunk-0 labels within two pages of the
same file, else OUTRO. In doubt, OUTRO: excluding a legitimate passage costs
more than keeping one of instrument text.

This is the chunk-level vote. What the evidence filter reads is the genre of
the whole DOCUMENT the chunk belongs to (segmentation.py, index.py); the chunk
labels only decide documents whose title does not name a known type.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

from extraction.noise import strip_extraction_noise

INSTRUMENT = "INSTRUMENTO"
OTHER = "OUTRO"
UNDECIDED = "INDECISO"

_UPPER = "A-ZÁÉÍÓÚÂÊÔÃÕÇÀÜ"
_PARTY = (
    r"(?:PODER CONCEDENTE|PODER P[ÚU]BLICO|CONCESSION[ÁA]RIAS?|CONTRATANTES?|CONTRATAD[AO]S?|"
    r"PARCEIRO P[ÚU]BLICO|PARCEIRO PRIVADO|LICITANTES?|ADJUDICAT[ÁA]RI[AO]S?|CONS[ÓO]RCIOS?|SPE|"
    r"PARTES?|VERIFICADOR INDEPENDENTE|ENTIDADE FISCALIZADORA|FINANCIADOR(?:ES)?|"
    r"PARTICIPANTES? CREDENCIAD[AO]S?|COMISS[ÃA]O DE (?:LICITA|CONTRATA)[ÇC][ÃA]O)"
)
_RE_PARTY = re.compile(r"\b" + _PARTY + r"\b")
_DEONTIC = re.compile(
    r"\b(?:dever[áã]o?|poder[áã]o?|caber[áã]o?|competir[áa]|obriga-se|obrigam-se|se obrigam?|"
    r"fica(?:r[áa]|m|r[ãa]o)? (?:obrigad|vedad|facultad|respons[áa]ve)\w*|ser[áã]o? (?:de )?respons[áa]v\w*|"
    r"responder[áã]o?|arcar[áã]o?|assumir[áã]o?|ter[áã]o? direito|[ée] vedad[oa]|[ée] facultad[oa]|"
    r"sob pena de|far[áã]o? jus|incumbe|incumbir[áa])\b",
    re.I,
)
_FUTURE = re.compile(r"\b[a-záéíóúâêôãõç]{2,}(?:ará|erá|irá|arão|erão|irão|ar-se-á|er-se-á)\b")
_PRESCRIPTIVE = re.compile(
    r"\b(?:n[ãa]o )?ser[áã]o? (?:aceit|admitid|exigid|aplicad|julgad|processad|devid|pag|cobrad|"
    r"realizad|executad|apresentad|assinad|emitid|publicad|recebid|reajustad|atualizad|mantid|"
    r"observad|inabilitad|desclassificad|rescindid|extint|computad|descontad|regid|conduzid)\w*\b"
    r"|\bfica(?:m)? (?:vedad|proibid|facultad|estabelecid|assegurad)\w*",
    re.I,
)
_SELF_REFERENCE = re.compile(
    r"\b(?:este|esta|deste|desta|neste|nesta|do presente|da presente|no presente|na presente|o presente|"
    r"a presente|pelo presente)\s+(?:contrato|edital|termo de refer[êe]ncia|anexo|instrumento|minuta|"
    r"licita[çc][ãa]o|concorr[êe]ncia)\b",
    re.I,
)
_ENUMERATED = re.compile(
    r"\((?:[ivxlc]{1,6}|[a-z])\)\s+(?:n[ãa]o\s+)?[A-ZÁÉÍÓÚa-záéíóú][a-záéíóúçãõâêô]{2,}(?:ar|er|ir)(?:-se)?\b"
)
_NUMBERED_DASH = re.compile(r"(?:^|\s)\d{1,2}(?:\.\d{1,2}){1,3}\.?\s+[–—-]\s+[A-ZÁÉÍÓÚ]")
_TITLED_CLAUSE = re.compile(
    r"(?:^|\s)\d{1,2}\.\d{1,2}(?:\.\d{1,2})?\.\s+[A-ZÁÉÍÓÚ][^.;:\d]{2,55}\.\s+[A-ZÁÉÍÓÚ(]"
)
_DEFINITION = re.compile(r"[“\"<«]\s*[" + _UPPER + r"0-9][" + _UPPER + r"0-9 \-–/,]{2,}[”\"=»]")
_PLACEHOLDER = re.compile(r"\[(?:[•·.\s]{1,6}|[^\]\[]{2,30})\]")
_MATRIX_ROW = re.compile(r"\b(?:COMPARTILHADO|COMPARTILHADA)\b|\b" + _PARTY + r"\s+[-–•]\s+[A-ZÁÉÍÓÚ]")
_RISK_ALLOCATED = re.compile(
    r"\briscos?\s+(?:[a-záéíóúçãõ]+\s+){0,2}?(?:assumid|alocad|suportad|atribu[íi]d|transferid)\w*\s+"
    r"(?:exclusivamente\s+)?(?:pel[ao]s?|[àa]s?|aos?|d[ao]s?)\s+" + _PARTY,
    re.I,
)
_PROCEDURE = re.compile(
    r"\b(?:LICITANTES?|ENVELOPES?|SESS[ÃA]O P[ÚU]BLICA|PROPOSTAS? (?:ECON[ÔO]MICAS?|COMERCIA(?:L|IS))|"
    r"DOCUMENTOS DE HABILITA[ÇC][ÃA]O|GARANTIA DE PROPOSTA|DIRETOR DA SESS[ÃA]O|REPRESENTANTE CREDENCIADO|"
    r"PARTICIPANTES? CREDENCIAD[AO]S?)\b"
)
_SANCTION = re.compile(
    r"\b(?:LEVE|M[ÉE]DIA|GRAVE|GRAV[ÍI]SSIMA)\b|infra[çc][ãa]o (?:ser[áa] considerada|de natureza) "
    r"(?:leve|m[ée]dia|grave|grav[íi]ssima)|\bpor ocorr[êe]ncia\b",
    re.I,
)
_CLAUSE_REFERENCE = re.compile(
    r"\b(?:[Cc]l[áa]usulas?|[Ss]ubcl[áa]usulas?|CL[ÁA]USULAS?)\s+\d{1,2}(?:\.\d{1,2})*"
)
_SEMICOLON_LIST = re.compile(r";\s*(?:e,?\s+|ou\s+)?\((?:[ivxlc]{1,6}|[a-z])\)\s")
_CAPS_WORD = re.compile(r"[" + _UPPER + r"]{3,}[,.;:)]?")

# The dateline of an act or letter: "<Cidade>, dd de <mês>". The prototype
# named the case's city; the city is any capitalised place name.
_PLACE = (
    r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+"
    r"(?: (?:d[aeo]s? )?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)*"
)
_MONTH = (
    r"(?i:janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
)
_DATELINE = _PLACE + r", \d{1,2}[º°]? de " + _MONTH + r"\b"
_ACT = re.compile(
    r"\b(?:DESPACHO|CERTID[ÃA]O|AUTORIZO|HOMOLOGO|ADJUDICO|CERTIFICO|Certifico que|OF[ÍI]CIO|MEMORANDO|"
    r"Assunto:|Matr[íi]cula:?|Atenciosamente|PROCURADORA?|ASSESSORA?|Encaminho|Solicito|"
    + _DATELINE
    + r")"
)
_ANALYSIS = re.compile(
    r"\b(?:estimou-se|estima-se|considerou-se|adotou-se|utilizou-se|optou-se|conclui-se|"
    r"observa-se|verifica-se|entende-se|vislumbra-se|ressalta-se|destaca-se|sugere-se|recomenda-se|"
    r"foram (?:considerad|analisad|utilizad|adotad|estimad|levantad|projetad|identificad|avaliad)\w*|"
    r"levou em considera[çc][ãa]o|para o c[áa]lculo|opina(?:-se|mos)?|opini[ãa]o|parecer|procuradoria|"
    r"assessoria|encaminhe-se|publique-se|ante o exposto|diante do exposto|trata-se de|cuida-se de|"
    r"em resposta|em aten[çc][ãa]o|s\.m\.j|estudos?|premissas?|metodologia|modelagem|cen[áa]rios?|"
    r"benchmark\w*|fluxo de caixa|vpl|tir|ebitda|capex|opex|fls?\.\s*\d+)",
    re.I,
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.;:!?])\s+")


def _sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def chunk_measures(text: str) -> dict[str, float]:
    """Marker counts of one chunk, over its noise-stripped, whitespace-joined text."""
    t = " ".join(strip_extraction_noise(text).split())
    words = t.split()
    n_words = max(1, len(words))
    sentences = _sentences(t)
    deontic = sum(1 for s in sentences if _RE_PARTY.search(s) and _DEONTIC.search(s))
    future_party = sum(
        1 for s in sentences
        if _RE_PARTY.search(s) and _FUTURE.search(s) and not _DEONTIC.search(s)
    )
    risk_allocated = len(_RISK_ALLOCATED.findall(t))
    return {
        "words": n_words,
        "self_reference": len(_SELF_REFERENCE.findall(t)),
        "deontic": deontic + future_party,
        "future_party": future_party,
        "prescriptive": len(_PRESCRIPTIVE.findall(t)),
        "enumerated": len(_ENUMERATED.findall(t)),
        "numbered_dash": len(_NUMBERED_DASH.findall(t)),
        "titled_clause": len(_TITLED_CLAUSE.findall(t)),
        "definition": len(_DEFINITION.findall(t)),
        "placeholder": len(_PLACEHOLDER.findall(t)),
        "matrix_row": len(_MATRIX_ROW.findall(t)) + risk_allocated,
        "risk_allocated": risk_allocated,
        "procedure": len(_PROCEDURE.findall(t)),
        "sanction": len(_SANCTION.findall(t)),
        "caps_share": round(sum(1 for w in words if _CAPS_WORD.fullmatch(w)) / n_words, 3),
        "clause_reference": len(_CLAUSE_REFERENCE.findall(t)),
        "semicolon_list": len(_SEMICOLON_LIST.findall(t)),
        "analysis": len(_ANALYSIS.findall(t)),
        "act": len(_ACT.findall(t)),
    }


def chunk_scores(m: dict[str, float]) -> tuple[int, int]:
    """(instrument score, analysis/act score). Every marker is capped so that
    one repeated device cannot decide a chunk alone."""
    instrument = (
        2 * min(m["self_reference"], 2) + 2 * min(m["deontic"], 3) + min(m["prescriptive"], 3)
        + 2 * min(m["enumerated"], 2) + min(m["sanction"], 3)
        + min(m["numbered_dash"], 2) + min(m["titled_clause"], 2) + min(m["definition"], 3)
        + min(m["placeholder"], 3) + 2 * min(m["matrix_row"], 2) + min(m["procedure"], 3)
        + (1 if m["caps_share"] >= 0.12 else 0) + (1 if m["caps_share"] >= 0.25 else 0)
        + min(m["clause_reference"], 2) + (1 if m["semicolon_list"] >= 2 else 0)
    )
    return int(instrument), int(min(m["analysis"] + m["act"], 6))


def decide_chunk(m: dict[str, float]) -> str:
    """INSTRUMENTO, OUTRO or INDECISO for one chunk, from its own text only."""
    instrument, analysis = chunk_scores(m)
    voice = m["analysis"] + m["act"]
    if voice >= 5 and 2 * voice >= instrument:
        # A strong analysis or act voice: a study or an opinion, even when it
        # quotes the instrument's obligations (annexed studies often repeat them).
        return OTHER
    if m["caps_share"] >= 0.25 and analysis == 0 and m["words"] >= 12:
        return INSTRUMENT  # a CAPS list, table or annex cover with no analysis voice
    if m["words"] < 25:
        return UNDECIDED
    if instrument >= 3 and instrument > 1.5 * analysis:
        return INSTRUMENT
    if analysis >= 2 and analysis >= instrument:
        return OTHER
    if m["words"] >= 80:
        # Long prose with too few instrument markers: a page of contract, edital
        # or TR with 80+ words almost always carries several.
        return OTHER
    return UNDECIDED


def classify_chunks(
    rows: Iterable[tuple[str, int, int, str]],
) -> dict[tuple[str, int, int], tuple[str, str]]:
    """{(filename, page, chunk_index): (label, own_decision)} for one process.

    rows are (filename, page_number, chunk_index, text). label is never
    INDECISO: an undecided chunk inherits from chunk 0 of its page, else from
    the strict majority of firm chunk-0 labels within two pages of the same
    file, else it is OUTRO. A document is continuous, so the neighbouring pages
    are the best evidence of genre when a passage says nothing (a list, a
    table, a signature footer).
    """
    own: dict[tuple[str, int, int], str] = {}
    for filename, page, chunk_index, text in rows:
        own[(filename, page, chunk_index)] = decide_chunk(chunk_measures(text))
    firm = {
        (f, p): label for (f, p, c), label in own.items() if c == 0 and label != UNDECIDED
    }
    out: dict[tuple[str, int, int], tuple[str, str]] = {}
    for (f, p, c), decision in own.items():
        label = decision
        if decision == UNDECIDED:
            same_page = own.get((f, p, 0), UNDECIDED) if c != 0 else UNDECIDED
            if same_page != UNDECIDED:
                label = same_page
            else:
                around = Counter(
                    firm[(f, q)] for q in range(p - 2, p + 3) if q != p and (f, q) in firm
                )
                if around and around.most_common(1)[0][1] > sum(around.values()) / 2:
                    label = around.most_common(1)[0][0]
                else:
                    label = OTHER
        out[(f, p, c)] = (label, decision)
    return out
