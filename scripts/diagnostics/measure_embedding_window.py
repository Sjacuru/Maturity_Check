"""How much of the corpus and of each vector query the embedder actually sees.

The vector lane is co-equal and always-on (ADR-0049), so whatever the embedding
model cannot fit in its context is invisible to the majority of retrieval. This
measures the gap between chunk size (_PAGE_CHUNK_MAX_CHARS=3000) and the
model's max_seq_length, in the model's own tokens — which for Portuguese legal
text in an English uncased WordPiece vocabulary is far more than 1 token/word.

Offline: the embedder is a local sentence-transformers model on CPU, unrelated
to the llama.cpp GPU server that serves the gate and the scorer.

Usage:
    python scripts/diagnostics/measure_embedding_window.py [--process PN]
"""

from __future__ import annotations

import argparse
import sqlite3
import statistics as st

from _common import DB_PATH, DEFAULT_PROCESS, load_profiles, vector_query_for

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _pct(values: list[int], q: int) -> float:
    return st.quantiles(values, n=100)[q - 1] if len(values) > 1 else float(values[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--process", default=DEFAULT_PROCESS)
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    tok = model.tokenizer
    window = model.max_seq_length
    usable = window - 2  # [CLS] + [SEP]

    con = sqlite3.connect(str(DB_PATH))
    try:
        texts = [
            r[0]
            for r in con.execute(
                "SELECT text FROM chunks WHERE process_number = ?", (args.process,)
            )
        ]
    finally:
        con.close()
    if not texts:
        print(f"no chunks indexed for process '{args.process}'")
        return 1

    print("=" * 78)
    print(f"EMBEDDING WINDOW — {MODEL_NAME}")
    print("=" * 78)
    print(f"max_seq_length : {window} tokens ({usable} usable after special tokens)")

    sample = " ".join(texts[:200])
    ratio = len(tok.encode(sample, add_special_tokens=False)) / len(sample.split())
    print(f"tokens/word on this corpus : {ratio:.2f}  (English text is typically ~1.3)")
    print(f"=> the window covers roughly {usable/ratio:.0f} words of this corpus")

    chars = [len(t) for t in texts]
    tokens = [len(tok.encode(t, add_special_tokens=False)) for t in texts]
    print(f"\nCHUNKS (n={len(texts)})")
    print(f"  chars  median={st.median(chars):.0f}  p90={_pct(chars,90):.0f}  max={max(chars)}")
    print(f"  tokens median={st.median(tokens):.0f}  p90={_pct(tokens,90):.0f}  max={max(tokens)}")
    truncated = [t for t in tokens if t > usable]
    discarded = sum(t - usable for t in truncated)
    print(
        f"  truncated : {len(truncated)}/{len(tokens)} "
        f"({100*len(truncated)/len(tokens):.1f}% of chunks)"
    )
    print(
        f"  discarded : {discarded}/{sum(tokens)} tokens "
        f"({100*discarded/sum(tokens):.1f}% of the corpus is never embedded)"
    )

    queries = [
        (acao_id, pid, vector_query_for(product))
        for acao_id, prof in sorted(load_profiles().items())
        for pid, product in prof.items()
    ]
    qt = [(a, p, len(tok.encode(q, add_special_tokens=False))) for a, p, q in queries]
    counts = [n for _, _, n in qt]
    print(f"\nVECTOR QUERIES (n={len(qt)})")
    print(f"  tokens median={st.median(counts):.0f}  p90={_pct(counts,90):.0f}  max={max(counts)}")
    over = [x for x in qt if x[2] > usable]
    print(f"  truncated : {len(over)}/{len(qt)} ({100*len(over)/len(qt):.0f}%)")
    if over:
        print("\n  most-truncated queries (the tail of retrieval_signal_concepts is dropped):")
        for a, p, n in sorted(over, key=lambda x: -x[2])[:12]:
            print(f"    Acao {a:>2} {p:<7} {n:>4} tokens -> {100*usable/n:.0f}% kept")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
