"""Intra-corpus retrieval test for Ação 1 subtask queries.

Tests two modes:
  1. Unfiltered  — full index, no hierarchy filter (baseline)
  2. Filtered    — stage + dimension + acao_num pre/post-filter applied
"""
from pathlib import Path
from maturity_check.reference_search import search_reference_lancedb

LANCEDB_DIR = Path("data/lancedb/reference")
MODEL_ID    = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

STAGE     = "Proposta Inicial de Investimento"
DIMENSION = "Estratégica"
ACAO_NUM  = 1

QUERIES = [
    ("i",   "Escrever uma descricao breve e concisa do motivo pelo qual o projeto e necessario"),
    ("ii",  "Descrever a estrategia da Autoridade e as estrategias governamentais mais amplas"),
    ("iii", "Definir os Objetivos Estrategicos que a Proposta de Investimento apoia"),
    ("iv",  "Mostrar como os Objetivos Estrategicos promovem o desenvolvimento sustentavel"),
    ("v",   "Incluir uma declaracao que resuma os possiveis impactos ambientais e sociais"),
    ("vi",  "Descrever como programas e projetos existentes podem influenciar o projeto"),
]


def run_mode(label: str, use_filter: bool) -> int:
    print(f"\n{'='*60}")
    print(f"  MODE: {label}")
    print(f"{'='*60}")
    hits_at_1 = 0
    for subtask_label, query in QUERIES:
        kwargs = dict(
            lancedb_dir=LANCEDB_DIR,
            query=query,
            limit=5,
            model_id=MODEL_ID,
        )
        if use_filter:
            kwargs["stage"]     = STAGE
            kwargs["dimension"] = DIMENSION
            kwargs["acao_num"]  = ACAO_NUM

        hits = search_reference_lancedb(**kwargs)

        correct_at_1 = (
            hits
            and hits[0].acao_num == ACAO_NUM
            and hits[0].subtask == f"{subtask_label}."
        )
        if correct_at_1:
            hits_at_1 += 1

        print(f"\n  Subtask {subtask_label}: {query[:60]}")
        for rank, h in enumerate(hits, 1):
            marker = " <-- CORRECT" if (h.acao_num == ACAO_NUM and h.subtask == f"{subtask_label}.") else ""
            sub    = h.subtask or "—"
            acao   = f"Ação {h.acao_num}" if h.acao_num else "—"
            print(f"    {rank}. [{acao:8s} > {sub:5s}] dist={h.distance:.4f}{marker}")

    print(f"\n  Hits@1 (exact subtask match): {hits_at_1}/{len(QUERIES)}")
    return hits_at_1


def main():
    run_mode("UNFILTERED — full index", use_filter=False)
    run_mode(f"FILTERED  — stage={STAGE[:20]}... | dim={DIMENSION} | Ação {ACAO_NUM}", use_filter=True)


if __name__ == "__main__":
    main()
