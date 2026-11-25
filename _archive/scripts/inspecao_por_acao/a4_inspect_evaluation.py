"""
A4: Inspect prompt and evaluation quality for Acao 1 on synthetic test corpus.

Runs the full pipeline (extraction -> indexing -> retrieval -> evaluation)
and prints:
  - The system prompt (first 300 chars)
  - The user prompt (evidence section)
  - LLM reasoning
  - Proposed score
  - parse_failed / uncertainty flags

Usage:
    python scripts/a4_inspect_evaluation.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ingestion import get_ipmp_store
from extraction import extract_document
from retrieval import configure as configure_retrieval, index, retrieve_for_acao
from retrieval.schema.ddl import init_db as retrieval_init_db
from evaluation import configure_llm, evaluate
from evaluation.prompt.builder import build_system_prompt, build_user_prompt

CORPUS_DIR = ROOT / "data" / "test_corpus"
SCORE3_PDF = CORPUS_DIR / "Caso_Teste_Acao1_Score3.pdf"
SCORE1_PDF = CORPUS_DIR / "Caso_Teste_Acao1_Score1.pdf"

PROCESS_SCORE3 = "A4-SCORE3-001"
PROCESS_SCORE1 = "A4-SCORE1-001"

SEP = "=" * 70
DIV = "-" * 70


def run_for(label: str, process_number: str, pdf: Path) -> None:
    print(f"\n{SEP}")
    print(f"EVALUATION: {label}")
    print(SEP)

    # Extract + index
    chunks = extract_document(pdf)
    index(process_number, chunks)
    print(f"Extracted {len(chunks)} chunks, indexed as {process_number}")

    # Retrieve
    retrieved = retrieve_for_acao(1, process_number)
    print(f"Retrieved {len(retrieved)} chunks for Acao 1")

    # Show prompt preview
    sys_prompt = build_system_prompt(1)
    user_prompt = build_user_prompt(retrieved)
    total_evidence = sum(len(c.text) for c in retrieved)

    print(f"\n{DIV}")
    print(f"SYSTEM PROMPT ({len(sys_prompt)} chars, first 400):")
    print(sys_prompt[:400])

    print(f"\n{DIV}")
    print(f"USER PROMPT ({len(user_prompt)} chars, {total_evidence} chars evidence, first 600):")
    print(user_prompt[:600])

    # Run evaluation
    print(f"\n{DIV}")
    print("Running LLM evaluation...")
    result = evaluate(1, process_number, retrieved)

    print(f"\n{DIV}")
    print(f"RESULT:")
    print(f"  parse_failed    : {result.parse_failed}")
    print(f"  proposed_score  : {result.proposed_score}")
    print(f"  uncertainty_flag: {result.uncertainty_flag}")
    print(f"  evidence_chars  : {result.evidence_char_count}")
    print(f"  raw_response len: {len(result.raw_llm_response or '')}")
    print(f"\nLLM REASONING (first 800 chars):")
    print((result.reasoning or "(none)")[:800])
    print(f"\nFull raw response ({len(result.raw_llm_response or '')} chars):")
    print((result.raw_llm_response or "(none)")[:1200])


def main() -> None:
    # Ollama must be running: ollama serve
    llm_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "mistral")
    configure_llm(provider="ollama", model=model, base_url=llm_host)
    print(f"LLM: {model} @ {llm_host}")

    for pdf in [SCORE3_PDF, SCORE1_PDF]:
        if not pdf.exists():
            print(f"ERROR: {pdf} not found. Run create_test_corpus.py first.")
            sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "a4_test.db"
        configure_retrieval(str(db_path))
        retrieval_init_db(db_path)

        run_for("Score3 (expected=3)", PROCESS_SCORE3, SCORE3_PDF)
        run_for("Score1 (expected=1)", PROCESS_SCORE1, SCORE1_PDF)

    print(f"\n{SEP}")
    print("Done.")


if __name__ == "__main__":
    main()
