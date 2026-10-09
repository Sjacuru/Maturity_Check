"""Per-chunk gate constancy, measured with the ledger OFF.

Item 2 of the revised order (2026-10-05). The question is NOT "is the gate
right" and NOT "does pass 2 agree with pass 1 once the ledger has frozen it" --
with the ledger on, the warm passes agree 46/46 by construction, so measuring
stability there is circular. The question the user set is CONSTANCY:

    "nao se trata de melhorar em relacao ao primeiro, mas sim de manter o
     resultado, mesmo que a primeira passada mude, o que importa e que o
     proximo resultado nao seja alterado durante as passadas seguintes"

and their acceptance scale, applied here per chunk+product:

    0 changes in 10 passes      = consistent
    1 change (+1 in another 10) = not consistent, tolerable
    more than 2 in 10           = inconsistent

Why a subpopulation and not all 2 513 verdicts: the join of the two independent
cold runs measured P(unstable | REJECTED) = 1.7 % against
P(unstable | ACCEPTED) = 38.5 %. The verdicts that can move are the ACCEPTS,
plus the rejections whose reasoning ran long (median 295 chars for flippers vs
192 for stable ones). Measuring those two groups costs ~1/6 of a full sweep and
covers the population that decides the batch.

What this script does NOT do: it does not re-run retrieval, and it does not
re-derive the examined pool. Both are deterministic (164/164 products
byte-identical over 3 passes, 2026-10-02), and the chunk+product tuples that
were actually gated in cycle 1 are recorded in that cycle's ledger -- including
the ones neighbour expansion reached from outside ranked[:16]. So the prompt is
rebuilt from the profile, the IPMP store and the chunk text, and then PROVEN
byte-identical by recomputing the ledger key and comparing it with the key the
production run stored. A tuple whose hash does not match is reported and
excluded rather than measured under a prompt we cannot prove is the same one.

Nothing is persisted: no ledger (asserted off), no app.db write, no
evaluation_results row. data/app.db is read for chunk text only.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import time
from collections import Counter
from pathlib import Path

from _common import DB_PATH, DEFAULT_PROCESS  # noqa: F401  (sets offline flags + sys.path)

from ingestion import get_ipmp_store
from ingestion.retrieval_profile import get_retrieval_profile_store

from evaluation._config import configure_gate_llm_client, get_gate_ledger
from evaluation.evidence_selection import (
    GATE_MAX_IN_FLIGHT,
    _gate_chunk,
    _ledger_model,
    strip_extraction_noise,
)
from evaluation.gate_ledger import prompt_hash
from evaluation.llm.llamacpp import LlamaCppClient
from evaluation.prompt.relevance_builder import (
    build_relevance_system_prompt,
    build_relevance_user_prompt,
)

# The frozen production gate wiring, copied from main.py rather than imported:
# importing main.py would also install a GateLedger, and this measurement must
# run with the ledger off.
BASE_URL = "http://189.60.217.20:8080"
MODEL = "gpt-oss-20b-F16.gguf"
REASONING_EFFORT = "low"


class GateTuple:
    """One chunk+product judgement to repeat."""

    __slots__ = (
        "acao_id", "product_id", "filename", "page_number", "chunk_index",
        "baseline", "reason_len", "system", "user", "stripped", "key", "group",
    )

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    @property
    def ident(self) -> str:
        return (f"{self.acao_id}|{self.product_id}|{self.filename}|"
                f"{self.page_number}|{self.chunk_index}")


def load_subpopulation(ledger_path: Path, reason_min: int, acoes: set[int] | None):
    """Accepts + long-reasoning rejections from a cycle's gate ledger."""
    con = sqlite3.connect(str(ledger_path))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT acao_id, product_id, filename, page_number, chunk_index,
               prompt_hash, relevant, COALESCE(LENGTH(reasoning), 0) AS rlen
        FROM gate_verdicts
        WHERE relevant = 1 OR COALESCE(LENGTH(reasoning), 0) >= ?
        ORDER BY acao_id, product_id, filename, page_number, chunk_index
        """,
        (reason_min,),
    ).fetchall()
    con.close()
    out = []
    for r in rows:
        if acoes and r["acao_id"] not in acoes:
            continue
        out.append(
            GateTuple(
                acao_id=r["acao_id"], product_id=r["product_id"],
                filename=r["filename"], page_number=r["page_number"],
                chunk_index=r["chunk_index"], baseline=bool(r["relevant"]),
                reason_len=r["rlen"], key=r["prompt_hash"],
                group="accept" if r["relevant"] else "reject_long",
                system=None, user=None, stripped=None,
            )
        )
    return out


def load_chunk_texts(process: str) -> dict[tuple[str, int, int], str]:
    con = sqlite3.connect(str(DB_PATH))
    rows = con.execute(
        "SELECT filename, page_number, chunk_index, text FROM chunks "
        "WHERE process_number = ?",
        (process,),
    ).fetchall()
    con.close()
    return {(f, p, i): t for f, p, i, t in rows}


def rebuild_prompts(items, texts, model_label: str, effort: str):
    """Rebuild each tuple's production prompt and prove it byte-identical.

    The proof is the ledger key: it hashes (model label, reasoning effort,
    system, user) with a 0x1f separator, so an equal sha256 means the two
    prompt pairs are the same bytes.
    """
    ipmp = get_ipmp_store().acoes
    profiles = get_retrieval_profile_store().acoes
    ok, bad = [], []
    for t in items:
        profile_acao = profiles.get(t.acao_id)
        product = profile_acao.expected_products.get(t.product_id) if profile_acao else None
        text = texts.get((t.filename, t.page_number, t.chunk_index))
        if product is None or not product.evidence_intent or text is None:
            bad.append((t, "sem perfil/texto"))
            continue
        t.stripped = strip_extraction_noise(text)
        t.system = build_relevance_system_prompt(
            product.evidence_intent,
            [c.text for c in product.retrieval_signal_concepts],
            product.negative_evidence_patterns,
            acao=ipmp.get(t.acao_id),
            product_id=t.product_id,
        )
        t.user = build_relevance_user_prompt(t.stripped, product_id=t.product_id)
        if prompt_hash(model_label, effort, t.system, t.user) != t.key:
            bad.append((t, "hash divergente"))
            continue
        ok.append(t)
    return ok, bad


def gate_once(t: GateTuple):
    """One real gate call through the production code path, ledger off."""
    ipmp = get_ipmp_store().acoes
    product = get_retrieval_profile_store().acoes[t.acao_id].expected_products[t.product_id]
    # chunk= / process_number= only annotate a ledger row; with the ledger off
    # they are provably unused, so they are omitted rather than faked.
    return _gate_chunk(
        t.stripped,
        product.evidence_intent,
        [c.text for c in product.retrieval_signal_concepts],
        product.negative_evidence_patterns,
        acao=ipmp.get(t.acao_id),
        product_id=t.product_id,
    )


def transitions(seq: list[bool]) -> int:
    return sum(1 for a, b in zip(seq, seq[1:]) if a != b)


def classify(n_changes: int) -> str:
    if n_changes == 0:
        return "consistente"
    if n_changes <= 2:
        return "toleravel"
    return "inconsistente"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", required=True,
                    help="cycle ledger sqlite to take the subpopulation from (read-only)")
    ap.add_argument("--passes", type=int, default=10)
    ap.add_argument("--reason-min", type=int, default=350,
                    help="minimum reasoning length for a REJECTION to enter the subpopulation")
    ap.add_argument("--process", default=DEFAULT_PROCESS)
    ap.add_argument("--acoes", default=None, help="comma-separated Acao filter (smoke runs)")
    ap.add_argument("--limit", type=int, default=0, help="cap the number of tuples (smoke runs)")
    ap.add_argument("--json-out", required=True)
    args = ap.parse_args()

    acoes = {int(x) for x in args.acoes.split(",")} if args.acoes else None

    client = LlamaCppClient(
        BASE_URL, MODEL,
        read_timeout=240.0, max_timeout_retries=2, max_tokens=8192,
        max_concurrent_requests=GATE_MAX_IN_FLIGHT,
        reasoning_effort=REASONING_EFFORT,
    )
    configure_gate_llm_client(client)
    assert get_gate_ledger() is None, "o ledger do gate precisa estar DESLIGADO nesta medicao"
    print(f"gate: 1 em voo={GATE_MAX_IN_FLIGHT <= 1}, reasoning_effort={REASONING_EFFORT}, "
          f"ledger={get_gate_ledger()}, modelo da chave={_ledger_model(client)}")

    items = load_subpopulation(Path(args.ledger), args.reason_min, acoes)
    texts = load_chunk_texts(args.process)
    ok, bad = rebuild_prompts(items, texts, _ledger_model(client), REASONING_EFFORT)
    n_acc = sum(1 for t in items if t.group == "accept")
    print(f"subpopulacao: {len(items)} tuplas ({n_acc} aceites + {len(items) - n_acc} "
          f"rejeicoes com raciocinio >= {args.reason_min} caracteres)")
    print(f"prompt byte-identico comprovado (hash recomputado == hash do ciclo): "
          f"{len(ok)}/{len(items)}")
    for t, why in bad[:20]:
        print(f"  EXCLUIDA ({why}): {t.ident}")
    if args.limit:
        ok = ok[: args.limit]
        print(f"--limit: medindo {len(ok)} tuplas")
    if not ok:
        raise SystemExit("nenhuma tupla mensuravel")

    results = {
        t.ident: {
            "acao_id": t.acao_id, "product_id": t.product_id, "filename": t.filename,
            "page_number": t.page_number, "chunk_index": t.chunk_index,
            "group": t.group, "baseline": t.baseline, "baseline_reason_len": t.reason_len,
            "verdicts": [], "reason_lens": [], "failures": 0,
        }
        for t in ok
    }
    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "process": args.process, "passes": args.passes, "reason_min": args.reason_min,
        "ledger_source": str(args.ledger), "model": MODEL,
        "reasoning_effort": REASONING_EFFORT, "gate_in_flight": GATE_MAX_IN_FLIGHT,
        "ledger_during_measurement": None, "n_tuples": len(ok),
        "n_excluded": len(bad), "pass_durations_s": [],
    }

    t0 = time.time()
    for p in range(1, args.passes + 1):
        p0 = time.time()
        # Pass-major (interleaved), same fixed order every pass: each pass is
        # one independent sample of the whole subpopulation, which is what
        # "muda a cada passada" means. Grouping by tuple instead would measure
        # back-to-back self-agreement on a warm cache.
        for n, t in enumerate(ok, 1):
            call = gate_once(t)
            rec = results[t.ident]
            if call.verdict.parse_failed:
                rec["failures"] += 1
                rec["verdicts"].append(None)
                rec["reason_lens"].append(None)
            else:
                rec["verdicts"].append(bool(call.verdict.relevant))
                rec["reason_lens"].append(len(call.reasoning or ""))
            if n % 100 == 0:
                print(f"  passada {p}: {n}/{len(ok)} ({(time.time() - p0) / 60:.1f} min)",
                      flush=True)
        meta["pass_durations_s"].append(round(time.time() - p0, 1))
        # Written after every pass: the GPU box lost power once today, and a
        # half-finished measurement is still worth something.
        out_path.write_text(
            json.dumps({"meta": meta, "tuples": results}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"passada {p}/{args.passes} concluida em {(time.time() - p0) / 60:.1f} min "
              f"(total {(time.time() - t0) / 60:.1f} min)", flush=True)

    report(results, args.passes)
    print(f"\nJSON: {out_path}")


def report(results: dict, passes: int) -> None:
    print(f"\n=== Constancia por tupla, {passes} passadas, ledger DESLIGADO ===")
    by_group: dict[str, list[dict]] = {}
    for rec in results.values():
        seq = [v for v in rec["verdicts"] if v is not None]
        rec["q"] = (sum(seq) / len(seq)) if seq else None
        rec["n_changes"] = transitions(seq)
        rec["minority"] = min(sum(seq), len(seq) - sum(seq)) if seq else 0
        rec["class"] = classify(rec["n_changes"])
        rec["seq"] = "".join("T" if v else ("F" if v is False else "?") for v in rec["verdicts"])
        by_group.setdefault(rec["group"], []).append(rec)

    labels = {"accept": "aceites no ciclo 1", "reject_long": "rejeicoes de raciocinio longo"}
    for group, recs in sorted(by_group.items()):
        cls = Counter(r["class"] for r in recs)
        changed = [r for r in recs if r["n_changes"] > 0]
        print(f"\n-- {labels.get(group, group)}: {len(recs)} tuplas")
        for name in ("consistente", "toleravel", "inconsistente"):
            n = cls.get(name, 0)
            print(f"   {name:>14}: {n:>4} ({n / len(recs):.0%})")
        print(f"   mudaram alguma vez: {len(changed)}/{len(recs)} = {len(changed) / len(recs):.0%}")
        if changed:
            print(f"   mudancas por tupla instavel: mediana "
                  f"{statistics.median(r['n_changes'] for r in changed):.1f}, "
                  f"max {max(r['n_changes'] for r in changed)}")
            qs = [r["q"] for r in changed if r["q"] is not None]
            print(f"   q das instaveis: mediana {statistics.median(qs):.2f}, "
                  f"min {min(qs):.2f}, max {max(qs):.2f}")
        qall = [r["q"] for r in recs if r["q"] is not None]
        print(f"   q do grupo: mediana {statistics.median(qall):.2f}")

    allrecs = list(results.values())
    fails = sum(r["failures"] for r in allrecs)
    print(f"\nfalhas de gate (chunk descartado sem julgamento): {fails} em "
          f"{sum(len(r['verdicts']) for r in allrecs)} chamadas")

    inc = [r for r in allrecs if r["class"] == "inconsistente"]
    print(f"\nINCONSISTENTES (> 2 mudancas em {passes}): {len(inc)} de {len(allrecs)}")
    for r in sorted(inc, key=lambda r: (-r["n_changes"], r["acao_id"]))[:40]:
        print(f"  Acao {r['acao_id']:>2} {r['product_id']:>7} {r['filename'][-14:]} "
              f"p.{r['page_number']:<4} idx={r['chunk_index']} {r['seq']} "
              f"q={r['q']:.2f} mudancas={r['n_changes']} ({r['group']})")

    # Which Acoes carry the instability, reported as a distribution and not as
    # an agenda: the next case will not break in the same items.
    per_acao = Counter(r["acao_id"] for r in allrecs if r["n_changes"] > 0)
    print(f"\nAcoes com alguma tupla instavel: {len(per_acao)} -> {dict(sorted(per_acao.items()))}")


if __name__ == "__main__":
    main()
