"""How many tokens does a scorer call actually spend on output?

measure_context_budget.py establishes the input side (system + evidence).
This measures the other half: what the scorer emits. It matters because the
scorer is the one client with NO max_tokens (llamacpp.py defaults to None), so
whatever it emits has to fit in whatever the prompt leaves of the 32k slot —
and since ADR-0058 it emits one verdict + justificativa per Expected Product,
so the output grows with the Ação's product count.

Real system/user prompts, real corpus chunks, real SCORER_SCHEMA. Reports
completion_tokens and finish_reason per call.

Usage:
    python scripts/diagnostics/measure_scorer_output.py --acoes 31,15,25,1
"""

from __future__ import annotations

import argparse
import sqlite3
import statistics
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

import httpx  # noqa: E402

from evaluation.prompt.builder import build_system_prompt, build_user_prompt  # noqa: E402
from evaluation.schemas import SCORER_SCHEMA  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402
from retrieval.interfaces.contracts import RetrievedChunk  # noqa: E402

BASE_URL = "http://189.60.217.20:8080"
MODEL = "gpt-oss-20b-F16.gguf"
DB_PATH = ROOT / "data" / "app.db"
PROCESS = "SMG-040_101607_2024"


def real_chunks(limit: int = 400) -> list[RetrievedChunk]:
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT filename, page_number, chunk_index, char_offset, page_total, "
        "       ocr_used, source_type, text "
        "FROM chunks WHERE process_number = ? ORDER BY chunk_index LIMIT ?",
        (PROCESS, limit),
    ).fetchall()
    con.close()
    return [
        RetrievedChunk(
            process_number=PROCESS, filename=r[0], page_number=r[1], chunk_index=r[2],
            char_offset=r[3], page_total=r[4], ocr_used=bool(r[5]), source_type=r[6],
            text=r[7], cascade_step="bm25", bm25_score=1.0, rank=1,
        )
        for r in rows
    ]


def fill_to(pool: list[RetrievedChunk], cap: int, pids: list[str]) -> list[RetrievedChunk]:
    out: list[RetrievedChunk] = []
    running = 0
    for i, c in enumerate(pool):
        if running + len(c.text) > cap:
            break
        out.append(c.model_copy(update={"expected_product_ids": [pids[i % len(pids)]]}))
        running += len(c.text)
    return out


def call(system: str, user: str) -> dict:
    started = time.time()
    r = httpx.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": SCORER_SCHEMA, "strict": True},
            },
        },
        timeout=httpx.Timeout(connect=10.0, read=900.0, write=60.0, pool=10.0),
    )
    elapsed = time.time() - started
    r.raise_for_status()
    body = r.json()
    choice = body["choices"][0]
    usage = body.get("usage") or {}
    return {
        "finish_reason": choice.get("finish_reason"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "content_chars": len(choice["message"].get("content") or ""),
        "seconds": elapsed,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="31,15,25,1")
    ap.add_argument("--cap", type=int, default=21_000, help="evidence chars per call")
    args = ap.parse_args()

    store = get_ipmp_store()
    pool = real_chunks()

    print(f"cap de evidência usado: {args.cap} chars\n")
    print(f"{'Ação':>5} {'prods':>6} {'prompt_tok':>11} {'compl_tok':>10} "
          f"{'finish':>10} {'segundos':>9}  vs read_timeout=45s")
    print("-" * 74)
    completions = []
    seconds = []
    for aid in (int(x) for x in args.acoes.split(",")):
        pids = [p.id for p in store.acoes[aid].produtos_esperados if p.scored]
        chunks = fill_to(pool, args.cap, pids)
        system = build_system_prompt(aid)
        user = build_user_prompt(chunks, aid)
        try:
            res = call(system, user)
        except Exception as exc:
            print(f"{aid:>5} {len(pids):>6}  ERRO: {type(exc).__name__}: {str(exc)[:60]}")
            continue
        completions.append(res["completion_tokens"])
        seconds.append(res["seconds"])
        print(
            f"{aid:>5} {len(pids):>6} {res['prompt_tokens']:>11} "
            f"{res['completion_tokens']:>10} {res['finish_reason']:>10} "
            f"{res['seconds']:>9.1f}  {'ESTOURA' if res['seconds'] > 45 else 'ok'}"
        )

    if completions:
        print(
            f"\ncompletion_tokens: min={min(completions)} "
            f"mediana={statistics.median(completions):.0f} max={max(completions)}"
        )
        print(
            f"segundos: min={min(seconds):.1f} mediana={statistics.median(seconds):.1f} "
            f"max={max(seconds):.1f} — {sum(1 for s in seconds if s > 45)}/{len(seconds)} "
            f"acima do read_timeout=45s do scorer"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
