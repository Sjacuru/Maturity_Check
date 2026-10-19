"""Variante S: seções narrativas dos documentos de instrumento voltam ao gate (2026-10-19).

Pedido do usuário: "capturar dentre esses casos as páginas/chunks de contratos,
editais e correlacionados aqueles vinculados à introdução, histórico, breve
análise, conclusão, cronograma, que estão presentes em editais, por exemplo e
podem contribuir com algumas das ações em tela. Faça um teste considerando essa
premissa e vamos avaliar o resultado."

Hoje (ADR-0074) todo trecho de um documento de gênero INSTRUMENTO sai antes do
gate para os produtos não isentos. Esta variante devolve ao gate só os trechos
que estão dentro de uma seção cujo TÍTULO é narrativo, segundo uma convenção
geral de redação de editais, termos de referência, contratos e seus anexos
(nenhum título foi tirado de uma página do caso, ADR-0073):

  INTRODUÇÃO, APRESENTAÇÃO, CONTEXTO, CONTEXTUALIZAÇÃO, HISTÓRICO,
  ANTECEDENTES, JUSTIFICATIVA, MOTIVAÇÃO, DIAGNÓSTICO, SITUAÇÃO ATUAL,
  BREVE ANÁLISE, ANÁLISE PRELIMINAR, CONSIDERAÇÕES INICIAIS/FINAIS,
  CONCLUSÃO, CRONOGRAMA

O título abre a seção. Ela termina no próximo título de mesmo nível ou acima
(numeração "2." fecha "1."; "1.4" não fecha "1."). Uma seção aberta por título
sem número termina no próximo título sem número que fica sozinho na linha
(linha anterior terminada em pontuação). Um título que é o do próprio documento
("ANEXO VIII – CRONOGRAMA DA LICITAÇÃO" na primeira página do segmento) libera o
documento inteiro. Um trecho volta ao gate quando metade ou mais do seu texto
limpo (extraction.noise) está dentro de uma seção narrativa. Linhas de sumário
(pontilhado ou número de página no fim) não são títulos. Os "considerandos" de
uma minuta não entram: não são título de seção, e o caso já mostrou um falso
crédito num deles (ADR-0074, ciclo 6, Ação 45).

Nada mais muda: produtos isentos como hoje; os trechos liberados passam pelo
mesmo caminho (quase-duplicatas, corte de 16, gate, expansão, rota focal),
porque a variante só troca o mapa de gênero que evidence_selection lê.

Usada por: reproducibility.py --narrative-sections. Nada em src/ muda.
"""

from __future__ import annotations

import re
import unicodedata

_NARRATIVO = re.compile(
    r"^(?:INTRODUCAO|APRESENTACAO|CONTEXTO|CONTEXTUALIZACAO|HISTORICO|ANTECEDENTES|"
    r"JUSTIFICATIVAS?|MOTIVACAO|DIAGNOSTICO|SITUACAO ATUAL|BREVE ANALISE|ANALISE PRELIMINAR|"
    r"CONSIDERACOES (?:INICIAIS|FINAIS)|CONCLUS(?:AO|OES)|CRONOGRAMAS?)\b"
)
_NUMERADO = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s*[-–—)]?\s+(\S.*)$")
_ANEXO = re.compile(r"^ANEXO\s+[IVXLC]+(?:\s*-\s*[A-Z])?\s*[-–—:]\s*")
_SUMARIO = re.compile(r"\.{4,}|\s\d{1,3}\s*$")
_FIM_FRASE = re.compile(r"[.;:!?]\s*$")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.replace("–", "-").replace("—", "-")).strip().upper()


def _maiusculas(s: str) -> float:
    letras = [c for c in s if c.isalpha()]
    return sum(c.isupper() for c in letras) / len(letras) if letras else 0.0


def _titulo_curto(t: str) -> bool:
    return 0 < len(t.split()) <= 10 and not re.search(r"[.;,]\s*$", t) and not _SUMARIO.search(t)


_SO_NUMERO = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.\s*$")


def _titulo(linha: str, anterior: str) -> tuple[int, str] | None:
    """(nível, título normalizado) se a linha é um título de seção; nível 0 = sem número.

    Quando a extração põe o número da seção sozinho numa linha ("1." e, na
    linha seguinte, "INTRODUÇÃO"), o título herda o nível desse número.
    """
    l = linha.strip()
    if not l:
        return None
    so = _SO_NUMERO.match(anterior.strip())
    if so and not _NUMERADO.match(l):
        l = f"{so.group(1)}. {l}"
    m = _NUMERADO.match(l)
    if m:
        nivel, t = m.group(1).count(".") + 1, m.group(2).strip()
        if _titulo_curto(t) and (_maiusculas(t) >= 0.7 or (nivel == 1 and len(t.split()) <= 6)):
            return nivel, _norm(t)
        return None
    if (_titulo_curto(l) and _maiusculas(l) >= 0.9 and len(l.split()) <= 8
            and (not anterior.strip() or anterior.strip().isdigit() or _FIM_FRASE.search(anterior))):
        return 0, _norm(l)
    return None


def _narrativo(titulo: str) -> bool:
    return bool(_NARRATIVO.match(_ANEXO.sub("", titulo)))


def trechos_liberados(rows, segmentos) -> dict[tuple[str, int, int], str]:
    """{(arquivo, página, chunk): título da seção narrativa} dos trechos liberados.

    rows: (arquivo, página, chunk, texto) do processo; segmentos: DocumentSegment
    do índice de documentos (só os de gênero INSTRUMENTO contam).
    """
    from extraction.noise import strip_extraction_noise

    por_arquivo: dict[str, list] = {}
    for f, p, c, t in rows:
        por_arquivo.setdefault(f, []).append((p, c, t or ""))
    out: dict[tuple[str, int, int], str] = {}
    for seg in segmentos:
        if seg.genre != "INSTRUMENTO":
            continue
        chunks = sorted(x for x in por_arquivo.get(seg.filename, [])
                        if seg.page_start <= x[0] <= seg.page_end)
        if not chunks:
            continue
        # O título do próprio documento (primeira página): o documento inteiro.
        primeira = [x for x in chunks if x[0] == seg.page_start]
        topo = " ".join(_norm(l) for _, _, t in primeira for l in strip_extraction_noise(t).splitlines())
        doc = re.search(r"\bANEXO\s+[IVXLC]+(?:\s*-\s*[A-Z])?\s*-\s*([A-Z][A-Z ,/]{3,60})", topo)
        if (seg.title and _narrativo(_norm(seg.title))) or (doc and _narrativo(doc.group(1))):
            nome = seg.title or doc.group(0)
            for p, c, _ in chunks:
                out[(seg.filename, p, c)] = _norm(nome)
            continue
        aberta: tuple[int, str] | None = None  # (nível que a abriu, título)
        for p, c, t in chunks:
            dentro = fora = 0
            visto = aberta[1] if aberta else None
            anterior = "."
            for linha in strip_extraction_noise(t).splitlines():
                h = _titulo(linha, anterior)
                if h:
                    nivel, tit = h
                    if aberta is not None:
                        na, _ = aberta
                        fecha = (nivel != 0 and na != 0 and nivel <= na) or (nivel == 0 and na == 0)
                        if fecha:
                            aberta = None
                    if aberta is None and _narrativo(tit):
                        aberta = (nivel, tit)
                        visto = visto or tit
                n = len(linha.strip())
                if aberta is not None:
                    dentro += n
                else:
                    fora += n
                if linha.strip():
                    anterior = linha
            if dentro and dentro >= fora:
                out[(seg.filename, p, c)] = visto
    return out


def instala() -> None:
    from evaluation import evidence_selection as es
    from retrieval import get_document_index
    from retrieval.genre import INSTRUMENT, OTHER
    import sqlite3
    from retrieval._config import get_db_path

    original = es._chunk_genres
    cache: dict[str, dict] = {}

    def generos(process_number):
        if process_number not in cache:
            g = dict(original(process_number))
            con = sqlite3.connect(get_db_path())
            try:
                rows = con.execute("SELECT filename, page_number, chunk_index, text FROM chunks "
                                   "WHERE process_number = ?", (process_number,)).fetchall()
            finally:
                con.close()
            for k in trechos_liberados(rows, get_document_index(process_number)):
                if g.get(k) == INSTRUMENT:
                    g[k] = OTHER
            cache[process_number] = g
        return cache[process_number]

    es._chunk_genres = generos
