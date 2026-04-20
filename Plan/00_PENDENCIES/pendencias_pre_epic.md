## Pendências pré-EPIC (decisões e confirmações)

Este arquivo lista **pendências que precisam ser respondidas/confirmadas antes da criação do EPIC** (ou, quando aplicável, explicitamente marcadas como “deferidas com racional” para o revisor do EPIC).

### 1) FR-008 — “document names” (nomes de documentos esperados) para classificação

**Contexto**: para documentos reais de processos antigos, não há padrão de nome. Um “documento necessário” pode:
- estar como arquivo separado com nome ruim,
- estar dentro de outro PDF,
- ter o “nome do documento” apenas no cabeçalho/título interno.

**Regra v0 (já acordada)**: **não existe lista fixa de nomes esperados** nesta fase; a classificação deve registrar o método utilizado:
- **Método 1 (melhor caso)**: match por **nome do arquivo**.
- **Método 2**: match por **título/cabeçalho extraído** do próprio PDF.
- **Método 3**: match por **similaridade semântica** do conteúdo.

**Pendência (a resolver antes do EPIC)**: verificar se faz sentido introduzir uma lista de “tipos/títulos esperados” já no v0.

**Possíveis resultados (definidos pelo PO)**:
1. **Nome/tipo pode ser extraído do próprio M5D** (framework passa a carregar “nomes/tipos esperados” por ação).
2. **Não há nome/tipo nesta etapa**: seguimos com v0 sem nomes esperados (pular qualquer etapa dependente disso; ir direto para header + semântica).
3. **Novo documento estático complementar** será adicionado (fora do M5D) com a lista de documentos esperados e nomes/tipos.
   - Implica criar **estrutura de relacionamento** entre M5D e esse documento (mapeamento “ação → documentos esperados”).

### 2) Ação vertical slice (FR-007…FR-015) — identificador e ID estável

**Decisão já confirmada**: começar pela **Ação 1**; expandir até **Ação 16** (fim do ciclo “Proposta Inicial de Investimento”).

**O que “ID estável” significa (para testes/EPIC)**:
- Definir um identificador interno **imutável** para cada ação, por exemplo:
  - `action_1` para “Ação 1”
  - `action_2` para “Ação 2”
  - …
  - `action_16` para “Ação 16”
- O título em PT-BR pode mudar por edição/normalização, mas o `action_N` deve permanecer como chave lógica.

**Pendência**:
- Confirmar que usaremos o esquema `action_<N>` como ID primário no armazenamento estruturado do framework (FR-001).

### 3) OQ-001 — pesos (FR-002 / FR-013)

**Fechado**: pesos **iguais** por enquanto (equal weights). Custom weights ficam fora até serem fornecidos.

### 4) OQ-002 — vínculo “sub-task ↔ complement row”

**Pendência**: definir, junto com o PO, a regra de vínculo entre:
- sub-tasks da ação
- e as “complement rows”/tabela-resumo relevante

Saída esperada desta pendência:
- regra objetiva (“quando existir linha X…”, “quando não existir…”) para orientar o contexto usado em FR-009/FR-014.

### 5) OQ-004 / NFR-006 — latência

**Deferido**: sem meta de tempo agora; prioridade é “funcionar primeiro”.

### 6) OQ-006 — threshold de UNCERTAINTY

**Fechado**: threshold = **70%** (confiança abaixo disso gera flag UNCERTAINTY).

### 7) OQ-007 — documentos pré-M5D

**Fechado**: avaliar documentos pré-M5D **pelos critérios M5D** (objetivo é evidenciar o gap de maturidade).

### 8) OQ-005 / NFR-008 — LLM local e fronteira de dados

**Fechado (diretriz)**:
- Usar **LLM local**.
- Preparar/segmentar documentos **antes** da inferência.
- Evitar que qualquer ferramenta auxiliar envie texto para fora por padrão.

**Pendência (para documentação no EPIC/Sign-off pack)**:
- Registrar explicitamente a “fronteira” (o que é local vs opt-in), especialmente se houver OCR/extração em nuvem como upgrade futuro.

### 9) Segmentation + retrieval architecture (vector vs não-vector)

**Pendência**: decidir se haverá embeddings (vector) ou retrieval sem embeddings (não-vector).

**Informações que você precisará definir (quando decidir)**:
- **OCR**: PDFs chegam com texto extraível ou muitos são “imagem”?
- **Estrutura**: existe índice, títulos, seções, numeração consistente?
- **Tamanho**: páginas típicas por documento; quantidade de PDFs por caso.
- **Precisão desejada**: prioridade em “recall” (não perder evidência) vs “precision” (não trazer lixo).
- **Custos/infra**: se rodará tudo local (CPU/GPU), limites de memória/disco.

**Nota**: “vectorless” não é um produto específico; significa apenas “retrieval sem embeddings” (ex.: full-text/BM25 + filtros + heurísticas de estrutura).

