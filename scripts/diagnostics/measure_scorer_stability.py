"""With the evidence held fixed, how stable is the scorer?

The 2026-09-29 outcome-level A/B found Ações 3 and 14 producing different scores
from an IDENTICAL accepted-evidence set, which locates that instability in the
scorer rather than in retrieval or the gate. Every earlier probe in this
investigation measured the gate, so the scorer has never been isolated.

This freezes the evidence - one call to the production _retrieve_and_select(),
reused for every subsequent scorer call - and then scores it N times. Anything
that varies is the scorer alone.

Since ADR-0058 there are two ways a score can move, and they need different
fixes, so both are reported separately:

  * the per-product verdicts moved, and the COUNT over them changed
    (score_source="computed") - a judgement flip on one product
  * the verdicts did not cover the expected product ids, so parse_llm_response
    fell back to the model's own "score" field and forced uncertainty=True
    (score_source="model") - a contract failure, not a judgement

Usage:
    python scripts/diagnostics/measure_scorer_stability.py --acoes 3,14 --passes 8
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

import main as app_main  # noqa: E402,F401 — import triggers _bootstrap(): real DB + LLM wiring

from assessment.service import _retrieve_and_select  # noqa: E402
from evaluation import evaluate  # noqa: E402

PROCESS = "SMG-040_101607_2024"


def verdict_signature(result) -> str:
    """Compact per-product verdict string, e.g. '3a=T'."""
    return " ".join(
        f"{v.product_id}={'T' if v.evidenced else 'F'}"
        for v in sorted(result.product_verdicts, key=lambda v: v.product_id)
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="3,14")
    ap.add_argument("--passes", type=int, default=8)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    acao_ids = [int(x) for x in args.acoes.split(",") if x.strip()]
    dump: dict[str, dict] = {}

    for acao_id in acao_ids:
        # Freeze the evidence ONCE. Every scorer call below sees byte-identical
        # input, so retrieval and the gate are removed as explanations.
        accepted, rejected, reports = _retrieve_and_select(acao_id, PROCESS)
        print(f"\n{'=' * 86}")
        print(f"Ação {acao_id}: evidência congelada, {len(accepted)} chunks aceitos")
        by_product: dict[str, int] = collections.Counter()
        for r in reports:
            by_product[r.expected_product_id] = r.n_accepted
        print(f"  aceitos por produto: {dict(by_product)}")
        if not accepted:
            print("  nenhuma evidência — o scorer nem é chamado; pulando")
            continue

        rows = []
        for p in range(1, args.passes + 1):
            started = time.time()
            try:
                r = evaluate(
                    acao_id,
                    PROCESS,
                    accepted,
                    rejected_chunks=rejected,
                    product_gate_reports=reports,
                )
            except Exception as exc:
                print(f"  passe {p:>2}  ERRO  {type(exc).__name__}: {exc}", flush=True)
                rows.append({"erro": f"{type(exc).__name__}: {exc}"})
                continue
            row = {
                "score": r.proposed_score,
                "source": r.score_source,
                "uncertainty": r.uncertainty_flag,
                "parse_failed": r.parse_failed,
                "verdicts": verdict_signature(r),
                "reasoning_chars": len(r.reasoning or ""),
                "seconds": round(time.time() - started, 1),
            }
            rows.append(row)
            print(f"  passe {p:>2}  score={str(row['score']):>4} "
                  f"src={row['source']:<8} unc={'S' if row['uncertainty'] else 'n'} "
                  f"{row['seconds']:>5.1f}s  {row['verdicts']}", flush=True)

        ok = [r for r in rows if "erro" not in r]
        if not ok:
            continue
        scores = collections.Counter(str(r["score"]) for r in ok)
        sources = collections.Counter(r["source"] for r in ok)
        verdicts = collections.Counter(r["verdicts"] for r in ok)
        modal = max(scores.values()) / len(ok)
        print(f"\n  score              : {dict(scores)}   modal={100 * modal:.0f}%")
        print(f"  score_source       : {dict(sources)}")
        print(f"  vereditos distintos: {len(verdicts)} em {len(ok)} passes")
        for sig, n in verdicts.most_common():
            print(f"      {n:>2}x  {sig}")
        # Which product is actually doing the flipping?
        flipping = []
        for pid in sorted(by_product):
            vals = {
                tok.split("=")[1]
                for r in ok
                for tok in r["verdicts"].split()
                if tok.split("=")[0] == pid
            }
            if len(vals) > 1:
                flipping.append(pid)
        print(f"  produtos que oscilam: {flipping or 'nenhum'}")
        secs = [r["seconds"] for r in ok]
        print(f"  tempo              : {min(secs):.1f}-{max(secs):.1f}s "
              f"(read_timeout do scorer = 45s)")
        dump[str(acao_id)] = {"n_accepted": len(accepted), "rows": rows}

    if args.out:
        Path(args.out).write_text(
            json.dumps(dump, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\ngravado em {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
