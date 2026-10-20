"""C16 (2026-10-20): a ideia alargada nas Ações 6 e 42.

Pedido do usuário (20/10): "Vamos alargar a ideia para 6 e 42." No C15 o ponto dessas duas Ações
dependia de UMA página limítrofe (6: _2 p.157; 42: _2 p.144/145) e virava moeda entre processos. Com
mais produtos lendo a ideia, mais páginas podem dar o ponto pelo OU da regra 0/1/3.

Este arquivo reaproveita os 7 candidatos do piloto (candidates_ideia_piloto.py, sem mudança) e acrescenta:
  6c  custos, benefícios e riscos de cada alternativa (comparação breve);
  6d  conclusão sobre a alternativa que segue (posicionamento conclusivo);
  42c efeitos das alterações sobre modelagem, cronograma e custo;
  42d versão final dos documentos: só o intent é reescrito. 42d é isento de gênero (lê texto de
      instrumento), então não recebe o corte das raias depois do filtro nem termos novos.

Regra de fonte (ADR-0073): termos do texto do IPMP, da Lei 14.133/2021 (art. 18 §1 V, VI, VIII e XIII)
ou vocabulário geral de análise. Nenhum termo foi tirado das páginas do caso; "nova versão dos
documentos" e "publique-se" ficam de fora porque vieram do despacho do caso (bloco C, revertido).
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "_piloto", Path(__file__).resolve().parent / "candidates_ideia_piloto.py")
_piloto = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_piloto)

frase, perto, GERAL, L14133_18V = _piloto.frase, _piloto.perto, _piloto.GERAL, _piloto.L14133_18V
L14133_18VIII = "Lei 14.133/2021 art. 18 §1 VIII (justificativas para o parcelamento ou não da contratação)"
L14133_18XIII = ("Lei 14.133/2021 art. 18 §1 XIII (posicionamento conclusivo sobre a adequação da "
                 "contratação para o atendimento da necessidade)")
L14133_18VI = "Lei 14.133/2021 art. 18 §1 VI (estimativa do valor da contratação)"
IPMP = "texto do IPMP do próprio produto"

CANDIDATOS = dict(_piloto.CANDIDATOS)

CANDIDATOS["6c"] = {
    "acao": 6,
    "corte_depois_filtro": True,
    "intent_substitui": (
        "Trecho de qualquer documento do processo que compara, mesmo de forma breve, custos, benefícios, "
        "vantagens ou riscos de mais de uma forma de atender à necessidade (por exemplo execução direta, "
        "contratação, concessão ou parcelamento em lotes). O que conta é a comparação entre alternativas, "
        "onde quer que esteja escrita; um estudo que calcula a viabilidade de uma única solução já escolhida "
        "não é essa comparação."
    ),
    "termos_add": [
        perto(["custos", "benefícios"], 6, IPMP),
        perto(["comparação", "alternativas"], 8, GERAL),
        perto(["alternativa", "mais", "vantajosa"], 6, L14133_18V),
        frase("justificativas para o parcelamento", L14133_18VIII),
    ],
}

CANDIDATOS["6d"] = {
    "acao": 6,
    "corte_depois_filtro": True,
    "intent_substitui": (
        "Trecho de qualquer documento do processo que conclui qual forma de atender à necessidade segue "
        "adiante — a solução escolhida, a opção adotada ou o posicionamento conclusivo sobre a contratação — "
        "depois de considerar as alternativas. Vale onde quer que esteja escrito; o nome do documento não "
        "decide."
    ),
    "termos_add": [
        frase("posicionamento conclusivo", L14133_18XIII),
        perto(["solução", "escolhida"], 4, L14133_18V),
        perto(["opção", "adotada"], 4, GERAL),
        perto(["conclui", "viável"], 10, GERAL),
    ],
}

CANDIDATOS["42c"] = {
    "acao": 42,
    "corte_depois_filtro": True,
    "intent_substitui": (
        "Trecho de qualquer documento do processo que diz que efeito uma alteração feita nos documentos da "
        "licitação tem sobre a modelagem, o cronograma, o valor estimado ou o custo da contratação — "
        "inclusive a conclusão de que a alteração não muda esses elementos. Vale a manifestação, o despacho "
        "ou a nota técnica que trate disso; não é preciso um relatório consolidado. Cláusula que prevê "
        "alterações futuras não é efeito de uma alteração já feita."
    ),
    "termos_add": [
        perto(["alterações", "impacto"], 8, IPMP),
        perto(["alteração", "cronograma"], 8, IPMP),
        perto(["alteração", "valor", "estimado"], 10, L14133_18VI),
        perto(["não", "altera"], 2, GERAL),
    ],
}

CANDIDATOS["42d"] = {
    "acao": 42,
    "intent_substitui": (
        "Versão final dos documentos da licitação, ou o ato que a aprova, com indicação das partes revistas "
        "em relação à versão anterior. Vale o próprio documento final com as seções revisadas destacadas ou "
        "o ato (despacho, manifestação, nota) que aprova a versão final e diz o que foi ajustado. Cláusula "
        "que apenas prevê alterações futuras não é a versão final."
    ),
}
