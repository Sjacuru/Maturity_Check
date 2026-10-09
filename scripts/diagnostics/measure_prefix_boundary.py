"""Where exactly does the server stop reusing cached KV, and is that boundary right?

measure_slot_contamination.py found no order-dependence on Acao 1/1a, but it had
two blind spots this closes:

  1. `/slots/{id}?action=erase` is NOT enabled on this server, so its
     "erase-antes" condition silently degraded into a repeat of "sequencial".
     `cache_prompt: false` is the only working way to bypass the cache here.
  2. Its six chunks were all unambiguous (every one gave the same verdict in
     every condition). Contamination, if it exists, would show up on the ~5% of
     chunks that sit near the decision boundary - so those are what to test.

The decisive measurement is not statistical. `timings.cache_n` says how many
prompt tokens came from cache; if that ever exceeds the TRUE common prefix
between the current prompt and anything asked before, the server is generating
from state that belongs to a different prompt. The production gate shares a long
system prompt across candidates and differs only in a tail, so the true common
prefix is known: it is the templated system prompt, measured here by sending one
call with an empty chunk.

Usage:
    python scripts/diagnostics/measure_prefix_boundary.py --acao 15 --product 15a
"""

from __future__ import annotations

import argparse
import json
import sys
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
    req = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        body = json.load(r)
    choice = body["choices"][0]
    timings = body.get("timings") or {}
    content = choice["message"].get("content") or ""
    try:
        verdict = bool(json.loads(content)["relevant"])
    except Exception:
        verdict = None
    return {
        "verdict": verdict,
        "cache_n": timings.get("cache_n") or 0,
        "prompt_n": timings.get("prompt_n") or 0,
        "predicted_n": timings.get("predicted_n") or 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acao", type=int, default=15)
    ap.add_argument("--product", default="15a")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--repeats", type=int, default=3)
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

    # --- 1. how long is the shared prefix, in tokens? -----------------------
    # An empty chunk isolates template + system prompt. Sent twice: the second
    # call's cache_n is the server's own view of that prefix length.
    call(system, build_relevance_user_prompt(""), cache_prompt=False)
    baseline = call(system, build_relevance_user_prompt(""))
    prefix_tokens = baseline["cache_n"] + baseline["prompt_n"]
    print(f"Acao {args.acao}/{args.product} - {len(users)} chunks")
    print(f"prefixo compartilhado (template + system prompt): ~{prefix_tokens} tokens\n")

    # --- 2. is reuse ever wider than that prefix? ---------------------------
    # Each call carries a different chunk, so nothing beyond the system prompt
    # can legitimately be reused on a first encounter.
    print("A) primeira vez que cada chunk e visto - reuso legitimo <= prefixo")
    over = []
    for label, user in zip(labels, users):
        res = call(system, user)
        total = res["cache_n"] + res["prompt_n"]
        flag = ""
        if res["cache_n"] > prefix_tokens + 5:
            over.append(label)
            flag = "  <- REUSO ALEM DO PREFIXO"
        print(f"  {label:>12} total={total:>5} cache_n={res['cache_n']:>5} "
              f"prompt_n={res['prompt_n']:>5}{flag}")
    print(f"  reuso alem do prefixo comum: {len(over)}/{len(labels)} {over}\n")

    # --- 3. does full cache reuse change the answer? ------------------------
    # Same chunks, now fully resident, against cache_prompt=false. Any verdict
    # that differs between the two columns is decided by cache state, not text.
    print("B) veredito com cache quente vs cache desligado, "
          f"{args.repeats} repeticoes cada")
    print(f"  {'chunk':>12} {'cache ON':>12} {'cache OFF':>12}   {'cache_n ON':>11}")
    disagree, unstable = [], []
    for label, user in zip(labels, users):
        on = [call(system, user) for _ in range(args.repeats)]
        off = [call(system, user, cache_prompt=False) for _ in range(args.repeats)]
        von = {r["verdict"] for r in on}
        voff = {r["verdict"] for r in off}
        fmt = lambda rs: "/".join(  # noqa: E731
            "T" if r["verdict"] else "F" if r["verdict"] is False else "?" for r in rs
        )
        note = ""
        if len(von) > 1 or len(voff) > 1:
            unstable.append(label)
            note = "  <- instavel (ruido do modelo)"
        elif von != voff:
            disagree.append(label)
            note = "  <- O CACHE MUDA A RESPOSTA"
        print(f"  {label:>12} {fmt(on):>12} {fmt(off):>12}   "
              f"{on[0]['cache_n']:>11}{note}")

    print(f"\ninstaveis mesmo com cache desligado (ruido) : "
          f"{len(unstable)}/{len(labels)} {unstable}")
    print(f"estaveis mas com resposta DIFERENTE ON/OFF  : "
          f"{len(disagree)}/{len(labels)} {disagree}")
    print("\n  o segundo grupo e a assinatura de contaminacao. o primeiro e o ruido")
    print("  do modelo, que nenhuma politica de cache corrige.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
