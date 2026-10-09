"""Does giving the gate's reasoning a field inside GATE_SCHEMA stop the truncation?

Run 1 lost 2 gate calls to the token cap, Run 2 lost 4 — each burning the full
2048 tokens and returning zero content characters. Raising the cap (Fase 3.1,
768 -> 2048) shrank the problem but did not remove it, and raising it further
has poor odds: a prompt that burns 2048 on hidden reasoning will plausibly burn
4096 too.

The hypothesis under test: gpt-oss emits an UNCONSTRAINED reasoning channel
before the schema-constrained final channel, and a cap that fires mid-reasoning
yields an empty content field. Giving reasoning a declared place inside the
schema may move that thinking into the constrained channel, where it counts
toward a structure the grammar must eventually close.

That is a hypothesis, not a fact — the same shape of assumption that made
`reasoning_effort: low` look attractive before measurement showed it flipped
verdicts. So this measures two things, and the second is the veto:

  1. do the prompts that ACTUALLY truncate stop truncating?
  2. do verdicts change, judged against the gate's own ~90.9% same-condition
     noise floor (measured 2026-09-28, measure_gate_token_budget.py)?

Phase 1 hunts for the truncating prompts among the products the two runs named
(1a, 22.2, 40d, 9d, 17a). Phase 2 re-runs every prompt under both schemas.

Usage:
    python scripts/diagnostics/measure_gate_reasoning_field.py
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

import httpx  # noqa: E402

from evaluation.evidence_selection import strip_extraction_noise  # noqa: E402
from evaluation.prompt.relevance_builder import (  # noqa: E402
    build_relevance_system_prompt,
    build_relevance_user_prompt,
)
from evaluation.schemas import GATE_SCHEMA  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402
from ingestion.retrieval_profile import get_retrieval_profile_store  # noqa: E402
from retrieval import configure as retrieval_configure  # noqa: E402
from retrieval.query.hybrid import retrieve_hybrid_candidates_for_acao  # noqa: E402

BASE_URL = "http://189.60.217.20:8080"
MODEL = "gpt-oss-20b-F16.gguf"
DB_PATH = ROOT / "data" / "app.db"
PROCESS = "SMG-040_101607_2024"
MAX_TOKENS = 2048  # production value since Fase 3.1
_MAX_EXAMINED = 8  # mirrors evidence_selection

# "reasoning" FIRST, so grammar-constrained generation makes the model state
# its reasoning before committing to a verdict — the same ordering rationale
# as SCORER_SCHEMA's "products" (ADR-0058).
GATE_SCHEMA_REASONING = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "relevant": {"type": "boolean"},
    },
    "required": ["reasoning", "relevant"],
    "additionalProperties": False,
}

# The products the two full runs reported gate failures on.
SUSPECT_PRODUCTS = {1: ["1a"], 22: ["22.2"], 40: ["40d"], 9: ["9d"], 17: ["17a"]}


def call(system: str, user: str, schema: dict) -> dict:
    r = httpx.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "stream": False,
            "max_tokens": MAX_TOKENS,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema, "strict": True},
            },
        },
        timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=10.0),
    )
    r.raise_for_status()
    body = r.json()
    choice = body["choices"][0]
    usage = body.get("usage") or {}
    content = choice["message"].get("content") or ""
    verdict = None
    reasoning = None
    try:
        parsed = json.loads(content)
        verdict = bool(parsed["relevant"])
        reasoning = parsed.get("reasoning")
    except Exception:
        pass
    return {
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
        "content_chars": len(content),
        "verdict": verdict,
        "reasoning": reasoning,
    }


def gate_prompts() -> list[tuple[str, str, str]]:
    """Real production gate prompts for the suspect products: (label, system, user)."""
    retrieval_configure(DB_PATH)
    out: list[tuple[str, str, str]] = []
    for acao_id, product_ids in SUSPECT_PRODUCTS.items():
        acao = get_ipmp_store().acoes[acao_id]
        profile = get_retrieval_profile_store().acoes.get(acao_id)
        candidates = retrieve_hybrid_candidates_for_acao(acao_id, PROCESS)
        for product in acao.produtos_esperados:
            if product.id not in product_ids:
                continue
            pp = profile.expected_products.get(product.id) if profile else None
            if pp is None or not pp.evidence_intent:
                continue
            system = build_relevance_system_prompt(
                pp.evidence_intent,
                [c.text for c in pp.retrieval_signal_concepts],
                pp.negative_evidence_patterns,
            )
            for i, (_score, chunk) in enumerate(candidates.get(product.id, [])[:_MAX_EXAMINED]):
                out.append((
                    f"{acao_id}/{product.id}#{i}",
                    system,
                    build_relevance_user_prompt(strip_extraction_noise(chunk.text)),
                ))
    return out


def summarise(label: str, results: list[dict]) -> None:
    n = len(results)
    trunc = [r for r in results if r["finish_reason"] == "length"]
    empty = [r for r in results if r["content_chars"] == 0]
    toks = [r["completion_tokens"] for r in results if r["completion_tokens"] is not None]
    print(f"\n--- {label} ---")
    print(f"  chamadas           : {n}")
    print(f"  truncadas (length) : {len(trunc)}")
    print(f"  sem conteúdo       : {len(empty)}")
    if toks:
        print(f"  completion_tokens  : min={min(toks)} mediana={statistics.median(toks):.0f} "
              f"p90={sorted(toks)[int(0.9 * (len(toks) - 1))]} max={max(toks)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", action="store_true",
                    help="also run the baseline twice, for the noise floor")
    args = ap.parse_args()

    prompts = gate_prompts()
    print(f"{len(prompts)} prompts reais de gate dos produtos que falharam nas Runs 1 e 2")
    print(f"produtos: {SUSPECT_PRODUCTS}")

    conditions = [("GATE_SCHEMA atual", GATE_SCHEMA)]
    if args.control:
        conditions.append(("GATE_SCHEMA atual (2a passada, controle)", GATE_SCHEMA))
    conditions.append(("GATE_SCHEMA + reasoning", GATE_SCHEMA_REASONING))

    collected: dict[str, list[dict]] = {}
    for label, schema in conditions:
        results = []
        for lbl, system, user in prompts:
            try:
                results.append(call(system, user, schema))
            except Exception as exc:
                print(f"  [{label}] {lbl}: {type(exc).__name__}: {str(exc)[:90]}")
                results.append({"finish_reason": "error", "completion_tokens": None,
                                "content_chars": 0, "verdict": None, "reasoning": None})
        collected[label] = results
        summarise(label, results)
        for lbl, r in zip((p[0] for p in prompts), results):
            if r["finish_reason"] == "length":
                print(f"      TRUNCOU: {lbl} ({r['completion_tokens']} tok, "
                      f"{r['content_chars']} chars)")

    base = collected["GATE_SCHEMA atual"]
    print("\n" + "=" * 72)
    print("CONCORDÂNCIA DE VEREDICTO (o veto)")
    print("=" * 72)
    for label in list(collected)[1:]:
        other = collected[label]
        pairs = [(a, b) for a, b in zip(base, other)
                 if a["verdict"] is not None and b["verdict"] is not None]
        disagree = [(i, a, b) for i, (a, b) in enumerate(zip(base, other))
                    if a["verdict"] is not None and b["verdict"] is not None
                    and a["verdict"] != b["verdict"]]
        pct = 100 * (len(pairs) - len(disagree)) / len(pairs) if pairs else 0.0
        print(f"  atual vs {label:<42} {pct:5.1f}%  "
              f"({len(disagree)} divergência(s) em {len(pairs)})")
        for i, a, b in disagree:
            print(f"      {prompts[i][0]:>10}: {a['verdict']} -> {b['verdict']}")

    sample = next((r["reasoning"] for r in collected["GATE_SCHEMA + reasoning"]
                   if r.get("reasoning")), None)
    if sample:
        print(f"\nexemplo de reasoning devolvido no campo:\n  {sample[:400]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
