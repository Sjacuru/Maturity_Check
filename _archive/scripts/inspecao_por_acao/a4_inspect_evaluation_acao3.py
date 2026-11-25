"""
A4 (Ação 3): Inspect prompt, gate, and evaluation quality for Ação 3 against
a real indexed case, driving the exact production pipeline
(assessment.service._retrieve_and_select -> evaluation.evaluate).

Prints:
  - Step A/B vs Step C routing decision (same as a3)
  - Gate verdicts: accepted chunks (with matched_concepts) vs rejected
    chunks that had a matched_concept (possible gate misses)
  - The assembled system/user prompts
  - The LLM's raw response, reasoning, score, uncertainty

Imports main.py to reuse the exact production LLM wiring (ADR-0054:
llama.cpp primary + Groq/Ollama fallback via FallbackLLMClient) — this
calls the real GPU server, not a stub or a different model.

No synthetic test corpus exists for Ação 3 yet — this inspects the real
indexed case (default: SMG-040_101607_2024) instead of fabricating one.

Usage:
    python scripts/a4_inspect_evaluation_acao3.py [process_number]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import main as app_main  # noqa: E402 — import triggers _bootstrap(): real retrieval/assessment/LLM config

from evaluation import evaluate, select_evidence  # noqa: E402
from evaluation.prompt.builder import build_system_prompt, build_user_prompt  # noqa: E402
from retrieval import retrieve_hybrid_candidates_for_acao  # noqa: E402
from retrieval.query.document import retrieve_document_focused  # noqa: E402

ACAO_ID = 3
DEFAULT_PROCESS_NUMBER = "SMG-040_101607_2024"

SEP = "=" * 70


def main() -> None:
    process_number = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESS_NUMBER

    print(f"A4 — Evaluation Inspection for Ação {ACAO_ID} (caso real, sem corpus sintético)")
    print(
        f"LLM: llama.cpp primary ({app_main._LLAMACPP_MODEL} @ {app_main._LLAMACPP_BASE_URL}), "
        "fallback Groq (scorer) / Ollama (gate) — ADR-0054"
    )

    doc_result = retrieve_document_focused(ACAO_ID, process_number)
    if doc_result is not None:
        accepted, rejected = doc_result, []
        print(f"\nStep A/B matched — {len(accepted)} chunks, sem gate de relevância.")
    else:
        print("\nStep A/B: sem documento focal — Step C (híbrido + gate de relevância, ADR-0050).")
        candidates = retrieve_hybrid_candidates_for_acao(ACAO_ID, process_number)
        selection = select_evidence(ACAO_ID, process_number, candidates)
        accepted, rejected = selection.accepted, selection.rejected

    print(f"\n{SEP}\nGATE — {len(accepted)} aceito(s) / {len(rejected)} rejeitado(s)\n{SEP}")

    print("\nAceitos:")
    if not accepted:
        print("  (nenhum)")
    for c in accepted:
        snippet = c.text[:100].replace("\n", " ")
        print(
            f"  {c.filename} p.{c.page_number} | produtos={c.expected_product_ids} "
            f"conceitos={c.matched_concepts}"
        )
        print(f"    -> {snippet}")

    flagged = [r for r in rejected if r.matched_concepts]
    print(f"\nRejeitados com matched_concepts não-vazio ({len(flagged)}/{len(rejected)} — possíveis falsos negativos do gate):")
    if not flagged:
        print("  (nenhum)")
    for r in flagged:
        print(f"  {r.filename} p.{r.page_number} | produto={r.expected_product_id} conceitos={r.matched_concepts}")

    if not accepted:
        print("\nNenhuma evidência aceita — evaluate() retornará no_evidence_found=True sem chamar a LLM.")
    else:
        system_prompt = build_system_prompt(ACAO_ID)
        user_prompt = build_user_prompt(accepted, acao_id=ACAO_ID)

        print(f"\n{SEP}\nSYSTEM PROMPT ({len(system_prompt)} chars) — primeiros 400\n{SEP}")
        print(system_prompt[:400])

        print(f"\n{SEP}\nUSER PROMPT ({len(user_prompt)} chars) — primeiros 600\n{SEP}")
        print(user_prompt[:600])

    print(f"\n{SEP}\nChamando LLM...\n{SEP}")
    result = evaluate(ACAO_ID, process_number, accepted, rejected_chunks=rejected)

    print(f"\n{SEP}\nRESULTADO\n{SEP}")
    print(f"  provider/model   : {result.provider}/{result.model}")
    print(f"  proposed_score   : {result.proposed_score}")
    print(f"  uncertainty_flag : {result.uncertainty_flag}")
    print(f"  no_evidence_found: {result.no_evidence_found}")
    print(f"  parse_failed     : {result.parse_failed}")
    print(f"  evidence_chars   : {result.evidence_char_count}")
    print(f"\nREASONING:\n{result.reasoning or '(none)'}")

    print(f"\n{SEP}\nDone.\n{SEP}")


if __name__ == "__main__":
    main()
