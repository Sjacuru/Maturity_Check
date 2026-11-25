"""Variante G do prompt do gate: o lugar do gate no processo (2026-10-13).

Pergunta do usuário (mensagem N): "o gate sabe quem é o scorer? Se não tiver
contexto no prompt como ele vai saber julgar isso?". Na mensagem seguinte: o
papel do gate está definido, falta posicionamento — "você é ..., a etapa que
você trata é ..., sua função é ..., para que a etapa final julgue
adequadamente".

O que os raciocínios gravados mostram (ciclo 3, 4 970 vereditos em dez processos;
réplica no ciclo 4 sem 23.3 e 32a; leitor argumentos_rejeicao.py da sessão):

  * A única pista de posição do prompt atual é a cláusula "julgar o cumprimento
    é da etapa seguinte, não deste classificador" (ADR-0066). Ela aparece em 3
    raciocínios (0,1 %). A regra de polaridade aparece em 4 %.
  * Nas rejeições dos pares que oscilam entre processos (as moedas que mexem nos
    pontos), o argumento costuma ser de suficiência, muito mais que nas rejeições
    estáveis:

      argumento                                  moedas   rejeições estáveis
      não basta (falta detalhe, completude)      30,5 %   6,9 %
      ausência lida como falta de evidência       7,4 %   0,8 %
      "só menciona"                              33,5 %   7,7 %
      "trata de outra coisa"                     19,7 %  25,8 %

    44 das 65 moedas têm ao menos uma rejeição por completude ou ausência.
  * Exemplo: 23.2 `_2` p.231 foi rejeitado porque "não mostra linguagem clara,
    compatibilidade, matriz de risco, critérios", isto é, um trecho cobrado pela
    lista inteira do produto.

  Leitura: nas rejeições estáveis, o gate faz o trabalho dele (o trecho é sobre
  outra coisa). Nas moedas, faz o do scorer (o trecho basta?).

Duas causas no texto do prompt, além da falta de posição:
  1. O critério que o gate lê foi escrito para o cumprimento: descreve o produto
     completo e é apresentado como "evidência válida".
  2. A frase de abertura dá um título ("classificador de relevância") sem dizer
     o que vem antes, o que vem depois e o que cada erro custa.

A variante troca duas coisas no prompt de sistema, e nada mais:
  1. A frase de abertura vira uma seção que diz:
     - onde o gate está entre a busca e a etapa final;
     - o que acontece com um trecho rejeitado e com um aceito por engano;
     - qual é a pergunta do gate, e qual não é.
  2. O título do critério passa a dizer que o critério descreve o produto
     completo que a etapa final vai exigir do conjunto, e que aqui basta o
     trecho tratar de uma parte dele.

Não mudam: o critério, o bloco de identidade (ADR-0064/0071), os padrões
negativos, a regra de polaridade (ADR-0066) e o prompt de usuário.

Risco conhecido: mais aceites. A variante 'rotulado' deu +11 % (ADR-0071). Os
créditos falsos que restam são erros de assunto, não de suficiência:
  - 23.3 p.145, a outorga lida como regra de pagamento;
  - 32a p.303, o pessoal da operação lido como equipe do projeto;
  - 35.2e p.3, a justificativa da contratação.
Por isso a seção diz também o custo de deixar passar outro assunto.

Usada com os mesmos bytes por:
  - measure_gate_positioning.py: um processo; mede direção e inocuidade;
  - reproducibility.py --gate-variant posicionado: processos completos.

Direção de G, medida em 13/10/2026 (um processo, prompt de produção e G
intercalados, 3 passadas; scratchpad/acc/posicao_direcao.json):
  - aceites -4 %; argumentos de suficiência nas rejeições caem cerca de um quarto;
  - 13 movimentos certos (evidência parcial legítima passa; confusões saem);
  - 10 errados: 3 aceites legítimos perdidos e 7 aceites falsos novos. Os falsos:
      - trechos que só nomeiam o elemento ou dizem onde ele está (a lista de
        anexos do contrato com "MATRIZ DE RISCO", a capa do anexo do cronograma);
      - regras do edital sobre o que será feito, lidas como registro do que foi
        feito;
      - o elemento de outra Ação;
      - um fragmento do instrumento lido como "parte do conjunto".
  O prompt de produção rejeitava esses trechos com o argumento "faltam
  detalhes", certo pelo motivo errado. G tirou o motivo errado sem dar o certo.

Variante G2 (14/10/2026): G mais o parágrafo NOMEAR, que dá o motivo certo com
marcas que o próprio trecho decide:
  - nomear o elemento ou dizer onde ele está não é tratar dele;
  - quando o critério pede o registro de algo feito, uma regra sobre o que será
    feito não é esse registro.
O elemento de outra Ação não se resolve aqui, porque o gate só vê os irmãos da
mesma Ação. Para 18b, ele vai num padrão de produto (candidates_g2.py).
Usada por:
  - measure_gate_positioning.py --condicoes g,g2;
  - reproducibility.py --gate-variant posicionado2.

Medição de G2, 14/10/2026 (um processo, G e G2 intercalados, 3 passadas, os
mesmos pools; scratchpad/acc/posicao_g2_direcao.json; critério registrado antes
em scratchpad/acc/criterio_g2.txt). G2 não passa, e o ciclo 5 não foi lançado.
  - G2 aceita 26 % menos que G e perde dois aceites estáveis (aceitos nos 20
    processos dos ciclos 3 e 4). O gate lê NOMEAR como "mencionar não basta", e
    a suficiência volta ("It's a review document... not evidence").
  - "Regra não é registro" funcionou nas duas regras de 45.
  - "Lista de anexos" funcionou numa das duas páginas de 22.2 e foi ignorada na
    outra ("lists annexes including ANEXO V MATRIZ DE RISCO... So relevant").
  - O padrão de 18b foi ignorado: o alvo passou a ser aceito nas 3 passadas.

G contra G em dois processos (13/10 e 14/10):
  - o mesmo prompt muda a maioria em 27 dos 464 pares;
  - a "direção" base -> G de 13/10 tinha mudado 29, e G repete só 16 delas;
  - pelas frequências dos ciclos 3 e 4, dois processos do mesmo prompt diferem
    em cerca de 21 pares só por sorteio.
Os 13 acertos e os 10 erros de G eram, na maior parte, moedas tiradas de novo.
O que se repete é o agregado: argumentos só de suficiência nas rejeições,
8,5 % na base contra 6,4 % e 5,8 % em G.
Consequência: uma variante que muda os 164 prompts não se avalia par a par num
processo; só ciclos de processos completos a medem.

Ciclo 5, 14/10/2026: G em 10 processos completos do commit bbc3d50, ledger
desligado, filtro de gênero e expansão ligados (scratchpad/acc/ciclo5_run1..10;
critério registrado antes em scratchpad/acc/criterio_ciclo5.txt). Resultado:
sem ganho além do acaso; o critério recomenda descartar G.
  - Mesmos pontos em 9+ de 10: 40 Ações, contra 41 nos ciclos 3 e 4.
  - Idênticas nos dez: 35, contra 38 e 34.
  - Pares-moeda: 76, contra 65 e 70.
  - Aceitos por processo: 43,9, contra 39,4 e 38,7.
  - Rejeições só por suficiência: 6,8 %, contra 8,8 % e 9,3 %.
G muda o raciocínio como escrito, mas a massa limítrofe se desloca em vez de
encolher:
  - aceites constantes viram moeda (23.3 _2 p.145 de 10/10 para 3/10; 25d);
  - aceites falsos ficam modais (13c _1 p.3, regras do edital de 45, a lista
    de anexos _2 p.232 em 25a);
  - em 5 de 10 processos, um padrão negativo canônico é ignorado (3a _2 p.161).
Registrado no ADR-0071 ("Variant G across ten full processes").

Decisão do usuário, 14/10/2026: G descartada; a frase equivalente no scorer
(S) sai junto. Nada em src/ usa G. Este módulo e as opções posicionado e
posicionado2 de reproducibility.py ficam como registro do que foi tentado.
"""

from __future__ import annotations

# O que a variante substitui, exatamente como relevance_builder o produz hoje;
# posiciona() confere a presença, então uma mudança no builder aborta a medição
# em vez de medir outra coisa.
CABECALHO_ATUAL = (
    "Você é um classificador de relevância de evidências para auditoria de "
    "processos de Parceria Público-Privada (PPP), avaliados segundo o "
    "framework IPMP.\n\n"
)
TITULO_ATUAL = "## Critério de relevância para este Produto Esperado\n\n"

POSICAO = """\
## Seu lugar no processo

Você é a etapa de triagem de uma auditoria de processos de Parceria \
Público-Privada (PPP) segundo o framework IPMP. A auditoria tem três etapas, e \
a triagem é a segunda:
1. A busca reúne, para cada Produto Esperado, trechos dos documentos do \
processo parecidos com o critério, por palavras ou por sentido. Muitos tratam \
de outro assunto.
2. Você recebe um trecho por vez e decide se ele trata do elemento descrito no \
critério deste Produto Esperado.
3. A etapa final lê juntos todos os trechos que você deixou passar, de todos os \
Produtos Esperados da Ação, e decide produto a produto se o critério foi \
atendido. Um auditor revisa essa decisão vendo os mesmos trechos.

Um trecho que você rejeita não chega à etapa final nem ao auditor: se ele \
tratava do elemento, a informação se perde. Um trecho que você deixa passar \
sobre outro assunto pode levar a etapa final a erro. Por isso, não pergunte se \
o trecho basta para atender o critério: um trecho sozinho raramente traz tudo, \
e juntar os trechos é tarefa da etapa final. Pergunte se ele trata do elemento \
descrito — por inteiro, em parte, ou registrando que ele falta ou não se \
aplica. Se ele trata de outro elemento, de outro Produto Esperado, de outra \
das partes envolvidas (por exemplo, a contratada no lugar do órgão \
responsável, ou o contrário) ou de outra etapa do projeto, ele não passa, \
mesmo que use as mesmas palavras.

"""

TITULO_NOVO = """\
## O que a etapa final vai procurar neste Produto Esperado

O critério abaixo descreve o produto completo, como a etapa final vai exigi-lo \
do conjunto dos trechos; aqui, basta que o trecho trate de uma parte dele.

"""

# G2: o motivo certo para o que o argumento "faltam detalhes" rejeitava por
# acaso (medição de direção de G, 13/10/2026; ver o docstring).
NOMEAR = """\
Nomear o elemento não é tratar dele. Um título, um sumário, uma lista de anexos \
ou a capa de um anexo só dizem que o elemento existe ou onde está, sem trazer o \
que ele contém: não passam. Quando o critério pede o registro de algo que foi \
feito, uma regra que diz o que será feito não é esse registro: também não passa.
"""

POSICAO_G2 = POSICAO.rstrip("\n") + "\n\n" + NOMEAR + "\n"


def posiciona(system: str, versao: str = "g") -> str:
    """O prompt de sistema de produção com a seção de posição e o título novo.

    versao "g": a variante G; "g2": G com o parágrafo NOMEAR no fim da seção.
    """
    assert versao in ("g", "g2"), versao
    assert system.startswith(CABECALHO_ATUAL), "abertura do prompt mudou no builder"
    assert system.count(TITULO_ATUAL) == 1, "título do critério mudou no builder"
    posicao = POSICAO if versao == "g" else POSICAO_G2
    return (posicao + system[len(CABECALHO_ATUAL):]).replace(TITULO_ATUAL, TITULO_NOVO, 1)
