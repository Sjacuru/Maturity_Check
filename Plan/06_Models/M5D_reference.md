# M5D — Referência das 46 Ações / Reference of 46 Actions

Fonte / Source: *Estruturação de Propostas de Investimento em Infraestrutura — Modelo de Cinco Dimensões (M5D)*, Ministério da Economia / BID / IPA-UK, 2022.

Este arquivo é a fonte de verdade estruturada para o mapeamento das Ações aos Estágios e Dimensões.
É usado como referência de validação pelo script `check_lancedb_chunks.py --coverage` e pelo dict `M5D_ACTION_METADATA` em `m5d_ingest.py`.

This file is the structured ground truth for mapping Actions to Stages and Dimensions.
It is used as the validation reference by `check_lancedb_chunks.py --coverage` and the `M5D_ACTION_METADATA` dict in `m5d_ingest.py`.

---

## Estrutura / Framework Structure

| Estágio / Stage | Sigla | Dimensões / Dimensions |
|---|---|---|
| Proposta Inicial de Investimento | PII | Estratégica, Econômica, Comercial, Financeira, Gerencial, Ponto de Transição |
| Proposta Intermediária de Investimento | PII2 | Estratégica, Econômica, Comercial, Financeira, Gerencial, Ponto de Transição |
| Proposta Completa de Investimento | PCI | Estratégica, Econômica, Comercial, Financeira, Gerencial, Ponto de Transição |

---

## Estágio 1 — Proposta Inicial de Investimento (PII)
### Stage 1 — Initial Investment Proposal

### Dimensão Estratégica / Strategic Dimension

| Nº | Título (PT) |
|---|---|
| 1 | Descreva o projeto, seu contexto estratégico e objetivos estratégicos |
| 2 | Determine objetivos, resultados, disposições e necessidades existentes |
| 3 | Defina o escopo potencial |
| 4 | Descreva os benefícios públicos, riscos, restrições e dependências do projeto |

### Dimensão Econômica / Economic Dimension

| Nº | Título (PT) |
|---|---|
| 5 | Defina os Fatores Críticos de Sucesso |
| 6 | Aplique a "Estrutura de Opções" |
| 7 | Defina o escopo de Avaliação de Impacto Ambiental e Social, estudos técnicos e outros |

### Dimensão Comercial / Commercial Dimension

| Nº | Título (PT) |
|---|---|
| 8 | Considere as disposições contratuais possíveis |
| 9 | Considere as possibilidades e as opções de contratação pública e o interesse do mercado |

### Dimensão Financeira / Financial Dimension

| Nº | Título (PT) |
|---|---|
| 10 | Estime custos, capacidade de custeio e capacidade de obter financiamento |

### Dimensão Gerencial / Management Dimension

| Nº | Título (PT) |
|---|---|
| 11 | Identifique a equipe do projeto (incluindo consultores externos) e a estrutura de gestão e governança |
| 12 | Desenvolva um plano de projeto inicial e um plano de controle de qualidade e aprovações |
| 13 | Identifique as partes interessadas, as ações de engajamento e o plano de gestão de mudanças |
| 14 | Elabore um plano inicial para identificação dos benefícios públicos |
| 15 | Elabore uma estratégia e um plano inicial de gestão de risco |

### Ponto de Transição / Transition Gate

| Nº | Título (PT) |
|---|---|
| 16 | Forme uma Comissão de Avaliação de Impacto Ambiental e Social (AIAS), estudos técnicos e outros |

---

## Estágio 2 — Proposta Intermediária de Investimento (PII2)
### Stage 2 — Intermediate Investment Proposal

### Dimensão Estratégica / Strategic Dimension

| Nº | Título (PT) |
|---|---|
| 17 | Reconsidere a Dimensão Estratégica e reconfirme a necessidade estratégica |

### Dimensão Econômica / Economic Dimension

| Nº | Título (PT) |
|---|---|
| 18 | Prepare a análise econômica para as opções identificadas |
| 19 | Realize uma análise qualitativa dos riscos e benefícios públicos |
| 20 | Selecione a Opção Mais Vantajosa e realize uma análise de sensibilidade |
| 21 | Revise a Avaliação de Impacto Ambiental e Social, estudos técnicos e outros |

### Dimensão Comercial / Commercial Dimension

| Nº | Título (PT) |
|---|---|
| 22 | Desenvolva uma estrutura contratual para a Opção Mais Vantajosa e a alocação de riscos |
| 23 | Elabore especificações do projeto e documentos do processo de contratação |
| 24 | Planeje a consulta e a apresentação dos fatores de interesse do mercado |
| 25 | Elabore um planejamento para realização da licitação e interaja com BMDs (se aplicável) |

### Dimensão Financeira / Financial Dimension

| Nº | Título (PT) |
|---|---|
| 26 | Confirmando as fontes de custeio do projeto |
| 27 | Construa um modelo financeiro |
| 28 | Teste a capacidade de custeio |

### Dimensão Gerencial / Management Dimension

| Nº | Título (PT) |
|---|---|
| 29 | Finalize a composição de equipe e a estrutura de gestão e governança |
| 30 | Elabore uma seção sobre o envolvimento e designação de consultores |
| 31 | Aprofunde o plano de projeto e o plano de controle de qualidade e aprovações |
| 32 | Finalize o orçamento de conclusão do projeto |
| 33 | Finalize e implemente o plano de engajamento das partes interessadas |
| 34 | Finalize o plano de gestão de mudanças |
| 35 | Finalize o plano de realização de benefícios públicos e o plano de gestão de riscos |
| 36 | Elabore um plano de avaliação do projeto |

### Ponto de Transição / Transition Gate

| Nº | Título (PT) |
|---|---|
| 37 | Finalize os documentos do processo de contratação, incluindo critérios de seleção |
| 38 | Consulte o mercado e a sociedade |

---

## Estágio 3 — Proposta Completa de Investimento (PCI)
### Stage 3 — Full Investment Proposal

### Dimensão Estratégica / Strategic Dimension

| Nº | Título (PT) |
|---|---|
| 39 | Atualize a Dimensão Estratégica, se necessário |

### Dimensão Econômica / Economic Dimension

| Nº | Título (PT) |
|---|---|
| 40 | Reconsidere as opções da Dimensão Econômica com base nas percepções colhidas junto ao mercado e sociedade |
| 41 | Confirme os critérios para seleção da melhor proposta econômica |

### Dimensão Comercial / Commercial Dimension

| Nº | Título (PT) |
|---|---|
| 42 | Documente todo o processo de ajustes aos documentos da licitação e seus efeitos |

### Dimensão Financeira / Financial Dimension

| Nº | Título (PT) |
|---|---|
| 43 | Confirme se o projeto possui capacidade de custeio |

### Dimensão Gerencial / Management Dimension

| Nº | Título (PT) |
|---|---|
| 44 | Revise e atualize todas as seções da Dimensão Gerencial |

### Ponto de Transição / Transition Gate

| Nº | Título (PT) |
|---|---|
| 45 | Execute o processo de contratação e selecione o licitante vencedor |
| 46 | Assine o contrato com o Licitante Vencedor |

---

## Contagem / Count

| Estágio / Stage | Ações / Actions |
|---|---|
| Proposta Inicial de Investimento (PII) | 1–16 (16 ações) |
| Proposta Intermediária de Investimento (PII2) | 17–38 (22 ações) |
| Proposta Completa de Investimento (PCI) | 39–46 (8 ações) |
| **Total** | **46 ações** |
