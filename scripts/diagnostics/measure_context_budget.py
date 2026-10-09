"""How much evidence actually fits in this server's context?

`_MAX_EVIDENCE_CHARS = 21_000` was not derived from any model's context window.
The comment in evaluator.py says so outright: it was sized against Groq's
on-demand tier rate limit of 12,000 tokens/minute. Groq has been unwired since
ADR-0059, so that constraint no longer exists — but the number it produced is
still capping evidence, and Run 1 (2026-09-28) showed it binding for real:
Ação 15 lost 2 chunks (24,406 -> 20,487 chars).

This measures the real ceiling instead of guessing at it, using the server's
own tokenizer (/tokenize) on the real prompts and the real corpus:

  * exact system-prompt token count for every one of the 46 Ações
  * exact user-prompt token count at several candidate caps, built from real
    indexed chunks through the real build_user_prompt()
  * the resulting headroom against this server's per-slot n_ctx

Usage:
    python scripts/diagnostics/measure_context_budget.py
"""

from __future__ import annotations

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

import sqlite3  # noqa: E402

import httpx  # noqa: E402

from evaluation.prompt.builder import build_system_prompt, build_user_prompt  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402
from retrieval.interfaces.contracts import RetrievedChunk  # noqa: E402

BASE_URL = "http://189.60.217.20:8080"
DB_PATH = ROOT / "data" / "app.db"
PROCESS = "SMG-040_101607_2024"

# Candidate caps to evaluate, including the current one.
CANDIDATE_CAPS = [40_000, 60_000, 70_000, 80_000, 90_000, 100_000]


def n_tokens(text: str) -> int:
    r = httpx.post(
        f"{BASE_URL}/tokenize",
        json={"content": text},
        timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0),
    )
    r.raise_for_status()
    return len(r.json()["tokens"])


def server_n_ctx() -> int:
    r = httpx.get(f"{BASE_URL}/props", timeout=20.0)
    r.raise_for_status()
    return int(r.json()["default_generation_settings"]["n_ctx"])


def real_chunks(limit: int = 400) -> list[RetrievedChunk]:
    """Real indexed chunks — same text the scorer actually sees."""
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
            process_number=PROCESS,
            filename=r[0],
            page_number=r[1],
            chunk_index=r[2],
            char_offset=r[3],
            page_total=r[4],
            ocr_used=bool(r[5]),
            source_type=r[6],
            text=r[7],
            cascade_step="bm25",
            bm25_score=1.0,
            rank=1,
        )
        for r in rows
    ]


def fill_to(pool: list[RetrievedChunk], cap: int, product_ids: list[str]) -> list[RetrievedChunk]:
    """Take chunks until `cap` chars, spreading them across products the way a
    real evidence set is spread (every product gets a block)."""
    out: list[RetrievedChunk] = []
    running = 0
    for i, c in enumerate(pool):
        if running + len(c.text) > cap:
            break
        c = c.model_copy(update={"expected_product_ids": [product_ids[i % len(product_ids)]]})
        out.append(c)
        running += len(c.text)
    return out


def main() -> int:
    n_ctx = server_n_ctx()
    print(f"servidor: n_ctx por slot = {n_ctx}\n")

    store = get_ipmp_store()
    acao_ids = sorted(store.acoes)

    # ---- 1. system prompts, all 46 Ações --------------------------------
    sys_rows = []
    for aid in acao_ids:
        s = build_system_prompt(aid)
        sys_rows.append((aid, len(s), n_tokens(s)))
    sys_rows.sort(key=lambda r: -r[2])
    worst_sys = sys_rows[0]
    print("SYSTEM PROMPT (46 Ações, tokenizador do servidor)")
    print(f"  maior : Ação {worst_sys[0]:>2}  {worst_sys[1]:>6} chars  {worst_sys[2]:>5} tokens")
    med = sorted(r[2] for r in sys_rows)[len(sys_rows) // 2]
    print(f"  mediana: {med} tokens")
    print(f"  menor : Ação {sys_rows[-1][0]:>2}  {sys_rows[-1][1]:>6} chars  {sys_rows[-1][2]:>5} tokens")
    print("  top 5 :", ", ".join(f"A{a}={t}t" for a, _, t in sys_rows[:5]))

    # ---- 2. chars/token on real corpus text ------------------------------
    pool = real_chunks()
    sample = "\n\n".join(c.text for c in pool[:60])
    ratio = len(sample) / n_tokens(sample)
    print(f"\nCORPUS REAL: {len(sample)} chars -> {n_tokens(sample)} tokens = {ratio:.2f} chars/token")
    print("  (o comentário em evaluator.py assume 2.87 chars/token)")

    # ---- 3. full user prompt at each candidate cap -----------------------
    # Worst case = the Ação with the most scored products (most block overhead).
    worst_acao = max(
        acao_ids, key=lambda a: sum(1 for p in store.acoes[a].produtos_esperados if p.scored)
    )
    pids = [p.id for p in store.acoes[worst_acao].produtos_esperados if p.scored]
    print(f"\nUSER PROMPT (Ação {worst_acao}, {len(pids)} produtos — maior overhead de blocos)")
    sys_worst_tokens = dict((a, t) for a, _, t in sys_rows)[worst_acao]
    print(f"  system desta Ação: {sys_worst_tokens} tokens")
    print(f"\n  {'cap chars':>10} {'user tok':>9} {'sys+user':>9} {'sobra p/ saída':>15}")
    for cap in CANDIDATE_CAPS:
        chunks = fill_to(pool, cap, pids)
        up = build_user_prompt(chunks, worst_acao)
        ut = n_tokens(up)
        total = ut + sys_worst_tokens
        print(f"  {cap:>10} {ut:>9} {total:>9} {n_ctx - total:>15}")

    print(
        "\nA sobra precisa cobrir a saída do scorer (raciocínio livre do gpt-oss +"
        "\num veredicto por produto). O scorer não tem max_tokens (llamacpp.py)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
