"""
A3: Inspect retrieval quality for Acao 1 on the synthetic test corpus.

Runs extraction → indexing → retrieval for both test PDFs and prints
every retrieved chunk with cascade step, score, and text excerpt.
Confirms A1 fix: BM25 now uses Rio Manual hints.

Usage:
    python scripts/a3_inspect_retrieval.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Ensure src/ is on the path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ingestion import get_ipmp_store, get_rio_manual_store
from extraction import extract_document
from retrieval import configure as configure_retrieval, index, retrieve_for_acao
from retrieval.schema.ddl import init_db as retrieval_init_db

CORPUS_DIR = ROOT / "data" / "test_corpus"
SCORE3_PDF = CORPUS_DIR / "Caso_Teste_Acao1_Score3.pdf"
SCORE1_PDF = CORPUS_DIR / "Caso_Teste_Acao1_Score1.pdf"

PROCESS_SCORE3 = "TESTE-SCORE3-001"
PROCESS_SCORE1 = "TESTE-SCORE1-001"

SEPARATOR = "-" * 70


def print_chunks(label: str, process_number: str) -> None:
    chunks = retrieve_for_acao(1, process_number)
    print(f"\n{'=' * 70}")
    print(f"RETRIEVAL: {label}  (process={process_number})")
    print(f"Total chunks retrieved: {len(chunks)}")
    print(SEPARATOR)

    if not chunks:
        print("  (no chunks retrieved)")
        return

    by_step: dict[str, list] = {}
    for c in chunks:
        by_step.setdefault(c.cascade_step, []).append(c)

    for step, step_chunks in by_step.items():
        print(f"\n  [{step.upper()}]  {len(step_chunks)} chunk(s)")
        for c in step_chunks:
            score_info = f"  bm25={c.bm25_score:.4f}" if c.bm25_score is not None else ""
            print(f"    chunk_index={c.chunk_index}  file={c.filename}  p={c.page_number}{score_info}  product={c.expected_product_id}")
            excerpt = c.text[:200].replace("\n", " ")
            print(f"    TEXT: {excerpt!r}")


def inspect_bm25_query() -> None:
    """Show what BM25 query strings would be generated for Acao 1."""
    from retrieval.query.query_builder import build_bm25_query
    ipmp_store = get_ipmp_store()
    rio_store = get_rio_manual_store()

    acao = ipmp_store.acoes[1]
    acronym_map = __import__("ingestion").get_acronym_store()
    queries: dict[str, str] = {}
    for product in acao.produtos_esperados:
        if product.id[-1:].isalpha():
            q = build_bm25_query(product.texto, acronym_map)
            if q:
                queries[product.id] = q

    rio_acao = rio_store.acoes.get(1)
    if rio_acao:
        hints = rio_acao.bm25_search_hints
        all_hints = hints.primary_terms + hints.secondary_terms
        if all_hints:
            queries["rio_hints"] = " OR ".join(f'"{t}"' for t in all_hints)

    print(f"\n{'=' * 70}")
    print("BM25 QUERIES for Acao 1")
    print(SEPARATOR)
    for name, q in queries.items():
        print(f"  [{name}]: {q[:120]}")


def main() -> None:
    print("A3 — Retrieval Quality Inspection for Acao 1")
    print("=" * 70)

    # Check PDFs exist
    for pdf in [SCORE3_PDF, SCORE1_PDF]:
        if not pdf.exists():
            print(f"ERROR: {pdf} not found. Run scripts/create_test_corpus.py first.")
            sys.exit(1)

    # Configure retrieval with a temp DB
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test_retrieval.db"
        configure_retrieval(str(db_path))
        retrieval_init_db(db_path)

        # Show the BM25 queries before indexing
        inspect_bm25_query()

        # Extract + index Score3
        print(f"\n{SEPARATOR}")
        print("Extracting Score3 PDF...")
        chunks3 = extract_document(SCORE3_PDF)
        print(f"  Extracted {len(chunks3)} chunks")
        index(PROCESS_SCORE3, chunks3)
        print(f"  Indexed as process={PROCESS_SCORE3}")

        # Extract + index Score1
        print(f"\nExtracting Score1 PDF...")
        chunks1 = extract_document(SCORE1_PDF)
        print(f"  Extracted {len(chunks1)} chunks")
        index(PROCESS_SCORE1, chunks1)
        print(f"  Indexed as process={PROCESS_SCORE1}")

        # Show all chunks to understand what was indexed
        print(f"\n{SEPARATOR}")
        print("ALL INDEXED CHUNKS — Score3:")
        for c in chunks3:
            print(f"  chunk {c.chunk_index} (p{c.page_number}): {len(c.text)} chars | {c.text[:80].replace(chr(10), ' ')!r}")

        print(f"\nALL INDEXED CHUNKS — Score1:")
        for c in chunks1:
            print(f"  chunk {c.chunk_index} (p{c.page_number}): {len(c.text)} chars | {c.text[:80].replace(chr(10), ' ')!r}")

        # Retrieve for each
        print_chunks("Score3 (expected score=3)", PROCESS_SCORE3)
        print_chunks("Score1 (expected score=1)", PROCESS_SCORE1)

        print(f"\n{'=' * 70}")
        print("Done.")


if __name__ == "__main__":
    main()
