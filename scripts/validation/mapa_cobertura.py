"""Mapa de cobertura por Produto Esperado: a lista de trabalho do especialista.

Uso (ambiente rel_voto, a partir da raiz do repositório):

    python scripts/validation/mapa_cobertura.py --process 040_101607_2024
    python scripts/validation/mapa_cobertura.py --process P --csv mapa.csv

Lê só a última avaliação gravada de cada Ação (evaluation_results): os
relatórios do gate por produto e os vereditos do avaliador. Não roda busca,
não chama modelo e abre o banco só para leitura.

Classifica cada um dos 164 produtos pontuados pela etapa onde parou:

  focal          a Ação usou o documento focal (Etapas A/B), sem gate por produto
  só instrumento a busca trouxe candidatos, mas todos eram texto de instrumento
                 (contrato, edital, TR) e o produto não é isento (ADR-0074)
  busca vazia    nenhuma das duas raias trouxe candidato
  gate recusou   houve candidatos examinados e o gate recusou todos
  avaliador      o gate aceitou trechos e o avaliador não deu o produto por evidenciado
  evidenciado    o avaliador deu o produto por evidenciado

Para o especialista, as três classes do meio são as perguntas: "o documento
tem isso e o sistema não achou?" Se tiver, aponte a página e rode
rastreia_evidencia.py para ver onde ela se perdeu.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "diagnostics"))
import _common  # noqa: E402,F401
from _common import DB_PATH  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--process", required=True)
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    from ingestion import get_genre_exemption_store, get_ipmp_store
    acoes = get_ipmp_store().acoes
    exempt = get_genre_exemption_store()

    con = sqlite3.connect(f"file:{Path(args.db).as_posix()}?mode=ro", uri=True)
    evs = {}
    for acao_id, created, raw in con.execute(
        "SELECT acao_id, created_at, raw_json FROM evaluation_results "
        "WHERE process_number = ? ORDER BY created_at", (args.process,)):
        evs[acao_id] = (created, json.loads(raw))
    con.close()
    if not evs:
        print(f"Nenhuma avaliação gravada para {args.process}.")
        return 2

    rows = []
    for acao_id in sorted(acoes):
        a = acoes[acao_id]
        ev = evs.get(acao_id)
        reports = {r["expected_product_id"]: r for r in (ev[1].get("product_gate_reports") or [])} if ev else {}
        verdicts = {v["product_id"]: v for v in (ev[1].get("product_verdicts") or [])} if ev else {}
        focal = bool(ev and ev[1].get("retrieved_chunks") and not reports)
        for p in a.produtos_esperados:
            if not p.scored:
                continue
            rep = reports.get(p.id)
            ver = verdicts.get(p.id)
            if ev is None:
                etapa = "sem avaliação"
            elif focal:
                etapa = "focal"
            elif ver and ver.get("evidenced"):
                etapa = "evidenciado"
            elif rep and rep["n_accepted"] > 0:
                etapa = "avaliador"
            elif rep and rep["n_examined"] > 0:
                etapa = "gate recusou"
            elif rep and rep["n_genre_excluded"] > 0:
                etapa = "só instrumento"
            else:
                etapa = "busca vazia"
            rows.append({
                "acao": acao_id, "produto": p.id, "dimensao": a.dimensao,
                "etapa": etapa,
                "candidatos": rep["n_candidates"] if rep else 0,
                "fora_por_genero": rep["n_genre_excluded"] if rep else 0,
                "examinados": rep["n_examined"] if rep else 0,
                "aceitos": rep["n_accepted"] if rep else 0,
                "isento_genero": p.id in exempt.produtos(acao_id),
                "criterio": " ".join(p.texto.split()),
                "justificativa_avaliador": " ".join(((ver or {}).get("justificativa") or "").split()),
            })

    datas = sorted(ev[0] for ev in evs.values())
    print(f"Processo {args.process}: avaliações de {datas[0][:16]} a {datas[-1][:16]}")
    c = Counter(r["etapa"] for r in rows)
    print("Produtos por etapa: " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    print()
    print(f"{'produto':>7s} {'etapa':14s} {'cand':>4s} {'gên':>4s} {'exam':>4s} {'acei':>4s}  critério")
    for r in rows:
        if r["etapa"] == "evidenciado":
            continue
        iso = " [isento]" if r["isento_genero"] else ""
        print(f"{r['produto']:>7s} {r['etapa']:14s} {r['candidatos']:>4d} {r['fora_por_genero']:>4d} "
              f"{r['examinados']:>4d} {r['aceitos']:>4d}  {r['criterio'][:80]}{iso}")
    print("\ncand = candidatos da busca · gên = removidos por serem texto de instrumento · "
          "exam = examinados pelo gate · acei = aceitos pelo gate")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"CSV: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
