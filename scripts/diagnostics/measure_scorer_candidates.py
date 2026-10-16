"""Candidatos de texto do scorer sobre levas fixas (2026-10-16): o antes/depois do item 3
do plano de 2026-10-04 (§4.3 de scratchpad/CICLO1_2026-10-04.md).

As levas são as de measure_scorer_reasoning.py: os vereditos gravados do gate de um
processo dos ciclos 3 a 7 são repetidos sobre a recuperação de HEAD, e a leva refeita
precisa ser igual à gravada. O gate não é chamado. Para cada leva, três braços:

- "atual": os prompts e o esquema de produção, tais como evaluate() os envia;
- "C": o contrato de saída proposto. Muda só o texto fixo e o esquema:
    * o nível de cada produto vem das definições do Guia do iPMP, seção 4.1
      (atendido / parcial / nao_atendido) em vez de um booleano sem definição;
    * o registro de que o produto falta ou não se aplica conta como nao_atendido;
    * a incerteza deixa de ser ligada pelos produtos sem trechos;
    * os campos do JSON são nomeados, na ordem em que o esquema os pede;
    * os trechos selecionados pelo gate são chamados de "trechos", não de "evidências";
    * corrige "acima" (os trechos vêm depois) e "licitário";
- "CH": C mais uma linha por cabeçalho: os Produtos Esperados que completam a frase de
  um item não pontuado (por exemplo, 32a a 32f completam «Orçamento ... custos de:»).

Em C e CH, o score é contado em código como em ADR-0058, com três níveis:
3 se todos os produtos forem "atendido"; 1 se algum for "atendido" ou "parcial"; 0 se não.
Nada muda em src/: os braços C e CH existem só neste script.

Braços acrescentados em 16/10/2026, depois da medição 2 (mensagem Y do usuário):
- "C2": C mais a seção "Por que é importante" do Guia (por_que_importante), entre a
  Ação e "O que esperar"; nada mais muda;
- "C2M": C2 mais a seção "Momento desta Ação no processo", logo depois dos Produtos
  Esperados: a fase do Guia e a faixa de Ações dela, o ponto de transição quando houver,
  o momento ideal do Guia, as relações da Ação com outras (data/ipmp/dependencias.json,
  ADR-0070, com o título de cada Ação) e a regra de uso. Os trechos não trazem a data do
  documento, então o momento não serve para atribuir nem negar um nível: só situa o produto.
A palavra "tempestiva" do Guia (4.1 e 5.1.1) fica fora de todos os braços: ela pede a data
de produção de cada documento, que o pipeline não extrai.
A medição 3 roda com --bracos atual,C,C2,C2M --semente 20261018
--out scratchpad/acc/scorer_c2.json.

Cada passada embaralha (leva, braço) com semente fixa. Cada chamada grava o nível ou o
veredito por produto, a justificativa, o score do próprio modelo, o score contado, a
incerteza, o canal de análise, os tokens e os hashes dos prompts. Nada vai para o banco.
Com --dry-run, só monta os prompts (sem GPU) e grava os textos para leitura.
Com --retoma, continua o --out existente: confere semente, braços, passadas e os hashes dos
prompts, mantém as chamadas sem erro e refaz o resto na mesma ordem (a semente embaralha
todas as passadas de novo). Uma chamada que falha (túnel ou servidor fora) é repetida até
duas vezes, com 45 s de espera; as falhas ficam em "falhas_anteriores".
"""
import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_scorer_reasoning as base  # noqa: E402  (wiring de produção, gate repetido)

from assessment.service import _retrieve_and_select  # noqa: E402
from evaluation import configure_llm_client, evaluate  # noqa: E402
from evaluation._config import get_llm_client, get_model, get_provider  # noqa: E402
from evaluation.parsing.response import parse_llm_response  # noqa: E402
from evaluation.prompt import builder  # noqa: E402
from evaluation.schemas import SCORER_SCHEMA  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402
from ingestion.dependencias import get_dependency_store  # noqa: E402

ACC = base.ACC
PROCESS = base.PROCESS

# ---------------------------------------------------------------- texto fixo do braço C
PERSONA_ATUAL = (
    "Você é um avaliador especializado no framework IPMP (Indicador de "
    "Percepção de Maturidade de Projetos) de concessões públicas. "
    "Sua tarefa é avaliar se as evidências extraídas de um processo "
    "licitário atendem aos critérios desta Ação IPMP."
)
PERSONA_C = (
    "Você é um avaliador especializado no framework IPMP (Indicador de "
    "Percepção de Maturidade de Projetos) de concessões públicas. "
    "Sua tarefa é avaliar se os trechos extraídos de um processo "
    "licitatório comprovam os Produtos Esperados desta Ação IPMP."
)

MARCA_C = "Nenhum trecho foi selecionado para este Produto Esperado."

INSTRUCAO_BLOCOS_C = (
    "Os trechos abaixo estão organizados por Produto Esperado. "
    "Há um bloco para cada Produto Esperado desta Ação, inclusive para os que "
    "ficaram sem trechos. Julgue cada produto apenas pelos trechos do seu bloco. "
    f'Um bloco marcado "{MARCA_C}" corresponde ao nível "nao_atendido".'
)


def instrucao_pontuacao_c(ids):
    rotulo = f"({', '.join(ids)})"
    n = len(ids)
    return f"""\
Com base exclusivamente nos trechos da mensagem a seguir, avalie a Ação e responda \
com um objeto JSON com estes campos, nesta ordem:
- "products": um item para cada Produto Esperado {rotulo}, com "product_id", \
"justificativa" e "nivel";
- "reasoning": texto livre em português que resume a avaliação dos produtos;
- "score": a pontuação da Ação, pela regra abaixo;
- "uncertainty": pela regra abaixo.

Avalie CADA UM dos Produtos Esperados {rotulo}, um por um, inclusive os que ficaram \
sem trechos. Para cada produto, julgue apenas os trechos do seu bloco e atribua um \
"nivel", com os critérios do Guia do iPMP (seção 4.1):
- "atendido": há evidência clara e completa do que o texto do produto pede.
- "parcial": há documentação tecnicamente consistente e aproveitável que comprova \
parte do que o produto pede, mesmo com falhas formais ou pontuais.
- "nao_atendido": não há trechos; ou os trechos são menções genéricas, evidências \
frágeis, ou documentos irrelevantes, desconexos ou superficiais em relação ao que o \
produto pede; ou os trechos registram que o produto não foi feito, está ausente ou não \
se aplica. O registro de que o produto falta é útil ao auditor, mas não comprova o produto.
Na "justificativa", escreva primeiro o que os trechos mostram e o que faltaria para \
um nível mais alto; depois atribua o "nivel".

Regra do "score", sobre os {n} Produtos Esperados:
- 3 somente quando os {n} produtos forem "atendido";
- 1 quando ao menos um produto for "atendido" ou "parcial", sem que todos sejam "atendido";
- 0 quando todos forem "nao_atendido".
Trate texto com ruído de OCR (caracteres ilegíveis ou garbled) como evidência não \
confiável; não atribua "atendido" nem "parcial" com base apenas nele.

Regra do "uncertainty": true somente quando, para algum produto com trechos, os trechos \
permitiriam com razão outro nível. Um produto sem trechos é "nao_atendido" e não torna, \
por si só, a avaliação incerta.\
"""


ESQUEMA_C = {
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "justificativa": {"type": "string"},
                    "nivel": {"type": "string", "enum": ["atendido", "parcial", "nao_atendido"]},
                },
                "required": ["product_id", "justificativa", "nivel"],
                "additionalProperties": False,
            },
        },
        "reasoning": {"type": "string"},
        "score": {"type": "integer", "enum": [0, 1, 3]},
        "uncertainty": {"type": "boolean"},
    },
    "required": ["products", "reasoning", "score", "uncertainty"],
    "additionalProperties": False,
}

RESUMO = re.compile(
    r"--- (\d+) trecho\(s\) recuperado\(s\), (\d+) caracteres"
    r"(?:; (\d+) de (\d+) Produto\(s\) Esperado\(s\) com evidência)?"
    r"(?:; SEM evidência: (.*?))? ---$")


def sistema_c(sistema_atual, ids):
    """O prompt de sistema de produção com a persona e as instruções de pontuação de C.
    Todo o resto (Ação, O que esperar, Produtos, Exemplos, Exceções) fica byte a byte."""
    assert sistema_atual.count(PERSONA_ATUAL) == 1
    s = sistema_atual.replace(PERSONA_ATUAL, PERSONA_C)
    marca = "## Instruções de pontuação\n\n"
    assert s.count(marca) == 1
    return s[: s.index(marca) + len(marca)] + instrucao_pontuacao_c(ids)


def cabecalhos(acao):
    """Uma linha por item não pontuado que tem filhos pontuados."""
    prods = acao.produtos_esperados
    linhas = []
    for h in prods:
        if h.scored:
            continue
        filhos = [p.id for p in prods if p.scored and p.id != h.id and p.id.startswith(h.id)]
        if filhos:
            linhas.append(f"Os Produtos Esperados {', '.join(filhos)} completam a frase: «{h.texto.strip()}»")
    return linhas


def usuario_c(usuario_atual, ids, acao, com_cabecalho):
    """O prompt de usuário de produção com a terminologia de C. Os trechos, a ordem e os
    blocos ficam iguais; mudam a instrução, os títulos, a marca de bloco vazio e o resumo."""
    inicio = builder._PRODUCT_BLOCK_INSTRUCTION + "\n\n"
    assert usuario_atual.startswith(inicio)
    corpo = usuario_atual[len(inicio):]
    n_tit = corpo.count("## Evidências para Produto ")
    assert n_tit >= len(ids), (n_tit, ids)
    corpo = corpo.replace("## Evidências para Produto ", "## Trechos para o Produto ")
    corpo = corpo.replace(builder._NO_EVIDENCE_MARKER, MARCA_C)
    linhas = corpo.split("\n\n")
    m = RESUMO.match(linhas[-1])
    assert m, linhas[-1]
    n_tr, n_car, com, tot, sem = m.groups()
    resumo = f"--- {n_tr} trecho(s), {n_car} caracteres"
    if tot:
        resumo += f"; produtos com trechos: {com} de {tot}"
        if sem:
            resumo += f"; sem trechos: {sem}"
    linhas[-1] = resumo + " ---"
    partes = [INSTRUCAO_BLOCOS_C]
    if com_cabecalho:
        partes += cabecalhos(acao)
    return "\n\n".join(partes + linhas)


def conta_c(niveis, ids):
    if not niveis or set(niveis) != set(ids):
        return None
    vals = [niveis[i] for i in ids]
    if all(v == "atendido" for v in vals):
        return 3
    if any(v in ("atendido", "parcial") for v in vals):
        return 1
    return 0


def le_c(conteudo, ids):
    try:
        dados = json.loads(conteudo)
    except (TypeError, ValueError):
        return {"falha": "json"}
    niveis, just = {}, {}
    for it in dados.get("products") or []:
        if isinstance(it, dict) and it.get("product_id") in ids:
            niveis[it["product_id"]] = it.get("nivel")
            just[it["product_id"]] = it.get("justificativa")
    contado = conta_c(niveis, ids)
    return {"niveis": niveis, "justificativas": just, "score_modelo": dados.get("score"),
            "score": contado if contado is not None else dados.get("score"),
            "fonte": "computed" if contado is not None else "model",
            "incerteza": bool(dados.get("uncertainty")), "reasoning": dados.get("reasoning")}


def le_atual(conteudo, ids):
    r = parse_llm_response(conteudo, expected_product_ids=ids)
    try:
        modelo = json.loads(conteudo).get("score")
    except (TypeError, ValueError, AttributeError):
        modelo = None
    return {"niveis": {v.product_id: ("evidenciado" if v.evidenced else "nao") for v in r.product_verdicts},
            "justificativas": {v.product_id: v.justificativa for v in r.product_verdicts},
            "score_modelo": modelo, "score": r.proposed_score, "fonte": r.score_source,
            "incerteza": r.uncertainty_flag, "reasoning": r.reasoning,
            **({"falha": "parse"} if r.parse_failed else {})}


# ---------------------------------------------------------------- braços C2 e C2M
FAIXA_FASE = {
    "Estudo das alternativas": (1, 20),
    "Aprimoramento da alternativa escolhida": (21, 37),
    "Consulta pública, Revisões e atualizações": (38, 46),
}

# Uma frase por tipo de aresta (ADR-0070), vista a partir desta Ação.
REL_CITANTE = {  # esta -> outra
    "pre": "pressupõe a Ação {n}",
    "artefato": "retoma e atualiza o documento da Ação {n}",
    "fraco": "recomenda partir do resultado da Ação {n}",
    "sucessora": "fornece insumo à Ação {n}, que vem depois",
    "contraste": "distingue-se da Ação {n}",
    "delega": "deixa parte do tema para a Ação {n}",
    "sequencia": "vem depois da Ação {n}",
    "lacuna": "pode suprir lacunas da Ação {n}",
}
REL_CITADA = {  # outra -> esta
    "pre": "é pressuposta pela Ação {n}",
    "artefato": "tem o documento retomado e atualizado pela Ação {n}",
    "fraco": "é o ponto de partida recomendado da Ação {n}",
    "sucessora": "usa o resultado da Ação {n}, que vem antes",
    "contraste": "distingue-se da Ação {n}",
    "delega": "recebe parte do tema da Ação {n}",
    "sequencia": "vem antes da Ação {n}",
    "lacuna": "pode ter lacunas supridas pela Ação {n}",
}

USO_MOMENTO = (
    "Use esta seção só para entender em que etapa do processo o produto deveria ser "
    "elaborado e o que ele pressupõe. Os trechos não trazem a data do documento de onde "
    "vieram: não atribua nem negue um nível por suposição sobre quando um documento foi "
    "produzido, e julgue cada produto pelo que os próprios trechos dizem."
)
USO_RELACOES = "As Ações relacionadas só situam esta Ação; não as avalie."


def secao_importancia(acao):
    return f"## Por que é importante\n\n{acao.por_que_importante.strip()}"


def secao_momento(acao, ipmp, deps):
    a, b = FAIXA_FASE[acao.fase]
    linhas = [f"Fase do Guia: {acao.fase} (Ações {a} a {b})."]
    if acao.ponto_transicao:
        linhas.append("Esta Ação é um dos cinco pontos de transição do Guia, que marcam a "
                      "passagem entre etapas do processo.")
    linhas.append(f"Momento ideal, segundo o Guia: {acao.momento_ideal.strip()}")
    rel, vistos = [], set()
    for d in sorted(deps.dependencias, key=lambda d: (d.citada, d.tipo)):
        if d.citante == acao.acao_id and (d.citada, d.tipo, "+") not in vistos:
            vistos.add((d.citada, d.tipo, "+"))
            rel.append(f"- Esta Ação {REL_CITANTE[d.tipo].format(n=d.citada)}: "
                       f"«{ipmp.acoes[d.citada].titulo.strip()}».")
    for d in sorted(deps.dependencias, key=lambda d: (d.citante, d.tipo)):
        if d.citada == acao.acao_id and (d.citante, d.tipo, "-") not in vistos:
            vistos.add((d.citante, d.tipo, "-"))
            rel.append(f"- Esta Ação {REL_CITADA[d.tipo].format(n=d.citante)}: "
                       f"«{ipmp.acoes[d.citante].titulo.strip()}».")
    corpo = "\n".join(linhas)
    if rel:
        corpo += "\n\nRelações desta Ação com outras, segundo o texto do Guia:\n" + "\n".join(rel)
    uso = USO_MOMENTO + (" " + USO_RELACOES if rel else "")
    return f"## Momento desta Ação no processo\n\n{corpo}\n\n{uso}"


def insere_antes(s, marca, secao):
    """Insere uma seção nova, com o separador do builder, antes da marca (que começa nele)."""
    assert s.count(marca) == 1, (s.count(marca), marca)
    i = s.index(marca)
    return s[:i] + "\n\n---\n\n" + secao + s[i:]


def sistema_c2(sistema_atual, ids, acao, ipmp=None, deps=None):
    """C2: o sistema de C mais "Por que é importante". Com ipmp e deps, C2M: mais o momento."""
    s = sistema_c(sistema_atual, ids)
    s = insere_antes(s, "\n\n---\n\n## O que esperar\n\n", secao_importancia(acao))
    if deps is not None:
        s = insere_antes(s, "\n\n---\n\n## Exemplos ilustrativos", secao_momento(acao, ipmp, deps))
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--alvos", default=None, help="Ação:ciclo:processo, separados por vírgula")
    ap.add_argument("--bracos", default="atual,C,CH")
    ap.add_argument("--passes", type=int, default=10)
    ap.add_argument("--semente", type=int, default=20261017)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=str(ACC / "scorer_candidatos.json"))
    ap.add_argument("--retoma", action="store_true",
                    help="continua o --out existente; refaz só o que falta, na mesma ordem")
    args = ap.parse_args()
    alvos = (base.ALVOS_PADRAO if not args.alvos
             else [tuple(int(x) for x in a.split(":")) for a in args.alvos.split(",") if a.strip()])
    bracos = [b.strip() for b in args.bracos.split(",") if b.strip()]
    ipmp = get_ipmp_store()
    deps = get_dependency_store()
    prod, provider, model = get_llm_client(), get_provider(), get_model()

    levas, descartados = [], []
    for acao_id, ciclo, proc in alvos:
        rotulo = f"A{acao_id}-C{ciclo}r{proc}"
        mapa, gravada, desfecho, verds = base._carrega(acao_id, ciclo, proc)
        base._REPLAY.clear()
        base._REPLAY.update(mapa)
        base._FALTAS.clear()
        accepted, rejected, reports = _retrieve_and_select(acao_id, PROCESS)
        refeita = base._assinatura(accepted)
        if refeita != gravada:
            print(f"{rotulo}: leva DIFERENTE da gravada; descartada", flush=True)
            descartados.append(rotulo)
            continue
        acao = ipmp.acoes[acao_id]
        ids = [p.id for p in acao.produtos_esperados if p.scored]
        configure_llm_client(base._Stub(ids), provider="stub", model="stub")
        r = evaluate(acao_id, PROCESS, accepted, rejected_chunks=rejected, product_gate_reports=reports)
        configure_llm_client(prod, provider=provider, model=model)
        prompts = {"atual": (r.system_prompt, r.user_prompt, SCORER_SCHEMA)}
        prompts["C"] = (sistema_c(r.system_prompt, ids), usuario_c(r.user_prompt, ids, acao, False), ESQUEMA_C)
        prompts["CH"] = (prompts["C"][0], usuario_c(r.user_prompt, ids, acao, True), ESQUEMA_C)
        prompts["C2"] = (sistema_c2(r.system_prompt, ids, acao), prompts["C"][1], ESQUEMA_C)
        prompts["C2M"] = (sistema_c2(r.system_prompt, ids, acao, ipmp, deps), prompts["C"][1], ESQUEMA_C)
        levas.append({"rotulo": rotulo, "acao": acao_id, "ids": ids, "assinatura": refeita,
                      "gravado": {"desfecho": desfecho, "vereditos": verds},
                      "prompts": {b: prompts[b] for b in bracos}})
        print(f"{rotulo}: leva IGUAL à gravada; " + "; ".join(
            f"{b} {len(prompts[b][0])}+{len(prompts[b][1])} car." for b in bracos), flush=True)

    out = {"process": PROCESS, "passes": args.passes, "semente": args.semente, "bracos": bracos,
           "dry_run": args.dry_run, "descartados": descartados, "levas": {}, "chamadas": []}
    for lv in levas:
        out["levas"][lv["rotulo"]] = {
            "acao": lv["acao"], "ids": lv["ids"], "assinatura": lv["assinatura"], "gravado": lv["gravado"],
            "prompts": {b: {"system": s, "user": u, "hash_system": base._h(s), "hash_user": base._h(u)}
                        for b, (s, u, _) in lv["prompts"].items()}}
    if args.dry_run or not levas:
        base._grava(out, args.out)
        print(f"gravado {args.out} (sem chamadas ao scorer)")
        return 0 if not descartados else 2

    feitos, anterior = set(), None
    if args.retoma and Path(args.out).exists():
        ant = json.loads(Path(args.out).read_text(encoding="utf-8"))
        mesmos = (ant["semente"], ant["bracos"], ant["passes"]) == (args.semente, bracos, args.passes)
        assert mesmos, "retomada com outros parâmetros"
        assert set(ant["levas"]) == set(out["levas"]), "retomada com outras levas"
        for rot, lv in out["levas"].items():
            for b, pr in lv["prompts"].items():
                velho = ant["levas"][rot]["prompts"][b]
                assert (velho["hash_system"], velho["hash_user"]) == (pr["hash_system"], pr["hash_user"]), (rot, b)
        out["chamadas"] = ant["chamadas"]
        feitos = {(c["passada"], c["leva"], c["braco"]) for c in ant["chamadas"] if "erro" not in c}
        out["retomadas"] = ant.get("retomadas", []) + [{
            "quando": time.strftime("%Y-%m-%d %H:%M:%S"), "mantidas": len(feitos),
            "falhas_anteriores": sum(1 for c in ant["chamadas"] if "erro" in c)}]
        if ant["chamadas"]:
            anterior = (ant["chamadas"][-1]["leva"], ant["chamadas"][-1]["braco"])
        print(f"retomada: {len(feitos)} chamadas mantidas; a mesma semente refaz a ordem", flush=True)
    rnd = random.Random(args.semente)
    erros_seguidos = 0
    try:
        for passada in range(1, args.passes + 1):
            ordem = [(lv, b) for lv in levas for b in bracos]
            rnd.shuffle(ordem)
            for lv, b in ordem:
                if (passada, lv["rotulo"], b) in feitos:
                    continue
                s, u, esquema = lv["prompts"][b]
                t0 = time.monotonic()
                item = {"passada": passada, "leva": lv["rotulo"], "braco": b, "anterior": anterior,
                        "hash_system": base._h(s), "hash_user": base._h(u)}
                c, falhas = None, []
                for tentativa in range(3):  # túnel ou servidor fora: espera e repete a mesma chamada
                    t0 = time.monotonic()
                    try:
                        c = prod.complete_detailed(s, u, schema=esquema)
                        break
                    except Exception as exc:
                        falhas.append(f"{type(exc).__name__}: {exc}")
                        if tentativa < 2:
                            time.sleep(45)
                if falhas:
                    item["falhas_anteriores"] = falhas
                try:
                    if c is None:
                        raise RuntimeError(falhas[-1])
                    lido = (le_atual if b == "atual" else le_c)(c.content, lv["ids"])
                    item.update(lido)
                    item.update({"conteudo": c.content, "analise": c.reasoning, "finish": c.finish_reason,
                                 "tokens": c.completion_tokens})
                    erros_seguidos = 0
                except Exception as exc:  # a medição segue; a falha fica registrada
                    item["erro"] = falhas[-1] if c is None else f"{type(exc).__name__}: {exc}"
                    erros_seguidos += 1
                item["segundos"] = round(time.monotonic() - t0, 1)
                out["chamadas"].append(item)
                anterior = (lv["rotulo"], b)
                com_trecho = sorted({p for *_, pids in lv["assinatura"] for p in pids})
                nv = " ".join(f"{p}={(item.get('niveis') or {}).get(p)}" for p in com_trecho)
                print(f"passada {passada:2d} {lv['rotulo']:12s} {b:5s} score={item.get('score', item.get('erro'))} "
                      f"{nv} ({item['segundos']} s, {item.get('tokens')} tokens)", flush=True)
                if erros_seguidos >= 3:
                    raise RuntimeError("três falhas seguidas do scorer; medição interrompida")
            base._grava(out, args.out)
    finally:
        base._grava(out, args.out)
    print(f"gravado {args.out}: {len(out['chamadas'])} chamadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
