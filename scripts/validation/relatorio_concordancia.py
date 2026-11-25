"""Concordância entre o score proposto pelo sistema e a revisão do especialista.

Uso (ambiente rel_voto, a partir da raiz do repositório):

    python scripts/validation/relatorio_concordancia.py --process 040_101607_2024
    python scripts/validation/relatorio_concordancia.py --process P --csv saida.csv

Lê a última avaliação de cada Ação (evaluation_results) e a revisão do auditor
(review_outcomes, ADR-0023), mais os overrides de veredito do gate
(gate_verdicts, ADR-0067). Não chama nenhum modelo e abre o banco só para
leitura.

Mostra, por Ação: o score proposto, o score final do especialista, se foi
aceite, override ou "não aplicável", e a justificativa; e, no total:
quantas Ações foram revisadas, a taxa de aceite, os overrides para cima e
para baixo (por dimensão), a distância média em pontos, as revisões em Ações
com o sinal de revisão sugerida (ADR-0068) e os trechos que o especialista
marcou no gate.

"sem evidência" conta 0 ponto, como no critério de aceitação (ADR-0068) e na
nota iPMP (ADR-0075).
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "diagnostics"))
import _common  # noqa: E402,F401
from _common import DB_PATH  # noqa: E402


def _pts(score) -> int:
    return 0 if score is None else int(score)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--process", required=True)
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--csv", default=None, help="grava também uma linha por Ação neste CSV")
    args = ap.parse_args()

    from ingestion import get_ipmp_store
    acoes = get_ipmp_store().acoes

    con = sqlite3.connect(f"file:{Path(args.db).as_posix()}?mode=ro", uri=True)
    evs = {}
    for acao_id, created, score, noev, raw in con.execute(
        "SELECT acao_id, created_at, proposed_score, no_evidence_found, raw_json "
        "FROM evaluation_results WHERE process_number = ? ORDER BY created_at",
        (args.process,),
    ):
        evs[acao_id] = (created, score, noev, json.loads(raw))
    revs = {}
    for acao_id, final, ovr, na, just, created in con.execute(
        "SELECT acao_id, final_score, is_override, not_applicable, justification, created_at "
        "FROM review_outcomes WHERE process_number = ? ORDER BY created_at",
        (args.process,),
    ):
        revs[acao_id] = (final, bool(ovr), bool(na), just or "", created)
    gate_ovr = con.execute(
        "SELECT acao_id, product_id, filename, page_number, chunk_index, relevant, "
        "override_justification FROM gate_verdicts WHERE process_number = ? "
        "AND overridden_at IS NOT NULL ORDER BY acao_id, product_id", (args.process,),
    ).fetchall()
    con.close()

    if not evs:
        print(f"Nenhuma avaliação gravada para {args.process}.")
        return 2

    rows = []
    for acao_id in sorted(acoes):
        a = acoes[acao_id]
        ev = evs.get(acao_id)
        rv = revs.get(acao_id)
        proposto = None if ev is None else ("sem evidência" if ev[2] else ev[1])
        sinal = bool(ev and (ev[3].get("score_margin") or {}).get("review_recommended"))
        if rv is None:
            tipo, final, delta = "não revisada", None, None
        elif rv[2]:
            tipo, final, delta = "não aplicável", None, None
        else:
            tipo = "override" if rv[1] else "aceite"
            final = rv[0]
            delta = _pts(final) - _pts(None if ev is None else ev[1])
        rows.append({
            "acao": acao_id, "dimensao": a.dimensao, "proposto": proposto,
            "final": final, "revisao": tipo, "delta": delta,
            "sinal_revisao": sinal, "justificativa": " ".join((rv[3] if rv else "").split()),
        })

    print(f"Processo {args.process}: {len(evs)} Ações avaliadas, {len(revs)} revisadas")
    print()
    print(f"{'Ação':>4}  {'dimensão':11s} {'proposto':>13s} {'final':>5s}  {'revisão':14s} {'Δ':>3s}  justificativa")
    for r in rows:
        if r["revisao"] == "não revisada":
            continue
        d = "" if r["delta"] is None else f"{r['delta']:+d}"
        f = "" if r["final"] is None else str(r["final"])
        mark = " *" if r["sinal_revisao"] else ""
        print(f"{r['acao']:>4}  {r['dimensao']:11s} {str(r['proposto']):>13s} {f:>5s}  "
              f"{r['revisao']:14s} {d:>3s}  {r['justificativa'][:70]}{mark}")
    print("  * a Ação tinha o sinal de revisão sugerida (ADR-0068)")

    rev = [r for r in rows if r["revisao"] in ("aceite", "override")]
    print()
    if rev:
        n_ac = sum(r["revisao"] == "aceite" for r in rev)
        up = [r for r in rev if (r["delta"] or 0) > 0]
        down = [r for r in rev if (r["delta"] or 0) < 0]
        same_ovr = [r for r in rev if r["revisao"] == "override" and r["delta"] == 0]
        print(f"Revisadas com score: {len(rev)} · aceites {n_ac} ({100 * n_ac / len(rev):.0f} %) · "
              f"overrides {len(rev) - n_ac} (para cima {len(up)}, para baixo {len(down)}, "
              f"mesmo ponto {len(same_ovr)})")
        print(f"Distância média |Δ|: {sum(abs(r['delta']) for r in rev) / len(rev):.2f} ponto")
        by_dim = defaultdict(Counter)
        for r in rev:
            by_dim[r["dimensao"]]["aceite" if r["revisao"] == "aceite" else
                                  ("acima" if r["delta"] > 0 else "abaixo" if r["delta"] < 0 else "igual")] += 1
        for dim, c in sorted(by_dim.items()):
            print(f"  {dim:11s} " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))
        com_sinal = [r for r in rev if r["sinal_revisao"]]
        if com_sinal:
            alt = sum(r["revisao"] == "override" for r in com_sinal)
            print(f"Com sinal de revisão sugerida: {len(com_sinal)} revisadas, {alt} alteradas")
    print(f"Não aplicável: {sum(r['revisao'] == 'não aplicável' for r in rows)} · "
          f"não revisadas: {sum(r['revisao'] == 'não revisada' for r in rows)}")

    print()
    print(f"Trechos marcados pelo especialista no gate: {len(gate_ovr)}")
    for acao_id, pid, fn, pg, ci, rel, just in gate_ovr:
        print(f"  Ação {acao_id} {pid}: {fn} p.{pg} c{ci} -> "
              f"{'relevante' if rel else 'não relevante'} — {' '.join((just or '').split())[:70]}")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\nCSV: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
