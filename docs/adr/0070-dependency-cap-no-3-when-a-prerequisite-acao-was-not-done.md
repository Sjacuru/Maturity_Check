# Teto por dependência: uma Ação que cita um pré-requisito não feito não recebe 3

Decidido em 2026-10-09 a partir de uma regra do usuário: *"Ações que citam uma ou
mais ações nas quais tais ações não tiveram evidências ou não tiveram pontuação
maior que zero não podem receber pontuação 3, pois não há revisão ou confirmação
do que não foi feito."* A regra é aritmética sobre scores que já existem quando
a citante é avaliada — a corrida percorre as Ações em ordem 1→46 — e entra em
código **depois** do score contado (ADR-0058), nunca no prompt do scorer
(decisão 4 de 2026-10-05: nada é alimentado ao modelo).

## O que entra e o que não entra

O IPMP cita outras Ações 54 vezes em 46 Ações, mas com sentidos diferentes.
Cada citação foi lida e tipada em `data/ipmp/dependencias.json`, com a frase
que a justifica; só dois tipos têm efeito:

| tipo | arestas | efeito |
|---|---|---|
| `pre` — a citada é insumo da citante ("a partir da Ação 25", "para cada opção da Ação 6") | 18 | **teto**: citante contada 3 com alguma citada em 0 / sem evidência → score 1, `score_before_cap = 3` |
| `artefato` — a citante é a versão posterior do MESMO documento (11→29, 12→31, 13→33/34, 14+15→35, 1–4→39, Gerencial→44) | 19 | **revisão sugerida**, nunca teto |
| `fraco` ("recomenda-se partir de…"), `sucessora`, `contraste`, `delega`, `sequencia`, `lacuna` | 17 | nenhum |

Decisões que a tipagem fixa, com a razão de cada uma:

- **`fraco` não entra** (usuário, 2026-10-09): "recomenda-se" não é um
  pré-requisito.
- **`artefato` vira revisão, não teto** (usuário, 2026-10-09). O corpus não tem
  eixo de tempo: o documento final de uma concessão evidencia a versão inicial
  e a final do mesmo plano ao mesmo tempo, então "citada vazia + citante cheia"
  não é um estado do processo, é o gate aplicando um teste de estágio à versão
  inicial ou aceitando um falso positivo na final. Isso é matéria de auditoria,
  não de pontuação. Onde o IPMP separa explicitamente os planos (Ação 35:
  35.1 = benefícios da Ação 14, 35.2a–g = riscos da Ação 15) a aresta é escopada
  por produto (`produtos_citante`): sem o escopo o sinal disparou em 13/13
  corridas deste caso com 35.1 nunca evidenciado — a evidência da 35 era
  35.2e/35.2f. O teto não precisa de escopo: só engata com score contado 3,
  isto é, todos os produtos evidenciados.
- **A Ação 43 é isenta** (`lacuna`): o próprio exemplo *Atendido* do IPMP para a
  43 tem a Ação 28 *não realizada* e a 43 realizando-a pela primeira vez, e o
  resultado é "atendimento pleno". Aplicar o teto ali contradiria o IPMP.
- **39 e 44 não citam por número**; as dependências vêm do produto ("documento
  original devidamente atualizado") e da dimensão — `artefato` sobre 1–4 e
  sobre as Ações Gerenciais 16/29–36.
- **Dependência desconhecida não engata** (citada não avaliada, falha de
  parsing, corrida parcial): o teto só fala de uma citada conhecidamente baixa.
- **O carregador recusa** aresta `pre`/`artefato` apontando para a frente, aresta
  duplicada, auto-referência e escopo de produto fora da citante: uma regra
  silenciosamente inerte é pior do que um arquivo recusado.

## Base do teto: score proposto, sem cascata do ReviewOutcome

O usuário pediu as duas bases medidas — o teto lendo o score **proposto** da
citada ou o **final** após ReviewOutcome — "medir consequências e risco de
acréscimo excessivo". Medido localmente sobre as 13 corridas reais do caso
SMG-040 (3 limpas + 10 de aceitação), `scratchpad/acc/teto_ambos.txt`:

- **Base proposta**: o teto engata em **1/13 corridas**, sempre na Ação 3
  (3→2 `pre`, quando a Ação 2 oscila para 0). Nenhuma outra citante contada 3
  tem citada baixa neste caso.
- **Base final (cascata)**: uma única revisão da Ação 2 para cima liberaria a 3
  (+2 pontos) na corrida em que o teto engatou; uma revisão da Ação 2 para
  *baixo* engataria a 3 em 12/13 corridas, e da 25 a 37 em 4/13. Pelo grafo, a
  Ação 2 é citada por 3 e 17 (`pre`) e 39 (`artefato`): uma revisão move até
  4 pontos em duas Ações que o auditor daquelas Ações não revisou; 6, 7 e 20
  têm leque 2; 3, 6, 18 e 20 são citantes e citadas ao mesmo tempo. O teto em
  si nunca cascateia (o mínimo é 1, que é "ok" para quem cita); só uma revisão
  a 0 / sem evidência cascatearia — e só na base final.

Decisão: **base proposta**. O score proposto de uma Ação é imutável depois de
persistido (ADR-0026 substitui por re-execução, não edita), e o único ponto de
intervenção humano é o ReviewOutcome da própria Ação ("nada de atuação após o
gate"). A cascata faria um ReviewOutcome alterar scores de Ações que o auditor
não abriu — exatamente o acréscimo excessivo que a medição quantifica. O
auditor da citante vê o teto, o score contado e os vereditos por produto, e
decide com isso à vista; se a citada for revisada depois, o painel da citante
diz que o teto não muda sozinho.

## Consequências

- `EvaluationResult.dependency_cap` (`DependencyCap`: `applied`,
  `score_before_cap`, `review_recommended`, `dependencies[]`, `explanation`),
  com default `None` — linhas persistidas antes continuam servidas sem migração
  (ADR-0031). `proposed_score` passa a ser o score **após** o teto; o contado
  fica em `score_before_cap` e nos `product_verdicts`, intactos.
- O intervalo do ADR-0068 é recortado no teto (`score_floor`/`score_ceiling`
  ≤ 1); margem de faixa e produtos frágeis não mudam — continuam fatos sobre a
  evidência. Não se estende o intervalo para "mostrar" o teto: sem decisão
  sobre o comportamento e sem onde exibir, seria cosmético (usuário,
  2026-10-09).
- `evaluate(..., prior_results=)` recebe as Ações já avaliadas na corrida;
  `AssessmentService` e `reproducibility.py` passam-nas, então a medição
  reproduz a produção. Sem `prior_results` (scripts que avaliam uma Ação
  isolada) não há teto nem alegação sobre dependências.
- A mesma entrada dá o mesmo teto: nenhuma chamada de modelo, custo zero,
  reprodutibilidade intacta. O prompt do scorer é byte-idêntico com e sem
  `prior_results` (teste).
- O efeito neste caso é pequeno (1/13 corridas) porque quase todas as citantes
  contadas 3 têm citadas ≥ 1 — a regra existe para o próximo caso, não para
  este. A alternativa de inserir o prompt da citada no gate (opção 1.4-a) foi
  descartada antes de medir: o gate julga relevância de trecho, não
  encadeamento de Ações, e a varredura do ledger mostrou o gate engajando
  referências cruzadas em 1,4 % dos vereditos sem nenhum aceite — o lugar da
  regra é o score, não o prompt.
