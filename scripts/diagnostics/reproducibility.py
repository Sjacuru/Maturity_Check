"""Acceptance test for the stabilisation work: how reproducible is a full run?

Runs the same case N times through the real production path
(assessment.service._retrieve_and_select -> evaluation.evaluate) and reports,
per Ação:

  * the distribution of proposed_score across runs
  * modal agreement — the fraction of runs that produced the most common score
  * whether the accepted-evidence set itself was stable, per product

With --json-out the file also carries, per Ação per run, the gate's explicit
rejections, the per-product examined/accepted counts and the scorer's
per-product verdicts, so a later flip can be attributed to a specific gate
call or to the scorer (the 2026-10-03 acceptance runs could not: only the
final evidence set was kept, and one gate flip cascades through the anchor
target, the cross-product dedup and the budget trim into a different set).

Target: >=90% modal agreement per Ação across 10 runs, whatever the score is.

Deliberately does NOT persist: a measurement run must never clobber the stored
evaluation_results the auditor is reviewing. Retrieval is deterministic, so any
disagreement this reports comes from the gate or the scorer, not from search.

Imports main.py to reuse the exact production LLM wiring — this calls the real
GPU server. Requires the canonical machine to be up; with the fail-fast wiring
a GPU outage aborts the run loudly instead of silently substituting a model.

Usage:
    python scripts/diagnostics/reproducibility.py --runs 10
    python scripts/diagnostics/reproducibility.py --runs 10 --acoes 31,37,40,43
    python scripts/diagnostics/reproducibility.py --runs 10 --ledger scratchpad/acc/ledger.sqlite
    python scripts/diagnostics/reproducibility.py --runs 1 --no-prompt-cache
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
from evaluation import GateLedger, configure_gate_ledger  # noqa: E402

# The gate verdict ledger (ADR-0067) would make every repeated run agree with
# the first by construction. A measurement of the ENGINE needs it off; a
# measurement of the PRODUCTION PATH (--ledger) switches it on, backed by a
# scratch file so the app DB's own ledger is never touched.
configure_gate_ledger(None)
from evaluation import evaluate  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402

DEFAULT_PROCESS = "SMG-040_101607_2024"


def _outcome(result) -> str:
    """Single comparable label per Ação per run."""
    if result.no_evidence_found:
        return "sem_evidencia"
    if result.parse_failed:
        return "parse_failed"
    return f"score={result.proposed_score}"


def _accepted_signature(result) -> tuple:
    return tuple(
        sorted(
            (c.filename, c.page_number, c.chunk_index, tuple(sorted(c.expected_product_ids)))
            for c in result.retrieved_chunks
        )
    )


def _gate_detail(result) -> dict:
    """What the gate and the scorer decided, beyond the final evidence set.

    rejected: every explicit negative verdict (and failed call) as
    (filename, page, chunk_index, product, failed). products: per Expected
    Product, candidates / examined / accepted / rejected / failures / ledger
    hits (the last one is 0 without --ledger). verdicts:
    the scorer's evidenced flag per product, plus score_source. Together with
    the accepted signature this pins each run's gate verdicts: an examined
    chunk that is in neither list was accepted and then dropped by the
    post-gate dedup or the budget trim.
    """
    return {
        "rejected": sorted(
            (r.filename, r.page_number, r.chunk_index, r.expected_product_id, bool(r.gate_failed))
            for r in result.rejected_chunks
        ),
        "products": {
            g.expected_product_id: [g.n_candidates, g.n_examined, g.n_accepted, g.n_rejected,
                                    g.n_gate_failures, g.n_ledger_hits]
            for g in result.product_gate_reports
        },
        "verdicts": {v.product_id: v.evidenced for v in result.product_verdicts},
        "score_source": result.score_source,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--process", default=DEFAULT_PROCESS)
    ap.add_argument("--acoes", default=None, help="comma-separated subset, e.g. 31,37,40")
    ap.add_argument("--json-out", default=None)
    ap.add_argument(
        "--ledger", default=None, metavar="SQLITE_FILE",
        help="switch the gate verdict ledger ON, backed by this scratch SQLite file: run 1 fills it, "
             "later runs answer repeated gate prompts from it. Measures the production path "
             "(ADR-0067) instead of the bare engine; what remains is the scorer. Never data/app.db.",
    )
    ap.add_argument(
        "--no-prompt-cache", action="store_true",
        help="send cache_prompt=false on every call, so the server rebuilds the KV prefix "
             "from scratch instead of reusing it. A server internal: use only when a clean "
             "run with no cache of anything is explicitly wanted. Costs prefill time and was "
             "measured on 2026-10-02 not to improve stability at serial+low.",
    )
    ap.add_argument(
        "--expansion", action="store_true",
        help="turn neighbour expansion back ON for this run. It is off in production "
             "since 2026-10-06 (the question it asks depends on a verdict); this flag "
             "exists to measure the output with it.",
    )
    args = ap.parse_args()
    if args.expansion:
        from evaluation import evidence_selection as _es
        _es.EXPANSION_ENABLED = True
        print("neighbour expansion ENABLED for this run")
    if args.no_prompt_cache:
        from evaluation._config import get_gate_llm_client, get_llm_client
        for _client in (get_llm_client(), get_gate_llm_client()):
            _client.cache_prompt = False
        print("cache_prompt=false on the scorer and the gate client")
    if args.ledger:
        ledger_path = Path(args.ledger).resolve()
        if ledger_path.name == "app.db":
            ap.error("--ledger must be a scratch file, not the app DB")
        configure_gate_ledger(GateLedger(ledger_path))
        print(f"gate verdict ledger ON: {ledger_path} ({GateLedger(ledger_path).count()} verdicts before this run)")

    acao_ids = sorted(get_ipmp_store().acoes)
    if args.acoes:
        wanted = {int(x) for x in args.acoes.split(",")}
        acao_ids = [a for a in acao_ids if a in wanted]

    print(f"reproducibility: {args.runs} runs x {len(acao_ids)} Ação(ões), case '{args.process}'")
    print("results are NOT persisted\n")

    outcomes: dict[int, list[str]] = collections.defaultdict(list)
    signatures: dict[int, list[tuple]] = collections.defaultdict(list)
    accepted_counts: dict[int, list[int]] = collections.defaultdict(list)
    errors: dict[int, list[str]] = collections.defaultdict(list)
    details: dict[int, list[dict]] = collections.defaultdict(list)

    for run in range(1, args.runs + 1):
        started = time.monotonic()
        # ADR-0070: production derives the dependency cap from the Ações already
        # scored in the run; a subset run (--acoes) sees only the subset, like
        # a production run that failed on the missing ones (unknown -> no cap).
        prior: dict[int, object] = {}
        for acao_id in acao_ids:
            try:
                accepted, rejected, gate_reports = _retrieve_and_select(acao_id, args.process)
                result = evaluate(
                    acao_id,
                    args.process,
                    accepted,
                    rejected_chunks=rejected,
                    product_gate_reports=gate_reports,
                    prior_results=prior,
                )
                prior[acao_id] = result
            except Exception as exc:  # a run must not die on one Ação
                errors[acao_id].append(f"{type(exc).__name__}: {exc}")
                outcomes[acao_id].append("erro")
                signatures[acao_id].append(())
                accepted_counts[acao_id].append(0)
                details[acao_id].append({})
                continue
            outcomes[acao_id].append(_outcome(result))
            signatures[acao_id].append(_accepted_signature(result))
            accepted_counts[acao_id].append(len(result.retrieved_chunks))
            details[acao_id].append(_gate_detail(result))
        print(f"  run {run}/{args.runs} done in {time.monotonic()-started:.0f}s")

    print("\n" + "=" * 86)
    print("PER-AÇÃO REPRODUCIBILITY")
    print("=" * 86)
    print("Ação  concord.  desfechos observados                       evid.estável  n_aceitos")
    below = []
    for acao_id in acao_ids:
        obs = outcomes[acao_id]
        counts = collections.Counter(obs)
        modal, modal_n = counts.most_common(1)[0]
        agreement = modal_n / len(obs)
        sig_stable = len(set(signatures[acao_id])) == 1
        counts_txt = " ".join(f"{k}x{v}" for k, v in counts.most_common())
        acc = accepted_counts[acao_id]
        acc_txt = f"{min(acc)}-{max(acc)}" if min(acc) != max(acc) else str(acc[0])
        flag = "" if agreement >= 0.9 else "  <-- abaixo de 90%"
        if agreement < 0.9:
            below.append(acao_id)
        print(
            f"{acao_id:>4}  {100*agreement:>6.0f}%  {counts_txt:<42} "
            f"{'sim' if sig_stable else 'NAO':<12} {acc_txt:>9}{flag}"
        )

    print("\n" + "=" * 86)
    overall = sum(
        collections.Counter(outcomes[a]).most_common(1)[0][1] / len(outcomes[a])
        for a in acao_ids
    ) / len(acao_ids)
    fully = sum(1 for a in acao_ids if len(set(outcomes[a])) == 1)
    print(f"mean modal agreement            : {100*overall:.1f}%")
    print(f"Ações identical in all {args.runs} runs : {fully}/{len(acao_ids)} ({100*fully/len(acao_ids):.0f}%)")
    print(f"Ações below the 90% target      : {len(below)} {below or ''}")
    stable_evidence = sum(1 for a in acao_ids if len(set(signatures[a])) == 1)
    print(f"Ações with an identical accepted-evidence set every run: {stable_evidence}/{len(acao_ids)}")
    if errors:
        print("\nerrors encountered:")
        for acao_id, msgs in sorted(errors.items()):
            print(f"  Ação {acao_id}: {len(msgs)}x  {msgs[0]}")

    if args.json_out:
        payload = {
            "process": args.process,
            "runs": args.runs,
            "outcomes": {str(a): outcomes[a] for a in acao_ids},
            "accepted_counts": {str(a): accepted_counts[a] for a in acao_ids},
            # Which chunks were accepted, per run: (filename, page, chunk_index,
            # product ids). Without it two sweeps with the same accepted COUNT
            # cannot be told apart (R10->R11, 2026-10-02: Ações 20 and 40 went
            # score 0->1 at an unchanged count, and the files could not say
            # whether the evidence or only the scorer had moved).
            "accepted": {
                str(a): [[list(sig) for sig in run_sig] for run_sig in signatures[a]]
                for a in acao_ids
            },
            "errors": {str(a): errors[a] for a in errors},
            # Gate rejections, per-product counts and scorer verdicts per run
            # (see _gate_detail). Added after the 2026-10-03 acceptance runs.
            "gate": {str(a): details[a] for a in acao_ids},
        }
        Path(args.json_out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nraw outcomes written to {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
