"""Which chunks flip at the gate, and what does the model say while flipping?

The input to the gate is now known constant: audit_pregate_determinism.py
confirmed that fused candidates, RRF scores, pre-gate dedup, the _MAX_EXAMINED
cut and the noise-stripped texts are all byte-identical across passes. So every
difference in the evidence set that reaches the scorer is produced here.

What was never captured is WHY. GATE_SCHEMA is {"relevant": boolean} — a verdict
with no rationale — but gpt-oss emits an unconstrained reasoning channel before
the schema-constrained content, and llama.cpp returns it as
`message.reasoning_content`. Reading it costs nothing and changes no behaviour,
unlike adding a `reasoning` field to the schema, which would alter the very
generation under study.

For every (product, examined chunk) pair of an Ação this runs N calls and reports:

  * the verdict sequence per chunk, so the flippers are named
  * for each flipper, the reasoning from an accepting call AND from a rejecting
    call, side by side — the question is whether the two readings disagree about
    the TEXT or about the CRITERION
  * whether the flipping products are the ones whose prompt is degenerate: 23 of
    164 products have every retrieval_signal_concept merely restating the
    evidence_intent, so their prompt asserts one sentence twice and offers the
    model no second discriminator, and 45 of 164 carry no negative pattern at all

Usage:
    python scripts/diagnostics/audit_gate_flips.py --acao 14 --passes 8
    python scripts/diagnostics/audit_gate_flips.py --acao 14 --passes 8 --in-flight 1
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
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

from rapidfuzz import fuzz  # noqa: E402

from evaluation.evidence_selection import (  # noqa: E402
    _MAX_EXAMINED,
    _prefilter_near_duplicates,
    strip_extraction_noise,
)
from evaluation.prompt.relevance_builder import (  # noqa: E402
    build_relevance_system_prompt,
    build_relevance_user_prompt,
)
from evaluation.schemas import GATE_SCHEMA  # noqa: E402
from ingestion import get_ipmp_store, get_retrieval_profile_store  # noqa: E402
from retrieval import configure as retrieval_configure  # noqa: E402
from retrieval.query.hybrid import retrieve_hybrid_candidates_for_acao  # noqa: E402

BASE_URL = "http://189.60.217.20:8080"
MODEL = "gpt-oss-20b-F16.gguf"
PROCESS = "SMG-040_101607_2024"


ENGINE: dict = {"cache_prompt": None, "reasoning_effort": None, "id_slot": None}


def call(system: str, user: str) -> dict:
    """One gate call, returning verdict AND the model's reasoning channel."""
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
    # Engine-level conditions under study. cache_prompt=False forces llama.cpp
    # to recompute the whole prompt instead of reusing a prefix KV computed
    # under a previous call's batch composition; reasoning_effort is the
    # gpt-oss chat-template knob (server default: medium).
    if ENGINE["cache_prompt"] is not None:
        payload["cache_prompt"] = ENGINE["cache_prompt"]
    if ENGINE["reasoning_effort"]:
        payload["chat_template_kwargs"] = {"reasoning_effort": ENGINE["reasoning_effort"]}
    if ENGINE.get("id_slot") is not None:
        payload["id_slot"] = ENGINE["id_slot"]
    request = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            body = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"verdict": None, "reasoning": "", "error": f"{type(exc).__name__}: {exc}"}
    choice = body["choices"][0]
    message = choice["message"]
    try:
        verdict = bool(json.loads(message.get("content") or "")["relevant"])
    except (ValueError, KeyError, TypeError):
        verdict = None
    return {
        "verdict": verdict,
        "reasoning": message.get("reasoning_content") or "",
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": (body.get("usage") or {}).get("completion_tokens"),
        # llama.cpp reports which slot served the call. Slot choice is prefix-
        # affinity + LRU, so it rotates with call history; if a verdict turns
        # out to be a function of (prompt, slot), pinning id_slot is the fix.
        "id_slot": body.get("id_slot", choice.get("id_slot")),
        "error": None,
    }


def _restates(concepts: list[str], intent: str) -> bool:
    norm = lambda t: " ".join(t.split()).rstrip(".").lower()  # noqa: E731
    return bool(concepts) and all(
        fuzz.ratio(norm(c), norm(intent)) >= 90 for c in concepts
    )


def build_targets(acao_id: int, products: set[str] | None = None) -> list[dict]:
    """Exactly what the gate is asked in production, per (product, chunk).
    products: optional subset of product ids (before/after checks of one
    product's profile edit need only that product's pool)."""
    acao = get_ipmp_store().acoes[acao_id]
    profile = get_retrieval_profile_store().acoes.get(acao_id)
    candidates = retrieve_hybrid_candidates_for_acao(acao_id, PROCESS)
    targets: list[dict] = []
    for product in acao.produtos_esperados:
        if not product.scored:
            continue
        if products is not None and product.id not in products:
            continue
        pp = profile.expected_products.get(product.id) if profile else None
        if pp is None or not pp.evidence_intent:
            continue
        concepts = [c.text for c in pp.retrieval_signal_concepts]
        system = build_relevance_system_prompt(
            pp.evidence_intent, concepts, pp.negative_evidence_patterns,
            acao=acao, product_id=product.id,
        )
        for _score, chunk in _prefilter_near_duplicates(
            candidates.get(product.id, [])
        )[:_MAX_EXAMINED]:
            text = strip_extraction_noise(chunk.text)
            targets.append({
                "label": f"{product.id}/pg{chunk.page_number}#{chunk.chunk_index}",
                "product_id": product.id,
                "system": system,
                "user": build_relevance_user_prompt(text, product_id=product.id),
                "text": text,
                "degenerate_prompt": _restates(concepts, pp.evidence_intent),
                "n_negative": len(pp.negative_evidence_patterns),
            })
    return targets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acao", type=int, default=14)
    ap.add_argument("--passes", type=int, default=8)
    ap.add_argument("--in-flight", type=int, default=4)
    ap.add_argument("--chars", type=int, default=420, help="reasoning chars to print")
    ap.add_argument("--out", default=None)
    ap.add_argument("--products", default=None,
                    help="comma-separated product ids; default = every scored product")
    ap.add_argument("--cache-prompt", choices=["default", "on", "off"], default="default")
    ap.add_argument("--reasoning-effort", choices=["default", "low", "medium", "high"],
                    default="default")
    ap.add_argument("--pin-slot", type=int, default=None,
                    help="send every call to this llama.cpp slot (id_slot)")
    args = ap.parse_args()
    if args.cache_prompt != "default":
        ENGINE["cache_prompt"] = args.cache_prompt == "on"
    if args.reasoning_effort != "default":
        ENGINE["reasoning_effort"] = args.reasoning_effort
    if args.pin_slot is not None:
        ENGINE["id_slot"] = args.pin_slot

    retrieval_configure(ROOT / "data" / "app.db")
    wanted = {x.strip() for x in args.products.split(",")} if args.products else None
    targets = build_targets(args.acao, wanted)
    print(f"Ação {args.acao}: {len(targets)} pares (produto, chunk) examinados em produção")
    print(f"{args.passes} passes, {args.in_flight} em voo, reasoning_content capturado\n",
          flush=True)

    results: list[list[dict]] = [[] for _ in targets]
    for p in range(1, args.passes + 1):
        started = time.time()
        if args.in_flight <= 1:
            out = [call(t["system"], t["user"]) for t in targets]
        else:
            with ThreadPoolExecutor(max_workers=args.in_flight) as pool:
                out = list(pool.map(lambda t: call(t["system"], t["user"]), targets))
        for i, r in enumerate(out):
            results[i].append(r)
        errors = sum(1 for r in out if r["error"])
        toks = [r["completion_tokens"] for r in out if r.get("completion_tokens")]
        tok_note = f"  tokens/chamada mediana={sorted(toks)[len(toks)//2]} max={max(toks)}" if toks else ""
        print(f"  passe {p}/{args.passes}  {time.time() - started:.0f}s{tok_note}"
              f"{f'  ({errors} erro(s))' if errors else ''}", flush=True)

    print(f"\n{'=' * 92}\nvereditos por chunk\n{'=' * 92}")
    flippers: list[int] = []
    for i, t in enumerate(targets):
        seq = "".join(
            "T" if r["verdict"] else "F" if r["verdict"] is False else "?"
            for r in results[i]
        )
        verdicts = {r["verdict"] for r in results[i] if r["verdict"] is not None}
        mark = ""
        if len(verdicts) > 1:
            flippers.append(i)
            mark = "  <<< OSCILA"
        flags = []
        if t["degenerate_prompt"]:
            flags.append("critério repetido")
        if not t["n_negative"]:
            flags.append("sem padrão negativo")
        suffix = f"  [{', '.join(flags)}]" if flags else ""
        print(f"  {t['label']:>26}  {seq}{mark}{suffix}")

    by_product = Counter(targets[i]["product_id"] for i in flippers)
    print(f"\n  chunks que oscilam: {len(flippers)}/{len(targets)}")
    print(f"  por produto: {dict(by_product)}")
    deg = [i for i in flippers if targets[i]["degenerate_prompt"]]
    print(f"  dos quais com critério repetido no prompt: {len(deg)}/{len(flippers)}")
    noneg = [i for i in flippers if not targets[i]["n_negative"]]
    print(f"  dos quais sem nenhum padrão negativo    : {len(noneg)}/{len(flippers)}")

    print(f"\n{'=' * 92}\nraciocínio nos dois lados, por chunk que oscila\n{'=' * 92}")
    for i in flippers:
        t = targets[i]
        accept = next((r for r in results[i] if r["verdict"] is True), None)
        reject = next((r for r in results[i] if r["verdict"] is False), None)
        print(f"\n--- {t['label']}  (produto {t['product_id']}) ---")
        print(f"  trecho: {' '.join(t['text'].split())[:260]}")
        for name, r in (("ACEITOU ", accept), ("REJEITOU", reject)):
            text = " ".join((r or {}).get("reasoning", "").split())[: args.chars]
            print(f"  {name}: {text or '(sem reasoning_content)'}")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"acao": args.acao, "passes": args.passes, "in_flight": args.in_flight,
             "cache_prompt": args.cache_prompt, "reasoning_effort": args.reasoning_effort,
             "targets": [{k: v for k, v in t.items() if k not in ("system", "user")}
                         for t in targets],
             "results": results},
            indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\ngravado em {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
