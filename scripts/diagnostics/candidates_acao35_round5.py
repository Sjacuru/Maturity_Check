"""Ação 35, quinta rodada (2026-10-10): só os dois chunks que ainda sustentam o
score 1 da Ação 35 entre processos independentes depois do bloco A (ADR-0072).

  35.2e  _2 p.776   linhas de matriz de riscos do contrato: danos a bens
                    (CONCESSIONÁRIA) e vício/defeito de bens (COMPARTILHADO),
                    com seguros, inspeção, relatório técnico, reuniões
  35.2f  _2 p.126   linhas de matriz de riscos do contrato: suspensão de
                    atividades (CONCESSIONÁRIA), falência e anulação
                    (COMPARTILHADO), com vistoria e acompanhamento periódico

Dentro do processo do harness os dois já são FFFFF sob o texto aplicado; entre
processos são moeda (A+B+C: p.776 TTF, p.126 TFT). A leitura dos dois chunks
aponta a lacuna de redação: os padrões aplicados falam de risco "atribuído a
uma das partes", e as linhas que o gate aceita às vezes são justamente as de
risco atribuído às DUAS partes — o risco compartilhado, cujas ações cabem em
parte ao contratante e a quem fiscaliza o contrato, o que se parece com a
resposta da própria equipe. Esta rodada fecha a lacuna com um marcador
verificável (cada risco vem com a parte que o assume?), em vocabulário do IPMP:
"risco compartilhado" e "contratante/contratada" são do produto 15e; a
separação entre responsabilidades contratuais e gestão operacional é a exceção
da própria Ação 35.

Medição: em processo (measure_integral_candidates.py, direção e inocuidade:
controles) e entre processos independentes (reproducibility.py --runs 1
--acoes 35 --candidates ... --apply 35.2e,35.2f, intercalado com a condição
atual) — a única medida de constância válida (ADR-0071). Depois desta rodada
não há sexta: o que restar fica com o sinal de revisão opcional do ADR-0068
(decisão do usuário, 2026-10-10).

Resultado (2026-10-10). Em processo: 35.2f `_2` p.126 FTTTT -> FFFFF com 12/12
controles inalterados; 35.2e `_2` p.776 FTTTT -> TTTTT (reprovada, não aplicada).
Entre processos (5 pares intercalados, --acoes 35, ledger off): pools idênticos
nos 10 processos; p.126 TFTTT -> FFFFF -> 35.2f aplicada (padrão negativo #3).
Ação 35: 1,1,1,1,1 -> 0,1,0,1,1 — o 1 constante era crédito falso sustentado por
moedas; a leva já variava em 4 de 5 processos nos dois braços (ADR-0072).

35.2e entre processos, a pedido do usuário (2026-10-10, tarde; a35e_cur/cand
1..5): p.776 aceita em 7 de 10 processos atuais e em 1 de 5 com o candidato
(direção confirmada, ao contrário da medição em processo), mas o desfecho da
Ação 35 ficou menos constante (mudanças contra a moda 1/5 -> 3/5; pares com o
mesmo score 60 % -> 20 %; leva e vereditos sem mudança). Não adotada pela regra
do usuário do mesmo dia: adotar apenas o que deixa o sistema mais consistente.
"""

_IPMP_35 = ("Produto 35.2: 'Documento completo que atualize e aprofunde o plano de "
            "gestão de riscos da Ação 15, alinhando-o à alternativa escolhida'. Exceção: "
            "'a primeira [Ação 22] trata das responsabilidades contratuais entre as partes, "
            "enquanto a segunda [Ação 35] foca a gestão operacional, incluindo monitoramento "
            "contínuo e estratégias de resposta pela equipe de projeto'. Produto 15e: "
            "'Delimitação simples dos riscos da contratante, da contratada e o risco "
            "compartilhado'.")

CANDIDATOS: dict[str, dict] = {
    "35.2e": {
        "acao": 35,
        "direcao": "rejeicao",
        "alvos": [("_2", 776)],
        "resumo": "linha de risco compartilhado numa matriz de riscos do contrato é alocação contratual, não a estratégia de resposta da equipe.",
        "ipmp": "Produto 35.2e: 'Estratégia de resposta (evitar, mitigar, transferir, aceitar) com ações específicas de gerenciamento'. " + _IPMP_35,
        "negativo": (
            "Linha de matriz de riscos que atribui o risco às duas partes — o risco "
            "compartilhado — continua sendo alocação contratual, mesmo quando as ações "
            "listadas cabem ao contratante ou a quem fiscaliza o contrato. Verifique no "
            "texto: cada risco aparece acompanhado da parte que o assume (contratada, "
            "contratante ou ambas)? Se sim, é o instrumento que reparte os riscos entre as "
            "partes — as responsabilidades contratuais que o IPMP separa desta Ação —, não "
            "a estratégia de resposta que a equipe do projeto escolheu (evitar, mitigar, "
            "transferir, aceitar) no plano de gestão de riscos."
        ),
    },
    "35.2f": {
        "acao": 35,
        "direcao": "rejeicao",
        "alvos": [("_2", 126)],
        "resumo": "linha de risco compartilhado numa matriz de riscos do contrato, com acompanhamento a cargo do contratante, é alocação contratual, não o acompanhamento contínuo do plano pela equipe.",
        "ipmp": "Produto 35.2f: 'Acompanhamento contínuo, com revisão periódica e atualização das estratégias de mitigação'. " + _IPMP_35,
        "negativo": (
            "Linha de matriz de riscos que atribui o risco às duas partes — o risco "
            "compartilhado — continua sendo alocação contratual, mesmo quando a ação listada "
            "é acompanhar, monitorar ou fiscalizar, a cargo do contratante ou de quem "
            "fiscaliza o contrato. Verifique no texto: cada risco aparece acompanhado da "
            "parte que o assume (contratada, contratante ou ambas)? Se sim, é o instrumento "
            "que reparte os riscos entre as partes, não o acompanhamento contínuo do plano "
            "de gestão de riscos pela equipe do projeto, com revisão periódica e atualização "
            "das estratégias de mitigação."
        ),
    },
}
