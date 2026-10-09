"""Are the gate's pathological calls caused by degenerate chunks?

inspect_truncating_gate_prompt.py found that the one deterministically
truncating gate call is not a big prompt and not a loop. It is a 141-character
user prompt containing an orphaned subordinate clause — "ORDEM DE INÍCIO que
possam interromper ou obstaculizar a Concessão, desde que não vinculados à
atuação da CONCESSIONÁRIA" — a 501-char chunk that strip_extraction_noise()
reduces to a sentence fragment with no subject. Asked whether that is evidence
for "a registry of data sources used in the revision", the model deliberated
for 7,871 tokens before answering False.

So the lever may not be on the LLM side at all: a chunk carrying no proposition
cannot be evidence for any IPMP criterion, and sending it to the gate spends a
call to learn nothing.

Before proposing a minimum-length filter, this measures the two things that
decide whether one is safe:

  1. the distribution of post-strip lengths among real gate candidates
  2. whether short chunks are ever ACCEPTED — the veto. If the gate accepts
     them, they carry evidence and the filter would destroy recall.

Usage:
    python scripts/diagnostics/measure_degenerate_chunks.py --acoes 1,4,15,22,25,40
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
_MAX_EXAMINED = 8
CANDIDATE_THRESHOLDS = [100, 150, 200, 250, 300, 400]


def call(system: str, user: str) -> dict:
    r = httpx.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0, "stream": False, "max_tokens": 2048,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": GATE_SCHEMA, "strict": True},
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
    try:
        verdict = bool(json.loads(content)["relevant"])
    except Exception:
        pass
    return {
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
        "verdict": verdict,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="1,4,15,22,25,40")
    args = ap.parse_args()

    retrieval_configure(DB_PATH)
    rows = []
    for acao_id in (int(x) for x in args.acoes.split(",")):
        acao = get_ipmp_store().acoes[acao_id]
        profile = get_retrieval_profile_store().acoes.get(acao_id)
        candidates = retrieve_hybrid_candidates_for_acao(acao_id, PROCESS)
        for product in acao.produtos_esperados:
            if not product.scored:
                continue
            pp = profile.expected_products.get(product.id) if profile else None
            if pp is None or not pp.evidence_intent:
                continue
            system = build_relevance_system_prompt(
                pp.evidence_intent,
                [c.text for c in pp.retrieval_signal_concepts],
                pp.negative_evidence_patterns,
            )
            for _score, chunk in candidates.get(product.id, [])[:_MAX_EXAMINED]:
                cleaned = strip_extraction_noise(chunk.text)
                try:
                    res = call(system, build_relevance_user_prompt(cleaned))
                except Exception as exc:
                    print(f"  erro {acao_id}/{product.id}: {type(exc).__name__}")
                    continue
                rows.append({
                    "label": f"{acao_id}/{product.id}",
                    "raw_chars": len(chunk.text),
                    "clean_chars": len(cleaned),
                    "step": chunk.cascade_step,
                    **res,
                })

    n = len(rows)
    lens = sorted(r["clean_chars"] for r in rows)
    print(f"\n{n} candidatos reais de gate (Ações {args.acoes})")
    print(f"comprimento pós-strip: min={lens[0]} p10={lens[int(0.10*(n-1))]} "
          f"mediana={statistics.median(lens):.0f} max={lens[-1]}")

    accepted = [r for r in rows if r["verdict"] is True]
    print(f"aceitos: {len(accepted)}/{n}")
    if accepted:
        alens = sorted(r["clean_chars"] for r in accepted)
        print(f"comprimento dos ACEITOS: min={alens[0]} p10={alens[int(0.10*(len(alens)-1))]} "
              f"mediana={statistics.median(alens):.0f}")

    print(f"\n{'limiar':>7} {'descartaria':>12} {'% dos cand.':>12} "
          f"{'ACEITOS perdidos':>17} {'tokens poupados':>16}")
    for t in CANDIDATE_THRESHOLDS:
        below = [r for r in rows if r["clean_chars"] < t]
        lost = [r for r in below if r["verdict"] is True]
        saved = sum(r["completion_tokens"] or 0 for r in below)
        print(f"{t:>7} {len(below):>12} {100*len(below)/n:>11.1f}% "
              f"{len(lost):>17} {saved:>16}")

    print("\nchamadas caras (>=1000 tokens) e o tamanho do chunk que as causou:")
    for r in sorted(rows, key=lambda r: -(r["completion_tokens"] or 0))[:10]:
        print(f"  {r['label']:>10} {r['completion_tokens']:>5} tok  "
              f"clean={r['clean_chars']:>5} raw={r['raw_chars']:>5}  "
              f"{r['step']:>8}  verdict={r['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
