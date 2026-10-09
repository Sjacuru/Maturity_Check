"""How many tokens does a gate call actually need?

The 2026-09-28 smoke run proved gpt-oss can spend the entire 768-token cap on
hidden reasoning and emit zero content characters, which drops the chunk
unjudged (ADR-0060). Raising the cap is the obvious fix, but it is paid on every
one of the ~30 gate calls per Ação, so it should be sized from measurement, not
guessed.

Sends REAL gate prompts (the exact production system/user prompts, via
relevance_builder + GATE_SCHEMA) against the real server under several
conditions and reports, per call: finish_reason, completion_tokens, and whether
any content came back.

Conditions:
  * the current production cap
  * higher caps
  * reasoning_effort=low via chat_template_kwargs, if this llama.cpp build
    honours it for gpt-oss — that attacks the cause (reasoning burn) instead of
    paying for it

Usage:
    python scripts/diagnostics/measure_gate_token_budget.py --acao 1 --n 12
"""

from __future__ import annotations

import argparse
import collections
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

from evaluation.prompt.relevance_builder import (  # noqa: E402
    build_relevance_system_prompt,
    build_relevance_user_prompt,
)
from evaluation.schemas import GATE_SCHEMA  # noqa: E402
from evaluation.evidence_selection import strip_extraction_noise  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402
from ingestion.retrieval_profile import get_retrieval_profile_store  # noqa: E402
from retrieval import configure as retrieval_configure  # noqa: E402
from retrieval.query.hybrid import retrieve_hybrid_candidates_for_acao  # noqa: E402

BASE_URL = "http://189.60.217.20:8080"
MODEL = "gpt-oss-20b-F16.gguf"
DB_PATH = ROOT / "data" / "app.db"
PROCESS = "SMG-040_101607_2024"


def _call(system: str, user: str, max_tokens: int, reasoning_effort: str | None):
    payload: dict = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "stream": False,
        "max_tokens": max_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "response", "schema": GATE_SCHEMA, "strict": True},
        },
    }
    if reasoning_effort is not None:
        payload["chat_template_kwargs"] = {"reasoning_effort": reasoning_effort}
    r = httpx.post(
        f"{BASE_URL}/v1/chat/completions", json=payload,
        timeout=httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0),
    )
    r.raise_for_status()
    body = r.json()
    choice = body["choices"][0]
    usage = body.get("usage") or {}
    content = choice["message"].get("content") or ""
    verdict = None
    try:
        import json as _json
        verdict = bool(_json.loads(content)["relevant"])
    except Exception:
        pass
    return {
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
        "content": content,
        "verdict": verdict,
    }


def _gate_prompts(acao_id: int, limit: int) -> list[tuple[str, str, str]]:
    """Build real gate prompts: (product_id, system, user)."""
    retrieval_configure(DB_PATH)
    acao = get_ipmp_store().acoes[acao_id]
    profile = get_retrieval_profile_store().acoes.get(acao_id)
    candidates = retrieve_hybrid_candidates_for_acao(acao_id, PROCESS)

    out: list[tuple[str, str, str]] = []
    for product in acao.produtos_esperados:
        if not product.scored:
            continue
        pool = candidates.get(product.id) or []
        pp = (profile.expected_products.get(product.id) if profile else None)
        if pp is None or not pp.evidence_intent:
            continue  # ungated degrade path in production — no gate call to measure
        # Exactly the production assembly (_select_for_product -> _gate_chunk).
        system = build_relevance_system_prompt(
            pp.evidence_intent,
            [c.text for c in pp.retrieval_signal_concepts],
            pp.negative_evidence_patterns,
        )
        for _score, chunk in pool[:8]:  # _MAX_EXAMINED
            out.append((product.id, system, build_relevance_user_prompt(
                strip_extraction_noise(chunk.text)
            )))
            if len(out) >= limit:
                return out
    return out


def _report(label: str, results: list[dict]) -> None:
    n = len(results)
    truncated = [r for r in results if r["finish_reason"] == "length"]
    empty = [r for r in results if not r["content"].strip()]
    toks = [r["completion_tokens"] for r in results if r["completion_tokens"] is not None]
    print(f"\n--- {label} ---")
    print(f"  chamadas              : {n}")
    print(f"  truncadas (length)    : {len(truncated)}  ({100*len(truncated)/n:.0f}%)")
    print(f"  sem conteúdo          : {len(empty)}  ({100*len(empty)/n:.0f}%)")
    if toks:
        print(f"  completion_tokens     : min={min(toks)} mediana={statistics.median(toks):.0f} "
              f"p90={sorted(toks)[int(0.9*(len(toks)-1))]} max={max(toks)}")
    fr = collections.Counter(r["finish_reason"] for r in results)
    print(f"  finish_reason         : {dict(fr)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="1", help="comma-separated, e.g. 1,31,40")
    ap.add_argument("--n", type=int, default=12, help="gate prompts per Ação")
    args = ap.parse_args()

    prompts: list[tuple[str, str, str]] = []
    for acao_id in (int(x) for x in args.acoes.split(",")):
        got = _gate_prompts(acao_id, args.n)
        prompts.extend((f"{acao_id}/{pid}", sysp, usr) for pid, sysp, usr in got)
    print(f"{len(prompts)} prompts reais de gate (Ações {args.acoes}, caso {PROCESS})")

    # "padrão (2a passada)" is the CONTROL: the same condition run twice gives
    # the gate's own run-to-run noise floor, which any comparison against
    # reasoning_effort=low has to be read against — this pipeline's gate is
    # documented as non-deterministic under concurrency (2026-08-27).
    conditions = [
        ("padrão 768", 768, None),
        ("padrão 768 (2a passada, controle)", 768, None),
        ("reasoning_effort=low", 768, "low"),
    ]
    collected: dict[str, list[dict]] = {}
    for label, cap, effort in conditions:
        results = []
        for pid, system, user in prompts:
            try:
                results.append(_call(system, user, cap, effort))
            except Exception as exc:
                print(f"  [{label}] {pid}: {type(exc).__name__}: {str(exc)[:120]}")
                results.append({"finish_reason": "error", "completion_tokens": None,
                                "content": "", "verdict": None})
        collected[label] = results
        _report(label, results)

    base = collected["padrão 768"]
    print(chr(10) + "=" * 70)
    print("CONCORDÂNCIA DE VEREDICTO (o que realmente importa)")
    print("=" * 70)
    for label in ("padrão 768 (2a passada, controle)", "reasoning_effort=low"):
        other = collected[label]
        pairs = [(a, b) for a, b in zip(base, other)
                 if a["verdict"] is not None and b["verdict"] is not None]
        disagree = [(i, a, b) for i, (a, b) in enumerate(zip(base, other))
                    if a["verdict"] is not None and b["verdict"] is not None
                    and a["verdict"] != b["verdict"]]
        pct = 100 * (len(pairs) - len(disagree)) / len(pairs) if pairs else 0
        print(f"  padrão vs {label:<36} {pct:5.1f}%  "
              f"({len(disagree)} divergência(s) em {len(pairs)})")
        for i, a, b in disagree:
            print(f"      {prompts[i][0]:>10}: padrão={a['verdict']} -> {b['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
