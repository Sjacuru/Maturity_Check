"""A/B the Acao/product identity block in the gate prompt, with enough power to decide.

The first attempt at this comparison ran 4 passes per condition and counted how
many chunks were "not unanimous in 4". That statistic is fragile twice over:

  1. Four calls detect a chunk that flips 20% of the time only ~59% of the time,
     so two runs of the same configuration disagree about WHICH chunks are
     unstable - and indeed only 3 of 12 overlapped between the two 4-pass runs.
  2. It is binary per chunk. A chunk that flips once in 10 and a chunk that
     splits 5/5 both count as exactly 1.

So this measures the aggregate minority-vote rate instead: over all calls of a
condition, the share that disagreed with that chunk's own majority. It uses every
call, is a proportion with a known standard error, and is the quantity that
actually propagates into a score (one flipped verdict is one flipped verdict,
whichever chunk it came from).

The two conditions are interleaved within the session, alternating which goes
first on each pass. The 4-pass run showed a first-pass anomaly - 9 of 12 unstable
chunks were F on pass 1 and T afterwards, 5 of them exactly F/T/T/T - which looks
like a cold-KV warm-up effect. Running one condition to completion and then the
other would hand that entire effect to whichever went first.

Usage:
    python scripts/diagnostics/measure_identity_ab.py --acoes 15 --passes 10
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from evaluation.evidence_selection import (  # noqa: E402
    _prefilter_near_duplicates,
    strip_extraction_noise,
)
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
PROCESS = "SMG-040_101607_2024"
MAX_EXAMINED = 8
IN_FLIGHT = 4  # production shape


def call(system: str, user: str) -> bool | None:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "stream": False,
        "max_tokens": 8192,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "response", "schema": GATE_SCHEMA, "strict": True},
        },
    }
    req = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            body = json.load(r)
        return bool(json.loads(body["choices"][0]["message"].get("content") or "")["relevant"])
    except Exception:
        return None


def build_prompts(acao_ids: list[int]) -> list[dict]:
    """One entry per (product, candidate), carrying BOTH system prompts.

    Same chunk, same criterion, same candidate set in both conditions - the only
    difference between the two system prompts is the identity block, which is
    what makes this a paired comparison rather than two separate samples.
    """
    ipmp, profiles = get_ipmp_store(), get_retrieval_profile_store()
    out: list[dict] = []
    for acao_id in acao_ids:
        acao = ipmp.acoes[acao_id]
        profile = profiles.acoes.get(acao_id)
        candidates = retrieve_hybrid_candidates_for_acao(acao_id, PROCESS)
        seen: set[str] = set()
        for product in acao.produtos_esperados:
            if not product.scored:
                continue
            pp = profile.expected_products.get(product.id) if profile else None
            if pp is None or not pp.evidence_intent:
                continue
            concepts = [c.text for c in pp.retrieval_signal_concepts]
            common = (pp.evidence_intent, concepts, pp.negative_evidence_patterns)
            with_id = build_relevance_system_prompt(
                *common, acao=acao, product_id=product.id
            )
            without_id = build_relevance_system_prompt(*common)
            for _score, chunk in _prefilter_near_duplicates(
                candidates.get(product.id, [])
            )[:MAX_EXAMINED]:
                user = build_relevance_user_prompt(strip_extraction_noise(chunk.text))
                if (key := f"{product.id}|{user}") in seen:
                    continue
                seen.add(key)
                out.append({
                    "label": f"{acao_id}/{product.id}/pg{chunk.page_number}#{chunk.chunk_index}",
                    "user": user,
                    "ON": with_id,
                    "OFF": without_id,
                })
    return out


def run_pass(prompts: list[dict], condition: str) -> list[bool | None]:
    with ThreadPoolExecutor(max_workers=IN_FLIGHT) as pool:
        return list(pool.map(lambda p: call(p[condition], p["user"]), prompts))


def minority_rate(votes: list[list[bool | None]]) -> tuple[int, int, int]:
    """(minority calls, total valid calls, chunks that were not unanimous)."""
    minority = total = split = 0
    for vs in votes:
        valid = [v for v in vs if v is not None]
        if not valid:
            continue
        t = sum(1 for v in valid if v)
        total += len(valid)
        minority += min(t, len(valid) - t)
        if t and t != len(valid):
            split += 1
    return minority, total, split


def two_proportion_z(a: tuple[int, int], b: tuple[int, int]) -> float:
    (x1, n1), (x2, n2) = a, b
    if not n1 or not n2:
        return 0.0
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return 0.0 if se == 0 else (x1 / n1 - x2 / n2) / se


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="15", help="comma-separated Acao ids")
    ap.add_argument("--passes", type=int, default=10, help="passes PER condition")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    acao_ids = [int(x) for x in args.acoes.split(",") if x.strip()]
    retrieval_configure(ROOT / "data" / "app.db")
    prompts = build_prompts(acao_ids)
    n = len(prompts)
    print(f"Acoes {acao_ids}: {n} prompts de gate (produto x candidato, apos dedup pre-gate)")
    print(f"{args.passes} passes por condicao, intercaladas, {IN_FLIGHT} em voo")
    print(f"total previsto: {2 * args.passes * n} chamadas\n", flush=True)

    votes = {"ON": [[] for _ in range(n)], "OFF": [[] for _ in range(n)]}
    for p in range(1, args.passes + 1):
        # Alternate which condition opens the pass, so the warm-up effect seen on
        # pass 1 of the earlier probe cannot land systematically on one of them.
        order = ("ON", "OFF") if p % 2 else ("OFF", "ON")
        for condition in order:
            started = time.time()
            for i, v in enumerate(run_pass(prompts, condition)):
                votes[condition][i].append(v)
            print(f"  passe {p:>2}/{args.passes}  {condition:>3}  "
                  f"{time.time() - started:.0f}s", flush=True)

    print()
    results = {}
    for condition in ("ON", "OFF"):
        minority, total, split = minority_rate(votes[condition])
        results[condition] = (minority, total, split)
        rate = 100 * minority / total if total else 0.0
        se = 100 * math.sqrt(rate / 100 * (1 - rate / 100) / total) if total else 0.0
        name = "COM identidade" if condition == "ON" else "SEM identidade"
        print(f"{name:>16}: voto minoritario {minority:>4}/{total:<5} = "
              f"{rate:>5.2f}% (+-{se:.2f})   chunks nao unanimes {split}/{n}")

    z = two_proportion_z(results["ON"][:2], results["OFF"][:2])
    print(f"\nz = {z:+.2f}  ", end="")
    if abs(z) < 1.96:
        print("=> diferenca NAO distinguivel de ruido (|z| < 1.96)")
    else:
        better = "COM identidade" if z < 0 else "SEM identidade"
        print(f"=> {better} tem menos voto minoritario (p < 0.05)")

    # Per-chunk detail, only where the two conditions disagree about stability.
    print("\nchunks nao unanimes em ao menos uma condicao:")
    header = f"{'chunk':>34} {'COM':>{args.passes + 2}} {'SEM':>{args.passes + 2}}"
    print(header)
    fmt = lambda vs: "".join(  # noqa: E731
        "T" if v else "F" if v is False else "?" for v in vs
    )
    for i, prompt in enumerate(prompts):
        on, off = votes["ON"][i], votes["OFF"][i]
        if len(set(on)) > 1 or len(set(off)) > 1:
            print(f"{prompt['label']:>34} {fmt(on):>{args.passes + 2}} "
                  f"{fmt(off):>{args.passes + 2}}")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "acoes": acao_ids,
            "passes": args.passes,
            "labels": [p["label"] for p in prompts],
            "votes": votes,
            "summary": {k: {"minority": v[0], "total": v[1], "split": v[2]}
                        for k, v in results.items()},
            "z": z,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\ngravado em {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
