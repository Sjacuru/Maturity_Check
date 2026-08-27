"""
A3 (Ação 2): Inspect retrieval quality for Ação 2 against a real indexed case.

Prints, for each Expected Product (2a-2d) and rio_hints:
  - The exact BM25 FTS5 query string (from data/retrieval_profiles/acao_02.json)
  - The exact vector query text
  - The document-focused short-circuit decision (Step A/B, ADR-0028/0047)
  - The RRF-fused candidate pool (retrieve_hybrid_candidates_for_acao), the
    same function the live server uses when no document-focused match exists
    (ADR-0049)

No synthetic test corpus exists for Ação 2 yet (Componente 5 of the Ação 2
stabilization plan is deliberately last) — this inspects the real indexed
case (default: SMG-040_101607_2024) instead of fabricating one. Read-only:
does not extract, index, or mutate anything.

Usage:
    python scripts/a3_inspect_retrieval_acao2.py [process_number]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ingestion import get_acronym_store, get_ipmp_store, get_retrieval_profile_store, get_rio_manual_store  # noqa: E402
from retrieval import configure as configure_retrieval  # noqa: E402
from retrieval.query.document import retrieve_document_focused  # noqa: E402
from retrieval.query.hybrid import _vector_query_text, retrieve_hybrid_candidates_for_acao  # noqa: E402
from retrieval.query.query_builder import build_bm25_query, build_query_from_terms  # noqa: E402

DB_PATH = ROOT / "data" / "app.db"
DEFAULT_PROCESS_NUMBER = "SMG-040_101607_2024"
ACAO_ID = 2

SEP = "=" * 70
MAX_CANDIDATES_SHOWN = 10


def inspect_queries() -> None:
    acao = get_ipmp_store().acoes[ACAO_ID]
    profile_acao = get_retrieval_profile_store().acoes.get(ACAO_ID)
    acronym_map = get_acronym_store()

    print(f"\n{SEP}\nBM25 + VECTOR QUERIES — Ação {ACAO_ID}\n{SEP}")
    for product in acao.produtos_esperados:
        if not product.id[-1:].isalpha():
            continue
        profile_product = profile_acao.expected_products.get(product.id) if profile_acao else None
        if profile_product and profile_product.query_terms:
            bm25_query = build_query_from_terms(profile_product.query_terms)
            n_active = sum(1 for t in profile_product.query_terms if t.status in ("active", "validated"))
            n_total = len(profile_product.query_terms)
        else:
            bm25_query = build_bm25_query(product.texto, acronym_map)
            n_active = n_total = None
        vector_query = _vector_query_text(profile_product, product.texto)

        print(f"\n[{product.id}]")
        print(f"  BM25 ({n_active}/{n_total} termos ativos): {bm25_query or '(vazio)'}")
        print(f"  Vector: {vector_query[:200]}{'...' if len(vector_query) > 200 else ''}")

    rio_acao = get_rio_manual_store().acoes.get(ACAO_ID)
    if rio_acao:
        hints = rio_acao.bm25_search_hints
        all_hints = hints.primary_terms + hints.secondary_terms
        if all_hints:
            rio_query = " OR ".join(f'"{t}"' for t in all_hints)
            print(f"\n[rio_hints] BM25-only ({len(all_hints)} termos): {rio_query}")
        else:
            print("\n[rio_hints] nenhum termo cadastrado")


def inspect_cascade(process_number: str) -> None:
    print(f"\n{SEP}\nCASCADE — Ação {ACAO_ID}, processo {process_number}\n{SEP}")

    doc_result = retrieve_document_focused(ACAO_ID, process_number)
    if doc_result is not None:
        print(
            f"Step A/B (document-focused) MATCHED — {len(doc_result)} chunks retornados "
            "sem gate de relevância (todos os chunks do documento identificado)."
        )
        for c in doc_result[:MAX_CANDIDATES_SHOWN]:
            print(f"  {c.filename} p.{c.page_number} | step={c.cascade_step}")
        if len(doc_result) > MAX_CANDIDATES_SHOWN:
            print(f"  ... e mais {len(doc_result) - MAX_CANDIDATES_SHOWN}")
        return

    print("Step A/B: nenhum documento focal reconhecido — caindo para Step C (híbrido BM25+vetor, RRF k=60).")

    candidates = retrieve_hybrid_candidates_for_acao(ACAO_ID, process_number)
    if not candidates:
        print("\n(nenhum candidato retornado para nenhum produto)")
        return

    for product_id, ranked in candidates.items():
        print(f"\n[{product_id}] {len(ranked)} candidatos")
        for rank_pos, (score, chunk) in enumerate(ranked[:MAX_CANDIDATES_SHOWN], 1):
            snippet = chunk.text[:100].replace("\n", " ")
            print(
                f"  #{rank_pos} score={score:.5f} step={chunk.cascade_step:8s} "
                f"{chunk.filename} p.{chunk.page_number} | {snippet}"
            )
        if len(ranked) > MAX_CANDIDATES_SHOWN:
            print(f"  ... e mais {len(ranked) - MAX_CANDIDATES_SHOWN}")


def main() -> None:
    process_number = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESS_NUMBER

    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} não existe. Rode uma avaliação via API real (/assess) primeiro.")
        sys.exit(1)

    configure_retrieval(DB_PATH)

    print(f"A3 — Retrieval Inspection for Ação {ACAO_ID} (caso real, sem corpus sintético — Componente 5 pendente)")
    inspect_queries()
    inspect_cascade(process_number)
    print(f"\n{SEP}\nDone.\n{SEP}")


if __name__ == "__main__":
    main()
