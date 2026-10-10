"""Bloco A (2026-10-10): "o original não é a revisão" — padrões negativos por
produto para as Ações que CITAM outra Ação e cujo gate vinha aceitando o
instrumento ORIGINAL da Ação citada como se fosse a revisão/finalização pedida.

Medido antes (ledger do ciclo 1 + seis processos independentes d1–d3 e
rota_a_conf1–3): dos 309 vereditos do gate sobre produtos citantes, 31 (10 %)
aceitam o original da citada. A Ação 43 pontua 1 em 6/6 passadas unicamente
porque 43b aceita a MATRIZ DE RISCO do contrato (instrumento da Ação 22) e as
cláusulas de reequilíbrio; a Ação 35 pontua 1 em 6/6 via 35.2e (cláusulas de
seguro, linhas da matriz) e 35.2f (linha da matriz cujo texto de mitigação é
"monitoramento rotineiro"). 33b aceitou uma vez (1/6) obrigações contratuais
permanentes da contratada (`_1` p.83).

Dois casos lidos e deixados SEM padrão, de propósito:
  28.3  `_2` p.136 — parecer que diz "requisito não atendido": aceite correto
        pela regra de polaridade (ADR-0066); o scorer julga 28.3 não
        evidenciado. Funciona como desenhado.
  37    `_1` p.29 — página do edital (condições gerais da licitação): faz parte
        do conjunto finalizado que o critério pede; a instabilidade de 37 é a
        moeda conhecida gate/scorer, não um falso crédito.

Linguagem de critério, citando o IPMP da própria Ação — nunca o documento do
caso. A auditoria de sobreajuste (3–5-gramas ausentes do IPMP da Ação e
presentes no corpus) roda sobre estes textos antes da medição. O IPMP da Ação
35 distingue expressamente a alocação contratual de riscos entre as partes
(Ação 22) da gestão operacional pela equipe de projeto (Ação 35); o padrão
escreve essa distinção como conteúdo, sem número de Ação (uma referência por
número não é resolúvel no prompt do gate, P1c).

Uso: python scripts/diagnostics/measure_integral_candidates.py --candidates \
         scripts/diagnostics/candidates_citing_originals.py ...
"""

CANDIDATOS: dict[str, dict] = {
    "43b": {
        "acao": 43,
        "direcao": "rejeicao",
        # `_1` p.193/194/196 = linhas da matriz de risco; p.105 = requisitos do
        # pedido de reequilíbrio; p.239 = cláusula de manutenção da alocação.
        # Todos aceitos em pelo menos 4 de 6 processos independentes.
        "alvos": [("_1", 193), ("_1", 194), ("_1", 196), ("_1", 105), ("_1", 239)],
        "resumo": "matriz de riscos do contrato e cláusulas de reequilíbrio são o instrumento de alocação contratual (original), não a avaliação revisional do impacto financeiro de riscos residuais e alterações externas.",
        "ipmp": ("Produto 43b: 'Avaliação de riscos residuais e impacto de alterações "
                 "externas'. Descrição: 'Confirmar se, após os ajustes no processo de "
                 "contratação e na minuta contratual, o projeto continua passível de custeio "
                 "e com previsão atualizada fidedigna do desembolso total'. O que esperar: "
                 "'Revisão final da capacidade de custeio, do orçamento e do modelo "
                 "financeiro, notadamente após ajustes decorrentes de fatores supervenientes "
                 "(como consultas públicas, auditorias ou alterações contratuais)'. Por que "
                 "importante: mudanças como 'readequações de escopo, inclusão de medidas "
                 "mitigadoras ou alterações contratuais' afetam o custo total; o exemplo da "
                 "transferência de encargos pela revisão da matriz de riscos é avaliado pelo "
                 "seu impacto financeiro."),
        # 3ª rodada: p.105/p.196 resistiram também à 2ª; acrescenta o marcador textual
        # verificável (valor, percentual ou conclusão sobre a suficiência dos recursos).
        # 1ª rodada (5 passadas): p.193/194/239 TTTTT->FFFFF; p.105 (requisitos de um
        # futuro pedido de recomposição: "laudo que demonstre o impacto") e p.196 (linha
        # "alteração superveniente na legislação … impacto nas receitas") seguiram TTTTT —
        # o gate lê a palavra "impacto" como avaliação. 2ª rodada nomeia as duas classes.
        "negativo": (
            "A matriz de riscos do contrato — linhas que definem cada risco, o atribuem à "
            "contratada, ao poder concedente ou a ambos e listam as ações de mitigação, "
            "inclusive a linha que atribui a uma das partes o risco de alteração "
            "superveniente de legislação, regulação ou tributos — e as cláusulas que "
            "disciplinam o reequilíbrio econômico-financeiro (hipóteses que o autorizam, "
            "requisitos e documentos de um futuro pedido, regra de que a alocação pactuada "
            "se mantém) são o instrumento de alocação contratual de riscos entre as partes, "
            "produto de outra etapa, e não evidência desta avaliação. Dizer quem suporta o "
            "impacto de um evento, ou exigir que o interessado demonstre no futuro o impacto "
            "desse evento sobre as projeções financeiras, não é avaliar esse impacto para o "
            "projeto. O critério pede a avaliação, na "
            "revisão final da dimensão financeira, de riscos residuais e do impacto de "
            "alterações externas sobre a capacidade de custeio, o orçamento e o modelo "
            "financeiro: um risco ou uma alteração nomeados, o efeito estimado sobre o custo "
            "ou o desembolso previsto e a conclusão de que o projeto continua passível de "
            "custeio após os ajustes. Se o trecho não traz valor, percentual ou conclusão "
            "sobre a suficiência dos recursos deste projeto, ele descreve um evento e sua "
            "consequência contratual, não a avaliação. A alocação de riscos só conta quando "
            "o texto analisa o efeito financeiro de uma revisão dela — por exemplo, a "
            "transferência de encargos ao poder público — sobre a viabilidade do projeto."
        ),
    },
    "35.2e": {
        "acao": 35,
        "direcao": "rejeicao",
        # `_1` p.251 e p.117 = cláusulas de seguros; `_2` p.126 e p.776 = linhas
        # da matriz de risco (aceites estáveis da mesma classe).
        "alvos": [("_1", 251), ("_1", 117), ("_2", 126), ("_2", 776)],
        "resumo": "cláusulas de seguro e linhas da matriz de riscos são alocação contratual entre as partes, não a estratégia de resposta operacional da equipe do projeto a cada risco.",
        "ipmp": ("Produto 35.2e: 'Estratégia de resposta (evitar, mitigar, transferir, "
                 "aceitar) com ações específicas de gerenciamento'. O que esperar: 'Plano de "
                 "gestão de riscos aprofundado a partir da alternativa escolhida'. Exceção: "
                 "'Ressalta-se a diferença entre as Ações 22 e 35 do M5D: a primeira trata "
                 "das responsabilidades contratuais entre as partes, enquanto a segunda foca "
                 "a gestão operacional, incluindo monitoramento contínuo e estratégias de "
                 "resposta pela equipe de projeto'. Por que importante: 'aqui o foco está na "
                 "capacidade da equipe do projeto de monitorar, responder e agir frente a "
                 "riscos institucionais, operacionais e ambientais'."),
        # 4ª rodada: a frase da 3ª sobre a justificativa não moveu p.3 e p.776 voltou a
        # TTTTT (chunk limítrofe sensível a qualquer byte); nova frase com marcadores
        # verificáveis (registro de risco, escolha entre as quatro respostas, ação da equipe).
        # 3ª rodada: a 2ª passou nos alvos (p.117/p.776 FFFFF) mas o bit seguia ligado
        # por `_1` p.3 (justificativa da contratação lida como estratégia "evitar") — outra
        # classe, estável TTTTT em todos os processos; acrescenta uma frase para ela.
        # 1ª rodada: p.251 (cláusulas de seguro) TTTTT->FFFFF; `_2` p.776 (linhas de
        # matriz sem o cabeçalho "MATRIZ DE RISCO": "seguros, inspeções, manutenção")
        # seguiu TTTTT — o gate lê a lista de mitigações como estratégia de resposta.
        # 2ª rodada nomeia a lista de mitigações da outra parte, com ou sem cabeçalho.
        "negativo": (
            "Cláusulas contratuais que impõem à contratada a obrigação de manter seguros "
            "(coberturas, limites, vigência) e listas de ações de mitigação associadas a "
            "riscos atribuídos à contratada ou ao poder concedente — seguros, inspeções, "
            "manutenção, comunicação ao contratante, com ou sem o cabeçalho da matriz de "
            "riscos — são o instrumento de alocação contratual de riscos entre as partes: "
            "responsabilidades contratuais, que o IPMP distingue expressamente da gestão "
            "operacional pela equipe de projeto tratada aqui. Não são a estratégia de "
            "resposta ao risco. O critério pede o plano de gestão de riscos da equipe do "
            "projeto, aprofundado a "
            "partir da alternativa escolhida: para cada risco identificado, a resposta "
            "escolhida (evitar, mitigar, transferir ou aceitar) e as ações específicas de "
            "gerenciamento que a concretizam — o que a equipe fará, quando e com que meio, "
            "para reduzir a probabilidade ou o impacto durante a execução. Ações cujo "
            "executor é a outra parte por força do contrato descrevem obrigações dela, não "
            "a resposta da equipe; transferir um risco à contratada ou a uma seguradora por "
            "cláusula só conta quando apresentado como escolha de resposta no próprio "
            "plano, ao lado das demais ações de gerenciamento. O texto que motiva a própria "
            "contratação — por que licitar, por que agora, o que se perderia sem ela — "
            "também não é o plano: não registra um risco identificado, não escolhe entre "
            "evitar, mitigar, transferir ou aceitar e não designa ação de gerenciamento da "
            "equipe."
        ),
    },
    "35.2f": {
        "acao": 35,
        "direcao": "rejeicao",
        # a linha "Anulação … Monitoramento rotineiro e periódico" da matriz, em
        # três cópias (`_1` p.198, `_2` p.20, `_2` p.497), e a página seguinte.
        "alvos": [("_1", 198), ("_2", 20), ("_2", 497), ("_1", 199)],
        "resumo": "monitoramento/fiscalização rotineira citada como mitigação numa linha da matriz de riscos ou numa obrigação contratual não é o acompanhamento contínuo com revisão periódica e atualização das estratégias.",
        "ipmp": ("Produto 35.2f: 'Acompanhamento contínuo, com revisão periódica e "
                 "atualização das estratégias de mitigação'. Exemplo Atendido: 'fixou "
                 "periodicidade de revisão e manteve vínculo explícito com os benefícios "
                 "mapeados'. Exemplo Parcialmente Atendido: o plano 'não explicitou "
                 "formalmente os responsáveis por cada ação nem apresentou rotina de "
                 "atualização periódica'. Exceção: a gestão operacional inclui 'monitoramento "
                 "contínuo e estratégias de resposta pela equipe de projeto'."),
        # 1ª rodada: p.198 e `_2` p.20 TTTTT->FFFFF; `_2` p.126 (linhas de matriz com
        # "acompanhamento periódico da situação financeira") seguiu TTTTT, e o reasoning
        # armazenado julga o chunk pelo critério de 35.2e ("strategy of response") — a
        # confusão de produto-alvo medida em 2026-10-07. 2ª rodada nomeia o acompanhamento
        # periódico como mitigação e diz, como conteúdo, que a estratégia de resposta é
        # outro produto.
        "negativo": (
            "A menção, numa linha da matriz de riscos do contrato ou numa cláusula de "
            "obrigação da contratada, a monitoramento rotineiro, acompanhamento periódico "
            "ou fiscalização da execução contratual como ação de mitigação de um risco "
            "atribuído a uma das partes é parte do instrumento de alocação contratual de "
            "riscos, não o acompanhamento contínuo pedido aqui. Este critério também não é "
            "a estratégia de resposta ao risco (evitar, mitigar, transferir, aceitar), que "
            "é outro produto: uma lista de ações de mitigação, por si, não o atende. O "
            "critério exige que o plano de gestão de riscos, "
            "aprofundado a partir da alternativa escolhida, preveja como a equipe do projeto "
            "acompanhará os riscos ao longo da execução: periodicidade de revisão do "
            "registro de riscos, responsável por essa revisão e atualização das estratégias "
            "de mitigação quando os riscos mudarem. Uma obrigação genérica de acompanhar a "
            "contratação ou de prestar informações a órgãos de controle não descreve rotina "
            "de revisão do plano de riscos nem atualização de suas estratégias."
        ),
    },
    # 1/6 aceites em produção (d1), classe "obrigações permanentes da contratada";
    # medido como os outros, aplicado só se inofensivo (defeito visto em produção).
    "33b": {
        "acao": 33,
        "direcao": "rejeicao",
        "olhar": True,
        "alvos": [("_1", 83)],
        "resumo": "cláusulas de obrigações permanentes da contratada (danos, legislação trabalhista, conservação de bens, comunicar o contratante) não são plano de engajamento das partes interessadas.",
        "ipmp": ("Produto 33b: 'Forma como essas partes serão envolvidas e comunicadas ao "
                 "longo do ciclo de vida do projeto ... métodos de comunicação (reuniões, "
                 "consultas), frequência, prazos, principais tópicos a serem discutidos, "
                 "responsabilidades por cada ação'. O que esperar: 'identifique e envolva os "
                 "grupos impactados pelo projeto'. Exceção: 'povos originários, comunidades "
                 "quilombolas, famílias a serem reassentadas, proprietários de imóveis a "
                 "serem desapropriados'."),
        "negativo": (
            "Cláusulas que enumeram obrigações permanentes da contratada — responder por "
            "danos a usuários e terceiros, cumprir a legislação trabalhista e de segurança "
            "do trabalho, conservar e reparar os bens do serviço, comunicar ocorrências ao contratante "
            "— são obrigações contratuais de execução, não o plano de engajamento das partes "
            "interessadas. O critério pede, para cada grupo impactado pelo projeto "
            "(comunidades, famílias, proprietários, órgãos), a forma de envolvimento e "
            "comunicação ao longo do ciclo de vida: método, frequência, prazos, tópicos e "
            "responsáveis. Uma obrigação de comunicar o contratante ou de responder perante "
            "terceiros não identifica grupo impactado nem descreve ação de engajamento com "
            "ele."
        ),
    },
}
