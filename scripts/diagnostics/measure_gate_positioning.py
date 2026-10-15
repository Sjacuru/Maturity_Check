"""Variante G do gate (gate_positioning.py) contra o prompt de produção, num processo.

O que mede: DIREÇÃO e INOCUIDADE. Não mede constância (ADR-0071): dentro de um
processo as passadas repetem a resposta, e a constância só se mede entre
processos completos (reproducibility.py --gate-variant posicionado).

Pool de produção:
  - filtro de gênero do ADR-0074 nos produtos não isentos;
  - pré-filtro de quase-duplicatas 0,92;
  - corte em 16.
Os vizinhos da expansão ficam de fora, porque dependem dos aceites.

Execução:
  - gate serial a reasoning_effort=low (ADR-0065);
  - chamadas diretas ao servidor, sem ledger;
  - nada é persistido além do --out.
Condições, intercaladas por passada (--condicoes, duas ou mais):
  - base: o prompt de produção;
  - g: a variante G;
  - g2: a variante G2 (G com o parágrafo NOMEAR).
--candidates/--apply aplicam padrões negativos de produto em memória, só nas
condições de --candidates-condicoes (padrão: g2). O perfil gravado não muda.

O rótulo de cada trecho inclui o arquivo (`23.2/_2/pg231#0`). O de
audit_gate_flips.build_targets não inclui, e duas páginas de mesmo número em
arquivos diferentes colidiriam.

Uso:
    python scripts/diagnostics/measure_gate_positioning.py --dry-run [--show 23.2]
    python scripts/diagnostics/measure_gate_positioning.py --passes 3 \
        --base-url http://127.0.0.1:18083 --out scratchpad/acc/posicao_direcao.json
    python scripts/diagnostics/measure_gate_positioning.py --condicoes g,g2 --passes 3 \
        --candidates scripts/diagnostics/candidates_g2.py --apply 18b \
        --base-url http://127.0.0.1:18083 --out scratchpad/acc/posicao_g2_direcao.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "diagnostics"))

from ingestion import get_genre_exemption_store, get_ipmp_store, get_retrieval_profile_store  # noqa: E402
from retrieval import configure as retrieval_configure  # noqa: E402

import gate_positioning as gp  # noqa: E402


def _sufixo(filename: str) -> str:
    return filename.rsplit("_", 1)[-1].split(".")[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--acoes", default=None, help="ex. 23,37,45 (padrão: todas)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="monta os prompts, confere a variante e conta chamadas, sem GPU")
    ap.add_argument("--show", default=None, help="imprime o prompt de sistema da variante de um produto")
    ap.add_argument("--base-url", default=os.environ.get("LLAMACPP_BASE_URL"),
                    help="servidor GPU (padrão: LLAMACPP_BASE_URL)")
    ap.add_argument("--condicoes", default="base,g", help="duas ou mais de base, g, g2 (padrão: base,g)")
    ap.add_argument("--candidates", default=None, help="arquivo de candidatos (dict CANDIDATOS); só a chave negativo")
    ap.add_argument("--apply", default=None, help="produtos de --candidates a aplicar")
    ap.add_argument("--candidates-condicoes", default="g2", help="condições que recebem os candidatos (padrão: g2)")
    args = ap.parse_args()
    conds = [c.strip() for c in args.condicoes.split(",") if c.strip()]
    if len(conds) < 2 or len(set(conds)) != len(conds) or not set(conds) <= {"base", "g", "g2"}:
        ap.error("--condicoes: duas ou mais, distintas, de base, g, g2")
    cand: dict[str, str] = {}
    if args.candidates:
        import importlib.util
        if not args.apply:
            ap.error("--candidates precisa de --apply")
        spec = importlib.util.spec_from_file_location("_candidatos", args.candidates)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for pid in (x.strip() for x in args.apply.split(",")):
            c = mod.CANDIDATOS[pid]
            assert set(c) <= {"acao", "direcao", "alvos", "resumo", "ipmp", "negativo"}, \
                f"{pid}: este medidor só aplica o padrão negativo"
            cand[pid] = c["negativo"]
    cand_conds = {c.strip() for c in args.candidates_condicoes.split(",")} if cand else set()

    retrieval_configure(ROOT / "data" / "app.db")
    import audit_gate_flips as g
    from evaluation import evidence_selection as es

    if args.base_url:
        g.BASE_URL = args.base_url.rstrip("/")
    g.ENGINE["reasoning_effort"] = "low"
    generos = es._chunk_genres(g.PROCESS)
    isencoes = get_genre_exemption_store()

    st = get_ipmp_store()
    perfis = get_retrieval_profile_store()
    acoes = [int(a) for a in args.acoes.split(",")] if args.acoes else sorted(st.acoes)

    # ------------------------------------------------------------------ plano
    plano: list[dict] = []
    for aid in acoes:
        acao = st.acoes[aid]
        prof = perfis.acoes.get(aid)
        bruto = g.retrieve_hybrid_candidates_for_acao(aid, g.PROCESS)
        isentos = isencoes.produtos(aid)
        for product in acao.produtos_esperados:
            if not product.scored:
                continue
            pp = prof.expected_products.get(product.id) if prof else None
            if pp is None or not pp.evidence_intent:
                continue
            ranked = bruto.get(product.id, [])
            if product.id not in isentos:
                ranked = es._drop_instrument_text(ranked, generos)[0]
            pool = g._prefilter_near_duplicates(ranked)[:g._MAX_EXAMINED]
            if not pool:
                continue
            concepts = [c.text for c in pp.retrieval_signal_concepts]
            system = g.build_relevance_system_prompt(
                pp.evidence_intent, concepts, pp.negative_evidence_patterns,
                acao=acao, product_id=product.id,
            )
            prompts: dict[str, str] = {}
            for c in conds:
                s = system
                if c in cand_conds and product.id in cand:
                    s = g.build_relevance_system_prompt(
                        pp.evidence_intent, concepts,
                        list(pp.negative_evidence_patterns) + [cand[product.id]],
                        acao=acao, product_id=product.id,
                    )
                prompts[c] = s if c == "base" else gp.posiciona(s, versao=c)
            users: dict[str, str] = {}
            for _score, ch in pool:
                lab = f"{product.id}/_{_sufixo(ch.filename)}/pg{ch.page_number}#{ch.chunk_index}"
                assert lab not in users, lab
                users[lab] = g.build_relevance_user_prompt(
                    g.strip_extraction_noise(ch.text), product_id=product.id)
            plano.append({"acao": aid, "pid": product.id, "isento": product.id in isentos,
                          "base": system, "prompts": prompts, "users": users})

    n_pares = sum(len(p["users"]) for p in plano)
    faltam = set(cand) - {p["pid"] for p in plano}
    if faltam:
        print(f"candidatos sem pool (não medidos): {sorted(faltam)}")
    n_cham = n_pares * len(conds) * args.passes
    cb = sum(len(p["base"]) for p in plano) / max(len(plano), 1)
    print(f"produtos com pool: {len(plano)}   pares: {n_pares}   chamadas: {n_cham} "
          f"({len(conds)} condições x {args.passes} passadas)   ~{n_cham * 0.9 / 60:.0f} min a 0,9 s/chamada")
    for c in conds:
        cc = sum(len(p["prompts"][c]) for p in plano) / max(len(plano), 1)
        print(f"prompt de sistema, média: {c} {cc:.0f} chars ({cc / cb - 1:+.0%} sobre o de produção)")
    if cand:
        print(f"candidatos em memória nas condições {sorted(cand_conds)}: {sorted(cand)}")

    if args.show:
        for p in plano:
            if p["pid"] == args.show:
                ultimo = conds[-1]
                print(f"\n===== {args.show} / {ultimo} ({len(p['prompts'][ultimo])} chars)\n")
                print(p["prompts"][ultimo])
                print(f"\n===== primeiro prompt de usuário\n\n{next(iter(p['users'].values()))[:600]}")
                break
        else:
            print(f"produto {args.show} sem pool ou inexistente")
        return 0
    if args.dry_run:
        return 0

    # ADR-0059 aplicado ao diagnóstico: servidor fora -> erro explícito agora.
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{g.BASE_URL}/health", timeout=20) as r:
            r.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"servidor GPU inacessível em {g.BASE_URL}: {type(exc).__name__}: {exc}")
        return 2

    # ---------------------------------------------------------------- medição
    import hashlib
    saida: dict = {"_condicao": {"base_url": g.BASE_URL, "reasoning_effort": "low",
                                 "passes": args.passes, "genre_filter": True,
                                 "pares": n_pares, "produtos": len(plano), "condicoes": conds,
                                 "candidatos": {"arquivo": args.candidates, "produtos": sorted(cand),
                                                "condicoes": sorted(cand_conds)},
                                 "sha_textos": {n: hashlib.sha256(getattr(gp, n).encode()).hexdigest()[:16]
                                                for n in ("POSICAO", "NOMEAR", "TITULO_NOVO")}}}
    t0 = time.time()
    for i, p in enumerate(plano, 1):
        res = {lab: {c: "" for c in conds} for lab in p["users"]}
        raz = {lab: {c: [] for c in conds} for lab in p["users"]}
        erros = 0
        for _passo in range(args.passes):
            for cond in conds:
                for lab, user in p["users"].items():
                    r = g.call(p["prompts"][cond], user)
                    v = r["verdict"]
                    res[lab][cond] += "T" if v else ("F" if v is False else "?")
                    raz[lab][cond].append(r.get("reasoning") or r.get("error") or "")
                    erros += 1 if r.get("error") else 0
        bits = {c: "".join("T" if any(res[lab][c][k] == "T" for lab in res) else "F"
                           for k in range(args.passes)) for c in conds}
        mudou = [lab for lab in res if len({res[lab][c] for c in conds}) > 1]
        print(f"[{i}/{len(plano)}] {p['pid']:6} pool={len(res):2} bit "
              + " ".join(f"{c}={bits[c]}" for c in conds)
              + f"  mudaram {len(mudou)}  ({time.time() - t0:.0f}s)", flush=True)
        for lab in mudou:
            print(f"      {lab:24} " + "  ".join(f"{c}={res[lab][c]}" for c in conds), flush=True)
        saida[p["pid"]] = {"acao": p["acao"], "isento": p["isento"], "pool": len(res),
                           "chars": {"base": len(p["base"]), **{c: len(p["prompts"][c]) for c in conds}},
                           "bits": bits, "resultado": res, "reasoning": raz, "erros": erros}
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            json.dump(saida, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\ntotal {time.time() - t0:.0f}s   produtos {len(plano)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
