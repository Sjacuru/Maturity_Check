"""Variante F20: o filtro de gênero dentro de cada trilha, antes da fusão (2026-10-19).

Pedido do usuário: "Vamos aplicar o filtro conforme sua sugestão e analisar o
resultado", depois da comparação sem GPU de três desenhos da janela (J20 hoje,
J40, F20).

Hoje (ADR-0074) cada trilha (BM25, vetor) entrega seus 20 primeiros, o RRF os
funde, e só então o filtro tira o texto de instrumento, sem repor. Para os
produtos não isentos, a maior parte das 40 posições é contrato, edital ou TR: 71
dos 148 ficam sem nenhum candidato. Em F20, cada trilha desce até juntar 20
trechos que não são instrumento e não ficam vazios após a limpeza de ruído
(extraction.noise); o RRF funde essas duas listas e o resto do caminho não muda
(quase-duplicatas, corte de 16, gate, expansão). Produtos isentos: como hoje.

Na projeção (2026-10-18), F20 reproduz o examinado: 2 199 chamadas ao pool por
processo (450 hoje), nenhum produto não isento sem candidato, posição vetorial
mediana do que entra 130 (hoje 14), e os mesmos trechos julgados por dezenas de
produtos (o ETP _2 p.157 por 106). É a opção B rejeitada em 12/10, agora medida
em processos completos.

Usada por: reproducibility.py --lane-genre-filter. Nada em src/ muda.
"""

from __future__ import annotations

_PROFUNDIDADE = 100_000  # a trilha inteira: o corpus do caso tem 1 429 chunks


def instala() -> None:
    from extraction.noise import strip_extraction_noise
    from ingestion import get_genre_exemption_store, get_ipmp_store
    from retrieval import get_chunk_genres
    from retrieval.genre import INSTRUMENT
    from retrieval.query import hybrid

    original = hybrid._fused_candidates_for_product
    store = get_genre_exemption_store()
    isentos = set()
    for acao_id in get_ipmp_store().acoes:
        isentos |= set(store.produtos(acao_id))
    generos: dict[str, dict] = {}

    def filtrado(product, profile_product, acronym_map, process_number):
        if product.id in isentos:
            return original(product, profile_product, acronym_map, process_number)
        if process_number not in generos:
            generos[process_number] = get_chunk_genres(process_number)
        g = generos[process_number]

        def serve(c):
            return (g.get(hybrid._natural_key(c)) != INSTRUMENT
                    and bool(strip_extraction_noise(c.text)))

        if profile_product and profile_product.query_terms:
            bm25_query = hybrid.build_query_from_terms(profile_product.query_terms)
        else:
            bm25_query = hybrid.build_bm25_query(product.texto, acronym_map)
        vector_query = hybrid._vector_query_text(profile_product, product.texto)
        n = hybrid._CANDIDATE_POOL_SIZE
        bm25_hits = ([c for c in hybrid.fetch_bm25_candidates(
            bm25_query, process_number, product.id, limit=_PROFUNDIDADE) if serve(c)][:n]
            if bm25_query else [])
        vector_hits = ([c for c in hybrid.vector_mod.search_vector(
            process_number, vector_query, k=_PROFUNDIDADE) if serve(c)][:n]
            if vector_query else [])
        if not bm25_hits and not vector_hits:
            return []
        by_key = {}
        for c in bm25_hits:
            by_key[hybrid._natural_key(c)] = c
        for c in vector_hits:
            by_key.setdefault(hybrid._natural_key(c), c)
        fused = hybrid.fuse_rankings([[hybrid._natural_key(c) for c in bm25_hits],
                                      [hybrid._natural_key(c) for c in vector_hits]])
        ks = sorted(fused, key=lambda k: fused[k], reverse=True)
        return [(fused[k], by_key[k].model_copy(update={"expected_product_ids": [product.id]}))
                for k in ks]

    hybrid._fused_candidates_for_product = filtrado
