"""Rastreia uma página apontada por um especialista pelo pipeline de evidência.

Uso (ambiente rel_voto, a partir da raiz do repositório):

    python scripts/validation/rastreia_evidencia.py --process 040_101607_2024 \
        --acao 25 --produto 25a --arquivo _2 --pagina 973

Quando um especialista diz "a evidência do produto 25a está na página 973 do
volume 2", este script diz em que etapa essa página se perdeu, na ordem em que
o pipeline de produção a processa (assessment.service._retrieve_and_select):

  1. indexação        a página tem trechos no índice?
  2. rota focal       a Ação tomou o documento focal (Etapas A/B)?
  3. gênero           o documento é texto de instrumento e o produto não é isento?
  4. ruído            o trecho fica vazio depois de strip_extraction_noise?
  5. busca            posição nas duas raias (BM25 e vetorial) e no pool fundido
  6. corte            sobra entre os _MAX_EXAMINED examinados pelo gate?
  7. gate             veredito registrado no ledger, com o raciocínio
  8. avaliação        o trecho chegou ao avaliador na avaliação gravada? veredito do produto

Também mostra quais termos de busca do perfil ocorrem no trecho (ativos e
experimentais), para separar "falta termo" de "o termo existe mas não pesa".

Só leitura: usa as mesmas funções da produção e não chama nenhum modelo. Lê
data/app.db e data/lancedb. A única gravação possível é a reconstrução dos
índices derivados (gênero, vetor) quando estiverem desatualizados, que a
própria produção faria na próxima leitura.

Regra do projeto (ADR-0073): um achado deste script nunca vira termo de busca
tirado do documento do caso. Ele diz ONDE a evidência se perde; a correção,
se houver, vem do texto do IPMP, da lei ou de vocabulário geral, e é medida em
processos completos antes de entrar.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "diagnostics"))
import _common  # noqa: E402,F401  (offline flags, utf-8 stdout, src on sys.path)
from _common import DB_PATH  # noqa: E402


def _ro(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)


def _clause(term) -> str:
    if term.encoding == "phrase":
        return f'"{term.text}"'
    return "NEAR(" + " ".join(f'"{t}"' for t in term.tokens) + f", {term.distance})"


def _term_label(term) -> str:
    if term.encoding == "phrase":
        return f'"{term.text}"'
    return f"NEAR({', '.join(term.tokens)}; {term.distance})"


def _rank_of(key, chunks) -> int | None:
    for i, c in enumerate(chunks):
        if (c.filename, c.page_number, c.chunk_index) == key:
            return i + 1
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--process", required=True)
    ap.add_argument("--acao", type=int, required=True)
    ap.add_argument("--produto", required=True, help="id do Produto Esperado, ex. 25a")
    ap.add_argument("--arquivo", required=True,
                    help="nome do arquivo ou um trecho único dele, ex. _2 ou _2.pdf")
    ap.add_argument("--pagina", type=int, required=True)
    ap.add_argument("--chunk", type=int, default=None, help="só este chunk_index da página")
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()

    db = Path(args.db)
    from retrieval import configure
    configure(db)

    from extraction.noise import strip_extraction_noise
    from ingestion import get_genre_exemption_store, get_ipmp_store, get_retrieval_profile_store
    from retrieval.genre import get_chunk_genres, get_narrative_sections
    from retrieval.genre.classifier import INSTRUMENT
    from retrieval.query import vector as vector_mod
    from retrieval.query.bm25 import fetch_bm25_candidates
    from retrieval.query.document import retrieve_document_focused
    from retrieval.query.hybrid import (
        _CANDIDATE_POOL_SIZE,
        _vector_query_text,
        retrieve_hybrid_candidates_for_acao,
    )
    from retrieval.query.neighbors import fetch_neighbor_chunks
    from retrieval.query.query_builder import build_bm25_query, build_query_from_terms
    from ingestion import get_acronym_store
    from evaluation import evidence_selection as es

    acao = get_ipmp_store().acoes.get(args.acao)
    if acao is None:
        print(f"Ação {args.acao} não existe no IPMP.")
        return 2
    product = next((p for p in acao.produtos_esperados if p.id == args.produto), None)
    if product is None or not product.scored:
        ids = [p.id for p in acao.produtos_esperados if p.scored]
        print(f"Produto {args.produto} não é um produto pontuado da Ação {args.acao}: {ids}")
        return 2
    profile_acao = get_retrieval_profile_store().acoes.get(args.acao)
    prof = profile_acao.expected_products.get(product.id) if profile_acao else None
    exempt = product.id in get_genre_exemption_store().produtos(args.acao)

    con = _ro(db)
    files = [r[0] for r in con.execute(
        "SELECT DISTINCT filename FROM chunks WHERE process_number = ?", (args.process,))]
    match = ([f for f in files if f == args.arquivo]
             or [f for f in files if f.endswith(args.arquivo) or f.endswith(args.arquivo + ".pdf")]
             or [f for f in files if args.arquivo in f])
    if len(match) != 1:
        print(f"--arquivo '{args.arquivo}' casa com {match or 'nenhum'} entre {files}")
        return 2
    filename = match[0]
    sql = ("SELECT id, chunk_index, text FROM chunks WHERE process_number = ? "
           "AND filename = ? AND page_number = ?")
    params: list = [args.process, filename, args.pagina]
    if args.chunk is not None:
        sql += " AND chunk_index = ?"
        params.append(args.chunk)
    targets = con.execute(sql + " ORDER BY chunk_index", params).fetchall()

    print(f"Processo {args.process} · Ação {args.acao} · produto {product.id}")
    print(f"Critério: {product.texto}")
    print(f"Alvo: {filename} p.{args.pagina}" + (f" chunk {args.chunk}" if args.chunk is not None else ""))
    print()

    # 1. indexação
    if not targets:
        print("1. INDEXAÇÃO: a página não tem trechos no índice. A perda é na extração "
              "(página vazia, imagem sem OCR ou fora do PDF enviado).")
        return 0
    print(f"1. indexação: {len(targets)} trecho(s) na página")

    # 2. rota focal
    focal = retrieve_document_focused(args.acao, args.process)
    if focal is not None:
        focal = es.filter_focal_document(args.acao, args.process, focal)
    if focal is not None:
        files_focal = sorted({c.filename for c in focal})
        print(f"2. ROTA FOCAL: a Ação usa o documento focal {files_focal} sem gate; "
              "nenhum outro documento é buscado para ela.")
    else:
        print("2. rota focal: não se aplica (busca BM25 + vetorial com gate)")

    genres = get_chunk_genres(args.process)
    narrative = get_narrative_sections(args.process)
    seg = {(r[0], r[1], r[2]): r[3] for r in con.execute(
        "SELECT filename, page_number, chunk_index, segment_index FROM chunk_genre "
        "WHERE process_number = ?", (args.process,))}
    docidx = {(r[0], r[1]): (r[2], r[3], r[4]) for r in con.execute(
        "SELECT filename, segment_index, doc_type, title, genre FROM document_index "
        "WHERE process_number = ?", (args.process,))}

    # 5. raias completas (uma vez por produto)
    if prof and prof.query_terms:
        bm25_query = build_query_from_terms(prof.query_terms)
    else:
        bm25_query = build_bm25_query(product.texto, get_acronym_store())
    vquery = _vector_query_text(prof, product.texto)
    total = con.execute("SELECT count(*) FROM chunks WHERE process_number = ?",
                        (args.process,)).fetchone()[0]
    bm25_all = fetch_bm25_candidates(bm25_query, args.process, product.id, limit=total) if bm25_query else []
    vec_all = vector_mod.search_vector(args.process, vquery, k=total) if vquery else []
    cut_after = bool(prof and prof.genre_filter_before_lane_cut and not exempt)

    def kept(c) -> bool:
        return (genres.get((c.filename, c.page_number, c.chunk_index)) != INSTRUMENT
                and bool(strip_extraction_noise(c.text)))

    pool = retrieve_hybrid_candidates_for_acao(args.acao, args.process).get(product.id, [])
    filtered = pool
    if es.GENRE_FILTER_ENABLED and not exempt:
        filtered, _ = es._drop_instrument_text(filtered, genres)
    filtered = es._drop_empty_text(filtered)
    filtered = es._prefilter_near_duplicates(filtered)
    examined = [c for _, c in filtered[: es._MAX_EXAMINED]]

    led = con.execute(
        "SELECT page_number, chunk_index, relevant, source, overridden_at, "
        "override_justification, created_at, reasoning FROM gate_verdicts "
        "WHERE process_number = ? AND acao_id = ? AND product_id = ? AND filename = ? "
        "ORDER BY created_at", (args.process, args.acao, product.id, filename)).fetchall()
    ev = con.execute(
        "SELECT created_at, proposed_score, no_evidence_found, raw_json FROM evaluation_results "
        "WHERE process_number = ? AND acao_id = ? ORDER BY created_at DESC LIMIT 1",
        (args.process, args.acao)).fetchone()
    stored = json.loads(ev[3]) if ev else None

    for cid, cidx, text in targets:
        key = (filename, args.pagina, cidx)
        print()
        print(f"── trecho {cidx} " + "─" * 60)
        print("   " + " ".join(strip_extraction_noise(text).split())[:400])
        lost = None

        # 3. gênero
        g = genres.get(key)
        s = seg.get(key)
        doc = docidx.get((filename, s)) if s is not None else None
        doc_txt = (f"documento {doc[0] or 'sem tipo'}" + (f" «{doc[1][:70]}»" if doc[1] else "")
                   if doc else "documento não segmentado")
        narr = f"; seção narrativa liberada: «{narrative[key][:60]}»" if key in narrative else ""
        print(f"3. gênero: {g or 'desconhecido'} ({doc_txt}){narr}; produto isento: {'sim' if exempt else 'não'}")
        if g == INSTRUMENT and not exempt and es.GENRE_FILTER_ENABLED:
            lost = lost or ("GÊNERO: o documento é texto de instrumento e o produto não é isento "
                            "(ADR-0074). Só muda se o critério do produto for o próprio instrumento "
                            "(lista de isenções) ou se o trecho estiver numa seção narrativa (ADR-0077).")

        # 4. ruído
        if not strip_extraction_noise(text):
            lost = lost or "RUÍDO: o trecho é só cabeçalho/assinatura; nada sobra para julgar."
            print("4. ruído: VAZIO depois da limpeza")
        else:
            print("4. ruído: tem texto depois da limpeza")

        # termos do perfil no trecho
        if prof:
            hits = []
            for t in prof.query_terms:
                try:
                    ok = con.execute(
                        "SELECT 1 FROM chunks_fts WHERE chunks_fts MATCH ? AND rowid = ?",
                        (_clause(t), cid)).fetchone()
                except sqlite3.OperationalError:
                    ok = None
                if ok:
                    hits.append(f"{_term_label(t)} [{t.status}]")
            print(f"   termos do perfil presentes: {', '.join(hits) if hits else 'nenhum'}")

        # 5. busca
        rb = _rank_of(key, bm25_all)
        rv = _rank_of(key, vec_all)
        rb_k = _rank_of(key, [c for c in bm25_all if kept(c)]) if cut_after else None
        rv_k = _rank_of(key, [c for c in vec_all if kept(c)]) if cut_after else None
        lane = lambda r, rk: ("sem casamento" if r is None else f"posição {r}"
                              + (f" ({rk} depois do filtro de gênero)" if rk else ""))
        print(f"5. busca: BM25 {lane(rb, rb_k)} · vetorial {lane(rv, rv_k)} · "
              f"cada raia leva {_CANDIDATE_POOL_SIZE} ao pool"
              + (" depois do filtro de gênero (ADR-0079)" if cut_after else ""))
        rp = _rank_of(key, [c for _, c in pool])
        print(f"   pool fundido (RRF): {'posição ' + str(rp) if rp else 'FORA'} de {len(pool)}")
        if rp is None:
            lost = lost or ("BUSCA: o trecho não entra no pool de nenhuma das duas raias. "
                            "Caminhos canônicos: um termo do IPMP ou da lei que o trecho contenha, "
                            "ou uma intenção/conceito que o aproxime na raia vetorial.")

        # 6. corte
        rf = _rank_of(key, [c for _, c in filtered])
        re_ = _rank_of(key, examined)
        if rp is not None:
            if rf is None:
                print("6. corte: removido antes do gate (gênero, texto vazio ou quase-duplicata de outro candidato)")
                lost = lost or "CORTE: removido como quase-duplicata (0,92) de um candidato mais bem posicionado."
            elif re_ is None:
                print(f"6. corte: posição {rf} depois dos filtros; o gate examina só {es._MAX_EXAMINED}")
                lost = lost or f"CORTE: fica na posição {rf}, abaixo dos {es._MAX_EXAMINED} examinados pelo gate."
            else:
                print(f"6. corte: examinado (posição {re_} de {len(examined)})")

        prev, nxt = fetch_neighbor_chunks(args.process, filename, args.pagina, cidx)
        acc_keys = {(filename, r[0], r[1]) for r in led if r[2]}
        for lbl, nb in (("anterior", prev), ("seguinte", nxt)):
            if nb and (nb.filename, nb.page_number, nb.chunk_index) in acc_keys:
                print(f"   vizinho {lbl} (p.{nb.page_number} c{nb.chunk_index}) já foi aceito para "
                      f"{product.id}: o trecho pode chegar por expansão de vizinhos")

        # 7. gate
        mine = [r for r in led if (r[0], r[1]) == (args.pagina, cidx)]
        if mine:
            for r in mine:
                ver = "RELEVANTE" if r[2] else "não relevante"
                ovr = f"; override do auditor em {r[4]}: {r[5]}" if r[4] else ""
                print(f"7. gate ({r[6][:16]}, {r[3]}): {ver}{ovr}")
                print("   raciocínio: " + " ".join((r[7] or "").split())[:500])
            if not mine[-1][2]:
                lost = lost or ("GATE: examinado e julgado não relevante. O auditor pode marcar como "
                                "relevante (override) e reavaliar a Ação (ADR-0078).")
        else:
            print("7. gate: nenhum veredito no ledger para este trecho e produto")

        # 8. avaliação gravada
        if stored is None:
            print("8. avaliação: nenhuma avaliação gravada para esta Ação")
        else:
            got = [c for c in stored.get("retrieved_chunks", [])
                   if (c.get("filename"), c.get("page_number"), c.get("chunk_index")) == key]
            pv = next((v for v in stored.get("product_verdicts") or []
                       if v.get("product_id") == product.id), None)
            pv_txt = (f"produto {'evidenciado' if pv['evidenced'] else 'NÃO evidenciado'} — "
                      f"{' '.join((pv.get('justificativa') or '').split())[:300]}") if pv else "sem veredito por produto"
            print(f"8. avaliação de {ev[0][:16]} (score {ev[1]}): trecho "
                  f"{'ENTREGUE ao avaliador' if got else 'não entregue'}; {pv_txt}")
            if got and pv and not pv["evidenced"]:
                lost = lost or "AVALIADOR: o trecho chegou, e o avaliador não o achou suficiente."
            if mine and mine[-1][2] and not got:
                lost = lost or ("ENTREGA: aceito no ledger mas ausente da avaliação gravada "
                                "(avaliação anterior ao veredito, deduplicação ou orçamento de caracteres).")

        print(f"=> {'PERDA NA ETAPA — ' + lost if lost else 'o trecho percorre o pipeline inteiro'}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
