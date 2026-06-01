from __future__ import annotations

from ingestion import get_ipmp_store
from retrieval.interfaces.contracts import RetrievedChunk

_CASCADE_ORDER = {"filename_match": 0, "variant_match": 1, "bm25": 2, "regex": 3}

_EXAMPLES_FRAMING = (
    "Os exemplos abaixo ilustram os níveis de pontuação em um contexto "
    "específico; aplique os mesmos critérios ao processo avaliado, "
    "independente do setor ou domínio."
)

_SCORING_INSTRUCTION = """\
Com base exclusivamente nas evidências fornecidas acima, avalie o processo e produza sua resposta em dois blocos:

1. **Raciocínio** (texto livre em português): explique quais Produtos Esperados foram ou não evidenciados e por quê.

Regras de avaliação:
- Pontue 3 quando todos os Produtos Esperados (1a, 1b, 1c, 1d) estiverem claramente evidenciados.
- Pontue 1 quando alguns, mas não todos, os Produtos Esperados estiverem evidenciados.
- Pontue 0 quando nenhum Produto Esperado estiver evidenciado.
- Trate texto com ruído de OCR (caracteres ilegíveis ou garbled) como evidência não confiável; não pontue positivamente com base apenas em texto OCR ilegível.
- Emita UNCERTAINTY: yes quando as evidências não permitirem avaliação segura de um ou mais Produtos Esperados (1a, 1b, 1c, 1d).

2. **Bloco sentinela** (obrigatório, últimas duas linhas, sem texto após):
SCORE: <0, 1 ou 3>
UNCERTAINTY: <yes ou no>\
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


def build_user_prompt(chunks: list[RetrievedChunk]) -> str:
    ordered = sorted(
        chunks,
        key=lambda c: (
            _CASCADE_ORDER[c.cascade_step],
            -(c.bm25_score or 0.0) if c.cascade_step == "bm25" else 0.0,
            (c.rank if c.rank is not None else 0) if c.cascade_step == "bm25" else 0,
            c.filename if c.cascade_step != "bm25" else "",
            c.page_number if c.cascade_step != "bm25" else 0,
            c.chunk_index,
        ),
    )

    blocks: list[str] = []
    for chunk in ordered:
        header = f"[Arquivo: {chunk.filename} | Página: {chunk.page_number}]"
        blocks.append(f"{header}\n{chunk.text}")

    total_chars = sum(len(c.text) for c in ordered)
    summary = f"--- {len(ordered)} trecho(s) recuperado(s), {total_chars} caracteres ---"

    parts = blocks + [summary]
    return "\n\n".join(parts)
