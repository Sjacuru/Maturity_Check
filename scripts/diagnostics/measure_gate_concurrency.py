"""Is the gate's run-to-run noise caused by how many calls share the GPU?

Run 3 eliminated gate failures entirely, and with that confounder gone the
residual instability became measurable: 7 Acoes changed outcome between Run 2
and Run 3 despite the cap change being a no-op for them — 39/46 = 84.8%
agreement between two effectively identical configurations. The 2026-08-27
forensics found that heterogeneous concurrency (different products' prompts
sharing GPU slots) was the ONLY condition that reproduced verdict flips;
homogeneous concurrency was 0/184.

IMPORTANT correction to an earlier hypothesis: evidence_selection opens
`ThreadPoolExecutor(max_workers=max(len(candidates), 1))` — the product count,
9 for Acao 31 — but that is NOT how many requests reach the server.
LlamaCppClient.complete() acquires a semaphore sized
`max_concurrent_requests` (default 4), so at most 4 gate calls are ever in
flight from this process. The pool's width is therefore irrelevant above 4, and
the real knob is the client semaphore. This script moves that one.

Two levels are compared, because they isolate different stages:

  * accepted-evidence set per Acao — upstream of the scorer, isolates gate noise
  * final outcome per Acao — what the acceptance criterion actually counts

A transport failure is recorded as an outcome rather than aborting: the gate
deliberately does not catch LlamaCppTimeout (ADR-0060), and one 240s stall would
otherwise destroy the whole measurement.

Nothing is persisted to the app DB; a JSON of the raw passes goes to --out.

Usage:
    python scripts/diagnostics/measure_gate_concurrency.py --acoes 31,35,15,25 --workers 3
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
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
from evaluation.llm.llamacpp import (  # noqa: E402
    LlamaCppBusy,
    LlamaCppTimeout,
    LlamaCppUnavailable,
)

_TRANSPORT = (LlamaCppTimeout, LlamaCppUnavailable, LlamaCppBusy)


def set_in_flight(n: int) -> None:
    """Resize the gate client's concurrency semaphore in place."""
    get_gate_llm_client()._semaphore = threading.Semaphore(n)


def _outcome(result) -> str:
    if result.no_evidence_found:
        return "sem_evidencia"
    if result.parse_failed:
        return "parse_failed"
    return f"score={result.proposed_score}"


def _accepted(result) -> list:
    return sorted(
        [c.filename, c.page_number, c.chunk_index] for c in result.retrieved_chunks
    )


def one_pass(acao_ids: list[int], process: str, tag: str) -> dict:
    out: dict = {}
    for aid in acao_ids:
        t0 = time.time()
        try:
            accepted, rejected, reports = _retrieve_and_select(aid, process)
            result = evaluate(aid, process, accepted, rejected_chunks=rejected,
                              product_gate_reports=reports)
            rec = {"outcome": _outcome(result), "accepted": _accepted(result),
                   "fail": None}
        except _TRANSPORT as exc:
            rec = {"outcome": f"FALHA_{type(exc).__name__}", "accepted": [],
                   "fail": f"{type(exc).__name__}: {exc}"}
        rec["seconds"] = round(time.time() - t0, 1)
        out[aid] = rec
        print(f"    [{tag}] Acao {aid:>2}: {rec['outcome']:>16}  "
              f"{len(rec['accepted'])} chunk(s)  {rec['seconds']:.0f}s", flush=True)
    return out


def compare(label: str, p1: dict, p2: dict) -> dict:
    ids = sorted(p1)
    same_out = [a for a in ids if p1[a]["outcome"] == p2[a]["outcome"]]
    same_ev = [a for a in ids if p1[a]["accepted"] == p2[a]["accepted"]]
    print(f"\n--- {label} ---", flush=True)
    print(f"  mesmo desfecho   : {len(same_out)}/{len(ids)} "
          f"({100*len(same_out)/len(ids):.0f}%)", flush=True)
    print(f"  mesma evidencia  : {len(same_ev)}/{len(ids)} "
          f"({100*len(same_ev)/len(ids):.0f}%)", flush=True)
    for a in ids:
        r1, r2 = p1[a], p2[a]
        if r1["outcome"] != r2["outcome"] or r1["accepted"] != r2["accepted"]:
            s1 = {tuple(x) for x in r1["accepted"]}
            s2 = {tuple(x) for x in r2["accepted"]}
            flag = "DESFECHO" if r1["outcome"] != r2["outcome"] else "evidencia"
            print(f"    Acao {a:>2}: {flag:>9}  {r1['outcome']} -> {r2['outcome']}  "
                  f"(|{len(s1)}| vs |{len(s2)}|, {len(s1 ^ s2)} chunk(s) de diferenca)",
                  flush=True)
    return {"same_outcome": len(same_out), "same_evidence": len(same_ev),
            "n": len(ids)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="31,35,15,25")
    ap.add_argument("--process", default="SMG-040_101607_2024")
    ap.add_argument("--workers", type=int, default=3,
                    help="in-flight gate calls in the reduced condition")
    ap.add_argument("--out", default=None, help="JSON dump of every pass")
    args = ap.parse_args()

    acao_ids = [int(x) for x in args.acoes.split(",")]
    current = get_gate_llm_client()._semaphore._value
    print(f"Acoes {acao_ids}, caso {args.process} — nada e persistido", flush=True)
    print(f"concorrencia em voo hoje (semaforo do cliente): {current}", flush=True)

    conditions = [(f"ATUAL ({current} chamadas em voo)", current),
                  (f"REDUZIDA a {args.workers} chamadas em voo", args.workers)]

    dump: dict = {"acoes": acao_ids, "conditions": {}}
    for label, n in conditions:
        set_in_flight(n)
        t0 = time.time()
        p1 = one_pass(acao_ids, args.process, f"{n}w p1")
        t_mid = time.time()
        p2 = one_pass(acao_ids, args.process, f"{n}w p2")
        t_end = time.time()
        summary = compare(label, p1, p2)
        print(f"  tempo: passe 1 = {t_mid-t0:.0f}s, passe 2 = {t_end-t_mid:.0f}s",
              flush=True)
        dump["conditions"][str(n)] = {"label": label, "summary": summary,
                                     "pass1": p1, "pass2": p2,
                                     "seconds": [round(t_mid-t0, 1),
                                                 round(t_end-t_mid, 1)]}
        if args.out:
            Path(args.out).write_text(json.dumps(dump, indent=2, ensure_ascii=False),
                                      encoding="utf-8")

    set_in_flight(current)
    print("\nNota: 2 passes por condicao e uma amostra pequena — isto indica "
          "direcao, nao mede o criterio de 90%.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
