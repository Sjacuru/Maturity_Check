"""Does the server's prompt cache leak state between different gate calls?

The production gate pattern is the worst case for prefix caching: every
candidate for a product is sent with the SAME long system prompt and differs
only in a short chunk of text at the very end. The shared prefix is ~1,000+
tokens; the discriminating part is the tail. If the server ever reuses KV state
past the true common prefix, a verdict would be conditioned on the PREVIOUS
chunk instead of the current one.

That would explain the 2026-08-27 forensics, which never had an explanation:
repeating one identical prompt was 100% stable (0/184) while interleaving
DIFFERENT prompts on shared slots produced flips. Correct reuse is stable;
leaking reuse only shows up when the neighbours differ. It also fits
`cache_prompt: false` having reduced but not eliminated the flips (2/40 -> 1/40).

`timings.cache_n` reports how many prompt tokens the server served from cache,
so reuse is observed directly rather than inferred. The verdict question is then
settled by asking the same chunks in different orders:

  sequencial     - natural order, cache warm (the production shape)
  invertida      - reverse order, so a chunk now follows a different neighbour
  erase-antes    - every slot's KV wiped before each call, no reuse possible
  sem-cache      - cache_prompt: false

A chunk whose verdict depends on the CONDITION is contaminated. A chunk that
varies WITHIN a repeated condition is ordinary noise. Those are different
problems with different fixes, and this separates them.

Usage:
    python scripts/diagnostics/measure_slot_contamination.py --acao 1 --product 1a --k 6
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from evaluation.evidence_selection import strip_extraction_noise  # noqa: E402
from evaluation.prompt.relevance_builder import (  # noqa: E402
    build_relevance_system_prompt,
    build_relevance_user_prompt,
)
from evaluation.schemas import GATE_SCHEMA  # noqa: E402
from ingestion.retrieval_profile import get_retrieval_profile_store  # noqa: E402
from retrieval import configure as retrieval_configure  # noqa: E402
from retrieval.query.hybrid import retrieve_hybrid_candidates_for_acao  # noqa: E402

BASE_URL = "http://189.60.217.20:8080"
MODEL = "gpt-oss-20b-F16.gguf"
PROCESS = "SMG-040_101607_2024"
N_SLOTS = 4


def _post(path: str, payload: dict | None, timeout: float = 300.0) -> dict:
    data = json.dumps(payload).encode() if payload is not None else b""
    req = urllib.request.Request(
        f"{BASE_URL}{path}", data, {"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def erase_all_slots() -> bool:
    ok = True
    for i in range(N_SLOTS):
        try:
            _post(f"/slots/{i}?action=erase", None, timeout=30.0)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError):
            ok = False
    return ok


def call(system: str, user: str, cache_prompt: bool | None = None) -> dict:
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
    body = _post("/v1/chat/completions", payload)
    choice = body["choices"][0]
    timings = body.get("timings") or {}
    content = choice["message"].get("content") or ""
    try:
        verdict = bool(json.loads(content)["relevant"])
    except Exception:
        verdict = None
    return {
        "verdict": verdict,
        "finish": choice.get("finish_reason"),
        "cache_n": timings.get("cache_n"),
        "prompt_n": timings.get("prompt_n"),
        "predicted_n": timings.get("predicted_n"),
    }


def _cell(votes: list) -> str:
    return "/".join("T" if v is True else "F" if v is False else "?" for v in votes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acao", type=int, default=1)
    ap.add_argument("--product", default="1a")
    ap.add_argument("--k", type=int, default=6, help="chunks under test")
    ap.add_argument("--repeats", type=int, default=2, help="repeats per condition")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    retrieval_configure(ROOT / "data" / "app.db")
    profile = get_retrieval_profile_store().acoes[args.acao].expected_products[args.product]
    system = build_relevance_system_prompt(
        profile.evidence_intent,
        [c.text for c in profile.retrieval_signal_concepts],
        profile.negative_evidence_patterns,
    )
    candidates = retrieve_hybrid_candidates_for_acao(args.acao, PROCESS)[args.product][: args.k]
    users = [build_relevance_user_prompt(strip_extraction_noise(c.text)) for _s, c in candidates]
    labels = [f"pg{c.page_number}#{c.chunk_index}" for _s, c in candidates]

    print(f"Acao {args.acao}/{args.product} - {len(users)} chunks, "
          f"system prompt {len(system)} chars", flush=True)
    print(f"/slots erase disponivel: {erase_all_slots()}\n", flush=True)

    conditions = [
        ("sequencial", list(range(len(users))), False, None),
        ("invertida", list(reversed(range(len(users)))), False, None),
        ("erase-antes", list(range(len(users))), True, None),
        ("sem-cache", list(range(len(users))), False, False),
    ]

    results: dict[str, dict[int, list]] = {}
    for name, order, erase_each, cache_prompt in conditions:
        results[name] = {i: [] for i in range(len(users))}
        for rep in range(1, args.repeats + 1):
            started = time.time()
            reuse = []
            for i in order:
                if erase_each:
                    erase_all_slots()
                res = call(system, users[i], cache_prompt)
                results[name][i].append(res["verdict"])
                reuse.append((res["cache_n"] or 0, res["prompt_n"] or 0))
            cached = sum(c for c, _ in reuse)
            processed = sum(p for _, p in reuse)
            total = cached + processed
            pct = (100 * cached / total) if total else 0
            print(f"  [{name:>11} r{rep}] {time.time()-started:5.0f}s  "
                  f"tokens do cache: {cached:>6} / processados: {processed:>6} "
                  f"= {pct:.0f}% reusado", flush=True)

    header = " ".join(f"{name:>13}" for name, *_ in conditions)
    print(f"\n{'chunk':>12} {header}")
    contaminated: list[str] = []
    noisy: list[str] = []
    for i, label in enumerate(labels):
        per_condition = {name: set(results[name][i]) for name, *_ in conditions}
        cells = [_cell(results[name][i]) for name, *_ in conditions]
        across = set().union(*per_condition.values())
        note = ""
        if any(len(v) > 1 for v in per_condition.values()):
            noisy.append(label)
            note = "  <- ruido (varia na MESMA condicao)"
        elif len(across) > 1:
            contaminated.append(label)
            note = "  <- DEPENDE DA CONDICAO"
        print(f"{label:>12} " + " ".join(f"{c:>13}" for c in cells) + note)

    print(f"\nvariam dentro da mesma condicao (ruido)      : "
          f"{len(noisy)}/{len(labels)} {noisy}")
    print(f"estaveis por condicao mas MUDAM entre elas   : "
          f"{len(contaminated)}/{len(labels)} {contaminated}")
    print("\n  o segundo grupo e a assinatura de contaminacao de cache: o veredito")
    print("  do chunk depende do que foi perguntado antes dele, nao do seu conteudo.")

    if args.out:
        payload = {
            "labels": labels,
            "results": {k: {str(i): v for i, v in d.items()} for k, d in results.items()},
        }
        Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
