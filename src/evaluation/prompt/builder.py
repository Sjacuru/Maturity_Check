from __future__ import annotations

from ingestion import get_ipmp_store
from retrieval.interfaces.contracts import RetrievedChunk

_CASCADE_ORDER = {"filename_match": 0, "variant_match": 1, "bm25": 2, "regex": 3, "vector": 4}

_EXAMPLES_FRAMING = (
    "Os exemplos abaixo ilustram os níveis de pontuação em um contexto "
    "específico; aplique os mesmos critérios ao processo avaliado, "
    "independente do setor ou domínio."
)

_PRODUCT_BLOCK_INSTRUCTION = (
    "As evidências abaixo estão organizadas por Produto Esperado. "
    "Use exclusivamente as evidências do bloco correspondente para avaliar cada produto. "
    "Se as evidências de um bloco forem insuficientes para concluir o atendimento, "
    "registre explicitamente essa limitação no raciocínio."
)

_SCORING_INSTRUCTION = """\
Com base exclusivamente nas evidências fornecidas acima, avalie o processo e \
responda com um objeto JSON contendo os campos "reasoning", "score" e "uncertainty".

No campo "reasoning" (texto livre em português): explique quais Produtos \
Esperados foram ou não evidenciados e por quê.

Regras de avaliação para o campo "score":
- Pontue 3 quando todos os Produtos Esperados (1a, 1b, 1c, 1d) estiverem claramente evidenciados.
- Pontue 1 quando alguns, mas não todos, os Produtos Esperados estiverem evidenciados.
- Pontue 0 quando nenhum Produto Esperado estiver evidenciado.
- Trate texto com ruído de OCR (caracteres ilegíveis ou garbled) como evidência não confiável; não pontue positivamente com base apenas em texto OCR ilegível.

Regra para o campo "uncertainty":
- Defina "uncertainty": true quando as evidências não permitirem avaliação segura de um ou mais Produtos Esperados (1a, 1b, 1c, 1d).\
"""


def build_system_prompt(acao_id: int) -> str:
    store = get_ipmp_store()
    acao = store.acoes[acao_id]

    sections: list[str] = []

    sections.append(
        "Você é um avaliador especializado no framework IPMP (Indicador de "
        "Percepção de Maturidade de Projetos) de concessões públicas. "
        "Sua tarefa é avaliar se as evidências extraídas de um processo "
        "licitário atendem aos critérios desta Ação IPMP."
    )

    sections.append(
        f"## Ação {acao.acao_id}: {acao.titulo}\n\n{acao.descricao_acao}"
    )

    sections.append(f"## O que esperar\n\n{acao.o_que_esperar}")

    produtos_lines = ["## Produtos Esperados\n"]
    for p in acao.produtos_esperados:
        produtos_lines.append(f"**{p.id}.** {p.texto}")
    sections.append("\n".join(produtos_lines))

    exemplos_lines = [f"## Exemplos ilustrativos\n\n{_EXAMPLES_FRAMING}\n"]
    for ex in acao.exemplos:
        exemplos_lines.append(f"### {ex.nivel} (pontuação: {ex.score})\n\n{ex.texto}")
    sections.append("\n\n".join(exemplos_lines))

    if acao.excecoes:
        excecoes_lines = ["## Exceções e observações\n"]
        for i, exc in enumerate(acao.excecoes, 1):
            excecoes_lines.append(f"{i}. {exc}")
        sections.append("\n".join(excecoes_lines))

    sections.append(f"## Instruções de pontuação\n\n{_SCORING_INSTRUCTION}")

    return "\n\n---\n\n".join(sections)


def _sort_key(chunk: RetrievedChunk):
    step = _CASCADE_ORDER[chunk.cascade_step]
    if chunk.cascade_step == "bm25":
        bm25_desc = -(chunk.bm25_score or 0.0)
        rank_asc = chunk.rank if chunk.rank is not None else 0
        return (step, bm25_desc, rank_asc, chunk.chunk_index)
    return (step, 0.0, 0, chunk.chunk_index, chunk.filename, chunk.page_number)


def _render_chunk(chunk: RetrievedChunk) -> str:
    return f"[Arquivo: {chunk.filename} | Página: {chunk.page_number}]\n{chunk.text}"


def build_user_prompt(chunks: list[RetrievedChunk], acao_id: int = 1) -> str:
    store = get_ipmp_store()
    acao = store.acoes.get(acao_id)

    # Build ordered product list from IPMP store, skipping the parent product
    # whose id equals str(acao_id) — e.g. "1" for Ação 1 (container, not scored).
    product_order: list[str] = []
    product_texts: dict[str, str] = {}
    if acao:
        parent_id = str(acao_id)
        for p in acao.produtos_esperados:
            if p.id != parent_id:
                product_order.append(p.id)
                product_texts[p.id] = p.texto

    # Separate chunks with no product attribution (document-focused steps)
    # from chunks tied to a specific expected product.
    ungrouped: list[RetrievedChunk] = []
    grouped: dict[str, list[RetrievedChunk]] = {pid: [] for pid in product_order}
    overflow: dict[str, list[RetrievedChunk]] = {}  # product ids not in IPMP order

    for chunk in chunks:
        pids = chunk.expected_product_ids
        if not pids:
            ungrouped.append(chunk)
        else:
            for pid in pids:
                if pid in grouped:
                    grouped[pid].append(chunk)
                else:
                    overflow.setdefault(pid, []).append(chunk)

    parts: list[str] = [_PRODUCT_BLOCK_INSTRUCTION]
    total_chunks = 0

    # Document-focused chunks first (filename_match, variant_match, regex),
    # sorted by cascade priority then filename/page for determinism.
    if ungrouped:
        ungrouped_sorted = sorted(ungrouped, key=_sort_key)
        parts.append("## Documentos Focais")
        for chunk in ungrouped_sorted:
            parts.append(_render_chunk(chunk))
            total_chunks += 1

    # One block per expected product in IPMP order (1a → 1b → 1c → 1d).
    for pid in product_order:
        product_chunks = sorted(grouped.get(pid, []), key=_sort_key)
        if not product_chunks:
            continue
        title = product_texts.get(pid, pid)
        parts.append(f"## Evidências para Produto {pid} — {title}")
        for chunk in product_chunks:
            parts.append(_render_chunk(chunk))
            total_chunks += 1

    # Any product ids not in the IPMP store (forward-compatible).
    for pid in sorted(overflow):
        product_chunks = sorted(overflow[pid], key=_sort_key)
        parts.append(f"## Evidências para Produto {pid}")
        for chunk in product_chunks:
            parts.append(_render_chunk(chunk))
            total_chunks += 1

    total_chars = sum(len(c.text) for c in chunks)
    parts.append(f"--- {total_chunks} trecho(s) recuperado(s), {total_chars} caracteres ---")

    return "\n\n".join(parts)
