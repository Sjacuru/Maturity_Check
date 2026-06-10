# PPP Maturity Check — Visão Geral do Projeto
# PPP Maturity Check — Project Overview

*Documento bilíngue — cada seção aparece primeiro em português, depois em inglês.*
*Bilingual document — each section appears first in Portuguese, then in English.*

*Versão 0.1 — 2026-06-08 — Rascunho de apresentação: Phase A concluída*
*Version 0.1 — 2026-06-08 — Presentation draft: Phase A complete*

---

## 1. Resumo Executivo | Executive Summary

### Português

O **PPP Maturity Check** é um sistema de suporte à decisão para avaliação de projetos de Parceria Público-Privada (PPP) do Município do Rio de Janeiro. O sistema avalia documentos de processos licitatórios contra o framework **IPMP** (Indicador de Percepção de Maturidade de Projetos), produzindo uma pontuação de maturidade para cada ação avaliada.

O objetivo é tornar o trabalho do auditor mais rápido, rastreável e replicável. O sistema recupera evidências dos documentos, raciocina sobre elas e propõe uma pontuação. O auditor avalia o resultado, verifica as evidências e decide — aceitando ou substituindo a pontuação com justificativa.

**Estado atual:** sete módulos implementados, 300 testes feitos por IA, fluxo ponta-a-ponta funcional para a Ação 1. A validação da cadeia de raciocínio (Phase A) foi concluída em junho, confirmando que o sistema produz os scores esperados em corpus de teste controlado. O próximo passo é a validação com documentos reais de PPP.

**Restrição central:** normalização de resultados. A mesma entrada deve produzir a mesma saída em qualquer execução. Esta restrição orienta todas as escolhas técnicas: recuperação BM25 determinística, temperatura zero no LLM, prompt fixo por ação.

### English

**PPP Maturity Check** is a decision-support system for evaluating Public-Private Partnership (PPP) project documents from the City of Rio de Janeiro. The system evaluates procurement process documents against the **IPMP** framework (Indicador de Percepção de Maturidade de Projetos — Project Maturity Perception Indicator), producing a maturity score for each evaluated action.

The objective is not to replace the auditor. It is to make the auditor's work faster, more traceable, and more reproducible. The system retrieves evidence from documents, reasons about it, and proposes a score. The auditor reads the reasoning, checks the evidence, and decides — accepting or overriding the score with a justification.

**Current state:** seven modules implemented, 300 tests passing, end-to-end pipeline functional for Action 1. The reasoning chain validation (Phase A) was completed in June 2026, confirming that the system produces expected scores on a controlled test corpus. The next step is validation with real PPP documents.

**Core constraint:** reproducibility. The same input must produce the same output on any run. This constraint drives all technical choices: deterministic BM25 retrieval, LLM temperature zero, fixed prompt per action.

---

## 2. Problema e Contexto | Problem and Context

### Português

#### 2.1 Projetos PPP e a necessidade de avaliação

Projetos de Parceria Público-Privada são instrumentos complexos de contratação pública que  envolvem comprometimento de recursos públicos por longo prazo, transferência de riscos entre poder público e iniciativa privada e impacto direto sobre a qualidade de serviços essenciais para a população. Um projeto mal estruturado pode resultar em litígios prolongados, paralização de obras estratégicas, perdas fiscais significativas para o município e prestação de serviço deficiente.

O processo de avaliação verifica se os documentos produzidos ao longo da estruturação do projeto atendem aos critérios de qualidade estabelecidos.

#### 2.2 O framework IPMP

O **IPMP** — Indicador de Percepção de Maturidade de Projetos — é o framework de avaliação adotado. Ele organiza a avaliação em **46 ações** distribuídas em **5 dimensões**:

1. Estratégica
2. Técnica
3. Financeira
4. Ambiental e Social
5. Jurídica e Regulatória

Cada ação é pontuada em uma escala de três níveis: **0** (Não Atendido), **1** (Parcialmente Atendido), **3** (Atendido). A pontuação máxima possível é **138 pontos** (46 × 3). Para cada ação, o IPMP define:

- Os **produtos esperados** que o projeto deve apresentar (subítens a, b, c, d...)
- Um **critério de pontuação** com exemplos concretos de cada nível
- Um **rubric de avaliação** com exemplos pontuados (Atendido / Parcialmente / Não Atendido)

#### 2.3 O problema da avaliação manual

A avaliação manual apresenta três problemas estruturais:

**Volume.** Um processo PPP típico produz dezenas de documentos com centenas de páginas. O auditor precisa identificar, em todo esse material, os trechos relevantes para cada uma das 46 ações. Esta busca é intensiva em tempo e propensa a omissões.

**Subjetividade.** Mesmo com critérios bem definidos, avaliadores diferentes podem chegar a pontuações distintas. A ausência de rastreabilidade impede identificar se discordâncias refletem interpretações legítimas ou omissões involuntárias.

**Reprodutibilidade.** Um resultado acadêmico ou técnico precisa ser replicável. A avaliação manual não garante que a mesma pontuação seria obtida por outro avaliador com acesso aos mesmos documentos e critérios.

O PPP Maturity Check foi construído para atacar esses três problemas diretamente.

### English

#### 2.1 PPP Projects and the need for evaluation

Public-Private Partnership projects are complex public procurement instruments. They involve commitments of public resources for decades, risk transfer between government and private sector, and direct impact on the quality of essential services for the population. A poorly structured project can result in prolonged litigation, stalling of strategic works, or significant fiscal losses for the municipality.

In the City of Rio de Janeiro, PPP project management is regulated by Complementary Law No. 105/2009 and guided by procedures documented in the **Manual of Best Practices in Concessions and PPPs of the Municipality of Rio de Janeiro** (Rio Manual). The evaluation process verifies whether documents produced throughout project structuring meet established quality criteria.

#### 2.2 The IPMP framework

The **IPMP** — Indicador de Percepção de Maturidade de Projetos (Project Maturity Perception Indicator) — is the adopted evaluation framework. It organizes the assessment into **46 actions** across **5 dimensions**:

1. Strategic
2. Technical
3. Financial
4. Environmental and Social
5. Legal and Regulatory

Each action is scored on a three-level scale: **0** (Not Met), **1** (Partially Met), **3** (Met). The maximum possible score is **138 points** (46 × 3). For each action, the IPMP defines:

- The **expected products** the project must present (sub-items a, b, c, d...)
- A **scoring criterion** with concrete examples for each level
- An **evaluation rubric** with scored examples (Met / Partial / Not Met)

#### 2.3 The manual evaluation problem

Manual evaluation presents three structural problems:

**Volume.** A typical PPP process produces dozens of documents with hundreds of pages. The auditor needs to identify, across all this material, the relevant passages for each of the 46 actions. This search is time-intensive and prone to omissions.

**Subjectivity.** Even with well-defined criteria, different evaluators may reach different scores. The lack of traceability prevents identifying whether disagreements reflect legitimate interpretations or inadvertent omissions.

**Reproducibility.** An academic or technical result must be replicable. Manual evaluation does not guarantee that the same score would be obtained by another evaluator given the same documents and criteria.

PPP Maturity Check was built to directly address these three problems.

---

## 3. Visão Geral da Solução | Solution Overview

### Português

#### 3.1 Conceito central: suporte à decisão, não substituição

O sistema não avalia sozinho. Ele prepara o material para que o auditor avalie com mais eficiência e confiança.

Para cada ação IPMP, o sistema executa uma sequência de quatro operações:

1. **Recuperação:** localiza os trechos do processo licitatório mais relevantes para a ação
2. **Avaliação:** envia os trechos ao LLM junto com os critérios IPMP, obtém raciocínio e pontuação proposta
3. **Apresentação:** exibe ao auditor os sete elementos do pacote de evidências
4. **Validação:** o auditor aceita a pontuação ou a substitui com justificativa

A pontuação proposta não é um resultado — é uma entrada para o julgamento do auditor.

#### 3.2 Escopo atual: Ação 1

O sistema foi construído para a Ação 1 do IPMP: *"Descreva o projeto, seu contexto e os objetivos estratégicos."* Esta ação pertence à dimensão Estratégica e avalia quatro produtos esperados (1a–1d).

A escolha de um escopo reduzido foi deliberada. O projeto segue o princípio de **módulos profundos/Deep modules**: um módulo completamente projetado e construído antes do próximo começar. Isso evita dívida técnica oculta e garante que cada camada da arquitetura esteja validada antes de ser estendida.

A extensão para as demais 45 ações requer apenas a adição de dados IPMP e Rio Manual correspondentes. A infraestrutura está construída.

#### 3.3 Princípios de projeto

**Reprodutibilidade:** BM25 (recuperação lexical determinística) + temperatura zero no LLM = mesma entrada → mesmo score. Esta propriedade é requisito acadêmico explícito e condição para comparação entre processos diferentes.

**Rastreabilidade:** cada score armazenado carrega sua cadeia de evidências completa — quais trechos foram recuperados, por qual método, qual prompt foi enviado, qual raciocínio foi produzido. O auditor pode auditar cada passo.

**Separação de responsabilidades:** cada módulo possui uma fronteira clara e uma única responsabilidade. Alterações em um módulo não propagam efeitos inesperados nos demais.

**Humano no loop/Human in the loop:** a pontuação final é sempre do auditor. O sistema nunca grava uma pontuação sem validação humana explícita.

### English

#### 3.1 Core concept: decision support, not replacement

The system does not evaluate alone. It prepares the material so the auditor can evaluate more efficiently and confidently.

For each IPMP action, the system executes a sequence of four operations:

1. **Retrieval:** locates the most relevant passages from the procurement process for the action
2. **Evaluation:** sends the passages to the LLM along with IPMP criteria, obtains reasoning and proposed score
3. **Presentation:** displays to the auditor the seven elements of the evidence package
4. **Validation:** the auditor accepts the score or overrides it with a justification

The proposed score is not a result — it is an input for the auditor's judgment.

#### 3.2 Current scope: Action 1

The system was built for IPMP Action 1: *"Describe the project, its context, and strategic objectives."* This action belongs to the Strategic dimension and evaluates four expected products (1a–1d).

The choice of a narrow scope was deliberate. The project follows the **deep modules** principle: one module fully designed and built before the next begins. This avoids hidden technical debt and ensures each architectural layer is validated before being extended.

Extension to the remaining 45 actions requires only adding corresponding IPMP and Rio Manual data. The infrastructure is built.

#### 3.3 Design principles

**Reproducibility:** BM25 (deterministic lexical retrieval) + LLM temperature zero = same input → same score. This property is an explicit academic requirement and a condition for comparison across different processes.

**Traceability:** every stored score carries its complete evidence chain — which passages were retrieved, by which method, which prompt was sent, which reasoning was produced. The auditor can audit the auditor.

**Separation of concerns:** each module has a clear boundary and a single responsibility. Changes to one module do not propagate unexpected effects to others.

**Human in the loop:** the final score always belongs to the auditor. The system never records a score without explicit human validation.

---

## 4. Arquitetura do Sistema | System Architecture

### Português

#### 4.1 Fluxo de informação ponta-a-ponta

```
Documento PDF do processo licitatório
        ↓  [Módulo 2 — Extraction]
Texto estruturado em chunks (página, offset, heurística de layout)
        ↓  [Módulo 3 — Retrieval]
Chunks relevantes para a Ação, com proveniência (cascata A→B→C→D→E)
        ↓  [Módulo 4 — Evaluation]
Raciocínio + pontuação proposta + flags
        ↓  [Módulo 5 — Assessment + API]
Resultado persistido; apresentado na interface
        ↓  [Módulo 7 — Frontend]
Pacote de evidências completo para revisão do auditor
        ↓  [Decisão do auditor]
Score final (ou com justificativa)
```

#### 4.2 O que ocorre em cada estágio

**Extração (PDF → chunks):** O PDF passa por um extrator que identifica texto nativo e, onde necessário, aplica OCR. O resultado é uma lista de `Chunk`s — unidades de texto com metadados de proveniência (arquivo, página, offset, indicador de OCR). Esta transformação preserva a localização original de cada trecho, que será exibida ao auditor.

**Recuperação (chunks → evidências):** O sistema executa uma cascata de estratégias de busca. Primeiro tenta identificar o documento certo pelo nome (match de filename e variant). Se não encontra, executa busca BM25 com termos derivados dos produtos esperados do IPMP e dos termos-chave curados no Rio Manual. Em paralelo, executa busca regex para padrões legais específicos (ex: "Lei Complementar n.º 105/2009"). Se nenhuma estratégia léxica retorna resultados, recorre ao fallback vetorial (LanceDB + sentence-transformers).

**Avaliação (evidências → pontuação proposta):** Os chunks recuperados são organizados e enviados ao LLM junto com um prompt estruturado contendo: critérios IPMP da ação, rubric de pontuação com exemplos, e instrução para produzir raciocínio livre seguido de um bloco sentinela (`SCORE: X / UNCERTAINTY: yes|no`). O LLM opera a temperatura zero.

**Persistência e apresentação:** O resultado é armazenado no SQLite com todos os campos — chunks, prompt completo, resposta bruta, raciocínio parseado, pontuação proposta, flags. A interface exibe esses campos ao auditor.

#### 4.3 Decisões arquiteturais fundamentais

**SQLite como base unificada.** BM25 via FTS5 é nativo no SQLite. Usar o mesmo banco para indexação e recuperação elimina dependências externas e garante comportamento determinístico.

**Cascata lexical antes do fallback vetorial.** BM25 e regex são determinísticos e interpretáveis. O fallback vetorial é probabilístico. A cascata garante que o método mais confiável é sempre tentado primeiro.

**Prompt fixo por ação.** O prompt não é gerado dinamicamente com base no processo ou nos resultados de recuperação. Ele é construído a partir dos dados IPMP da ação e dos chunks recuperados. Isso garante que todos os processos avaliados pela mesma ação recebem o mesmo critério de julgamento.

**Módulo de assessment como orquestrador.** O módulo 5 (Assessment) não implementa lógica de negócio de nenhum dos outros módulos. Ele os chama em sequência, persiste os resultados, e expõe a API. A lógica de cada domínio fica dentro do módulo que a possui.

### English

#### 4.1 End-to-end information flow

```
PDF document from the procurement process
        ↓  [Module 2 — Extraction]
Structured text in chunks (page, offset, layout heuristic)
        ↓  [Module 3 — Retrieval]
Action-relevant chunks with provenance (cascade A→B→C→D→E)
        ↓  [Module 4 — Evaluation]
Reasoning + proposed score + flags
        ↓  [Module 5 — Assessment + API]
Result persisted; presented in interface
        ↓  [Module 7 — Frontend]
Complete evidence package for auditor review
        ↓  [Auditor decision]
Final score recorded with justification
```

#### 4.2 What changes at each stage

**Extraction (PDF → chunks):** The PDF passes through an extractor that identifies native text and, where necessary, applies OCR. The result is a list of `Chunk`s — units of text with provenance metadata (file, page, offset, OCR flag). This transformation preserves the original location of each passage, which will be shown to the auditor.

**Retrieval (chunks → evidence):** The system executes a cascade of search strategies. It first tries to identify the right document by name (filename and variant match). If not found, it runs BM25 search with terms derived from the IPMP expected products and key terms curated in the Rio Manual. In parallel, it runs regex search for specific legal patterns (e.g., "Complementary Law No. 105/2009"). If no lexical strategy returns results, it falls back to vector retrieval (LanceDB + sentence-transformers).

**Evaluation (evidence → proposed score):** Retrieved chunks are organized and sent to the LLM along with a structured prompt containing: IPMP criteria for the action, scoring rubric with examples, and an instruction to produce free reasoning followed by a sentinel block (`SCORE: X / UNCERTAINTY: yes|no`). The LLM operates at temperature zero.

**Persistence and presentation:** The result is stored in SQLite with all fields — chunks, complete prompt, raw response, parsed reasoning, proposed score, flags. The interface displays these fields to the auditor.

#### 4.3 Fundamental architectural decisions

**SQLite as the unified database.** BM25 via FTS5 is native in SQLite. Using the same database for indexing and retrieval eliminates external dependencies and guarantees deterministic behavior.

**Lexical cascade before vector fallback.** BM25 and regex are deterministic and interpretable. Vector fallback is probabilistic. The cascade ensures the most reliable method is always tried first.

**Fixed prompt per action.** The prompt is not dynamically generated based on the process or retrieval results. It is constructed from the action's IPMP data and the retrieved chunks. This ensures all processes evaluated by the same action receive the same judgment criteria.

**Assessment module as orchestrator.** Module 5 (Assessment) does not implement business logic from any other module. It calls them in sequence, persists results, and exposes the API. The logic of each domain stays within the module that owns it.

---

## 5. Percurso pelos Módulos | Module Walkthrough

### Português

#### 5.1 Mapa de responsabilidades

| Módulo                | Estágio               | Entrada                               | Saída |
|--------               |---------              |---------                              |-------|
| 1 — Ingestion         | Referência            | Arquivos IPMP + Rio Manual + siglas   | Store de critérios e metadados de busca |
| 2 — Extraction        | Extração              | PDF do processo licitatório           | Lista de `Chunk`s estruturados |
| 3 — Retrieval         | Recuperação           | Chunks indexados + critérios da ação  | `RetrievedChunk`s com proveniência |
| 4 — Evaluation        | Avaliação             | `RetrievedChunk`s + critérios IPMP    | `EvaluationResult` com raciocínio |
| 5 — Assessment        | Orquestração + API    | PDFs do caso                          | Resultados persistidos; endpoints REST |
| 6 — Vector Fallback   | Recuperação (fallback)| Chunks sem resultado léxico           | Chunks por similaridade semântica |
| 7 — Frontend          | Interface do auditor  | API REST                              | Painel Vue.js com pacote de evidências |

Cada módulo tem uma única superfície pública (seu `__init__.py`) e não acessa os internos de outros módulos diretamente. Dependências entre módulos são explícitas e unidirecionais.

#### 5.2 Módulo 3 — Retrieval: a cascata de recuperação

A cascata de recuperação é o estágio mais crítico do sistema. Evidências de má qualidade comprometem todos os estágios subsequentes — independentemente da qualidade do prompt ou do modelo.

A cascata executa cinco estratégias em ordem de confiabilidade decrescente:

**Etapa A — Filename match.** O sistema compara os nomes dos arquivos do processo contra os nomes de documentos listados no Rio Manual para a ação. Se encontra correspondência (ex: arquivo chamado "Relatório de Pré-Análise.pdf"), retorna todos os chunks desse arquivo como resultado focado.

**Etapa B — Variant match.** Se nenhum arquivo corresponde ao nome exato, o sistema busca nos primeiros chunks de cada arquivo por variantes do nome do documento (ex: "Relatório de Pré Análise" sem hífens ou acentos). Esta etapa trata nomes de arquivo não padronizados.

**Etapas C + D — BM25 + Regex.** Se as etapas A e B não identificam um documento focal, a busca passa a ser sobre todo o corpus indexado. O BM25 usa duas fontes de termos: (1) palavras significativas extraídas dos textos dos produtos esperados do IPMP; (2) termos curados no Rio Manual (`bm25_search_hints` — 15 termos primários + 10 secundários para a Ação 1). O regex busca padrões legais específicos configurados no Rio Manual (ex: `Lei Complementar\s+n[.º]*\s*105`).

**Etapa E — Vector fallback.** Executada apenas quando nenhuma das etapas léxicas retorna resultados. Usa embeddings de texto (modelo `all-MiniLM-L6-v2`) indexados no LanceDB para recuperação por similaridade semântica.

**Descoberta de validação (A1):** A análise de código identificou que a Etapa C não estava usando os termos curados do Rio Manual. O BM25 estava gerando queries apenas com palavras genéricas dos produtos esperados (ex: "descrever", "natureza", "projeto"), ignorando os 25 termos específicos como "Relatório de Pré-Análise" e "conveniência e oportunidade". Esta falha não foi detectada pelos testes unitários existentes porque os testes verificavam o comportamento da função dada uma query, mas não verificavam de onde a query vinha. A correção foi aplicada antes da validação controlada.

#### 5.3 Módulo 4 — Evaluation: o prompt e o parse

O LLM recebe dois inputs: um prompt de sistema e um prompt de usuário.

**Prompt de sistema** contém: (1) papel (role) ("você é um avaliador IPMP"); (2) critérios detalhados da ação incluindo todos os produtos esperados; (3) exemplos pontuados (Atendido, Parcialmente Atendido, Não Atendido) extraídos do IPMP; (4) instrução de formato para o bloco sentinela obrigatório.

**Prompt de usuário** contém os chunks recuperados, formatados como `[Arquivo: nome | Página: n]\n\nTexto...`. Cada chunk inclui sua proveniência.

O LLM produz texto livre (raciocínio) seguido do bloco sentinela:
```
SCORE: 3
UNCERTAINTY: no
```

O parser extrai o score e o flag de incerteza. Se o bloco sentinela não for encontrado, o resultado é marcado como `parse_failed=True` e o auditor é notificado. Este é o modo de falha seguro — o sistema falha explicitamente ao invés de produzir um score silenciosamente incorreto.

**Limite de evidências:** Para evitar que o LLM ultrapasse sua janela de contexto, o sistema aplica um cap de 20.000 caracteres de evidência por avaliação, priorizando os chunks de maior qualidade (filename_match > variant_match > bm25 > regex > vector, desempate por score BM25).

### English

#### 5.1 Responsibility map

| Module | Stage | Input | Output |
|--------|-------|-------|--------|
| 1 — Ingestion | Reference | IPMP + Rio Manual + acronym files | Criteria and search metadata store |
| 2 — Extraction | Extraction | PDF of procurement process | List of structured `Chunk`s |
| 3 — Retrieval | Retrieval | Indexed chunks + action criteria | `RetrievedChunk`s with provenance |
| 4 — Evaluation | Evaluation | `RetrievedChunk`s + IPMP criteria | `EvaluationResult` with reasoning |
| 5 — Assessment | Orchestration + API | Case PDFs | Persisted results; REST endpoints |
| 6 — Vector Fallback | Retrieval (fallback) | Chunks with no lexical result | Chunks by semantic similarity |
| 7 — Frontend | Auditor interface | REST API | Vue.js panel with evidence package |

Each module has a single public surface (its `__init__.py`) and does not access other modules' internals directly. Dependencies between modules are explicit and unidirectional.

#### 5.2 Module 3 — Retrieval: the retrieval cascade

The retrieval cascade is the most critical stage in the system. Low-quality evidence compromises all subsequent stages — regardless of prompt or model quality.

The cascade executes five strategies in decreasing order of reliability:

**Step A — Filename match.** The system compares the names of process files against document names listed in the Rio Manual for the action. If a match is found (e.g., a file named "Pre-Analysis Report.pdf"), it returns all chunks from that file as a focused result.

**Step B — Variant match.** If no file matches the exact name, the system searches the first chunks of each file for variants of the document name (e.g., "Pre Analysis Report" without hyphens or accents). This step handles non-standardized file names.

**Steps C + D — BM25 + Regex.** If steps A and B do not identify a focal document, the search covers the entire indexed corpus. BM25 uses two term sources: (1) significant words extracted from IPMP expected product texts; (2) terms curated in the Rio Manual (`bm25_search_hints` — 15 primary + 10 secondary terms for Action 1). The regex searches for specific legal patterns configured in the Rio Manual (e.g., `Complementary Law\s+No[.]*\s*105`).

**Step E — Vector fallback.** Executed only when none of the lexical steps returns results. Uses text embeddings (model `all-MiniLM-L6-v2`) indexed in LanceDB for semantic similarity retrieval.

**Validation finding (A1):** Code analysis identified that Step C was not using the curated Rio Manual terms. BM25 was generating queries only with generic words from expected products (e.g., "describe", "nature", "project"), ignoring the 25 specific terms such as "Pre-Analysis Report" and "convenience and opportunity." This failure was not detected by existing unit tests because the tests verified function behavior given a query, but not where the query came from. The fix was applied before controlled validation.

#### 5.3 Module 4 — Evaluation: the prompt and the parse

The LLM receives two inputs: a system prompt and a user prompt.

**System prompt** contains: (1) role instruction ("you are an IPMP evaluator"); (2) detailed action criteria including all expected products; (3) scored examples (Met, Partially Met, Not Met) extracted from the IPMP; (4) format instruction for the mandatory sentinel block.

**User prompt** contains the retrieved chunks, formatted as `[File: name | Page: n]\n\nText...`. Each chunk includes its provenance.

The LLM produces free text (reasoning) followed by the sentinel block:
```
SCORE: 3
UNCERTAINTY: no
```

The parser extracts the score and uncertainty flag. If the sentinel block is not found, the result is marked `parse_failed=True` and the auditor is notified. This is the safe failure mode — the system fails explicitly rather than silently producing an incorrect score.

**Evidence cap:** To prevent the LLM from exceeding its context window, the system applies a 20,000-character evidence cap per evaluation, prioritizing the highest-quality chunks (filename_match > variant_match > bm25 > regex > vector, tie-broken by BM25 score).

---

## 6. Fluxo de Trabalho do Auditor | Auditor Workflow

### Português

#### 6.1 Jornada do auditor

*Cenário: o auditor recebe um processo PPP para avaliação de maturidade.*

O auditor acessa o sistema pelo navegador. Na tela inicial, informa o número do processo e faz upload dos documentos do processo licitatório — PDFs como o EVTEA (Estudo de Viabilidade Técnica, Econômica e Ambiental) e o Relatório de Pré-Análise. O sistema aceita múltiplos arquivos e tenta identificar automaticamente documentos já indexados (uso do SHA-256 como fingerprint - HASH) versus documentos novos.

O sistema extrai e indexa o texto dos documentos novos. Para a Ação 1, executa a cascata de recuperação e identifica os trechos relevantes. Em seguida, envia esses trechos ao LLM com os critérios IPMP e aguarda o raciocínio. Todo o processo é síncrono — o auditor aguarda o resultado na mesma sessão.

A interface exibe o painel da Ação 1. O auditor encontra, em sequência:

1. Os critérios IPMP completos da ação (collapsible)
2. Os trechos recuperados com fonte, página, tipo de busca e query exata utilizada
3. O prompt completo enviado ao modelo (collapsible)
4. O raciocínio livre produzido pelo LLM
5. O flag de incerteza (se `UNCERTAINTY: yes`, um indicador de alerta é exibido)
6. A pontuação proposta (0, 1 ou 3)

O auditor lê o raciocínio. Se concordar, clica em "Aceitar". Se discordar — por exemplo, porque o modelo não encontrou um documento relevante que o auditor conhece — clica em "Substituir", seleciona a pontuação correta e escreve a justificativa. A decisão é gravada com a pontuação final, a justificativa e o registro de se houve substituição.

#### 6.2 Pacote de evidências: qualidade da informação

O valor do sistema para o auditor está na qualidade do pacote de evidências, não na pontuação proposta. A pontuação pode estar errada. O que não pode falhar é o rastreamento.

| Elemento | O que apresenta | Questão de qualidade |
|---|---|---|
| Evidências recuperadas | Trechos do documento com arquivo e página | Os melhores chunks  foram recuperados? |
| Proveniência da recuperação | Etapa da cascata + query exata | O método de busca foi adequado para este documento? |
| Critérios IPMP | Texto completo da ação | O auditor pode verificar se o modelo avaliou pelos critérios corretos |
| Prompt completo | System + user prompt exatos | O auditor pode verificar o que foi enviado ao modelo |
| Raciocínio | Texto livre explicando a avaliação por produto esperado | O modelo raciocinou pelos produtos 1a, 1b, 1c, 1d individualmente? |
| Flag de incerteza | Sim / Não | O modelo identificou onde faltam evidências? |
| Pontuação proposta | 0, 1 ou 3 | Está alinhada ao raciocínio apresentado? |

### English

#### 6.1 Auditor journey

*Scenario: the auditor receives a PPP process for maturity evaluation.*

The auditor accesses the system via browser. On the initial screen, they enter the process number and upload the procurement process documents — PDFs such as the EVTEA (Technical, Economic and Environmental Feasibility Study) and the Pre-Analysis Report. The system accepts multiple files and automatically identifies previously indexed documents (reuse by SHA-256 fingerprint) versus new documents.

The system extracts and indexes text from new documents. For Action 1, it executes the retrieval cascade and identifies relevant passages. It then sends these passages to the LLM with the IPMP criteria and waits for reasoning. The entire process is synchronous — the auditor waits for the result in the same session.

The interface displays the Action 1 panel. The auditor finds, in sequence:

1. Complete IPMP criteria for the action (collapsible)
2. Retrieved passages with source, page, search type and exact query used
3. Complete prompt sent to the model (collapsible)
4. Free reasoning produced by the LLM
5. The uncertainty flag (if `UNCERTAINTY: yes`, an alert chip is displayed)
6. The proposed score (0, 1, or 3)

The auditor reads the reasoning. If they agree, they click "Accept." If they disagree — for example, because the model did not find a relevant document the auditor knows about — they click "Override," select the correct score, and write a justification. The decision is recorded with the final score, the justification, and a flag indicating whether an override occurred.

#### 6.2 Evidence package: information quality

The system's value to the auditor lies in the quality of the evidence package, not the proposed score. The score may be wrong. What cannot fail is the traceability.

| Element | What it presents | Quality question |
|---|---|---|
| Retrieved evidence | Document passages with file and page | Were the right chunks found? |
| Retrieval provenance | Cascade step + exact query | Was the search method appropriate for this document? |
| IPMP criteria | Full action text | The auditor can verify whether the model evaluated against the correct criteria |
| Full prompt | Exact system + user prompts | The auditor can verify what was sent to the model |
| Reasoning | Free text explaining evaluation per expected product | Did the model reason through products 1a, 1b, 1c, 1d individually? |
| Uncertainty flag | Yes / No | Did the model identify where evidence is missing? |
| Proposed score | 0, 1, or 3 | Is it aligned with the reasoning presented? |

---

## 7. Estado Atual | Current State

### Português

#### 7.1 O que foi implementado

O sistema está completo para o fluxo ponta-a-ponta da Ação 1. Sete módulos foram implementados, totalizando 300 testes automatizados.

**Módulos concluídos:**

- **Módulo 1 (Ingestion):** store de critérios IPMP, Rio Manual e siglas para a Ação 1. Dados ingeridos manualmente a partir do PDF do IPMP TCU 2026.
- **Módulo 2 (Extraction):** extração de texto nativo via heurística de contagem de palavras + OCR via Tesseract como fallback. Chunking por página com suporte a sub-páginas longas.
- **Módulo 3 (Retrieval):** cascata completa A→B→C→D→E. BM25 via SQLite FTS5. Regex via função definida pelo usuário em SQLite. Vector fallback via LanceDB + sentence-transformers.
- **Módulo 4 (Evaluation):** cliente Ollama (local, Mistral) e Groq (nuvem). Prompt fixo por ação. Parse com sentinelas. Flag de incerteza. Evidence cap de 20k chars.
- **Módulo 5 (Assessment):** orquestrador + API REST FastAPI. 5 rotas Phase 1. Persistência híbrida no SQLite. Controle de ciclo de vida por fingerprint/HASH SHA-256.
- **Módulo 6 (Vector Fallback):** LanceDB com indexação sob demanda. Invalidação automática na substituição de chunks.
- **Módulo 7 (Frontend):** Vue.js 3 + Vuetify 3. Duas views: Upload e Resultado do Assessment. Painel de Ação com pacote de evidências completo. Formulário de revisão do auditor. Servido pelo FastAPI como arquivos estáticos.

#### 7.2 O que foi observado

**Primeiro teste com documento real (M5D):**
O sistema foi testado com um documento real de PPP (o M5D) usando um número de processo fictício. Para a Ação 1, o LLM não produziu a pontuação. O resultado foi marcado como `parse_failed=True`.

*Causa identificada:* 57.000 caracteres de evidência foram recuperados (27 chunks). O modelo Mistral, com o `num_ctx` padrão do Ollama, esgotou a janela de contexto antes de produzir o bloco sentinela `SCORE:`.

*Correções aplicadas:*
1. `num_ctx=32768` explícito na configuração do Ollama
2. Cap de 20.000 caracteres de evidência com ordenação por prioridade de cascata

**Descoberta: BM25 não usava os hints do Rio Manual (A1):**
Análise de código revelou que a função `retrieve_bm25_for_acao()` gerava queries apenas com palavras dos textos dos produtos esperados do IPMP, ignorando os 25 termos curados em `bm25_search_hints` do Rio Manual para a Ação 1. Esta falha existia desde a implementação inicial do módulo 3, mas não havia sido detectada pelos testes unitários porque eles verificavam o comportamento da função, não a completude das queries.

*Correção aplicada:* `cascade.py` passa a ler `rio_acao.bm25_search_hints.primary_terms + secondary_terms` e adicionar como `queries["rio_hints"]` com sintaxe de frase FTS5.

#### 7.3 Limitações atuais

- **Escopo:** Ação 1 apenas. As demais 45 ações requerem dados IPMP e Rio Manual correspondentes.
- **Modelo:** Mistral via Ollama (local) como padrão. Groq disponível como alternativa. Nenhuma comparação de modelos foi realizada.
- **Validação com documentos reais:** apenas um smoke test com o M5D, sem análise da qualidade dos resultados.
- **Frontend:** funcional mas não validado com usuários reais.
- **Performance:** sem benchmarks de tempo de resposta para processos com muitos documentos.

### English

#### 7.1 What was implemented

The system is complete for the Action 1 end-to-end pipeline. Seven modules were implemented, totaling 300 automated tests.

**Completed modules:**

- **Module 1 (Ingestion):** IPMP criteria, Rio Manual, and acronym stores for Action 1. Data ingested manually from the IPMP TCU 2026 PDF.
- **Module 2 (Extraction):** native text extraction via word-count heuristic + OCR via Tesseract as fallback. Per-page chunking with support for long sub-pages.
- **Module 3 (Retrieval):** complete A→B→C→D→E cascade. BM25 via SQLite FTS5. Regex via SQLite user-defined function. Vector fallback via LanceDB + sentence-transformers.
- **Module 4 (Evaluation):** Ollama client (local, Mistral) and Groq (cloud). Fixed prompt per action. Sentinel-based parsing. Uncertainty flag. 20k char evidence cap.
- **Module 5 (Assessment):** orchestrator + FastAPI REST API. 5 Phase 1 routes. Hybrid persistence in SQLite. Lifecycle control by SHA-256 fingerprint.
- **Module 6 (Vector Fallback):** LanceDB with on-demand indexing. Automatic invalidation on chunk replacement.
- **Module 7 (Frontend):** Vue.js 3 + Vuetify 3. Two views: Upload and Assessment Result. Action panel with complete evidence package. Auditor review form. Served by FastAPI as static files.

#### 7.2 What was observed

**First test with a real document (M5D):**
The system was tested with a real PPP document (the M5D) using a fictitious process number. For Action 1, the LLM did not produce a score. The result was marked `parse_failed=True`.

*Identified cause:* 57,000 characters of evidence were retrieved (27 chunks). The Mistral model, with Ollama's default `num_ctx`, exhausted the context window before producing the `SCORE:` sentinel block.

*Applied corrections:*
1. Explicit `num_ctx=32768` in the Ollama configuration
2. 20,000-character evidence cap with cascade-priority ordering

**Discovery: BM25 was not using Rio Manual hints (A1):**
Code analysis revealed that the `retrieve_bm25_for_acao()` function was generating queries only from words in IPMP expected product texts, ignoring the 25 curated terms in the Rio Manual `bm25_search_hints` for Action 1. This failure had existed since the initial Module 3 implementation but was not detected by unit tests because they verified function behavior, not query completeness.

*Applied correction:* `cascade.py` now reads `rio_acao.bm25_search_hints.primary_terms + secondary_terms` and adds them as `queries["rio_hints"]` with FTS5 phrase syntax.

#### 7.3 Current limitations

- **Scope:** Action 1 only. The remaining 45 actions require corresponding IPMP and Rio Manual data.
- **Model:** Mistral via Ollama (local) as default. Groq available as alternative. No model comparison has been performed.
- **Validation with real documents:** only one smoke test with the M5D, without quality analysis of results.
- **Frontend:** functional but not validated with real users.
- **Performance:** no response-time benchmarks for processes with many documents.

---

## 8. Validação | Validation

### Português

#### 8.1 Evidências reunidas (Phase A)

A Phase A de validação foi concluída em junho. Seu objetivo foi validar cada estágio da cadeia de raciocínio para a Ação 1 usando um corpus de teste controlado.

**Corpus de teste criado (A2):**

Dois documentos sintéticos foram criados para permitir validação com ground truth conhecida:

- **Caso de Teste Score 3** (4 páginas): cobre todos os produtos esperados 1a–1d com linguagem específica e referências às leis e instrumentos de planejamento exigidos (Lei Complementar n.º 105/2009, Lei Federal n.º 11.079/2004, PPA 2026-2029, LOA, LDO). Inclui frases exatas dos hints do Rio Manual. Score esperado: **3 (Atendido)**.

- **Caso de Teste Score 1** (1 página): linguagem genérica e vaga. Produto 1a parcialmente evidenciado; 1b, 1c, 1d ausentes. Nenhuma referência legal específica. Score esperado: **1 (Parcialmente Atendido)**.

Os documentos são artefatos reproduzíveis — gerados por script (`scripts/create_test_corpus.py`) com conteúdo fixo e determinístico.

**Resultados da validação:**

| Estágio | Tarefa | Resultado |
|---------|--------|-----------|
| A1 — Recuperação | Fix: BM25 + hints Rio Manual | Aplicado. 3 de 4 chunks do Score3 recuperados via `rio_hints`. |
| A3 — Cobertura de chunks | Score3: 4/4 páginas recuperadas? | Sim. Todos os 4 chunks via BM25 (3 via `rio_hints`, 1 via `1b`). |
| A3 — Cobertura de chunks | Score1: recuperação limitada? | Sim. 1 chunk via BM25, refletindo a ausência de linguagem específica. |
| A4 — Qualidade do prompt | Score3: score proposto = 3? | **Sim.** `parse_failed=False`, `uncertainty=False`, `evidence=6120 chars`. |
| A4 — Qualidade do prompt | Score1: score proposto = 1? | **Sim.** `parse_failed=False`, `uncertainty=False`, `evidence=1633 chars`. |

O raciocínio produzido pelo LLM para o Score3 mapeou corretamente cada seção do documento para o produto esperado correspondente (1a→Seção 1, 1b→Seção 2, 1c→Seção 3, 1d→Seção 4). Para o Score1, identificou corretamente que 1a é fraco, 1b ausente, 1c presente mas insuficiente, 1d ausente (sem instrumentos de planejamento).

#### 8.2 Lacunas de validação

**Estágio 1 — Qualidade de recuperação (BM25) | Stage 1 — Retrieval quality**

- *O que foi validado:* BM25 com hints do Rio Manual recupera todos os chunks de um documento sintético bem estruturado.
- *O que não foi validado:* comportamento com documentos reais de PPP, onde a linguagem pode variar significativamente, nomes de seção podem não coincidir com os esperados, e alguns produtos podem estar implicitamente cobertos em vez de explicitamente declarados.
- *Confiança atual:* **Média** — a correção funcionou no corpus controlado; comportamento no mundo real é desconhecido.

**Estágio 2 — Cobertura de produtos esperados | Stage 2 — Expected product coverage**

- *O que foi validado:* o corpus controlado foi construído para cobrir 1a–1d explicitamente, e o sistema os recuperou.
- *O que não foi validado:* documentos reais raramente organizam o conteúdo por produto esperado. Pode ser necessário ajuste nos termos de busca ou nas configurações de chunk.
- *Confiança atual:* **Baixa** para documentos reais.

**Estágio 3 — Qualidade do prompt e do raciocínio | Stage 3 — Prompt and reasoning quality**

- *O que foi validado:* o prompt guiou o modelo a raciocinar pelos quatro produtos esperados e produzir os scores corretos no corpus controlado.
- *O que não foi validado:* comportamento em casos ambíguos, documentos com evidências parciais distribuídas por múltiplos arquivos, ou quando o produto está implícito no contexto mas não declarado explicitamente.
- *Confiança atual:* **Média** — funcionou no caso ideal (Score3) e no caso vago (Score1); casos intermediários não foram testados.

**Estágio 4 — Comparação de modelos | Stage 4 — Model comparison**

- *O que foi validado:* nada. Apenas Mistral (Ollama) foi usado.
- *O que não foi validado:* se um modelo diferente (Groq, outro local) produziria raciocínios mais defensáveis ou pontuações mais consistentes com avaliadores humanos.
- *Confiança atual:* **Desconhecida.**

### English

#### 8.1 Evidence gathered (Phase A)

Phase A validation was completed in June 2026. Its objective was to validate each stage of the reasoning chain for Action 1 using a controlled test corpus.

**Test corpus created (A2):**

Two synthetic documents were created to enable validation with known ground truth:

- **Score 3 Test Case** (4 pages): covers all expected products 1a–1d with specific language and references to required laws and planning instruments (Complementary Law No. 105/2009, Federal Law No. 11.079/2004, PPA 2026-2029, LOA, LDO). Includes exact phrases from Rio Manual hints. Expected score: **3 (Met)**.

- **Score 1 Test Case** (1 page): generic and vague language. Product 1a partially evidenced; 1b, 1c, 1d absent. No specific legal references. Expected score: **1 (Partially Met)**.

The documents are reproducible artifacts — generated by script (`scripts/create_test_corpus.py`) with fixed, deterministic content.

**Validation results:**

| Stage | Task | Result |
|-------|------|--------|
| A1 — Retrieval | Fix: BM25 + Rio Manual hints | Applied. 3 of 4 Score3 chunks retrieved via `rio_hints`. |
| A3 — Chunk coverage | Score3: 4/4 pages retrieved? | Yes. All 4 chunks via BM25 (3 via `rio_hints`, 1 via `1b`). |
| A3 — Chunk coverage | Score1: limited retrieval? | Yes. 1 chunk via BM25, reflecting absence of specific language. |
| A4 — Prompt quality | Score3: proposed score = 3? | **Yes.** `parse_failed=False`, `uncertainty=False`, `evidence=6120 chars`. |
| A4 — Prompt quality | Score1: proposed score = 1? | **Yes.** `parse_failed=False`, `uncertainty=False`, `evidence=1633 chars`. |

The LLM reasoning for Score3 correctly mapped each document section to the corresponding expected product (1a→Section 1, 1b→Section 2, 1c→Section 3, 1d→Section 4). For Score1, it correctly identified that 1a is weak, 1b absent, 1c present but insufficient, 1d absent (no planning instruments).

#### 8.2 Validation gaps

**Stage 1 — Retrieval quality (BM25)**

- *What was validated:* BM25 with Rio Manual hints retrieves all chunks from a well-structured synthetic document.
- *What was not validated:* behavior with real PPP documents, where language may vary significantly, section names may not match expected patterns, and some products may be implicitly rather than explicitly covered.
- *Current confidence:* **Medium** — the fix worked on the controlled corpus; real-world behavior is unknown.

**Stage 2 — Expected product coverage**

- *What was validated:* the controlled corpus was built to explicitly cover 1a–1d, and the system retrieved them.
- *What was not validated:* real documents rarely organize content by expected product. Search term adjustments or chunk configuration changes may be needed.
- *Current confidence:* **Low** for real documents.

**Stage 3 — Prompt and reasoning quality**

- *What was validated:* the prompt guided the model to reason through all four expected products and produce correct scores on the controlled corpus.
- *What was not validated:* behavior on ambiguous cases, documents with partial evidence distributed across multiple files, or when a product is implicit in context but not explicitly stated.
- *Current confidence:* **Medium** — worked on the ideal case (Score3) and the vague case (Score1); intermediate cases not tested.

**Stage 4 — Model comparison**

- *What was validated:* nothing. Only Mistral (Ollama) was used.
- *What was not validated:* whether a different model (Groq, another local model) would produce more defensible reasoning or scores more consistent with human evaluators.
- *Current confidence:* **Unknown.**

---

## 9. Roteiro de Melhoria | Improvement Roadmap

### Português

#### 9.1 Lógica do roteiro

O roteiro é dirigido por lacunas de confiança, não por cronograma arbitrário. Cada fase aumenta a confiança em um ou mais estágios da cadeia de raciocínio antes de avançar para o estágio seguinte.

A regra é: não expandir o escopo (novas ações) antes de ter confiança suficiente na cadeia para a Ação 1.

#### 9.2 Phase A — Validação da cadeia de raciocínio (Concluída: jun/2026)

*Objetivo: estabelecer confiança na cadeia para um corpus controlado.*

| Tarefa | Status | Impacto |
|--------|--------|---------|
| A1 — Fix BM25 + Rio Manual hints | ✓ Concluído | Retrieval: Baixa → Média |
| A2 — Corpus de teste sintético | ✓ Concluído | Permite ground truth controlado |
| A3 — Inspecionar qualidade de retrieval | ✓ Concluído | Cobertura de chunks confirmada |
| A4 — Inspecionar qualidade do prompt | ✓ Concluído | Reasoning chain validada ponta-a-ponta |
| A5 — Deck de slides + este documento | Em andamento | Comunicação dos resultados |

#### 9.3 Phase B — Validação com documento real (Jul/2026)

*Objetivo: substituir o corpus sintético por um processo PPP real.*

| Tarefa | Dependência | Impacto esperado |
|--------|-------------|-----------------|
| B1 — Obter processo PPP completo | Acesso ao acervo | Retrieval: Média → Alta |
| B2 — Avaliar Ação 1 no processo real | B1 | Prompt/reasoning: Média → Alta ou identificar lacunas |
| B3 — Revisão do auditor no resultado real | B2 | Identificar padrões de substituição de score |
| B4 — Comparação de modelos (Mistral vs. Groq) | B2 | Model: Desconhecida → Alguma evidência |

#### 9.4 Phase C — Backlog de melhoria (Não agendado)

*Priorizado após Phase B, com base em lacunas identificadas.*

- Extensão para as demais 45 ações IPMP
- Validação do frontend com auditores reais
- Benchmarks de performance
- Análise de consistência entre avaliações (mesmo processo, diferentes rodadas)

### English

#### 9.1 Roadmap logic

The roadmap is driven by confidence gaps, not an arbitrary schedule. Each phase increases confidence in one or more stages of the reasoning chain before advancing to the next stage.

The rule is: do not expand scope (new actions) before having sufficient confidence in the chain for Action 1.

#### 9.2 Phase A — Reasoning chain validation (Complete: Jun/2026)

*Objective: establish confidence in the chain for a controlled corpus.*

| Task | Status | Impact |
|------|--------|--------|
| A1 — Fix BM25 + Rio Manual hints | ✓ Complete | Retrieval: Low → Medium |
| A2 — Synthetic test corpus | ✓ Complete | Enables controlled ground truth |
| A3 — Inspect retrieval quality | ✓ Complete | Chunk coverage confirmed |
| A4 — Inspect prompt quality | ✓ Complete | Reasoning chain validated end-to-end |
| A5 — Slide deck + this document | In progress | Results communication |

#### 9.3 Phase B — Real-document validation (Jul/2026)

*Objective: replace synthetic corpus with a real PPP process.*

| Task | Dependency | Expected impact |
|------|------------|----------------|
| B1 — Obtain complete PPP process | Archive access | Retrieval: Medium → High |
| B2 — Evaluate Action 1 on real process | B1 | Prompt/reasoning: Medium → High or identify gaps |
| B3 — Auditor review of real result | B2 | Identify score override patterns |
| B4 — Model comparison (Mistral vs. Groq) | B2 | Model: Unknown → Some evidence |

#### 9.4 Phase C — Improvement backlog (Not scheduled)

*Prioritized after Phase B, based on identified gaps.*

- Extension to the remaining 45 IPMP actions
- Frontend validation with real auditors
- Performance benchmarks
- Consistency analysis across evaluations (same process, different runs)

---

## Apêndices | Appendices

*A ser preenchido conforme a Phase B produza resultados.*
*To be populated as Phase B produces results.*

### Apêndice A | Appendix A — Critérios IPMP: Ação 1 | IPMP Criteria: Action 1

*Texto completo dos critérios, produtos esperados e rubric de pontuação da Ação 1, extraído do IPMP TCU 2026.*
*Full text of criteria, expected products, and scoring rubric for Action 1, extracted from IPMP TCU 2026.*

*(Disponível em `data/ipmp/acao_01.json`)*

### Apêndice B | Appendix B — Log de validação: Phase A | Validation log: Phase A

*Resultados detalhados da validação por estágio da cadeia de raciocínio.*
*Detailed validation results by reasoning chain stage.*

| Etapa | Script | Saída-chave |
|-------|--------|-------------|
| A3 | `scripts/a3_inspect_retrieval.py` | 4/4 chunks Score3 via BM25; 1/1 chunk Score1 |
| A4 | `scripts/a4_inspect_evaluation.py` | Score3→3, Score1→1; reasoning mapeado por produto |

### Apêndice C | Appendix C — Exemplos de raciocínio do modelo | Model reasoning examples

*Raciocínio completo produzido pelo Mistral para o Score3 (excerpts):*
*Complete reasoning produced by Mistral for Score3 (excerpts):*

> *"Os Produtos Esperados (1a, 1b, 1c, 1d) estão claramente evidenciados no documento.*
> *1a. A necessidade do projeto é descrita na seção 'SECAO 1 - NECESSIDADE E DESCRICAO DO PROJETO'...*
> *1b. A situação atual e o cenário em que o projeto se insere são descritos na seção 'SECAO 2 - CONTEXTO ECONOMICO, SOCIAL E AMBIENTAL'...*
> *1c. Os objetivos estratégicos do projeto são definidos na seção 'SECAO 3 - OBJETIVOS ESTRATEGICOS'.*
> *1d. A demonstração de como o projeto se conecta e está em consonância com as políticas públicas... está na seção 'SECAO 4 - ALINHAMENTO COM POLITICAS PUBLICAS E PLANEJAMENTO GOVERNAMENTAL'.*
> *SCORE: 3 / UNCERTAINTY: no"*

*Raciocínio completo produzido pelo Mistral para o Score1 (excerpts):*

> *"Os Produtos Esperados (1a, 1b, 1c, 1d) não estão claramente evidenciados no documento apresentado.*
> *1a. A descrição concisa dos motivos... está presente, mas não é completamente clara...*
> *1b. A descrição do panorama mais amplo... não está claramente evidenciada.*
> *1c. Enquanto a definição... está presente, ela não é formalmente definida...*
> *1d. A demonstração de como o projeto se conecta... [ausente: nenhum instrumento de planejamento citado]*
> *SCORE: 1 / UNCERTAINTY: no"*

---

*Documento gerado em 2026-06-08. Autoria: Salim Jacuru (sjacuru@gmail.com).*
*Document generated 2026-06-08. Author: Salim Jacuru (sjacuru@gmail.com).*
