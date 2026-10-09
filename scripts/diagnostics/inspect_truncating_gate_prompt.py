"""What is in the one gate prompt that reliably burns the whole token cap?

measure_gate_reasoning_field.py isolated it: product 40d, candidate #3, which
truncated in 3 of 3 attempts across two different schemas — deterministic, not
GPU noise. That makes it inspectable, which the aggregate failure counts in the
full runs never were.

Two questions, both cheap:
  1. what is the chunk, and what is the gate being asked to decide about it?
  2. is the reasoning unbounded, or just long? A higher cap answers that: if
     8192 finishes, it is deliberation and the cap is the wrong lever; if 8192
     also burns out, it is a loop and no cap will ever be enough.

Usage:
    python scripts/diagnostics/inspect_truncating_gate_prompt.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

import httpx  # noqa: E402

from evaluation.evidence_selection import strip_extraction_noise  # noqa: E402
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
DB_PATH = ROOT / "data" / "app.db"
PROCESS = "SMG-040_101607_2024"
ACAO, PRODUCT, INDEX = 40, "40d", 3


def call(system: str, user: str, max_tokens: int) -> dict:
    r = httpx.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0, "stream": False, "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": GATE_SCHEMA, "strict": True},
            },
        },
        timeout=httpx.Timeout(connect=10.0, read=900.0, write=30.0, pool=10.0),
    )
    r.raise_for_status()
    body = r.json()
    choice = body["choices"][0]
    usage = body.get("usage") or {}
    return {
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
        "content": choice["message"].get("content") or "",
    }


def main() -> int:
    retrieval_configure(DB_PATH)
    acao = get_ipmp_store().acoes[ACAO]
    profile = get_retrieval_profile_store().acoes.get(ACAO)
    pp = profile.expected_products[PRODUCT]
    candidates = retrieve_hybrid_candidates_for_acao(ACAO, PROCESS)
    _score, chunk = candidates[PRODUCT][INDEX]

    print("=" * 74)
    print(f"CHUNK — {chunk.filename} pg={chunk.page_number} idx={chunk.chunk_index}")
    print(f"cascade_step={chunk.cascade_step}  chars={len(chunk.text)}")
    print("=" * 74)
    cleaned = strip_extraction_noise(chunk.text)
    print(cleaned[:2200])
    if len(cleaned) > 2200:
        print(f"... [+{len(cleaned) - 2200} chars]")

    print("\n" + "=" * 74)
    print(f"EVIDENCE INTENT ({PRODUCT})")
    print("=" * 74)
    print(pp.evidence_intent)
    print(f"\nnegative_evidence_patterns: {len(pp.negative_evidence_patterns)}")
    for p in pp.negative_evidence_patterns:
        print(f"  - {p}")

    system = build_relevance_system_prompt(
        pp.evidence_intent,
        [c.text for c in pp.retrieval_signal_concepts],
        pp.negative_evidence_patterns,
    )
    user = build_relevance_user_prompt(cleaned)
    print(f"\nsystem prompt: {len(system)} chars | user prompt: {len(user)} chars")

    print("\n" + "=" * 74)
    print("LOOP OU DELIBERAÇÃO? — mesmo prompt, tetos crescentes")
    print("=" * 74)
    for cap in (2048, 4096, 8192):
        res = call(system, user, cap)
        ok = "OK" if res["finish_reason"] == "stop" else "TRUNCOU"
        verdict = ""
        if res["content"]:
            try:
                verdict = f" verdict={json.loads(res['content'])['relevant']}"
            except Exception:
                verdict = " (conteúdo não parseável)"
        print(f"  max_tokens={cap:>5}: {ok:>8}  completion={res['completion_tokens']:>5}"
              f"  content={len(res['content']):>4} chars{verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
