"""Mede o efeito do texto INTEGRAL dos irmãos no prompt do gate (P1a).

Hoje `_sibling_contrast()` corta o texto IPMP de cada irmão em
`_SIBLING_TEXT_MAX` = 140 caracteres. Medido em 2026-10-09: 52 dos 164 textos
passam de 140, e o corte preserva a oração de abertura genérica e descarta a
enumeração — justamente a parte que discrimina um irmão do outro (18b perde
571 de 710 chars; 1d perde a lista de instrumentos federais; 5b corta no meio
de uma palavra). Custo do texto integral: +3,1 % na média, máximo inalterado.

O que este script mede é o que o custo não responde: se o texto integral muda
VEREDITOS, em que direção, e se mexe na constância. Condições:

  hoje      _SIBLING_TEXT_MAX = 140 (produção)
  integral  _SIBLING_TEXT_MAX = sem limite
  rotulado  integral + o produto EM AVALIAÇÃO identificado como os irmãos
            (id na linha do texto; id no título do critério) — ver rotula_alvo()
  ids       lista de irmãos só com os ids, sem texto (opcional)

Só os produtos cujo prompt de sistema DIFERE entre as condições são medidos:
um prompt byte-idêntico não traz informação. O pool é o examinado da produção
(dedup 0.92, `ranked[:_MAX_EXAMINED]`), as condições são intercaladas por
passada, o gate roda serial a `reasoning_effort=low` (ADR-0065), o ledger está
fora por construção (chamadas diretas, nada persistido), e a constante é
alterada só em memória — `src/` não muda.

Leitura, pelo critério de constância do usuário (0 / 1-2 / >2 mudanças):
  * por chunk: trajetória em cada condição (TTTTT, FTFTF, ...)
  * por produto: o bit `evidenced` (OR dos chunks) por passada em cada condição
  * verdadeiros positivos conhecidos (22.2 p.774/p.193, 22.2b p.921, 26d p.136)
    e falsos positivos conhecidos aparecem no relatório final, nominalmente.

Uso:
    python scripts/diagnostics/measure_sibling_text.py --dry-run
    python scripts/diagnostics/measure_sibling_text.py --passes 5 \
        --out scratchpad/acc/p1a_siblings.json
    python scripts/diagnostics/measure_sibling_text.py --acoes 22,26 --passes 5
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "diagnostics"))

from evaluation.prompt import relevance_builder as rb  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402
from retrieval import configure as retrieval_configure  # noqa: E402

CONDICOES = {
    "hoje": 140,
    "integral": 10 ** 9,
    "rotulado": 10 ** 9,   # integral + alvo rotulado (ver rotula_alvo)
    "ids": 0,
}

_TITULO_CRITERIO = "## Critério de relevância para este Produto Esperado"


def rotula_alvo(system: str, pid: str, texto: str) -> str:
    """Condição 'rotulado': o produto EM AVALIAÇÃO passa a ser identificado como
    os irmãos são — id na frente do texto — e o título do critério leva o id.

    Motivo (medido no ledger do ciclo 1, 2026-10-09): em 88 de 2 498 vereditos
    (3,5 %) o reasoning mostra o modelo em dúvida sobre QUAL produto está
    avaliando ("product 4c is not described earlier"; "earlier they said product
    2a is the one"). O bloco de identidade descreve os irmãos como `- 4a — texto`
    e o alvo ou sem texto (quando o dedup com o intent o omite) ou entre «aspas»
    sem id. Nada de conteúdo novo entra; só a identificação.
    """
    assert system.count(_TITULO_CRITERIO) == 1, pid
    system = system.replace(
        _TITULO_CRITERIO, f"## Critério de relevância do Produto Esperado {pid}")
    citacao = f"\n«{texto}»"
    if texto and citacao in system:
        return system.replace(
            citacao, f"\n- {pid} (EM AVALIAÇÃO) — {texto}", 1)
    # texto omitido pelo dedup: aponta para a seção do critério, sem repetir
    linhas = system.split("\n")
    for i, linha in enumerate(linhas):
        if linha.startswith(f"Produto Esperado {pid},") or linha.startswith(
                f"Produto Esperado {pid} "):
            linhas.insert(i + 1, f"- {pid} (EM AVALIAÇÃO) — critério na seção "
                                 f"«Critério de relevância do Produto Esperado {pid}» abaixo.")
            return "\n".join(linhas)
    raise AssertionError(f"linha do produto {pid} não encontrada")


def _sibling_ids_only(scored, product_id: str) -> str:
    """Variante 'ids': a lista de irmãos sem texto. Mesma moldura da produção."""
    others = [p for p in scored if p.id != product_id]
    if not others:
        return ""
    linhas = "\n".join(f"- {p.id}" for p in others)
    return ("\nOs demais Produtos Esperados desta Ação, que NÃO estão em "
            f"avaliação aqui:\n{linhas}\n")


def aplica_condicao(nome: str) -> None:
    if nome == "ids":
        rb._SIBLING_TEXT_MAX = 140
        rb._sibling_contrast = _sibling_ids_only
        return
    rb._sibling_contrast = _SIBLING_ORIGINAL
    rb._SIBLING_TEXT_MAX = CONDICOES[nome]


_SIBLING_ORIGINAL = rb._sibling_contrast


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=5)
    ap.add_argument("--acoes", default=None, help="ex. 22,26 (padrão: todas)")
    ap.add_argument("--conditions", default="hoje,integral")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="conta produtos afetados e chamadas, sem GPU")
    ap.add_argument("--show", default=None,
                    help="imprime o bloco de identidade de um produto em cada condição")
    args = ap.parse_args()

    conds = [c.strip() for c in args.conditions.split(",")]
    for c in conds:
        if c not in CONDICOES:
            print(f"condição desconhecida: {c}")
            return 2
    if conds[0] != "hoje":
        print("a primeira condição deve ser 'hoje' (linha de base)")
        return 2

    retrieval_configure(ROOT / "data" / "app.db")
    import audit_gate_flips as g

    _bruto = g.retrieve_hybrid_candidates_for_acao
    _memo: dict[tuple, dict] = {}

    def _memoizado(acao_id, process_number):
        chave = (acao_id, process_number)
        if chave not in _memo:
            _memo[chave] = _bruto(acao_id, process_number)
        return _memo[chave]

    g.retrieve_hybrid_candidates_for_acao = _memoizado
    g.ENGINE["reasoning_effort"] = "low"

    if not args.dry_run:
        import urllib.error
        import urllib.request
        try:
            with urllib.request.urlopen(f"{g.BASE_URL}/health", timeout=20) as r:
                r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"servidor GPU inacessível em {g.BASE_URL}: {type(exc).__name__}: {exc}")
            print("nada medido. Use --dry-run para a contagem sem servidor.")
            return 2

    st = get_ipmp_store()
    acoes = ([int(a) for a in args.acoes.split(",")] if args.acoes
             else sorted(st.acoes))

    # ---------------------------------------------------------------- prompts
    # Por Ação, os alvos em cada condição. Só entram na medição os produtos
    # cujo prompt difere da linha de base em alguma condição.
    plano: list[dict] = []
    for aid in acoes:
        por_cond: dict[str, dict[str, tuple[str, str]]] = {}
        for c in conds:
            aplica_condicao(c)
            alvos = g.build_targets(aid)
            if c == "rotulado":
                for t in alvos:
                    # o texto cru do IPMP é o que _identity_block cita; o
                    # normalizado serve só para o caso de o builder normalizar
                    bruto = next(p.texto for p in st.acoes[aid].produtos_esperados
                                 if p.id == t["product_id"])
                    t["system"] = rotula_alvo(t["system"], t["product_id"], bruto)
            por_cond[c] = {t["label"]: (t["system"], t["user"]) for t in alvos}
        aplica_condicao("hoje")
        base = por_cond["hoje"]
        if any(set(por_cond[c]) != set(base) for c in conds):
            print(f"  !! Ação {aid}: o pool mudou entre condições — abortando a Ação")
            continue
        por_produto: dict[str, list[str]] = {}
        for lab in base:
            por_produto.setdefault(lab.split("/")[0], []).append(lab)
        for pid, labels in por_produto.items():
            if not labels:
                continue
            difere = {c: base[labels[0]][0] != por_cond[c][labels[0]][0]
                      for c in conds if c != "hoje"}
            if not any(difere.values()):
                continue
            plano.append({
                "acao": aid, "pid": pid, "labels": labels,
                "prompts": {c: {lab: por_cond[c][lab] for lab in labels} for c in conds},
                "chars": {c: len(por_cond[c][labels[0]][0]) for c in conds},
            })

    if args.show:
        for p in plano:
            if p["pid"] != args.show:
                continue
            for c in conds:
                sys_ = p["prompts"][c][p["labels"][0]][0]
                i = sys_.find("## O que"); j = sys_.find("## Critério")
                print()
                print(f"===== {args.show} / {c}  ({len(sys_)} chars)")
                print(sys_[i:j + 80])
        return 0

    n_chunks = sum(len(p["labels"]) for p in plano)
    n_calls = n_chunks * len(conds) * args.passes
    print(f"produtos com prompt alterado: {len(plano)}   chunks: {n_chunks}   "
          f"chamadas: {n_calls} ({len(conds)} condições x {args.passes} passadas)   "
          f"~{n_calls * 0.85 / 60:.0f} min a 0,85 s/chamada", flush=True)
    for p in plano:
        print(f"  {p['pid']:7} pool={len(p['labels']):2}  chars="
              + "  ".join(f"{c}={p['chars'][c]}" for c in conds))
    if args.dry_run:
        return 0

    # ---------------------------------------------------------------- medição
    saida: dict[str, dict] = {}
    t0 = time.time()
    for i, p in enumerate(plano, 1):
        pid = p["pid"]
        res = {lab: {c: "" for c in conds} for lab in p["labels"]}
        razoes = {lab: {c: [] for c in conds} for lab in p["labels"]}
        erros = 0
        for passo in range(args.passes):
            for c in conds:
                for lab in p["labels"]:
                    system, user = p["prompts"][c][lab]
                    r = g.call(system, user)
                    v = r["verdict"]
                    res[lab][c] += "T" if v else ("F" if v is False else "?")
                    razoes[lab][c].append(r.get("reasoning") or r.get("error") or "")
                    if r.get("error"):
                        erros += 1
        bits = {c: "".join(
            "T" if any(res[lab][c][k] == "T" for lab in p["labels"]) else "F"
            for k in range(args.passes)) for c in conds}
        print(f"\n[{i}/{len(plano)}] {pid}  pool={len(p['labels'])}  "
              f"bit " + "  ".join(f"{c}={bits[c]}" for c in conds)
              + f"   ({time.time() - t0:.0f}s)", flush=True)
        for lab in p["labels"]:
            linha = "  ".join(f"{c}={res[lab][c]}" for c in conds)
            mudou = len({res[lab][c] for c in conds}) > 1
            print(f"    {lab:22} {linha}{'   <-- difere' if mudou else ''}", flush=True)
        saida[pid] = {
            "acao": p["acao"], "pool": len(p["labels"]), "chars": p["chars"],
            "bits": bits, "resultado": res, "reasoning": razoes, "erros": erros,
        }
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            json.dump(saida, open(args.out, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

    print(f"\ntotal {time.time() - t0:.0f}s   produtos {len(saida)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
