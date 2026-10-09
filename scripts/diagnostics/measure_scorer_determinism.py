"""Is the scorer non-deterministic, or is every score flip inherited from upstream?

measure_scorer_stability.py froze ONE evidence set and found the scorer perfectly
stable over 8 calls - but it froze whichever set _retrieve_and_select() happened
to return, which turned out to be the stable one. The outcome-level A/B had seen
an apparently identical evidence set produce different scores, so the question
was still open.

The flaw was the signature that A/B used: sorted (filename, page, chunk_index).
build_user_prompt() also depends on chunk.expected_product_ids (which product
block a chunk lands in, and whether it lands in any) and on order within each
block, and evaluate() applies _cap_evidence() first. Two passes can therefore
share that signature and still send different prompts.

So this signs the thing that actually decides the answer: the system+user prompt
the scorer client really receives, captured by wrapping complete(). Then:

  * same prompt hash, different score  => the SCORER is non-deterministic
  * every prompt hash maps to one score => the scorer is deterministic and every
    observed flip was inherited from the gate, however similar the evidence looked

Usage:
    python scripts/diagnostics/measure_scorer_determinism.py --acoes 3,14 --passes 10
"""

from __future__ import annotations

import argparse
import collections
import hashlib
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
from evaluation._config import get_llm_client  # noqa: E402

PROCESS = "SMG-040_101607_2024"

_captured: list[str] = []


def install_prompt_capture() -> None:
    """Record a digest of every (system, user) pair the scorer client is given.

    Wrapping the client rather than rebuilding the prompt here keeps the digest
    honest: it is whatever evaluate() actually sent, including _cap_evidence()
    truncation and per-product block assembly.
    """
    client = get_llm_client()
    real = client.complete

    def wrapped(system: str, user: str, schema: dict | None = None) -> str:
        _captured.append(
            hashlib.sha256(f"{system}\x00{user}".encode("utf-8")).hexdigest()[:12]
        )
        return real(system, user, schema)

    client.complete = wrapped  # type: ignore[method-assign]


def verdicts(result) -> str:
    return " ".join(
        f"{v.product_id}={'T' if v.evidenced else 'F'}"
        for v in sorted(result.product_verdicts, key=lambda v: v.product_id)
    )


def outcome(result) -> str:
    if result.no_evidence_found:
        return "sem_evidencia"
    if result.parse_failed:
        return "parse_failed"
    return f"score={result.proposed_score}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="3,14")
    ap.add_argument("--passes", type=int, default=10)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    install_prompt_capture()
    acao_ids = [int(x) for x in args.acoes.split(",") if x.strip()]
    dump: dict[str, list[dict]] = {}

    for acao_id in acao_ids:
        print(f"\n{'=' * 92}")
        print(f"Ação {acao_id}: {args.passes} passes completos (recuperação + gate + scorer)")
        rows: list[dict] = []
        for p in range(1, args.passes + 1):
            _captured.clear()
            started = time.time()
            accepted, rejected, reports = _retrieve_and_select(acao_id, PROCESS)
            r = evaluate(
                acao_id, PROCESS, accepted,
                rejected_chunks=rejected, product_gate_reports=reports,
            )
            # Attribution is part of the prompt, so it is part of the identity of
            # the evidence - the earlier A/B's chunk-only signature missed it.
            attribution = tuple(
                (c.filename, c.page_number, c.chunk_index, tuple(sorted(c.expected_product_ids)))
                for c in accepted
            )
            row = {
                "prompt": _captured[-1] if _captured else "(scorer nao chamado)",
                "outcome": outcome(r),
                "verdicts": verdicts(r),
                "n": len(accepted),
                "attr": hashlib.sha256(repr(attribution).encode()).hexdigest()[:8],
                "votes": r.n_scorer_votes,
                "splits": r.n_verdict_splits,
                "seconds": round(time.time() - started, 1),
            }
            rows.append(row)
            print(f"  passe {p:>2}  prompt={row['prompt']}  attr={row['attr']}  "
                  f"n={row['n']:>2}  {row['outcome']:<14} {row['seconds']:>6.1f}s  "
                  f"votos={row['votes']} splits={row['splits']}  "
                  f"{row['verdicts']}", flush=True)
        dump[str(acao_id)] = rows

        by_prompt: dict[str, set[str]] = collections.defaultdict(set)
        for r in rows:
            by_prompt[r["prompt"]].add(r["outcome"])
        outcomes = collections.Counter(r["outcome"] for r in rows)
        print(f"\n  desfechos          : {dict(outcomes)}  "
              f"modal={100 * max(outcomes.values()) / len(rows):.0f}%")
        print(f"  prompts distintos  : {len(by_prompt)} em {len(rows)} passes")
        print(f"  atribuições distintas: {len({r['attr'] for r in rows})}")
        with_split = sum(1 for r in rows if r["splits"])
        print(f"  passes com divergência entre votos: {with_split}/{len(rows)}")
        ambiguous = {k: v for k, v in by_prompt.items() if len(v) > 1}
        if ambiguous:
            print(f"  >>> SCORER NAO DETERMINISTICO: {len(ambiguous)} prompt(s) "
                  f"com mais de um desfecho")
            for k, v in ambiguous.items():
                print(f"        {k} -> {sorted(v)}")
        else:
            print("  >>> scorer DETERMINISTICO: cada prompt deu sempre o mesmo "
                  "desfecho; toda a variação vem do gate")

    if args.out:
        Path(args.out).write_text(
            json.dumps(dump, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\ngravado em {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
