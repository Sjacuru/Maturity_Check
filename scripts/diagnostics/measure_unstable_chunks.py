"""Find the chunks that actually flip, then test what makes them flip.

Two earlier experiments found no cache contamination, but neither had tested a
chunk that is known to be unstable - they sampled chunks that happen to be
unambiguous, where nothing flips under any condition. Testing a brake on dry
tarmac proves little.

So this works in two phases:

  1. PROBE - ask every candidate of every scored product N times, in the exact
     production shape (concurrent, cache on), and keep the chunks whose verdict
     was not unanimous. Those are the ones that decide scores between runs.
  2. CONFIRM - re-ask only those, M times each, under three conditions that
     separate the three candidate causes:

       seq-ON    sequential, cache on   - one call at a time, cache reused
       seq-OFF   sequential, cache off  - cache bypassed entirely
       conc-ON   4 in flight, cache on  - the production shape

     Stable in seq-ON and seq-OFF but unstable in conc-ON => concurrency/batching
     is the cause, not the cache. Stable in seq-OFF only => the cache is. Unstable
     everywhere => the model itself, which no serving policy fixes.

`/slots/{id}?action=erase` is NOT enabled on this server, so cache_prompt=false
is the only available bypass.

Usage:
    python scripts/diagnostics/measure_unstable_chunks.py --acao 15
"""

from __future__ import annotations

import argparse
import json
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


def call(system: str, user: str, cache_prompt: bool | None = None) -> bool | None:
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
    if cache_prompt is not None:
        payload["cache_prompt"] = cache_prompt
    req = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            body = json.load(r)
        content = body["choices"][0]["message"].get("content") or ""
        return bool(json.loads(content)["relevant"])
    except Exception:
        return None


IDENTITY = True  # include the Acao/product identity block in the gate prompt


def build_prompts(acao_id: int) -> list[tuple[str, str, str]]:
    """(label, system, user) for every candidate of every scored product."""
    acao = get_ipmp_store().acoes[acao_id]
    profile = get_retrieval_profile_store().acoes.get(acao_id)
    candidates = retrieve_hybrid_candidates_for_acao(acao_id, PROCESS)
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()
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
            acao=acao if IDENTITY else None,
            product_id=product.id if IDENTITY else None,
        )
        ranked = _prefilter_near_duplicates(candidates.get(product.id, []))
        for _score, chunk in ranked[:MAX_EXAMINED]:
            user = build_relevance_user_prompt(strip_extraction_noise(chunk.text))
            label = f"{product.id}/pg{chunk.page_number}#{chunk.chunk_index}"
            if (key := f"{product.id}|{user}") in seen:
                continue
            seen.add(key)
            out.append((label, system, user))
    return out


def run_batch(prompts, cache_prompt, workers) -> list:
    if workers <= 1:
        return [call(s, u, cache_prompt) for _l, s, u in prompts]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda p: call(p[1], p[2], cache_prompt), prompts))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acao", type=int, default=15)
    ap.add_argument("--probe", type=int, default=4, help="passes to find unstable chunks")
    ap.add_argument("--confirm", type=int, default=6, help="calls per condition")
    ap.add_argument("--no-identity", action="store_true",
                    help="baseline: gate prompt WITHOUT the Acao/product block")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    global IDENTITY
    IDENTITY = not args.no_identity
    retrieval_configure(ROOT / "data" / "app.db")
    prompts = build_prompts(args.acao)
    print(f"bloco de identidade Acao/produto: {'SIM' if IDENTITY else 'NAO (baseline)'}")
    print(f"Acao {args.acao}: {len(prompts)} prompts de gate "
          f"(produtos x candidatos, apos dedup pre-gate)\n", flush=True)

    print(f"FASE 1 - sondagem: {args.probe} passes na forma de producao "
          f"(4 em voo, cache on)", flush=True)
    votes: dict[int, list] = {i: [] for i in range(len(prompts))}
    for p in range(1, args.probe + 1):
        started = time.time()
        for i, v in enumerate(run_batch(prompts, None, 4)):
            votes[i].append(v)
        print(f"  passe {p}/{args.probe}  {time.time()-started:.0f}s", flush=True)

    unstable = [i for i in votes if len(set(votes[i])) > 1]
    print(f"\nchunks instaveis: {len(unstable)}/{len(prompts)} "
          f"({100*len(unstable)/len(prompts):.1f}%)", flush=True)
    for i in unstable:
        seq = "/".join("T" if v else "F" if v is False else "?" for v in votes[i])
        print(f"    {prompts[i][0]:>26}  {seq}", flush=True)
    if not unstable:
        print("\nnenhum chunk instavel nesta Acao - nada a confirmar.")
        return 0

    print(f"\nFASE 2 - {args.confirm} chamadas por condicao, so nos instaveis", flush=True)
    subset = [prompts[i] for i in unstable]
    conditions = [("seq-ON", None, 1), ("seq-OFF", False, 1), ("conc-ON", None, 4)]
    table: dict[str, list[list]] = {}
    for name, cache_prompt, workers in conditions:
        per_chunk: list[list] = [[] for _ in subset]
        started = time.time()
        for _ in range(args.confirm):
            for i, v in enumerate(run_batch(subset, cache_prompt, workers)):
                per_chunk[i].append(v)
        table[name] = per_chunk
        print(f"  {name:>8}  {time.time()-started:.0f}s", flush=True)

    print(f"\n{'chunk':>26} " + " ".join(f"{n:>{args.confirm+2}}" for n, *_ in conditions))
    verdict_counts = {n: 0 for n, *_ in conditions}
    for j, (label, _s, _u) in enumerate(subset):
        cells = []
        for name, *_ in conditions:
            vs = table[name][j]
            cells.append("".join("T" if v else "F" if v is False else "?" for v in vs))
            if len(set(vs)) > 1:
                verdict_counts[name] += 1
        print(f"{label:>26} " + " ".join(f"{c:>{args.confirm+2}}" for c in cells))

    print(f"\ninstaveis por condicao (de {len(subset)} chunks sabidamente instaveis):")
    for name, *_ in conditions:
        print(f"  {name:>8}: {verdict_counts[name]}/{len(subset)}")
    print("\n  seq-ON e seq-OFF estaveis, conc-ON instavel => concorrencia/batching")
    print("  so seq-OFF estavel                          => o cache")
    print("  instavel nas tres                           => o modelo")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"labels": [p[0] for p in subset],
             "table": {k: v for k, v in table.items()}},
            indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
