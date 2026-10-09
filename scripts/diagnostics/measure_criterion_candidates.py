"""Mede candidatos de CRITÉRIO por produto, sem tocar em src/ nem persistir nada.

Item 4 do plano de constância: depois que a expansão de vizinhos saiu (ADR-0069)
a lista de perguntas passou a ser função só da recuperação, e 100% das diferenças
restantes entre passadas são o gate respondendo diferente a um prompt
byte-idêntico. A ambiguidade está no critério, não no mecanismo.

A leitura dos 78 pares instáveis (2026-10-06) agrupou-os em 11 classes de página.
O achado que decide onde a correção pode morar: a mesma página é alvo legítimo de
alguns produtos e confusão de outros — a linha de matriz de riscos é a evidência
literal de 8d/23.4/22.2 e ruído para 11 produtos de 7 Ações; o edital procedimental
é o alvo de 25b/25c/25d e ruído para 5 produtos. Logo nenhuma regra global serve, e
a correção é por produto, no perfil de recuperação, escrita em linguagem de critério
e justificável citando o IPMP — nunca o documento do caso.

Cada candidato declara:
  * direção   -- aceite firme (o alvo É o critério e o gate hesita) ou rejeição
                 firme (o alvo não é o critério e o gate às vezes aceita)
  * patch     -- o que muda no perfil daquele produto (intent e/ou negativo)
  * ipmp      -- a passagem do IPMP que fundamenta, textualmente
  * alvos     -- os chunks que devem mudar de lado
  * controle  -- os demais chunks do mesmo pool, que NÃO podem mudar

O patch é aplicado só em memória. Como cada Produto Esperado tem o seu próprio
prompt, um candidato só pode alterar os vereditos daquele produto: o risco de cada
mudança é estruturalmente limitado a um produto, e o conjunto de controle é o
restante do pool examinado dele.

Uso:
    python scripts/diagnostics/measure_criterion_candidates.py --passes 5 \
        --out scratchpad/acc/item4.json
    python scripts/diagnostics/measure_criterion_candidates.py --only 33b,42c --passes 5
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

# --------------------------------------------------------------------------- candidatos

CANDIDATOS: dict[str, dict] = {
    # ---------------------------------------------------------------- aceite firme
    "8d": {
        "acao": 8,
        "direcao": "aceite",
        "alvos": [("_1", 196)],
        "ipmp": ("Produto: 'Levantamento de riscos contratuais relevantes (licenciamento, "
                 "interferências, desapropriações etc.)'. A nota 53 do IPMP, agora no dado, "
                 "diz que a decisão de modelagem costuma exceder a competência da unidade e "
                 "que 'há de se ter o registro formal dos fundamentos'; a modelagem "
                 "definitiva é da Ação 22."),
        "intent_add": (
            " Para este critério importa que o trecho IDENTIFIQUE um risco contratual "
            "relevante — licenciamento, interferências, desapropriações, regulatório, "
            "demanda, legislação — ainda que já o apresente sob a forma de alocação a uma "
            "das partes: o levantamento é justamente o inventário desses riscos. O estágio "
            "de maturidade do levantamento é juízo do pontuador, não condição de relevância."
        ),
    },
    "8b": {
        "acao": 8,
        "direcao": "aceite",
        "alvos": [("_2", 134)],
        "ipmp": ("Produto: 'Articulação entre escopo do projeto e regime de execução proposto "
                 "(direta, convênio, delegação etc.)'. Nota 53: 'há de se ter o registro "
                 "formal dos fundamentos que embasaram a escolha pela execução direta'."),
        "intent_add": (
            " Parecer, manifestação técnica ou despacho que registre formalmente os "
            "fundamentos da escolha do regime de execução atende este critério, ainda que a "
            "decisão tenha sido tomada em instância superior à unidade contratante."
        ),
    },
    "37": {
        "acao": 37,
        "direcao": "aceite",
        "alvos": [("_2", 144), ("_2", 145), ("_3", 2)],
        "ipmp": ("Produto: 'Conjunto completo dos documentos do processo de contratação "
                 "finalizados e aprovados internamente'. O exemplo Atendido fala em "
                 "documentos 'revisados, atualizados e aprovados formalmente'; o "
                 "Parcialmente, em 'formalizados e aprovados internamente'; o Não Atendido "
                 "é definido pela presença de 'versões preliminares' — anteprojeto sem "
                 "compatibilização, minuta em branco, critérios ausentes."),
        "intent_add": (
            " Conta como aprovação interna o ato formal que registra a conformidade ou a "
            "aprovação das peças: termo de atestação de conformidade, parecer jurídico ou "
            "manifestação técnica interna que examine e aprove os documentos, ou registro "
            "datado de aprovação. O que afasta o critério é a presença de versões "
            "preliminares sem qualquer ato de aprovação."
        ),
    },
    "45": {
        "acao": 45,
        "direcao": "aceite",
        "alvos": [("_2", 23)],
        "ipmp": ("Produto: 'Registro da realização do processo licitatório, nos termos da "
                 "legislação aplicável'. O exemplo Atendido enumera os atos: sessão pública "
                 "'com registro em ata', 'o resultado foi publicado', 'a autoridade "
                 "competente homologou o certame e adjudicou o objeto'. O Não Atendido "
                 "conclui pela 'inexistência de atos formais de encerramento ou "
                 "cancelamento'."),
        "intent_add": (
            " Conta como registro da realização o documento que comprova esses atos — ata da "
            "sessão pública, publicação do resultado, ato de homologação e de adjudicação — "
            "inclusive quando o registro aparece em instrumento posterior que os ateste, como "
            "os considerandos de um contrato que declaram a licitação realizada, homologada e "
            "o objeto adjudicado. O critério se apoia na existência dos atos formais."
        ),
    },
    # -------------------------------------------------------------- rejeição firme
    "27c": {
        "acao": 27,
        "direcao": "rejeicao",
        "alvos": [("_2", 50)],
        "ipmp": ("Produto: 'Inclusão de riscos e cenários de estresse'. O que esperar: "
                 "'inclusão de margens de contingência; análise de cenários de risco "
                 "sistemáticos e não sistemáticos'."),
        "negativo": (
            "Cláusula contratual que prevê a atualização futura de um plano de negócios, de "
            "um financiamento ou do equilíbrio do contrato não é cenário de estresse: o "
            "critério pede o teste do modelo financeiro sob variação de premissas — margem de "
            "contingência, cenário sistemático ou não sistemático — com o efeito dessa "
            "variação sobre o resultado. Exige, no trecho, uma premissa variada e o seu efeito."
        ),
    },
    "27d": {
        "acao": 27,
        "direcao": "rejeicao",
        "alvos": [("_2", 756), ("_2", 884)],
        "ipmp": ("Produto: 'Compatibilização com o cronograma físico-financeiro do projeto'. "
                 "O exemplo Parcialmente Atendido descreve 'projeção do fluxo de caixa "
                 "compatível com o cronograma físico-financeiro'."),
        "negativo": (
            "Obrigação operacional de execução — sinalização e proteção de áreas de passeio, "
            "emprego de equipes especializadas, minimização de interferência em vias — não é "
            "compatibilização com o cronograma físico-financeiro. O critério pede a "
            "correspondência entre o fluxo de caixa ou os desembolsos do modelo financeiro e "
            "as datas ou marcos do cronograma, o que exige no trecho uma referência temporal "
            "(marco, data, parcela, período) ligada a valor ou desembolso."
        ),
    },
    "31.1g": {
        "acao": 31,
        "direcao": "rejeicao",
        "alvos": [("_2", 595)],
        "ipmp": ("Produto: 'Padrões de qualidade a serem alcançados em cada etapa'. O que "
                 "esperar: cronograma 'considerando prazos, tarefas, responsabilidades, "
                 "recursos e controles'."),
        "negativo": (
            "Especificação técnica de produto ou equipamento — materiais, dimensões, modelos, "
            "desenhos, fotos — não é padrão de qualidade por etapa. O critério pede o padrão a "
            "ser ALCANÇADO em uma etapa do projeto, o que exige que o trecho vincule o padrão "
            "a uma etapa, fase ou marco e indique como o seu atendimento será verificado ou "
            "aprovado."
        ),
    },
    "33b": {
        "acao": 33,
        "direcao": "rejeicao",
        "alvos": [("_1", 83)],
        "ipmp": ("Produto: 'Forma como essas partes serão envolvidas e comunicadas ao longo do "
                 "ciclo de vida do projeto, considerando a alternativa escolhida, incluindo "
                 "métodos de comunicação (reuniões, consultas), frequência, prazos, principais "
                 "tópicos a serem discutidos, responsabilidades por cada ação'."),
        "negativo": (
            "Obrigação contratual corrente da contratada — responsabilizar-se por danos a "
            "usuários ou terceiros, publicar demonstrações financeiras, prestar contas a órgão "
            "de controle, manter sítio na internet — não é plano de engajamento. O critério "
            "pede, para grupos de partes interessadas identificados, o método de comunicação, "
            "a periodicidade, o prazo, o tópico e o responsável por cada ação de engajamento; "
            "um dever contratual perante o poder concedente ou o público em geral não "
            "identifica grupo, método nem responsável por ação de engajamento."
        ),
    },
    "42c": {
        "acao": 42,
        "direcao": "rejeicao",
        "alvos": [("_2", 493)],
        "ipmp": ("Produto: 'Análise dos efeitos das alterações na modelagem, cronograma e custo "
                 "da contratação'. O que esperar: 'explicação fundamentada sempre que ajustes "
                 "tenham se mostrado necessários, evidenciando o impacto'; o exemplo "
                 "Parcialmente Atendido reprova justamente a falta do registro do impacto."),
        "negativo": (
            "Cláusula que prevê hipóteses futuras de reequilíbrio, de revisão extraordinária ou "
            "de alteração normativa não é análise dos efeitos de uma alteração já realizada. O "
            "critério pede o efeito de um ajuste efetivamente feito nos documentos sobre a "
            "modelagem, o cronograma ou o custo, o que exige no trecho a referência a uma "
            "alteração ocorrida e ao seu impacto."
        ),
    },
}


def aplica(product_id: str) -> None:
    """Aplica o patch do candidato no store em memória."""
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
    ap.add_argument("--only", default=None, help="lista de produtos, ex. 33b,42c")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="constroi os dois prompts e confere os alvos, sem chamar a GPU")
    args = ap.parse_args()

    retrieval_configure(ROOT / "data" / "app.db")
    import audit_gate_flips as g

    # build_targets recupera por Acao a cada chamada, e cada candidato chama duas
    # vezes (base e candidato) mais uma para o pool. A recuperacao e deterministica
    # (164/164 byte-identica, 2026-10-02), logo memoizar nao altera nada e corta
    # 3x para 1x por Acao.
    _bruto = g.retrieve_hybrid_candidates_for_acao
    _memo: dict[tuple, dict] = {}

    def _memoizado(acao_id, process_number):
        chave = (acao_id, process_number)
        if chave not in _memo:
            _memo[chave] = _bruto(acao_id, process_number)
        return _memo[chave]

    g.retrieve_hybrid_candidates_for_acao = _memoizado

    # produção hoje: gate serial, reasoning_effort=low (ADR-0065)
    g.ENGINE["reasoning_effort"] = "low"

    if not args.dry_run:
        # ADR-0059 aplicado ao diagnóstico: servidor fora -> erro explícito agora.
        # Sem isto cada chamada arrasta o timeout de 600s e a corrida parece travada.
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
    saida: dict[str, dict] = {}
    t0 = time.time()

    for pid in escolhidos:
        cand = CANDIDATOS[pid]
        # pools: o mesmo pool examinado da produção, construído do store vivo
        base_targets = g.build_targets(cand["acao"], products={pid})
        base_prompts = {t["label"]: (t["system"], t["user"]) for t in base_targets}
        # build_targets nao devolve o chunk; o pool examinado e reconstruido com
        # as MESMAS funcoes da producao, de modo que label -> chunk e exato.
        pool = g._prefilter_near_duplicates(
            g.retrieve_hybrid_candidates_for_acao(cand["acao"], g.PROCESS).get(pid, [])
        )[:g._MAX_EXAMINED]
        chunks = {f"{pid}/pg{ch.page_number}#{ch.chunk_index}": ch for _s, ch in pool}

        aplica(pid)
        cand_targets = g.build_targets(cand["acao"], products={pid})
        cand_prompts = {t["label"]: (t["system"], t["user"]) for t in cand_targets}
        # desfaz: o patch e em memoria e o proximo candidato precisa do perfil
        # original. O store e um global de modulo, nao um lru_cache.
        _rp._store = None

        if set(base_prompts) != set(cand_prompts):
            print(f"  !! {pid}: o pool mudou entre as condições — abortando este candidato")
            continue
        mudou_prompt = sum(1 for k in base_prompts if base_prompts[k] != cand_prompts[k])

        # quais labels do pool EXAMINADO sao alvo. Um alvo fora de ranked[:16]
        # nao e mensuravel: o gate nunca o ve.
        alvos = {lab for lab, ch in chunks.items() if e_alvo(cand, ch)}
        fora = [a for a in cand["alvos"]
                if not any(e_alvo({"alvos": [a]}, ch) for ch in chunks.values())]

        print(f"\n=== {pid} ({cand['direcao']})  pool={len(base_prompts)} "
              f"prompts alterados={mudou_prompt}/{len(base_prompts)}", flush=True)
        print(f"    alvos no pool: {sorted(alvos) or 'NENHUM'}"
              + (f"   FORA DO POOL: {fora}" if fora else ""), flush=True)
        if args.dry_run:
            # conferência estrutural: um alvo fora de ranked[:16] não é mensurável,
            # porque o gate nunca o vê. Nenhuma chamada ao servidor aqui.
            saida[pid] = {
                "pool": len(base_prompts), "prompts_alterados": mudou_prompt,
                "alvos": sorted(alvos), "alvos_fora_do_pool": fora,
                "chars_base": len(next(iter(base_prompts.values()))[0]),
                "chars_cand": len(next(iter(cand_prompts.values()))[0]),
            }
            continue

        res = {lab: {"base": "", "cand": ""} for lab in base_prompts}
        for passo in range(args.passes):
            for cond, prompts in (("base", base_prompts), ("cand", cand_prompts)):
                for lab in base_prompts:
                    system, user = prompts[lab]
                    r = g.call(system, user)
                    v = r["verdict"]
                    res[lab][cond] += "T" if v else ("F" if v is False else "?")
            print(f"    passada {passo + 1}/{args.passes} ok  ({time.time() - t0:.0f}s)", flush=True)

        for lab in sorted(res, key=lambda l: (l not in alvos, l)):
            marca = "ALVO " if lab in alvos else "ctrl "
            b, c = res[lab]["base"], res[lab]["cand"]
            sinal = "" if b == c else "   <-- mudou"
            print(f"    {marca}{lab:22} base={b}  cand={c}{sinal}")

        saida[pid] = {
            "acao": cand["acao"], "direcao": cand["direcao"], "ipmp": cand["ipmp"],
            "patch": {k: cand.get(k) for k in ("intent_add", "negativo") if cand.get(k)},
            "pool": len(base_prompts), "prompts_alterados": mudou_prompt,
            "alvos": sorted(alvos), "resultado": res,
        }
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            json.dump(saida, open(args.out, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

    print(f"\ntotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
