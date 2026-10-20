"""C17 (2026-10-20): a ideia do documento no grupo 1 — 14a, 27a, 27b, 41a.

Pedido do usuário (20/10): "3 - 14a, 27a/27b, 41a", depois de adotar a ideia nas Ações 8 e 15
(ADR-0079). São os produtos em que a leitura do corpus (só teste, nunca fonte de termos) achou a ideia
presente fora do documento nomeado. Na produção as três Ações dão "sem evidência" em 10/10 (C15), com
pools de 0 a 4 trechos: o texto de instrumento ocupa os 20 lugares das raias.

Cada produto recebe, só em memória (reproducibility.py --candidates ... --apply ...), as mesmas chaves do
piloto C15: intent pela ideia, termos canônicos novos, corte das raias depois do filtro de gênero. Em
14a e 27a, um padrão negativo existente exclui a própria ideia e é trocado (negativos_substitui):
  14a  "parágrafo narrativo ... não caracteriza por si só o documento/tabela" -> o benefício tem de ser
       público (não receita ou retorno do contratado) e dito como ganho;
  27a  "orçamento restrito aos custos operacionais ... não atende" (completude, julgamento do scorer)
       -> um valor global único, sem categorias, não é estrutura de custos.
Os demais negativos ficam (são distinções de sentido entre Ações).

Regra de fonte (ADR-0073): termos do IPMP, da Lei 14.133/2021 (art. 11 I, art. 18 §1 VI e IX, art. 33),
da Lei 8.987/1995 (art. 15) ou vocabulário geral. Nenhum termo foi tirado das páginas do caso.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "_piloto", Path(__file__).resolve().parent / "candidates_ideia_piloto.py")
_piloto = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_piloto)

frase, perto, GERAL = _piloto.frase, _piloto.perto, _piloto.GERAL
IPMP = "texto do IPMP do próprio produto"
L14133_18IX = ("Lei 14.133/2021 art. 18 §1 IX (demonstrativo dos resultados pretendidos em termos de "
               "economicidade e de melhor aproveitamento dos recursos)")
L14133_18VI = "Lei 14.133/2021 art. 18 §1 VI (estimativa do valor da contratação)"
L14133_33 = "Lei 14.133/2021 art. 33 (critérios de julgamento das propostas)"
L14133_11 = "Lei 14.133/2021 art. 11 I (proposta apta a gerar o resultado de contratação mais vantajoso)"
L8987_15 = "Lei 8.987/1995 art. 15 (critérios de julgamento na licitação de concessão)"

NEG14A_VELHO = (
    "Um parágrafo narrativo de benefícios estratégicos apresentado apenas como justificativa da viabilidade "
    "do projeto (sentido da Ação 4a), sem qualquer estrutura que permita associá-lo a métodos de entrega, "
    "mensuração, responsáveis e reporte por benefício individual (os demais produtos desta ação), não "
    "caracteriza por si só o documento/tabela preliminar de benefícios exigido por esta ação"
)
NEG27A_VELHO = (
    "Orçamento restrito aos custos operacionais do empreendimento, sem valores referentes a desapropriações, "
    "reassentamentos, licenciamento ambiental ou fiscalização, não atende a este produto (padrão do exemplo "
    "Não Atendido)."
)

CANDIDATOS = {
    "14a": {
        "acao": 14,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento do processo que diz quais benefícios o projeto deve trazer à "
            "população, aos usuários ou à Administração — econômicos, sociais ou ambientais, como acesso, tempo "
            "de deslocamento, segurança, qualidade do serviço ou economia de recursos. O que conta é a "
            "identificação do benefício público esperado, onde quer que esteja escrita; não é preciso uma tabela "
            "de gestão de benefícios."
        ),
        "termos_add": [
            frase("benefícios esperados", IPMP),
            frase("resultados pretendidos", L14133_18IX),
            perto(["benefícios", "população"], 8, GERAL),
            perto(["ganhos", "usuários"], 8, GERAL),
        ],
        "negativos_substitui": {
            NEG14A_VELHO: (
                "Receita, remuneração ou retorno do contratado ou da concessionária não são benefícios públicos; "
                "um objetivo enunciado sem dizer que ganho traz à população, aos usuários ou à Administração "
                "também não identifica um benefício."
            ),
        },
    },
    "27a": {
        "acao": 27,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento do processo que organiza os custos da solução escolhida por categoria "
            "— investimento, operação, manutenção, desapropriações, licenças, fiscalização ou outras —, em "
            "valores ou em estimativas. O que conta é a estrutura de custos, onde quer que esteja escrita "
            "(orçamento, estudo econômico, estudo técnico preliminar, planilha); o nome do documento não decide."
        ),
        "termos_add": [
            frase("estimativa do valor da contratação", L14133_18VI),
            perto(["custos", "investimento"], 4, GERAL),
            perto(["custos", "operação"], 4, GERAL),
            perto(["despesas", "operacionais"], 3, GERAL),
        ],
        "negativos_substitui": {
            NEG27A_VELHO: (
                "Um valor global único da contratação, sem desdobrar os custos em categorias, não é uma estrutura "
                "de custos."
            ),
        },
    },
    "27b": {
        "acao": 27,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento do processo que projeta ao longo do tempo as entradas e saídas de "
            "recursos da solução escolhida — fluxo de caixa por período —, com as premissas ou os parâmetros "
            "que a sustentam. Vale onde quer que esteja escrito; o nome do documento não decide."
        ),
        "termos_add": [
            perto(["fluxo", "caixa", "projetado"], 6, GERAL),
            perto(["premissas", "adotadas"], 4, GERAL),
            perto(["horizonte", "projeção"], 6, GERAL),
        ],
    },
    "41a": {
        "acao": 41,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento interno do processo (manifestação, nota técnica, despacho, resposta "
            "a órgão de controle ou à análise jurídica) que confirma ou justifica o critério de julgamento "
            "escolhido para selecionar a melhor proposta econômica — por exemplo maior oferta, menor tarifa, "
            "menor preço ou técnica e preço. Vale onde quer que esteja escrito; o critério apenas transcrito "
            "numa cláusula de edital não é a confirmação."
        ),
        "termos_add": [
            perto(["critério", "julgamento"], 3, L14133_33),
            frase("maior oferta", L8987_15),
            perto(["melhor", "proposta"], 3, IPMP),
            perto(["proposta", "mais", "vantajosa"], 4, L14133_11),
        ],
    },
}
