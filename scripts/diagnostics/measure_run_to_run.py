"""Run-to-run agreement under ONE fixed configuration.

This exists because the sweep-to-sweep comparisons this investigation has been
using cannot measure stability: R6->R7, R7->R8 and R8->R9 each straddle a
CONFIGURATION CHANGE, so their disagreement mixes "the system is noisy" with
"the system was deliberately altered". The acceptance criterion — 90% of runs
producing the same output — is about repeating the SAME configuration.

It also reads what the reproducibility harness does not record: WHERE a flip
comes from. Identical accepted evidence with a different score is the SCORER;
different evidence is the GATE. They need different fixes, and the sweep
harness cannot tell them apart because it stores no evidence signature.

This is the harness that measured and killed best-of-N gate voting (ADR-0061).

Nothing is persisted to the app DB.

Usage:
    python scripts/diagnostics/measure_run_to_run.py --acoes 12,20,31,5,11,28,15
"""

from __future__ import annotations

import argparse
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

import main as app_main  # noqa: E402,F401 — triggers _bootstrap(): real DB + LLM wiring

from assessment.service import _retrieve_and_select  # noqa: E402
from evaluation import evaluate  # noqa: E402
from evaluation._config import get_gate_llm_client  # noqa: E402


def _outcome(result) -> str:
    if result.no_evidence_found:
        return "sem_evidencia"
    if result.parse_failed:
        return "parse_failed"
    return f"score={result.proposed_score}"


def _evidence(result) -> list:
    return sorted([c.filename, c.page_number, c.chunk_index] for c in result.retrieved_chunks)


def one_pass(acao_ids: list[int], process: str, tag: str) -> dict:
    out: dict = {}
    for aid in acao_ids:
        t0 = time.time()
        accepted, rejected, reports = _retrieve_and_select(aid, process)
        result = evaluate(aid, process, accepted, rejected_chunks=rejected,
                          product_gate_reports=reports)
        reps = result.product_gate_reports or []
        rec = {
            "outcome": _outcome(result),
            "evidence": _evidence(result),
            "n_examined": sum(r.n_examined for r in reps),
            "n_failures": sum(r.n_gate_failures for r in reps),
            "seconds": round(time.time() - t0, 1),
        }
        out[aid] = rec
        print(f"    [{tag}] Ação {aid:>2}: {rec['outcome']:>14}  "
              f"{len(rec['evidence']):>2} chunk(s)  "
              f"gate {rec['n_examined']:>3} chunks, {rec['n_failures']} falha(s)  "
              f"{rec['seconds']:.0f}s", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="12,20,31,5,11,28,15")
    ap.add_argument("--process", default="SMG-040_101607_2024")
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--in-flight", type=int, default=None,
                    help="cap concurrent gate calls (client semaphore); "
                         "omit to keep the wired value")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    acao_ids = [int(x) for x in args.acoes.split(",")]
    client = get_gate_llm_client()
    if args.in_flight is not None:
        import threading
        client._semaphore = threading.Semaphore(args.in_flight)
    in_flight = client._semaphore._value
    print(f"Ações {acao_ids} — {args.passes} passes na MESMA configuração, "
          f"{in_flight} chamada(s) de gate em voo, nada é persistido", flush=True)

    passes = []
    elapsed = []
    for i in range(1, args.passes + 1):
        started = time.time()
        passes.append(one_pass(acao_ids, args.process, f"p{i}"))
        elapsed.append(time.time() - started)
        if args.out:
            Path(args.out).write_text(json.dumps(passes, indent=2, ensure_ascii=False),
                                      encoding="utf-8")

    print("\n=== concordância entre passes da MESMA configuração ===", flush=True)
    first = passes[0]
    same_out = [a for a in acao_ids if len({p[a]["outcome"] for p in passes}) == 1]
    same_ev = [a for a in acao_ids
               if all(p[a]["evidence"] == first[a]["evidence"] for p in passes)]
    n = len(acao_ids)
    print(f"  mesmo desfecho  : {len(same_out)}/{n} ({100*len(same_out)/n:.0f}%)")
    print(f"  mesma evidência : {len(same_ev)}/{n} ({100*len(same_ev)/n:.0f}%)")

    print(f"\n{'Ação':>5}  {'origem':>14}  desfechos")
    for a in acao_ids:
        outs = [p[a]["outcome"] for p in passes]
        evs_same = all(p[a]["evidence"] == first[a]["evidence"] for p in passes)
        if len(set(outs)) == 1:
            origem = "estável" if evs_same else "só evidência"
        else:
            origem = "SCORER" if evs_same else "gate+scorer"
        print(f"{a:>5}  {origem:>14}  {' | '.join(outs)}")

    tot_chunks = sum(p[a]["n_examined"] for p in passes for a in acao_ids)
    diff = sum(len({tuple(x) for x in passes[0][a]["evidence"]}
                   ^ {tuple(x) for x in p[a]["evidence"]})
               for p in passes[1:] for a in acao_ids)
    print("")
    print(f"chunks julgados: {tot_chunks} | chunks de evidência que "
          f"divergiram entre passes: {diff}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
