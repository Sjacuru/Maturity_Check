"""Piloto C15 (2026-10-19): consultas pela IDEIA do produto, não pelo nome do documento.

Pedido do usuário (19/10): nas Ações que pedem um documento nomeado, buscar o que o documento deve
conter ("a alma do documento") e não o documento em si; sem o documento a Ação não chega a 3, mas a
presença da ideia vale 0 ou 1. Piloto em 7 produtos de 4 Ações (6a, 6b, 8a, 15a, 15c, 42a, 42b).

Cada produto recebe, só em memória (reproducibility.py --candidates ... --apply ...):
  intent_substitui     o evidence_intent reescrito pela ideia;
  termos_add           termos novos, ativos e canônicos;
  corte_depois_filtro  as raias BM25 e vetorial cortadas em 20 DEPOIS do filtro de gênero, só neste
                       produto (lane_genre_filter.instala(produtos=...)). Sem isso o texto de
                       instrumento ocupa os 20 lugares e o pool fica com 0 a 4 trechos.

Regra de fonte (ADR-0073): cada termo vem do texto do IPMP ou da legislação em que o conceito se apoia
(Lei 14.133/2021 art. 18 §1 e art. 53; Lei 8.987/1995 art. 5; Lei 11.079/2004 art. 10), ou é
vocabulário geral de análise em português administrativo. Nenhum termo foi tirado das páginas do caso.

Medido sem GPU (2026-10-19, pool examinado; páginas da C14 contidas / total):
  6a 0/2 -> 2/2 (n 3 -> 13); 6b 0/2 -> 1/2 (1 -> 11); 8a 1/4 -> 4/4 (1 -> 15); 15a 1/2 -> 2/2 (2 -> 13);
  15c n 4 -> 15; 42a 1/3 -> 2/3 (1 -> 12); 42b 0/2 -> 1/2 (0 -> 13). Os pools trazem 3 a 7 cópias do
  estudo econômico de referência e o termo de atestação de conformidade.
"""


T = "C"  # tipo de termo usado nos perfis para termos de conteúdo


def frase(texto, fonte, conceito=None):
    return {"encoding": "phrase", "text": texto, "type": T, "provenance": "canonical", "status": "active",
            "concept_ref": conceito, "_fonte": fonte}


def perto(tokens, dist, fonte, conceito=None):
    return {"encoding": "near", "tokens": tokens, "distance": dist, "type": T, "provenance": "canonical",
            "status": "active", "concept_ref": conceito, "_fonte": fonte}


L14133_18V = "Lei 14.133/2021 art. 18 §1 V (análise das alternativas possíveis e justificativa da escolha)"
L8987_5 = "Lei 8.987/1995 art. 5 (ato justificativo da conveniência da outorga)"
L11079_10 = "Lei 11.079/2004 art. 10 I a (razões que justifiquem a opção pela PPP)"
L14133_53 = "Lei 14.133/2021 art. 53 (controle prévio de legalidade pelo órgão de assessoramento jurídico)"
GERAL = "vocabulário geral de análise em português administrativo"

CANDIDATOS = {
    "6a": {
        "acao": 6,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento do processo (estudo técnico preliminar, justificativa, parecer, nota "
            "técnica ou estudo de viabilidade) que compara mais de uma forma de atender à necessidade pública — "
            "por exemplo execução direta pela Administração, contratação de obra ou serviço, concessão, parceria "
            "público-privada ou não intervir — e indica, para cada uma, o escopo, a solução técnica, a forma de "
            "entrega, a viabilidade econômico-financeira ou a fonte de financiamento. O que conta é a comparação "
            "entre alternativas, onde quer que esteja escrita; o nome ou o formato do documento não decide."
        ),
        "termos_add": [
            frase("análise das alternativas possíveis", L14133_18V),
            frase("levantamento de mercado", L14133_18V),
            perto(["alternativas", "avaliadas"], 8, GERAL),
            perto(["vantagens", "desvantagens"], 6, GERAL),
            perto(["execução", "direta", "concessão"], 20, L8987_5),
        ],
    },
    "6b": {
        "acao": 6,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento do processo que explica por que uma forma de atender à necessidade foi "
            "escolhida e as outras foram afastadas — as razões técnicas, econômicas ou de gestão da escolha da "
            "solução. Vale a justificativa onde quer que esteja escrita (estudo técnico preliminar, justificativa "
            "da contratação, ato justificativo da concessão, parecer); o nome do documento não decide."
        ),
        "termos_add": [
            frase("justificativa técnica e econômica da escolha", L14133_18V),
            perto(["razões", "opção", "forma"], 8, L11079_10),
            perto(["conveniência", "oportunidade"], 3, L11079_10),
            perto(["alternativa", "descartada"], 8, GERAL),
        ],
    },
    "8a": {
        "acao": 8,
        "corte_depois_filtro": True,
        # 2ª redação (19/10): a 1ª listava formatos e regimes e puxou a consulta vetorial para texto de
        # contrato (ETP p.156 caiu de #2 para #86); esta fica curta e na ideia.
        "intent_substitui": (
            "Justificativa fundamentada de por que o formato de contratação escolhido (obra pública direta, "
            "concessão, PPP ou outro) é o mais adequado, em comparação com os demais. Vale onde quer que esteja "
            "escrita; o nome do documento não decide."
        ),
        "termos_add": [
            frase("conveniência da outorga", L8987_5),
            perto(["razões", "opção", "parceria"], 10, L11079_10),
            perto(["conveniência", "oportunidade"], 3, L11079_10),
            perto(["concessão", "vantagens"], 15, GERAL),
            frase("justificativa técnica e econômica da escolha", L14133_18V),
        ],
    },
    "15a": {
        "acao": 15,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento do processo que aponta riscos ou ameaças capazes de afetar a contratação "
            "ou a execução do projeto — ambientais, sociais, técnicos, financeiros, regulatórios ou de obtenção "
            "de licenças —, mesmo que não estejam organizados num plano ou numa tabela de riscos. O que conta é "
            "a identificação do risco, onde quer que esteja escrita."
        ),
        "termos_add": [
            perto(["riscos", "identificados"], 5, GERAL),
            perto(["possíveis", "riscos"], 3, GERAL),
            perto(["risco", "atraso"], 6, GERAL),
            perto(["poderá", "comprometer"], 6, GERAL),
        ],
    },
    "15c": {
        "acao": 15,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento do processo que indica o que será feito para evitar um risco ou reduzir "
            "sua probabilidade ou seu impacto antes da contratação — providências, cautelas ou medidas "
            "mitigadoras —, mesmo fora de um plano de riscos formal. O que conta é a medida ligada a um risco "
            "identificado."
        ),
        "termos_add": [
            frase("medidas mitigadoras", "Lei 14.133/2021 art. 18 §1 XII (impactos ambientais e medidas mitigadoras)"),
            frase("providências a serem adotadas", "Lei 14.133/2021 art. 18 §1 X (providências prévias à celebração)"),
            frase("a fim de evitar", GERAL),
            perto(["mitigar", "risco"], 6, GERAL),
        ],
    },
    "42a": {
        "acao": 42,
        "corte_depois_filtro": True,
        "intent_substitui": (
            "Trecho de qualquer documento do processo que registra alterações feitas nos documentos da licitação "
            "(edital, termo de referência, minuta de contrato, anexos) e o motivo de cada uma — por exemplo, em "
            "resposta à análise jurídica, a órgão de controle ou a contribuições recebidas. Vale a manifestação, "
            "o despacho, a nota técnica ou a resposta que diz o que mudou e por quê; não é preciso um relatório "
            "consolidado."
        ),
        "termos_add": [
            frase("controle prévio de legalidade", L14133_53),
            perto(["análise", "jurídica"], 3, L14133_53),
            perto(["ajustes", "minuta"], 8, GERAL),
            perto(["foi", "incluída", "cláusula"], 6, GERAL),
            perto(["alteração", "edital", "motivo"], 12, GERAL),
        ],
    },
    "42b": {
        "acao": 42,
        "corte_depois_filtro": True,
        # 2ª redação (19/10): a 1ª puxou a consulta vetorial para as cópias do estudo econômico.
        "intent_substitui": (
            "Registro das contribuições externas recebidas (consulta pública, assessoria jurídica, órgãos de "
            "controle) e da resposta a cada uma, dizendo se foi acolhida ou não e por quê. Vale onde quer que "
            "esteja escrito; não é preciso um relatório consolidado."
        ),
        "termos_add": [
            perto(["recomendação", "acolhida"], 8, GERAL),
            perto(["sugestão", "acolhida"], 8, GERAL),
            perto(["não", "acolhida"], 2, GERAL),
            frase("pedido de esclarecimento", "Lei 14.133/2021 art. 164 (impugnação e pedido de esclarecimento)"),
            perto(["em", "atendimento", "recomendação"], 6, GERAL),
        ],
    },
}
