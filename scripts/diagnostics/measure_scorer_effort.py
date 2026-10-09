"""Scorer-only stability: the same frozen evidence set, scored N times at the
production reasoning effort (medium) and at low, interleaved.

Why this exists. The 2026-10-03 acceptance runs (10 × 46 Ações, frozen tree,
gate serial+low, no ledger) left two kinds of residue: evidence sets that differ
between runs (gate verdicts that flip, amplified by the anchor target and the
post-gate dedup — what the gate verdict ledger, ADR-0067, freezes) and scores
that differ on IDENTICAL evidence (Ação 32: one chunk, scores 1/0/1/1/0/1 over
six runs; Ação 37: 3 vs 0 on the same two chunks). The second kind is the
scorer's own, and the ledger does nothing about it. This script measures it in
isolation: retrieval + gate run once per Ação, then only the scorer is repeated,
so every difference it reports is the scorer's.

It is a measurement, not a change: nothing in main.py is touched. Both clients
point at the project's own GPU server (ADR-0059); `reasoning_effort` is a model
setting passed through the chat template, not a server internal.

Never run it while another measurement or assessment is using the server — a
second caller breaks the one-call-in-flight condition of ADR-0065.

Usage:
    python scripts/diagnostics/measure_scorer_effort.py --acoes 32,37,10,4,23 --passes 6
    python scripts/diagnostics/measure_scorer_effort.py --acoes 32 --passes 10 --json-out out.json
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

import main as app_main  # noqa: E402 — production wiring (DB, gate client, scorer client)

from assessment.service import _retrieve_and_select  # noqa: E402
from evaluation import configure_gate_ledger, configure_llm_client, evaluate  # noqa: E402
from evaluation._config import get_llm_client, get_model, get_provider  # noqa: E402
from evaluation.llm.llamacpp import LlamaCppClient  # noqa: E402

configure_gate_ledger(None)  # measure the engine, not the ledger

DEFAULT_PROCESS = "SMG-040_101607_2024"


def _outcome(result) -> str:
    if result.no_evidence_found:
        return "sem_evidencia"
    if result.parse_failed:
        return "parse_failed"
    return f"score={result.proposed_score}"


def _verdicts(result) -> dict[str, bool]:
    return {v.product_id: v.evidenced for v in result.product_verdicts}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--acoes", required=True, help="comma-separated Ação ids")
    ap.add_argument("--passes", type=int, default=6)
    ap.add_argument("--process", default=DEFAULT_PROCESS)
    ap.add_argument("--efforts", default="medium,low",
                    help="comma-separated reasoning efforts to compare; 'medium' means the production client")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    acao_ids = [int(x) for x in args.acoes.split(",") if x.strip()]
    efforts = [e.strip() for e in args.efforts.split(",") if e.strip()]

    # The production scorer client (medium = server default) is whatever main.py
    # wired; the others are built the same way with the effort set explicitly.
    prod_client, provider, model = get_llm_client(), get_provider(), get_model()
    clients = {}
    for e in efforts:
        if e == "medium":
            clients[e] = prod_client
        else:
            clients[e] = LlamaCppClient(app_main._LLAMACPP_BASE_URL, app_main._LLAMACPP_MODEL, reasoning_effort=e)

    print(f"scorer stability: Ações {acao_ids}, {args.passes} passes × {efforts}, case {args.process!r}")
    print("retrieval + gate once per Ação; only the scorer repeats; results are NOT persisted\n")

    out = {"process": args.process, "passes": args.passes, "efforts": efforts, "acoes": {}}
    for acao_id in acao_ids:
        t0 = time.monotonic()
        accepted, rejected, gate_reports = _retrieve_and_select(acao_id, args.process)
        t_gate = time.monotonic() - t0
        n_acc = len(accepted)
        prods = sorted({p for c in accepted for p in c.expected_product_ids})
        print(f"Ação {acao_id}: {n_acc} chunks aceitos para {prods} (gate {t_gate:.0f}s)")
        rec = {"n_accepted": n_acc, "products_evidenced": prods, "runs": {e: [] for e in efforts}}
        if n_acc == 0:
            print("  sem evidência — o scorer não é chamado; pulando\n")
            out["acoes"][str(acao_id)] = rec
            continue
        for p in range(1, args.passes + 1):
            for e in efforts:
                configure_llm_client(clients[e], provider=provider, model=model)
                t1 = time.monotonic()
                try:
                    r = evaluate(acao_id, args.process, accepted,
                                 rejected_chunks=rejected, product_gate_reports=gate_reports)
                    item = {"outcome": _outcome(r), "verdicts": _verdicts(r),
                            "uncertainty": r.uncertainty_flag, "score_source": r.score_source,
                            "seconds": round(time.monotonic() - t1, 1)}
                except Exception as exc:  # keep measuring; record the failure
                    item = {"outcome": f"erro:{type(exc).__name__}", "verdicts": {},
                            "uncertainty": None, "score_source": None,
                            "seconds": round(time.monotonic() - t1, 1)}
                rec["runs"][e].append(item)
        configure_llm_client(prod_client, provider=provider, model=model)  # leave production wiring intact
        for e in efforts:
            outs = [x["outcome"] for x in rec["runs"][e]]
            dist = collections.Counter(outs)
            modal_cnt = dist.most_common(1)[0][1]
            secs = [x["seconds"] for x in rec["runs"][e]]
            # per-product verdict stability
            flips = []
            for pid in prods:
                vs = [x["verdicts"].get(pid) for x in rec["runs"][e]]
                if len(set(vs)) > 1:
                    flips.append(f"{pid}:{''.join('T' if v else ('F' if v is False else '?') for v in vs)}")
            print(f"  {e:<7} {' '.join(o.replace('score=', 's').replace('sem_evidencia', 'sem') for o in outs):<40}"
                  f" concordância {modal_cnt / args.passes:4.0%}  {sum(secs) / len(secs):5.1f}s/chamada"
                  f"  produtos que oscilam: {flips or 'nenhum'}")
        print()
        out["acoes"][str(acao_id)] = rec

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"raw results written to {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
