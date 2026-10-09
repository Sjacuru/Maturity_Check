"""Is everything BEFORE the gate byte-identical from run to run?

The gate and the scorer have both been shown non-deterministic. Retrieval has
been *asserted* deterministic since ADR-0049 (flat LanceDB scan, fixed CPU
embedding model, FTS5, RRF with fixed k) but the whole chain up to the gate's
input has never been re-measured as one unit, and it has several places where a
tie or an unstable sort could leak order variance into the gate's input:

  * RRF fusion of two lanes, where equal fused scores need a tiebreak
  * _prefilter_near_duplicates, whose output depends on the order it sees
  * the _MAX_EXAMINED truncation, which makes order decide WHICH candidates are
    judged at all - an order flip there changes the gate's input set, not just
    its sequence

So this runs the real production calls N times and compares, per Expected
Product: the fused candidate list, its scores, the post-dedup list, and the
first _MAX_EXAMINED of it. No LLM is involved, so any difference reported here
is a defect upstream of every finding so far.

Usage:
    python scripts/diagnostics/audit_pregate_determinism.py --acoes 14,3 --passes 5
"""

from __future__ import annotations

import argparse
import hashlib
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

from evaluation.evidence_selection import (  # noqa: E402
    _MAX_EXAMINED,
    _prefilter_near_duplicates,
    strip_extraction_noise,
)
from ingestion import get_ipmp_store  # noqa: E402
from retrieval import configure as retrieval_configure  # noqa: E402
from retrieval.query.hybrid import retrieve_hybrid_candidates_for_acao  # noqa: E402

PROCESS = "SMG-040_101607_2024"


def key(chunk) -> str:
    return f"{chunk.filename}|p{chunk.page_number}|c{chunk.chunk_index}"


def digest(items: list[str]) -> str:
    return hashlib.sha256("\n".join(items).encode()).hexdigest()[:10]


def snapshot(acao_id: int) -> dict[str, dict]:
    """One pass: fused -> deduped -> truncated, per scored Expected Product."""
    candidates = retrieve_hybrid_candidates_for_acao(acao_id, PROCESS)
    out: dict[str, dict] = {}
    for product_id, ranked in candidates.items():
        deduped = _prefilter_near_duplicates(ranked)
        examined = deduped[:_MAX_EXAMINED]
        out[product_id] = {
            "fused": [key(c) for _s, c in ranked],
            # Scores are part of the identity: equal keys in a different order
            # with different scores would mean the fusion itself moved.
            "scores": [f"{s:.10f}" for s, _c in ranked],
            "deduped": [key(c) for _s, c in deduped],
            "examined": [key(c) for _s, c in examined],
            # What the gate actually reads, so a text change cannot hide behind
            # a stable key.
            "texts": [
                hashlib.sha256(strip_extraction_noise(c.text).encode()).hexdigest()[:8]
                for _s, c in examined
            ],
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acoes", default="14,3")
    ap.add_argument("--passes", type=int, default=5)
    args = ap.parse_args()

    retrieval_configure(ROOT / "data" / "app.db")
    acao_ids = [int(x) for x in args.acoes.split(",") if x.strip()]
    ipmp = get_ipmp_store()
    problems = 0

    for acao_id in acao_ids:
        scored = [p.id for p in ipmp.acoes[acao_id].produtos_esperados if p.scored]
        print(f"\n{'=' * 92}")
        print(f"Ação {acao_id}: {len(scored)} produto(s) pontuado(s), {args.passes} passes")
        print(f"{'=' * 92}")

        passes = [snapshot(acao_id) for _ in range(args.passes)]

        product_sets = {frozenset(p) for p in passes}
        if len(product_sets) > 1:
            print(f"  [FALHA] o conjunto de produtos com candidatos variou entre passes")
            problems += 1

        stages = ("fused", "scores", "deduped", "examined", "texts")
        header = f"  {'produto':>8} {'fundidos':>9} " + " ".join(f"{s:>9}" for s in stages)
        print(header)
        for product_id in sorted(passes[0], key=lambda p: scored.index(p) if p in scored else 99):
            n_fused = len(passes[0][product_id]["fused"])
            cells = []
            for stage in stages:
                digests = {digest(p[product_id][stage]) for p in passes}
                cells.append("estavel" if len(digests) == 1 else f"VARIA({len(digests)})")
                if len(digests) > 1:
                    problems += 1
            flag = "" if all(c == "estavel" for c in cells) else "   <<<"
            print(f"  {product_id:>8} {n_fused:>9} " + " ".join(f"{c:>9}" for c in cells) + flag)

        # Dedup is the one stage that can silently discard real evidence, so
        # report how much it removes and what the truncation then leaves behind.
        print(f"\n  dedup e truncamento (_MAX_EXAMINED={_MAX_EXAMINED}), passe 1:")
        for product_id in sorted(passes[0], key=lambda p: scored.index(p) if p in scored else 99):
            s = passes[0][product_id]
            dropped = len(s["fused"]) - len(s["deduped"])
            cut = max(0, len(s["deduped"]) - _MAX_EXAMINED)
            dup_texts = len(s["texts"]) - len(set(s["texts"]))
            note = ""
            if dup_texts:
                note = f"  <<< {dup_texts} texto(s) IDENTICO(s) ainda examinado(s)"
            print(f"    {product_id:>8}  fundidos={len(s['fused']):>3}  "
                  f"-dedup={dropped:>3}  -truncados={cut:>3}  "
                  f"examinados={len(s['examined']):>2}{note}")

    print(f"\n{'=' * 92}")
    if problems:
        print(f"{problems} divergência(s) encontrada(s) antes do gate — "
              "a entrada do gate NAO é constante")
        return 1
    print("tudo constante antes do gate: mesmos candidatos, mesmas pontuações, "
          "mesmo recorte, mesmos textos")
    print("=> toda a variação observada nasce no gate ou depois dele")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
