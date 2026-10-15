"""Ciclo 6 (2026-10-14): três candidatos para o resíduo da linha de base 5be6d44,
depois do descarte de G. Abaixo de 9 de 10 nos ciclos 3 e 4: Ações 10, 23, 35,
37 e 45.

Leitura por processo dos ciclos 3, 4 e 5 (scratchpad/acc/ciclo{3,4,5}_run*.json):
  23  O 3 só sai quando 23.2 e 23.3 são evidenciados no mesmo processo. 23.1 é
      evidenciado nos 30 processos. 23.3 depende de um trecho, `_2` p.145, aceito
      em 10 de 10 no ciclo 3. Se 23.3 não for evidenciado, a Ação fica em 1. Uma
      redução parcial já ajuda, porque o 3 exige as duas moedas juntas.
  35  O único trecho aceito nos 30 processos é `_1` p.3 (35.2e), a justificativa
      da contratação: 6 de 20 nos ciclos 3 e 4. O desfecho modal já é sem
      evidência, então qualquer redução ajuda.
  45  O único trecho que sustenta o 3 é `_2` p.23 (15 de 20): o preâmbulo da
      minuta do contrato, com campo a preencher ("Edital [•]"). Ele narra a
      licitação, a homologação e a adjudicação como fatos passados, mas é texto
      modelo, escrito antes do certame; o último ato do processo é o despacho
      que manda publicar o edital. O 3 é crédito falso. Depois do ciclo 3 a 45
      ficou como resíduo documentado porque o trecho foi lido como alvo
      legítimo; essa leitura estava errada.
  10  O scorer muda de veredito sobre a mesma leva (10a: `_2` p.763 e p.764), 10
      de 20. Não há alavanca no gate.
  37  Seis páginas-moeda, e o scorer dá 3 ou 0 conforme a leva. Nenhuma mudança
      única resolve.

Candidatos:
  23.3  A segunda rodada do padrão do ciclo 4 (rascunho de 13/10), com um
        marcador que o próprio texto decide: quem recebe o valor é o poder
        público? O p.145 diz "em favor do Poder Concedente através do pagamento
        de outorga". Nos aceites dos ciclos 3 e 4 o gate leu "pagamento em dois
        momentos, durante a execução" como regra ligada à execução; o padrão diz
        "seja qual for o cronograma desse pagamento". Leva junto o `_2` p.144,
        que só chega a 23.3 como vizinho do p.145 (regra de polaridade do
        ADR-0066): 23.3 fica sem evidência, sem o trecho que explica por quê.
  35.2e Um segundo padrão, curto, com um marcador que o trecho decide: a ação
        apresentada como estratégia é contratar o próprio objeto? O
        padrão atual já nomeia a classe, mas afirma que a justificativa "não
        escolhe entre evitar, mitigar, transferir ou aceitar", e o p.3 diz "a
        melhor estratégia para evitar". O gate casa "evitar" mais uma ação e
        aceita. O novo padrão ressalva o seguro contratado para transferir um
        risco identificado, que é uma resposta legítima.
  45    Sem texto novo: o produto sai da lista de isenção do filtro de gênero
        (ADR-0074), só em memória. O registro da realização do certame está nos
        atos (ata, resultado, homologação, adjudicação, publicação no Diário
        Oficial), como no exemplo Atendido do IPMP, e os atos têm gênero OUTRO;
        o contrato só os menciona. Sem a isenção, o pool examinado passa de 16
        trechos de instrumento (minuta, regras do edital, matriz) para 2 páginas
        do ETP (`_2` p.157 e p.158), nunca julgadas para 45. A mudança contraria
        a lista de isenção que o usuário confirmou em 12/10: medir não é adotar.

Medição:
  1. Em um processo: measure_integral_candidates.py --sibling-text integral
     --candidates este arquivo, 5 passadas. Mede direção e inocuidade.
  2. Dez processos completos: reproducibility.py --runs 1 --record-reasoning
     --candidates este arquivo --apply 23.3,35.2e,45, ledger fora, comparados com
     os ciclos 3 e 4.
A regra de leitura é registrada antes do lançamento, em
scratchpad/acc/criterio_ciclo6.txt.

Medição de direção, 14/10/2026 (um processo, 5 passadas, 0 erros;
scratchpad/acc/ciclo6_direcao.{json,log}):
  23.3  Não passa. A base deste processo rejeitou o p.145 nas 5 passadas, e o
        padrão fez o gate aceitá-lo nas 5. O raciocínio não consulta o marcador
        ("payment of outorga before and during execution after grace period.
        That is payment schedule tied to execution"). O p.60 foi na direção
        certa (TTTTT -> FFFFF, "It's about payment of outorga"). Os 13 controles
        não mudaram. Como no ciclo 4, o p.145 é um limítrofe que vira com
        qualquer byte do prompt, e o marcador não é lido nele.
  35.2e Entra pela letra da regra: o p.3 foi aceito em 4 de 5 com e sem o
        padrão. A passada que rejeita usa o motivo do padrão; as 4 que aceitam
        leem "evitar" mais "nova licitação" como resposta a risco, sem consultá-lo.
  45    Passa. Os 2 trechos do pool novo foram rejeitados nas 5 passadas pelo
        motivo certo (não há sessão, ata, homologação, adjudicação ou
        publicação).
O ciclo 6 roda com --apply 35.2e,45.

Ciclo 6, 14/10/2026: dez processos completos, 15:18 a 17:46, 0 erros e 0
falhas do gate (scratchpad/acc/ciclo6_run1..10).
  Mesmos pontos em 9 ou mais de 10: 42 Ações (ciclos 3 e 4: 41). O
  bloco-réplica (Ações 1 a 34) ficou em 32 nos três ciclos. Abaixo de 9:
  10, 23, 35 e 37.
  35.2e Não gravar. O p.3 foi aceito em 8 de 10 (ciclo 3: 5 de 10, mesmo
        prompt até 35.2e). Os raciocínios que aceitam não consultam o
        marcador; os 2 que rejeitam usam o motivo do padrão.
  45    0 pontos em 10 de 10, nenhum trecho aceito. A regra recomenda tirar
        45 da lista de isenção; a decisão é do usuário. O 3 do ciclo 3 vinha
        do considerando da minuta (_2 p.23, "conforme o Edital [•]"), um
        modelo e não um registro: os documentos do caso param na publicação
        do edital.
Registrado no ADR-0074 ("Test cycle 6").
"""

_IPMP_23 = ("Produto 23.3: 'Regras de pagamento proporcionais à execução e entregas do "
            "projeto'.")
_IPMP_35 = ("Produto 35.2e: 'Estratégia de resposta (evitar, mitigar, transferir, aceitar) "
            "com ações específicas de gerenciamento', no 'Documento completo que atualize e "
            "aprofunde o plano de gestão de riscos da Ação 15, alinhando-o à alternativa "
            "escolhida'.")
_IPMP_45 = ("Produto 45: 'Registro da realização do processo licitatório, nos termos da "
            "legislação aplicável'. Exemplo Atendido: sessão pública com registro em ata, "
            "resultado publicado, homologação e adjudicação, atos divulgados no Diário Oficial "
            "e juntados ao processo.")

CANDIDATOS: dict[str, dict] = {
    "23.3": {
        "acao": 23,
        "direcao": "rejeicao",
        "alvos": [("_2", 145), ("_1", 60)],
        "ipmp": _IPMP_23,
        "resumo": "a outorga devida ao poder concedente nunca é regra de pagamento à contratada, em nenhuma forma ou momento.",
        "negativo": (
            "Valor devido ao poder público pela contratada ou concessionária, como a "
            "outorga, não é regra de pagamento proporcional à execução, em nenhuma forma ou "
            "momento: à vista ou parcelado, no início ou ao longo do contrato. O critério "
            "pede como e quando o contratante paga o contratado, em proporção às etapas "
            "executadas e às entregas. Verifique no texto: quem recebe o valor descrito é o "
            "poder público? Se for, o trecho não trata deste critério, seja qual for o "
            "cronograma desse pagamento."
        ),
    },
    "35.2e": {
        "acao": 35,
        "direcao": "rejeicao",
        "alvos": [("_1", 3)],
        "ipmp": _IPMP_35,
        "resumo": "a justificativa de contratar o próprio objeto não é estratégia de resposta a risco, mesmo chamada de estratégia para evitar um problema.",
        "negativo": (
            "O texto que justifica contratar o próprio objeto não é estratégia de resposta "
            "a risco, mesmo quando chama a contratação de estratégia e diz que ela evita um "
            "problema. Verifique no texto: a ação apresentada como estratégia é "
            "contratar ou licitar o próprio objeto, ou fazê-lo antes de um prazo? Se for, o "
            "trecho explica por que contratar e não trata deste critério. A estratégia que "
            "o critério pede é escolhida no plano de gestão de riscos para cada risco da "
            "execução do projeto, com ações de gerenciamento da equipe durante essa "
            "execução; contratar um seguro para transferir um risco identificado é uma "
            "dessas escolhas."
        ),
    },
    "45": {
        "acao": 45,
        "direcao": "rejeicao",
        "alvos": [("_2", 23), ("_2", 223), ("_1", 55)],
        "ipmp": _IPMP_45,
        "resumo": "o registro da realização do certame está nos atos, de gênero OUTRO; sem a isenção, o texto de instrumento sai antes do gate.",
        "sem_isencao_genero": True,
    },
}
