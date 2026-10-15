"""Resíduo do ciclo de testes 3 (ADR-0074, 2026-10-13): os dois créditos falsos
constantes que sobraram depois do filtro de gênero.

  23.3  _2 p.145   item de parecer sobre o critério de julgamento de uma
                   concessão sem tarifa paga pelo poder público: o excedente do
                   projeto reverte ao Poder Concedente pelo pagamento de outorga.
                   O gate lê a divisão desse pagamento como "regra de pagamento
                   ligada à execução": aceito em 10 de 10 processos do ciclo 3.
                   23.3 é isento (lê texto de instrumento), e é esse aceite
                   constante que deixa a moeda de 23.2 levar a Ação 23 a 3.
  32a   _1 p.303   quadro de despesa com o pessoal operacional da concessão
                   (salários, encargos, benefícios por função). O gate lê como
                   "custo da equipe": aceito em 10 de 10.

Os padrões nomeiam a classe, não a página, e trazem um marcador verificável no
próprio texto (quem paga a quem; de quem é a equipe), em vocabulário do IPMP da
própria Ação e da legislação em que ele se apoia (Lei 8.987/1995, art. 15: a
maior oferta pelo pagamento ao poder concedente da outorga como critério de
julgamento). Nenhum nome, página ou frase do caso (ADR-0073).

O que o padrão de 23.3 leva junto (medido no ciclo 3, sem GPU): `_2` p.144 — a
resposta que registra que o termo de referência não traz critérios de medição e
de pagamento porque, numa concessão, o poder público não paga o contratado — não
está no pool de 23.3; ela só chega como vizinha do p.145, aceita em 8 de 10
processos. Pela regra de polaridade do ADR-0066 ela trata do que o critério
pede. Se o p.145 sair, o p.144 sai da leva junto, e 23.3 fica sem evidência: o
desfecho correto do produto neste caso, mas sem o trecho que explica por quê. O
`_1` p.60 (cláusula do edital sobre o pagamento da parcela de outorga, aceita em
1 de 10) é da mesma classe do p.145 e entra como alvo.

Medição (regra do usuário: adotar só o que não reduz a constância):
  1. em processo: measure_integral_candidates.py --candidates este arquivo,
     5 passadas, pool de produção (com o filtro de gênero) — direção e
     inocuidade nos controles;
  2. dez processos completos independentes: reproducibility.py --runs 1
     --record-reasoning --candidates este arquivo --apply 23.3,32a, ledger fora,
     comparados com o ciclo 3 (ADR-0071: constância só entre processos completos).

Resultado (2026-10-13; ADR-0074, seção Test cycle 4): NENHUM DOS DOIS ESCRITO.
  1. em processo: p.145 e p.303 passaram de aceitos a rejeitados nas cinco
     passadas, sem mudança nos controles.
  2. dez processos completos: o p.145 foi aceito em 4 de 10 (era 10 de 10) e o
     p.303 em 3 de 10 (era 10 de 10). Os dois viraram moedas, não rejeições.
  3. Ação 32: de 1 para 3 mudanças (inconsistente).
  4. Ação 23: de 3 para 1 mudança, porque um 3 agora exige duas moedas juntas
     (23.2 e 23.3). Em compensação, o bit de 23.3 virou moeda, e o vizinho
     p.144 passou de aceito em 8 de 10 processos, pela regra de polaridade do
     ADR-0066, a rejeitado nas 4 vezes em que foi julgado.
  5. Causa, no raciocínio do gate: nos aceites do p.145 o gate não consulta o
     marcador; no p.303 o marcador não é decidível pelo texto, porque o trecho
     não diz quem é o empregador.
"""

_IPMP_23 = ("Produto 23.3: 'Regras de pagamento proporcionais à execução e entregas do "
            "projeto'. Descrição: 'critérios de pagamento proporcionais às etapas e "
            "entregas'. Por que importa: 'os critérios de medição, as entregas esperadas, "
            "os indicadores de desempenho e as formas de pagamento'. Exemplo Atendido: "
            "'condições de pagamento compatíveis com as entregas previstas'.")

_IPMP_32 = ("Produto 32a: 'Composição da equipe e estrutura de governança', no 'orçamento "
            "de suporte para as despesas correntes do projeto'. Descrição: 'designação da "
            "equipe do projeto'. Por que importa: 'Além do orçamento da obra em si, é "
            "necessário prever e organizar os recursos de suporte à gestão do projeto'. "
            "Exceção: 'verificar se as condições do órgão estão suficientes para o "
            "adequado andamento e monitoramento das obras'.")

CANDIDATOS: dict[str, dict] = {
    "23.3": {
        "acao": 23,
        "direcao": "rejeicao",
        "alvos": [("_2", 145), ("_1", 60)],
        "resumo": "valor que a contratada ou concessionária paga ao poder público (outorga, maior oferta) não é regra de pagamento à contratada.",
        "ipmp": _IPMP_23,
        "negativo": (
            "Valor devido ao poder público pela contratada ou concessionária — a outorga, "
            "ou o critério de julgamento pela maior oferta por ela — não é regra de "
            "pagamento proporcional à execução. O critério pede como e quando o contratante "
            "paga o contratado, em proporção às etapas executadas e às entregas. Verifique "
            "no texto: quem paga e quem recebe? Se quem paga é a contratada ou "
            "concessionária e quem recebe é o poder público, o trecho não trata deste "
            "critério, mesmo que fixe valores, parcelas ou prazos para esse pagamento."
        ),
    },
    "32a": {
        "acao": 32,
        "direcao": "rejeicao",
        "alvos": [("_1", 303)],
        "resumo": "custo de pessoal da contratada ou concessionária não é o custo da equipe do projeto do órgão.",
        "ipmp": _IPMP_32,
        "negativo": (
            "Custo de pessoal da contratada ou concessionária — salários, encargos e "
            "benefícios da equipe que vai executar, operar ou manter o objeto, previstos no "
            "modelo financeiro da contratação — não é o custo da equipe do projeto. O "
            "critério pede o custo da equipe do órgão responsável que vai gerir e "
            "fiscalizar o projeto e da sua estrutura de governança, como despesa de suporte "
            "da gestão pública. Verifique no texto: de quem é a equipe? Se é a equipe da "
            "contratada ou concessionária, não conta."
        ),
    },
}
