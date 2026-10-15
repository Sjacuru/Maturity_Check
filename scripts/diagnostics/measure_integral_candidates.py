"""Rota A (2026-10-09): mede padrões negativos por produto SOB O PROMPT INTEGRAL.

P1a (`measure_sibling_text.py`, 17 190 chamadas) mostrou que o texto integral dos
irmãos no bloco de identidade (ADR-0064) é a condição mais constante — lotes
constantes em 22/23 Ações contra 17/23 hoje — mas cria três bits falsos estáveis
que o corte em 140 chars não criava, todos por casamento lexical com o critério:

  11a   p.214  organograma do GRUPO ECONÔMICO do licitante (habilitação)  ≠ equipe do órgão
  22.2a p.231  cláusula de subcontratação (atribuição de responsabilidade) ≠ justificativa
  31.1h p.194  rotina de inspeção/manutenção numa matriz de riscos        ≠ controle de qualidade

e um limítrofe (33b p.284, FTTTT: plano de transição operacional lido como
engajamento). A regra do item 4 (bit do produto constante; carregado por alvo
legítimo; nenhum controle estável regride; nada de fraseado do corpus) manda
medir cada padrão ANTES de aplicar o builder. Este script é
`measure_criterion_candidates.py` com uma diferença: os dois prompts de cada
candidato (sem/com padrão) são construídos com `_SIBLING_TEXT_MAX` sem limite,
alterado só em memória por `measure_sibling_text.aplica_condicao("integral")`.
`src/` não muda; nada é persistido; o ledger está fora por construção.

Decisão por candidato (direção = rejeição):
  passa  -> alvo FFFFF em `cand` (era TTTTT em `base`), controles iguais nas duas
            condições (um controle heterogêneo em `base` é ruído, não regressão),
            e o padrão sem expressão corpus-específica (`audita_sobreajuste`).
  reprova-> qualquer uma das três falha; o builder não muda.

Uso:
    python scripts/diagnostics/measure_integral_candidates.py --dry-run
    python scripts/diagnostics/measure_integral_candidates.py --passes 5 \
        --out scratchpad/acc/rota_a.json
    python scripts/diagnostics/measure_integral_candidates.py --sibling-text hoje ...
        (mesmos candidatos sob o prompt de produção, para comparação)
    python scripts/diagnostics/measure_integral_candidates.py --candidates \
        scripts/diagnostics/candidates_citing_originals.py ...
        (outro conjunto de candidatos, mesmo método — bloco A de 2026-10-10)

Desde 2026-10-13 o pool de cada produto não isento passa pelo filtro de gênero
do ADR-0074, como em produção; --no-genre-filter reproduz as medições anteriores.

Desde 2026-10-14, um candidato com "sem_isencao_genero" tira o produto da lista de
isenção do filtro de gênero, só em memória (Ação 45, candidates_cycle6.py). O
prompt não muda; muda o pool. Mede-se o pool novo sob o prompt de produção.
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

from ingestion import get_retrieval_profile_store  # noqa: E402
from ingestion import retrieval_profile as _rp  # noqa: E402
from retrieval import configure as retrieval_configure  # noqa: E402

import measure_sibling_text as mst  # noqa: E402

# --------------------------------------------------------------------------- candidatos
#
# Linguagem de critério, citando o IPMP da própria Ação — nunca o documento do
# caso. A auditoria de sobreajuste (3–5-gramas ausentes do IPMP da Ação e
# presentes no corpus) roda sobre estes textos antes da medição.

CANDIDATOS: dict[str, dict] = {
    "11a": {
        "acao": 11,
        "direcao": "rejeicao",
        "alvos": [("_2", 214)],
        "resumo": "exigência de habilitação/qualificação do licitante (organograma societário ou de pessoal do proponente) não é o organograma da equipe do projeto do órgão.",
        "ipmp": ("Produto 11a: 'Organograma, em nível inicial, que estabeleça quais "
                 "servidores/setores estarão envolvidos no projeto, indicando as funções e as "
                 "responsabilidades de cada um'. Descrição: 'Definir quem irá realizar o "
                 "trabalho de consolidar a documentação e gerir o projeto. Definir como as "
                 "decisões serão tomadas'. O exemplo Atendido fala da 'composição da equipe "
                 "técnica do órgão federal responsável'."),
        "negativo": (
            "Exigência de habilitação ou de qualificação dirigida ao licitante ou proponente "
            "— documentos que ele deve apresentar sobre a própria empresa ou o grupo que "
            "integra, inclusive organograma societário ou da estrutura de pessoal do "
            "proponente — não é o organograma da equipe do projeto. O critério pede quais "
            "servidores ou setores do órgão responsável estarão envolvidos no projeto, com "
            "as funções e responsabilidades de cada um e as instâncias de decisão; o "
            "organograma de uma empresa candidata à contratação não identifica servidores, "
            "setores nem instâncias decisórias do órgão."
        ),
    },
    "22.2a": {
        "acao": 22,
        "direcao": "rejeicao",
        "alvos": [("_1", 231)],
        "resumo": "cláusula que só atribui responsabilidade a uma parte (terceiros, danos, obrigações) não é justificativa técnica da alocação de riscos.",
        "ipmp": ("Produto 22.2a: 'Justificativa técnica da alocação dos riscos, com base em "
                 "critérios como capacidade de controle, custo e previsibilidade'. Exemplo "
                 "Atendido: 'Para cada risco relevante, foram detalhados a capacidade de "
                 "controle da parte responsável, os custos estimados e os mecanismos de "
                 "custeio'. Exceção: 'a alocação genérica de riscos, sem base em estudos "
                 "anteriores, pode indicar comprometimento da maturidade'."),
        "negativo": (
            "Cláusula que apenas atribui a uma das partes a responsabilidade por terceiros "
            "que ela contrate, por danos ou por obrigações, sem dizer por que a alocação foi "
            "feita assim, não é justificativa técnica da alocação de riscos. O critério pede "
            "a fundamentação da alocação com base em critérios como capacidade de controle, "
            "custo e previsibilidade, aplicados a riscos nomeados; a atribuição contratual de "
            "responsabilidade, por si, não aplica critério algum a risco algum."
        ),
    },
    "31.1h": {
        "acao": 31,
        "direcao": "rejeicao",
        "alvos": [("_1", 194)],
        "resumo": "rotina de inspeção/manutenção listada como resposta a risco ou dever operacional corrente não é procedimento de controle de qualidade do projeto.",
        "ipmp": ("Produto 31.1h: 'Procedimentos de controle de qualidade que serão "
                 "implementados (inspeções, revisões, testes, aprovações)'. Descrição: "
                 "'responsabilidades definidas por quem revisa, aprova e valida os produtos "
                 "técnicos; critérios de qualidade e conformidade que orientam as análises; "
                 "prazos e marcos para as etapas de revisão e aprovação; procedimentos padrão "
                 "para o tratamento de não conformidades'. Exemplo Atendido: 'critérios "
                 "técnicos objetivos, pontos de verificação em cada etapa e responsáveis "
                 "designados por validar as entregas'."),
        "negativo": (
            "Rotina de inspeção, manutenção ou conservação listada como resposta a um risco, "
            "ou como obrigação operacional corrente da contratada, não é procedimento de "
            "controle de qualidade do projeto. O critério pede como os produtos técnicos e "
            "as entregas serão verificados — inspeções, revisões, testes e aprovações — com "
            "critérios de qualidade e conformidade, responsáveis por revisar e aprovar, "
            "marcos de revisão e tratamento de não conformidades; uma ação de resposta a "
            "risco ou um dever de manutenção do ativo não define quem verifica o quê, com "
            "que critério, nem o que ocorre quando há não conformidade."
        ),
    },
    # "um olhar em 33b" (usuário, 2026-10-09): medido como os outros, decidido à parte.
    "33b": {
        "acao": 33,
        "direcao": "rejeicao",
        "olhar": True,
        "alvos": [("_1", 284)],
        "resumo": "plano de transição/assunção do serviço pela contratada não é plano de engajamento das partes interessadas.",
        "ipmp": ("Produto 33b: 'Forma como essas partes serão envolvidas e comunicadas ao "
                 "longo do ciclo de vida do projeto ... métodos de comunicação (reuniões, "
                 "consultas), frequência, prazos, principais tópicos a serem discutidos, "
                 "responsabilidades por cada ação'. O que esperar: 'identifique e envolva os "
                 "grupos impactados pelo projeto'. Exceção: 'povos originários, comunidades "
                 "quilombolas, famílias a serem reassentadas, proprietários de imóveis a "
                 "serem desapropriados'."),
        "negativo": (
            "Plano de transição ou de assunção do serviço pela contratada — reuniões com o "
            "contratante ou com o prestador anterior para conhecer rotinas, vistoria de "
            "bens, assunção da operação — não é plano de engajamento das partes "
            "interessadas. O critério pede como os grupos impactados pelo projeto "
            "(comunidades, famílias, proprietários, órgãos) serão envolvidos e comunicados "
            "ao longo do ciclo de vida, com método, frequência, tópicos e responsáveis; a "
            "passagem operacional entre contratada e contratante não identifica grupo "
            "impactado nem ação de engajamento com ele."
        ),
    },
}


def aplica(product_id: str) -> None:
    """Aplica o padrão do candidato no store em memória."""
    cand = CANDIDATOS[product_id]
    pp = get_retrieval_profile_store().acoes[cand["acao"]].expected_products[product_id]
    if cand.get("intent_add"):
        pp.evidence_intent = pp.evidence_intent.rstrip() + cand["intent_add"]
    if cand.get("negativo"):
        pp.negative_evidence_patterns = list(pp.negative_evidence_patterns) + [cand["negativo"]]


def e_alvo(cand: dict, chunk) -> bool:
    for sufixo, pagina in cand["alvos"]:
        if chunk.page_number == pagina and chunk.filename.rstrip(".pdf").endswith(sufixo):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=5)
    ap.add_argument("--only", default=None, help="lista de produtos, ex. 11a,31.1h")
    ap.add_argument("--sibling-text", default="integral", choices=("integral", "hoje"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="constrói os dois prompts e confere os alvos, sem chamar a GPU")
    ap.add_argument("--candidates", default=None,
                    help="arquivo .py com um dict CANDIDATOS no mesmo formato; "
                         "substitui os candidatos da rota A (ex.: candidates_citing_originals.py)")
    ap.add_argument("--base-url", default=None,
                    help="URL do servidor GPU (padrão: audit_gate_flips.BASE_URL); "
                         "útil quando o servidor só é alcançável por um túnel SSH")
    ap.add_argument("--no-genre-filter", action="store_true",
                    help="pool sem o filtro de gênero do ADR-0074 (como nas medições "
                         "anteriores a 2026-10-13)")
    args = ap.parse_args()

    if args.candidates:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_candidatos", args.candidates)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        CANDIDATOS.clear()
        CANDIDATOS.update(mod.CANDIDATOS)
        print(f"candidatos: {args.candidates} ({', '.join(CANDIDATOS)})")

    retrieval_configure(ROOT / "data" / "app.db")
    import audit_gate_flips as g
    if args.base_url:
        g.BASE_URL = args.base_url.rstrip("/")

    # A condição do bloco de identidade, só em memória (src/ intacto).
    mst.aplica_condicao(args.sibling_text)
    assert mst.rb._SIBLING_TEXT_MAX == mst.CONDICOES[args.sibling_text]

    # recuperação determinística (164/164 byte-idêntica): memoizar não altera nada.
    # ADR-0074: o pool de um produto não isento perde o texto de instrumento antes
    # do pré-filtro de quase-duplicatas e do corte de 16, como em select_evidence;
    # os produtos isentos ficam como estão.
    _bruto = g.retrieve_hybrid_candidates_for_acao
    _memo: dict[tuple, dict] = {}
    from evaluation import evidence_selection as _es
    from ingestion import get_genre_exemption_store
    _generos = {} if args.no_genre_filter else _es._chunk_genres(g.PROCESS)
    # produtos tratados como não isentos (candidato sem_isencao_genero), só em memória
    _sem_isencao: set[str] = set()

    def _memoizado(acao_id, process_number):
        chave = (acao_id, process_number, frozenset(_sem_isencao))
        if chave not in _memo:
            bruto = _bruto(acao_id, process_number)
            if _generos:
                isentos = get_genre_exemption_store().produtos(acao_id) - _sem_isencao
                bruto = {pid: (r if pid in isentos else _es._drop_instrument_text(r, _generos)[0])
                         for pid, r in bruto.items()}
            _memo[chave] = bruto
        return _memo[chave]

    g.retrieve_hybrid_candidates_for_acao = _memoizado

    # produção: gate serial, reasoning_effort=low (ADR-0065)
    g.ENGINE["reasoning_effort"] = "low"

    if not args.dry_run:
        # ADR-0059 aplicado ao diagnóstico: servidor fora -> erro explícito agora.
        import urllib.error
        import urllib.request
        try:
            with urllib.request.urlopen(f"{g.BASE_URL}/health", timeout=20) as r:
                r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"servidor GPU inacessível em {g.BASE_URL}: {type(exc).__name__}: {exc}")
            print("nada medido. Use --dry-run para a conferência estrutural sem servidor.")
            return 2

    escolhidos = ([p.strip() for p in args.only.split(",")] if args.only
                  else list(CANDIDATOS))
    saida: dict[str, dict] = {"_condicao": {"sibling_text": args.sibling_text, "base_url": g.BASE_URL,
                                            "reasoning_effort": "low", "passes": args.passes,
                                            "genre_filter": not args.no_genre_filter}}
    t0 = time.time()

    for pid in escolhidos:
        cand = CANDIDATOS[pid]
        if cand.get("sem_isencao_genero"):
            # O produto sai da lista de isenção: o prompt de sistema tem de ser o
            # mesmo; o pool novo é julgado sob ele.
            if not _generos:
                print(f"  !! {pid}: sem_isencao_genero exige o filtro de gênero; pulado")
                continue

            def _pool(acao, produto):
                return g._prefilter_near_duplicates(
                    g.retrieve_hybrid_candidates_for_acao(acao, g.PROCESS).get(produto, [])
                )[:g._MAX_EXAMINED]

            base_t = g.build_targets(cand["acao"], products={pid})
            base_pool = _pool(cand["acao"], pid)
            _sem_isencao.add(pid)
            novo_t = g.build_targets(cand["acao"], products={pid})
            novo_pool = _pool(cand["acao"], pid)
            _sem_isencao.discard(pid)
            sistemas = {t["system"] for t in base_t} | {t["system"] for t in novo_t}
            assert len(sistemas) == 1, f"{pid}: o prompt de sistema mudou"
            assert [t["label"] for t in novo_t] == [
                f"{pid}/pg{ch.page_number}#{ch.chunk_index}" for _s, ch in novo_pool]
            arq = {t["label"]: ch for t, (_s, ch) in zip(novo_t, novo_pool)}
            hoje = {(ch.filename, ch.page_number, ch.chunk_index) for _s, ch in base_pool}
            prompts = {t["label"]: (t["system"], t["user"]) for t in novo_t}
            print()
            print(f"=== {pid} (sem isenção de gênero)  pool hoje={len(base_t)}  "
                  f"pool novo={len(novo_t)}", flush=True)
            for lab, ch in arq.items():
                marca = "mesmo" if (ch.filename, ch.page_number, ch.chunk_index) in hoje else "novo "
                print(f"      {marca} {lab:22} {ch.filename}", flush=True)
            registro = {"acao": cand["acao"], "direcao": cand["direcao"], "ipmp": cand["ipmp"],
                        "patch": {"sem_isencao_genero": True},
                        "pool_hoje": len(base_t), "pool_novo": len(novo_t),
                        "arquivo_por_label": {lab: ch.filename for lab, ch in arq.items()}}
            if args.dry_run:
                saida[pid] = registro
                continue
            res = {lab: "" for lab in prompts}
            razoes = {lab: [] for lab in prompts}
            for passo in range(args.passes):
                for lab, (system, user) in prompts.items():
                    r = g.call(system, user)
                    v = r["verdict"]
                    res[lab] += "T" if v else ("F" if v is False else "?")
                    razoes[lab].append(r.get("reasoning") or r.get("error") or "")
                print(f"    passada {passo + 1}/{args.passes} ok  ({time.time() - t0:.0f}s)", flush=True)
            for lab in sorted(res):
                print(f"    {lab:22} {res[lab]}")
            saida[pid] = dict(registro, resultado=res, reasoning=razoes)
            if args.out:
                Path(args.out).parent.mkdir(parents=True, exist_ok=True)
                json.dump(saida, open(args.out, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
            continue
        base_targets = g.build_targets(cand["acao"], products={pid})
        base_prompts = {t["label"]: (t["system"], t["user"]) for t in base_targets}
        pool = g._prefilter_near_duplicates(
            g.retrieve_hybrid_candidates_for_acao(cand["acao"], g.PROCESS).get(pid, [])
        )[:g._MAX_EXAMINED]
        chunks = {f"{pid}/pg{ch.page_number}#{ch.chunk_index}": ch for _s, ch in pool}

        aplica(pid)
        cand_targets = g.build_targets(cand["acao"], products={pid})
        cand_prompts = {t["label"]: (t["system"], t["user"]) for t in cand_targets}
        _rp._store = None   # desfaz o patch (store é global de módulo)

        if set(base_prompts) != set(cand_prompts):
            print(f"  !! {pid}: o pool mudou entre as condições — abortando este candidato")
            continue
        mudou_prompt = sum(1 for k in base_prompts if base_prompts[k] != cand_prompts[k])
        # o padrão entra no prompt de sistema; o de usuário (chunk) é o mesmo
        assert all(base_prompts[k][1] == cand_prompts[k][1] for k in base_prompts), pid
        # e o prompt de sistema base é o INTEGRAL (nenhum irmão truncado)
        if args.sibling_text == "integral":
            assert "…\n" not in next(iter(base_prompts.values()))[0].split(
                "NÃO estão em avaliação aqui")[-1], pid

        alvos = {lab for lab, ch in chunks.items() if e_alvo(cand, ch)}
        fora = [a for a in cand["alvos"]
                if not any(e_alvo({"alvos": [a]}, ch) for ch in chunks.values())]

        print(f"\n=== {pid} ({cand['direcao']}{', olhar' if cand.get('olhar') else ''})  "
              f"pool={len(base_prompts)} prompts alterados={mudou_prompt}/{len(base_prompts)}  "
              f"irmãos={args.sibling_text}", flush=True)
        print(f"    alvos no pool: {sorted(alvos) or 'NENHUM'}"
              + (f"   FORA DO POOL: {fora}" if fora else ""), flush=True)
        if args.dry_run:
            arquivos = {lab: ch.filename for lab, ch in chunks.items()}
            saida[pid] = {
                "pool": len(base_prompts), "prompts_alterados": mudou_prompt,
                "alvos": sorted(alvos), "alvos_fora_do_pool": fora,
                "arquivo_por_label": arquivos,
                "chars_base": len(next(iter(base_prompts.values()))[0]),
                "chars_cand": len(next(iter(cand_prompts.values()))[0]),
            }
            for lab in sorted(chunks):
                print(f"      {lab:22} {arquivos[lab]}")
            continue

        res = {lab: {"base": "", "cand": ""} for lab in base_prompts}
        razoes = {lab: {"base": [], "cand": []} for lab in base_prompts}
        for passo in range(args.passes):
            for cond, prompts in (("base", base_prompts), ("cand", cand_prompts)):
                for lab in base_prompts:
                    system, user = prompts[lab]
                    r = g.call(system, user)
                    v = r["verdict"]
                    res[lab][cond] += "T" if v else ("F" if v is False else "?")
                    razoes[lab][cond].append(r.get("reasoning") or r.get("error") or "")
            print(f"    passada {passo + 1}/{args.passes} ok  ({time.time() - t0:.0f}s)", flush=True)

        for lab in sorted(res, key=lambda l: (l not in alvos, l)):
            marca = "ALVO " if lab in alvos else "ctrl "
            b, c = res[lab]["base"], res[lab]["cand"]
            sinal = "" if b == c else "   <-- mudou"
            print(f"    {marca}{lab:22} base={b}  cand={c}{sinal}")

        saida[pid] = {
            "acao": cand["acao"], "direcao": cand["direcao"], "olhar": bool(cand.get("olhar")),
            "ipmp": cand["ipmp"],
            "patch": {k: cand.get(k) for k in ("intent_add", "negativo") if cand.get(k)},
            "pool": len(base_prompts), "prompts_alterados": mudou_prompt,
            "alvos": sorted(alvos), "resultado": res, "reasoning": razoes,
        }
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            json.dump(saida, open(args.out, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

    print(f"\ntotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
