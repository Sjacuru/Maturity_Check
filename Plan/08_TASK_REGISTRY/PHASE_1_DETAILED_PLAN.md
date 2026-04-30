# FASE 1 — Plano Detalhado (28 de Abril — 29 de Maio de 2026) / PHASE 1 — Detailed Plan (April 28 — May 29, 2026)

## MVP Objetivo / MVP Objective
**Português:** Sistema completo capaz de avaliar a Ação 1, Sub-tarefa 1.1 end-to-end: upload de documentos → busca de evidências → avaliação por IA → resultado com citações para o auditor

**English:** Complete system capable of evaluating Action 1, Sub-task 1.1 end-to-end: document upload → evidence retrieval → AI evaluation → result with citations for auditor

---

## Escopo Fase 1 / Phase 1 Scope

### Incluso / Included:
- ✅ Ambiente local totalmente funcional (VS Code, Python 3.11+, Ollama, SQLite, LanceDB)
- ✅ M5D Ação 1 ingerida em banco de dados estruturado
- ✅ Crosswalk Rio + TCDF para sub-tarefa 1.1 carregado
- ✅ Pipeline de upload e chunking de documentos
- ✅ Busca híbrida (BM25 + dense) funcionando localmente
- ✅ Inferência local com Ollama (modelo Mistral)
- ✅ Interface auditor mostrando resultado + evidências + anotações
- ✅ Documentação completa (arquitetura, como usar)

### Não Incluso / NOT Included:
- ❌ Deployment em servidor Rio (Phase 2)
- ❌ Ações 2–46 (Phase 2)
- ❌ Integração Groq API (Phase 2, após testes)
- ❌ Interface web avançada (versão 1 é CLI + arquivo de saída)

---

# SEMANA 1 / WEEK 1: Ambiente & Ferramentas (28 de Abril — 4 de Maio)

## Objetivo Semanal / Weekly Objective
Ter todas as ferramentas instaladas, configuradas e testadas localmente. Nenhuma linha de código de aplicação ainda; apenas setup.

**English:** Have all tools installed, configured and tested locally. No application code yet; setup only.

---

### Tarefa 1.1 / Task 1.1: Instalar VS Code e Extensões Essenciais
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 28 de Abril / April 28  
**Data Conclusão / Completion Date:** 28 de Abril / April 28  
**Atribuído a / Assigned to:** You (Solo)

#### Verificações / Verification Checklist:
- [ ] VS Code instalado (versão 1.88+)
- [ ] Extensão "Python" (Microsoft) instalada
- [ ] Extensão "Pylance" instalada (para type checking)
- [ ] Settings do VS Code configurados: formato automático (Black), linter (Pylint)
- [ ] Terminal (PowerShell ou CMD) configurado no VS Code
- [ ] GitHub integrado ou Git instalado para commits

#### Entrega / Deliverable:
📸 **Screenshot:** VS Code aberto com extensões visíveis no painel Extensions  
📄 **Documento:** `SETUP_WEEK1_ENVIRONMENT.md` (PT + EN) listando versões instaladas

---

### Tarefa 1.2 / Task 1.2: Instalar Python 3.11+ e Configurar Virtual Environment
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 28 de Abril / April 28  
**Data Conclusão / Completion Date:** 29 de Abril / April 29  

#### Verificações / Verification Checklist:
- [ ] Python 3.11 ou superior instalado via Anaconda
- [ ] `python --version` mostra 3.11+
- [ ] `conda --version` funciona
- [ ] Ambiente Anaconda criado: `conda create -n maturity_check python=3.11`
- [ ] Ambiente ativado: `conda activate maturity_check`
- [ ] `pip --version` funciona no ambiente
- [ ] `pip install --upgrade pip setuptools wheel`
- [ ] Repositório Git clonado/inicializado no diretório do projeto

#### Entrega / Deliverable:
📸 **Screenshot:** Terminal (PowerShell ou CMD) mostrando `(maturity_check)` ativo + `python --version` com 3.11+  
📄 **Documento:** `SETUP_WEEK1_PYTHON.md` (PT + EN) com comandos executados

---

### Tarefa 1.3 / Task 1.3: Instalar e Configurar Ollama + Modelo Mistral
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 29 de Abril / April 29  
**Data Conclusão / Completion Date:** 2 de Maio / May 2  

#### O que é Ollama / What is Ollama:
Ollama é uma ferramenta para rodar modelos de linguagem (LLM) localmente no seu computador, sem conexão com internet ou APIs externas. Mistral é um modelo rápido e eficiente.

**English:** Ollama is a tool to run language models (LLMs) locally on your computer, without internet connection or external APIs. Mistral is a fast and efficient model.

#### Verificações / Verification Checklist:
- [ ] Ollama baixado e instalado (ollama.ai)
- [ ] Ollama adicionado ao PATH do Windows
- [ ] Comando `ollama --version` funciona no terminal (PowerShell ou CMD)
- [ ] Serviço Ollama iniciado: `ollama serve` (deixar rodando em terminal separado)
- [ ] Modelo Mistral baixado: `ollama pull mistral:latest` (esperar download completo, ~4GB)
- [ ] Modelo testado: `ollama list` mostra `mistral:latest`
- [ ] API local testada: `curl http://localhost:11434/api/generate` (ou `Invoke-WebRequest` no PowerShell) retorna resposta

#### Entrega / Deliverable:
📸 **Screenshot 1:** Janela de comando mostrando `ollama serve` rodando (com "listening on..." visível)  
📸 **Screenshot 2:** `ollama list` mostrando modelo mistral carregado  
📄 **Documento:** `SETUP_WEEK1_OLLAMA.md` (PT + EN) com instruções de instalação e verificação

---

### Tarefa 1.4 / Task 1.4: Instalar Dependências Python do Projeto
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 2 de Maio / May 2  
**Data Conclusão / Completion Date:** 3 de Maio / May 3  

#### Verificações / Verification Checklist:
- [ ] Repositório Maturity_Check clonado localmente
- [ ] `cd` para diretório do projeto
- [ ] Ambiente Anaconda ativado: `conda activate maturity_check`
- [ ] `pip install -r requirements.txt` executado com sucesso (ou instalar direto: `pip install pydantic lancedb pyarrow numpy tqdm sentence-transformers`)
- [ ] Packages instalados verificados: `pip list | findstr pydantic`
- [ ] Teste de import no Python: `python -c "import pydantic, lancedb, sentence_transformers; print('OK')"`

#### Entrega / Deliverable:
📸 **Screenshot:** Terminal (PowerShell ou CMD) mostrando `pip list` com todas as dependências  
📄 **Documento:** `SETUP_WEEK1_DEPENDENCIES.md` (PT + EN) com versões de cada package

---

### Tarefa 1.5 / Task 1.5: Instalar SQLite + LanceDB Setup
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 3 de Maio / May 3  
**Data Conclusão / Completion Date:** 4 de Maio / May 4  

#### O que são / What are:
- **SQLite:** Banco de dados local simples (arquivo .sqlite no disco)
- **LanceDB:** Índice de vetores otimizado para busca semântica (também local)

#### Verificações / Verification Checklist:
- [ ] SQLite3 CLI instalado ou acessível via Python `sqlite3`

- [ ] Diretório `data/` criado no projeto

- [ ] Teste de criação de banco: `python -c "import sqlite3; sqlite3.connect('data/test.sqlite')"`

- [ ] LanceDB instalado via pip (já incluído em requirements.txt)

- [ ] Diretório `data/lancedb/` criado

- [ ] Teste de inicialização LanceDB: `python -c "import lancedb; db = lancedb.connect('data/lancedb/test')"`

#### Entrega / Deliverable:
📸 **Screenshot:** Terminal (PowerShell ou CMD) mostrando diretórios criados e Python test executado com sucesso  
📄 **Documento:** `SETUP_WEEK1_DATABASE.md` (PT + EN) explicando arquitetura de dados

---

### Tarefa 1.6 / Task 1.6: Teste End-to-End Básico de Todos os Componentes
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 4 de Maio / May 4  
**Data Conclusão / Completion Date:** 4 de Maio / May 4  

#### Verificações / Verification Checklist:
- [ ] VS Code abre projeto sem erros
- [ ] Terminal (PowerShell ou CMD) no VS Code com ambiente Anaconda ativado
- [ ] Ollama rodando em background (`ollama serve` em terminal separado)
- [ ] Python consegue importar todas as dependências
- [ ] SQLite consegue criar/ler banco de dados
- [ ] LanceDB consegue inicializar diretório
- [ ] Git repositório pronto com `.gitignore` configurado (data/, .env, __pycache__)

#### Entrega / Deliverable:
📸 **Screenshot:** VS Code aberto com projeto; terminal ativo mostrando Python + ambiente Anaconda; Ollama em background  
📄 **Relatório:** `WEEK1_COMPLETE_SUMMARY.md` (PT + EN) resumindo setup; lista de checklist completada

---

## Resumo Semana 1 / Week 1 Summary

| Tarefa / Task | Status | Entrega / Deliverable |
|---------------|--------|---------------------|
| VS Code + Extensões | ✅ Concluído | Screenshot + docs |
| Python 3.11 + Anaconda | ✅ Concluído | Screenshot + docs |
| Ollama + Mistral | ✅ Concluído | 2 screenshots + docs |
| Dependências Python | ✅ Concluído | Screenshot + docs |
| SQLite + LanceDB | ✅ Concluído | Screenshot + docs |
| Teste E2E | ✅ Concluído | Screenshot + relatório |

**Total Horas Estimadas / Estimated Hours:** 16–20h  
**Status Geral / Overall Status:** ✅ **Concluído / Complete**

---

# SEMANA 2 / WEEK 2: Estrutura do Projeto & Database Schema (5 de Maio — 11 de Maio)

## Objetivo Semanal / Weekly Objective
Ter a estrutura do projeto criada, database schemas prontos (SQLite), e primeira linha de código rodando.

**English:** Have project structure created, database schemas ready (SQLite), and first line of code running.

---

### Tarefa 2.1 / Task 2.1: Criar Estrutura de Diretórios e Arquivos Base
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 5 de Maio / May 5  
**Data Conclusão / Completion Date:** 5 de Maio / May 5  

#### Estrutura Criada / Structure Created:

```
Maturity_Check/
├── src/
│   └── maturity_check/
│       ├── __init__.py
│       ├── cli.py
│       ├── db.py
│       ├── config.py
│       ├── ingest/
│       │   ├── __init__.py
│       │   ├── m5d_ingest.py
│       │   ├── case_ingest.py
│       │   └── chunking.py
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── hybrid_search.py
│       │   └── fusion.py
│       ├── evaluation/
│       │   ├── __init__.py
│       │   ├── evaluator.py
│       │   └── assurance.py
│       └── persistence/
│           ├── __init__.py
│           └── audit_log.py
├── config/
│   ├── llm_backends.template.json
│   └── chunking_config.json
├── data/
│   ├── framework.sqlite
│   ├── lancedb/
│   └── logs/
├── tests/
│   ├── __init__.py
│   └── test_imports.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── SETUP.md
├── .gitignore
├── pyproject.toml (já existe)
└── README.md
```

#### Verificações / Verification Checklist:
- [ ] Todos os diretórios criados conforme estrutura acima
- [ ] `__init__.py` criado em cada subpacote Python
- [ ] Arquivo `.gitignore` configurado (data/, .env, __pycache__)
- [ ] `config/` com templates JSON para configuração
- [ ] Estrutura testada: `python -c "from maturity_check import *"`

#### Entrega / Deliverable:
📸 **Screenshot:** VS Code File Explorer mostrando estrutura de diretórios completa  
📄 **Documento:** `PROJECT_STRUCTURE.md` (PT + EN) explicando cada diretório

---

### Tarefa 2.2 / Task 2.2: Desenhar e Criar Schema SQLite (Database)
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 5 de Maio / May 5  
**Data Conclusão / Completion Date:** 7 de Maio / May 7  

#### Database Schema para Fase 1 / Database Schema for Phase 1:

```sql
-- Tabelas de Referência (M5D, Rio, TCDF)
CREATE TABLE reference_documents (
  doc_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  title TEXT NOT NULL,
  path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE reference_chunks (
  chunk_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL REFERENCES reference_documents(doc_id),
  ordinal INTEGER NOT NULL,
  heading_path TEXT,
  start_char INTEGER NOT NULL,
  end_char INTEGER NOT NULL,
  text TEXT NOT NULL,
  text_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Tabelas de Caso (Case Documents)
CREATE TABLE cases (
  case_id TEXT PRIMARY KEY,
  case_name TEXT NOT NULL,
  institution TEXT NOT NULL,
  contract_reference TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  created_by TEXT
);

CREATE TABLE case_documents (
  doc_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  filename TEXT NOT NULL,
  file_hash TEXT NOT NULL,
  validation_status TEXT CHECK(validation_status IN ('ACCEPTED', 'WARNED', 'REJECTED')),
  validation_reason TEXT,
  uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE case_chunks (
  chunk_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL REFERENCES case_documents(doc_id),
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  ordinal INTEGER NOT NULL,
  heading_path TEXT,
  start_char INTEGER,
  end_char INTEGER,
  text TEXT NOT NULL,
  text_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Tabelas de Avaliação (Evaluation)
CREATE TABLE evaluations (
  eval_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  action_id TEXT NOT NULL,
  subtask_id TEXT NOT NULL,
  status TEXT CHECK(status IN ('present', 'not_present', 'uncertain')),
  confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  reasoning TEXT,
  evaluator_model TEXT,
  evaluator_timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE evidence_links (
  link_id TEXT PRIMARY KEY,
  eval_id TEXT NOT NULL REFERENCES evaluations(eval_id),
  case_chunk_id TEXT NOT NULL REFERENCES case_chunks(chunk_id),
  artifact_id TEXT,
  retrieval_method TEXT,
  disposition TEXT CHECK(disposition IN ('hit', 'weak', 'none')),
  similarity_score REAL
);

CREATE TABLE audit_log (
  log_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  action_id TEXT NOT NULL,
  subtask_id TEXT NOT NULL,
  event_type TEXT,
  event_data TEXT,
  timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Índices para Performance
CREATE INDEX idx_reference_chunks_doc_ordinal ON reference_chunks(doc_id, ordinal);
CREATE INDEX idx_case_chunks_case_ordinal ON case_chunks(case_id, ordinal);
CREATE INDEX idx_evaluations_case_action ON evaluations(case_id, action_id);
CREATE INDEX idx_evidence_links_eval ON evidence_links(eval_id);
CREATE INDEX idx_audit_log_case ON audit_log(case_id);
```

#### Verificações / Verification Checklist:
- [ ] Schema criado em `data/framework.sqlite` via script Python
- [ ] Todas as tabelas criadas com sucesso
- [ ] Índices criados para otimizar buscas
- [ ] Foreign keys habilitadas (`PRAGMA foreign_keys = ON`)
- [ ] WAL mode habilitado (`PRAGMA journal_mode = WAL`)
- [ ] Teste: `sqlite3 data/framework.sqlite ".tables"` mostra todas as tabelas

#### Entrega / Deliverable:
📄 **Documento:** `DATABASE_SCHEMA.md` (PT + EN) com explicação de cada tabela  
📸 **Screenshot:** SQLite CLI mostrando `.tables` listando todas as tabelas  
📄 **Código:** `src/maturity_check/db.py` com função `init_database_schema()`

---

### Tarefa 2.3 / Task 2.3: Implementar `config.py` para Configuração Global
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 7 de Maio / May 7  
**Data Conclusão / Completion Date:** 8 de Maio / May 8  

#### Configurações Principais / Main Configurations:

```python
# config.py
from pathlib import Path
import os
from typing import Optional

class Config:
    """Global configuration for M5D Evaluation System"""
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = DATA_DIR / "logs"
    LANCEDB_DIR = DATA_DIR / "lancedb"
    
    # Database
    SQLITE_PATH = DATA_DIR / "framework.sqlite"
    ENABLE_WAL = True
    
    # LLM
    OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
    LLM_TIMEOUT = 60  # seconds
    LLM_MAX_TOKENS = 2000
    LLM_TEMPERATURE = 0.3
    
    # Embedding Model
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Chunking
    CHUNK_MAX_CHARS = 3500
    CHUNK_OVERLAP_CHARS = 350
    
    # Retrieval
    RETRIEVAL_TOP_K = 5
    SIMILARITY_THRESHOLD = 0.5
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.LANCEDB_DIR.mkdir(parents=True, exist_ok=True)
```

#### Verificações / Verification Checklist:
- [ ] `config.py` implementado com todas as configurações
- [ ] Paths funcionam corretamente em Windows
- [ ] Variáveis de ambiente podem sobrescrever defaults
- [ ] `Config.ensure_directories()` cria diretórios necessários
- [ ] Teste: `python -c "from maturity_check.config import Config; Config.ensure_directories(); print('OK')"`

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/config.py`  
📄 **Documento:** `CONFIGURATION.md` (PT + EN) explicando cada configuração

---

### Tarefa 2.4 / Task 2.4: Implementar `db.py` com Funções de Database Básicas
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 8 de Maio / May 8  
**Data Conclusão / Completion Date:** 9 de Maio / May 9  

#### Funções Principais / Main Functions:

```python
def connect_sqlite(path: Path) -> sqlite3.Connection:
    """Connect to SQLite database with optimizations"""

def init_database_schema(conn: sqlite3.Connection) -> None:
    """Initialize all required database tables and indexes"""

def insert_case(conn, case_id, case_name, institution, contract_ref) -> bool:
    """Create a new case record"""

def insert_case_document(conn, doc_id, case_id, filename, validation_status) -> bool:
    """Register uploaded document"""

def insert_case_chunks(conn, chunk_rows: list[dict]) -> bool:
    """Batch insert document chunks"""

def query_case_chunks(conn, case_id: str, action_id: str) -> list[dict]:
    """Retrieve chunks for a specific case/action"""
```

#### Verificações / Verification Checklist:
- [ ] Todas as funções implementadas e testadas
- [ ] Conexão SQLite com PRAGMA settings corretos
- [ ] Foreign keys funcionam (testes de integridade)
- [ ] Teste unitário: `pytest tests/test_db.py`
- [ ] Teste manual: criar caso, inserir chunks, consultar

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/db.py`  
📄 **Testes:** `tests/test_db.py` com testes unitários  
📸 **Screenshot:** Pytest rodando com todos os testes passando

---

### Tarefa 2.5 / Task 2.5: Implementar CLI Base com Subcomandos
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 9 de Maio / May 9  
**Data Conclusão / Completion Date:** 11 de Maio / May 11  

#### CLI Comandos para Fase 1 / CLI Commands for Phase 1:

```bash
maturity-check init-db                    # Initialize database
maturity-check create-case --name=... --institution=... --contract=...
maturity-check upload-documents --case-id=... --files=...
maturity-check list-cases                 # Show all cases
maturity-check show-case --case-id=...    # Show case details
```

#### Verificações / Verification Checklist:
- [ ] CLI principal implementado usando argparse
- [ ] Subcomandos estruturados corretamente
- [ ] Todos os comandos testados manualmente
- [ ] Mensagens de erro claras (português + inglês)
- [ ] `maturity-check --help` mostra documentação
- [ ] Comando pode ser rodado via `python -m maturity_check`

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/cli.py`  
📸 **Screenshot:** `maturity-check --help` mostrando subcomandos  
📸 **Screenshot:** `maturity-check create-case --help` com opções detalhadas

---

### Tarefa 2.6 / Task 2.6: Criar Documento de Arquitetura Completo
**Status:** Backlog → Em andando → Concluído  
**Data Início / Start Date:** 10 de Maio / May 10  
**Data Conclusão / Completion Date:** 11 de Maio / May 11  

#### Conteúdo / Content:
1. Visão geral do sistema (diagrama)
2. Estrutura de dados (tabelas, relacionamentos)
3. Fluxo de dados (pipeline)
4. Componentes principais (ingest, retrieval, evaluation)
5. Tecnologias escolhidas e razões
6. Como executar código (setup + exemplos)

#### Verificações / Verification Checklist:
- [ ] Documento escrito em português e inglês
- [ ] Diagramas incluídos (ASCII ou imagem)
- [ ] Explicações claras para técnicos e não-técnicos
- [ ] Exemplos de código incluídos
- [ ] Links funcionais para arquivos do projeto

#### Entrega / Deliverable:
📄 **Documento:** `docs/ARCHITECTURE.md` (PT + EN, ~4000 palavras)

---

## Resumo Semana 2 / Week 2 Summary

| Tarefa / Task | Status | Entrega / Deliverable |
|---------------|--------|---------------------|
| Estrutura Diretórios | ✅ Concluído | Screenshot |
| Database Schema | ✅ Concluído | SQL + docs |
| Config.py | ✅ Concluído | Código + docs |
| DB.py Functions | ✅ Concluído | Código + testes |
| CLI Base | ✅ Concluído | Screenshots |
| Documentação Arquitetura | ✅ Concluído | Documento completo |

**Total Horas Estimadas / Estimated Hours:** 20–24h  
**Status Geral / Overall Status:** ✅ **Concluído / Complete**

---

# SEMANA 3 / WEEK 3: Ingestão M5D e Corpus de Referência (12 de Maio — 18 de Maio)

## Objetivo Semanal / Weekly Objective
M5D Ação 1 completamente ingerida em SQLite e LanceDB. Busca de referência funcionando (keyword + semântica).

**English:** M5D Action 1 completely ingested into SQLite and LanceDB. Reference search working (keyword + semantic).

---

### Tarefa 3.1 / Task 3.1: Implementar Chunking de Markdown com Hierarquia
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 12 de Maio / May 12  
**Data Conclusão / Completion Date:** 13 de Maio / May 13  

#### O que é Chunking / What is Chunking:
Dividir um documento longo em pedaços menores (chunks) que cabem no contexto da IA, preservando estrutura (headings).

#### Verificações / Verification Checklist:
- [ ] Função `iter_markdown_blocks()` implementada
- [ ] Função `chunk_text()` implementada
- [ ] Preservação de hierarquia de headings (`## Heading → heading_path = "Heading"`)
- [ ] Sobreposição (overlap) entre chunks funcionando
- [ ] Teste com arquivo M5D.md: chunks criados corretamente

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/ingest/chunking.py`  
📄 **Testes:** `tests/test_chunking.py`  
📸 **Screenshot:** Pytest mostrando chunks criados corretamente

---

### Tarefa 3.2 / Task 3.2: Implementar Ingestão M5D para SQLite + Hashes
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 13 de Maio / May 13  
**Data Conclusão / Completion Date:** 14 de Maio / May 14  

#### Função Principal / Main Function:
```python
def ingest_m5d(
    m5d_path: Path,
    sqlite_path: Path,
    lancedb_dir: Path,
    embed: bool = False,
    model_id: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    max_chars: int = 3500,
    overlap_chars: int = 350
) -> None:
    """Ingest M5D.md into SQLite reference_chunks table"""
```

#### Verificações / Verification Checklist:
- [ ] M5D.md localizado em `Plan/06_Models/M5D.md`
- [ ] Função `ingest_m5d()` implementada
- [ ] Arquivo lido, parseado, chunked
- [ ] Chunks inseridos em `reference_documents` e `reference_chunks`
- [ ] Hashes SHA256 computados para cada chunk
- [ ] CLI comando `maturity-check ingest-m5d` funcionando
- [ ] Teste: `sqlite3 data/framework.sqlite "SELECT COUNT(*) FROM reference_chunks"`

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/ingest/m5d_ingest.py`  
📸 **Screenshot:** `maturity-check ingest-m5d` rodando com sucesso  
📸 **Screenshot:** SQLite mostrando chunks inseridos

---

### Tarefa 3.3 / Task 3.3: Implementar Busca por Keyword em SQLite
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 14 de Maio / May 14  
**Data Conclusão / Completion Date:** 15 de Maio / May 15  

#### Função Principal / Main Function:
```python
def search_reference_sqlite(
    sqlite_path: Path,
    query: str,
    heading_contains: str | None = None,
    limit: int = 10
) -> list[ReferenceHit]:
    """Search reference chunks by keyword (LIKE query)"""
```

#### Verificações / Verification Checklist:
- [ ] Busca por keyword implementada
- [ ] Filtro opcional por heading
- [ ] LIMIT respeitado
- [ ] Resultados retornam: chunk_id, doc_id, heading_path, text
- [ ] CLI comando `maturity-check search-ref-sqlite` funcionando
- [ ] Teste: buscar por "Ação 1" retorna resultados relevantes

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/reference_search.py` (função SQLite)  
📸 **Screenshot:** CLI command `maturity-check search-ref-sqlite "Ação 1" --limit=5` mostrando resultados

---

### Tarefa 3.4 / Task 3.4: Implementar Download + Cache de Embedding Model
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 15 de Maio / May 15  
**Data Conclusão / Completion Date:** 15 de Maio / May 15  

#### O que Faz / What It Does:
Baixa o modelo de embedding `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (~400MB) para cache local.

#### Verificações / Verification Checklist:
- [ ] Modelo baixado para `~/.cache/huggingface/hub/` (automático via sentence-transformers)
- [ ] Teste: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"`
- [ ] Primeira execução pode levar 5–10 minutos; próximas usam cache

#### Entrega / Deliverable:
📸 **Screenshot:** Comando Python rodando; modelo sendo baixado  
📄 **Documento:** `MODEL_DOWNLOAD.md` (PT + EN) explicando processo

---

### Tarefa 3.5 / Task 3.5: Implementar Embedding e Ingestão em LanceDB
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 16 de Maio / May 16  
**Data Conclusão / Completion Date:** 17 de Maio / May 17  

#### Função Principal / Main Function:
```python
def ingest_m5d_to_lancedb(
    sqlite_path: Path,
    lancedb_dir: Path,
    model_id: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    table_name: str = "reference_m5d_chunks"
) -> None:
    """Load reference chunks from SQLite, embed with SentenceTransformer, store in LanceDB"""
```

#### Verificações / Verification Checklist:
- [ ] Chunks lidos de SQLite
- [ ] Cada chunk embarcado (gera vetor 384-dimensional para MiniLM)
- [ ] Vetores armazenados em LanceDB com chunk_id, text, heading_path, vector
- [ ] Índice criado em LanceDB para busca rápida
- [ ] Teste: `lancedb.connect('data/lancedb').open_table('reference_m5d_chunks').search([0.1]*384).limit(5).to_list()`

#### Entrega / Deliverable:
📄 **Código:** Extensão de `src/maturity_check/ingest/m5d_ingest.py`  
📸 **Screenshot:** LanceDB index criado mostrando chunks embarcados

---

### Tarefa 3.6 / Task 3.6: Implementar Busca Semântica em LanceDB
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 17 de Maio / May 17  
**Data Conclusão / Completion Date:** 18 de Maio / May 18  

#### Função Principal / Main Function:
```python
def search_reference_lancedb(
    lancedb_dir: Path,
    query: str,
    limit: int = 10,
    model_id: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
) -> list[ReferenceHit]:
    """Search reference chunks using semantic similarity (vector search)"""
```

#### Verificações / Verification Checklist:
- [ ] Query é embarcado com mesmo modelo
- [ ] LanceDB retorna top-K resultados mais similares
- [ ] Similaridade baseada em cosine distance
- [ ] CLI comando `maturity-check search-ref-vector` funcionando
- [ ] Teste: buscar "avaliação de demanda" retorna chunks sobre market analysis

#### Entrega / Deliverable:
📄 **Código:** Extensão de `src/maturity_check/reference_search.py` (função LanceDB)  
📸 **Screenshot:** CLI command `maturity-check search-ref-vector "Ação 1" --limit=5` mostrando resultados  
📄 **Comparação:** Keyword search vs. semantic search mostrando diferenças

---

## Resumo Semana 3 / Week 3 Summary

| Tarefa / Task | Status | Entrega / Deliverable |
|---------------|--------|---------------------|
| Chunking Markdown | ✅ Concluído | Código + testes |
| Ingestão M5D → SQLite | ✅ Concluído | Código + screenshots |
| Busca Keyword SQLite | ✅ Concluído | Código + screenshots |
| Download Embedding Model | ✅ Concluído | Screenshots |
| LanceDB Embedding + Ingestão | ✅ Concluído | Código + screenshots |
| Busca Semântica LanceDB | ✅ Concluído | Código + screenshots |

**Total Horas Estimadas / Estimated Hours:** 24–28h  
**Status Geral / Overall Status:** ✅ **Concluído / Complete**

---

# SEMANA 4 / WEEK 4: Ingestão de Documentos de Caso & Busca Híbrida (19 de Maio — 25 de Maio)

## Objetivo Semanal / Weekly Objective
Uploads de casos funcionando. Documentos chunkeados e indexados (BM25 + dense). Busca híbrida pronta.

**English:** Case uploads working. Documents chunked and indexed (BM25 + dense). Hybrid search ready.

---

### Tarefa 4.1 / Task 4.1: Implementar Validação de Documento Carregado
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 19 de Maio / May 19  
**Data Conclusão / Completion Date:** 20 de Maio / May 20  

#### Validações / Validations:
- [ ] Arquivo é readável (não corrompido)
- [ ] Idioma = Português (detect via langdetect)
- [ ] Contém vocabulário de procurement (keywords relacionados)

#### Verificações / Verification Checklist:
- [ ] Pacote `python-docx`, `pdfplumber`, `python-magic` instalado
- [ ] Função `validate_document()` implementada
- [ ] Retorna status: ACCEPTED / WARNED / REJECTED
- [ ] Teste: PDF válido → ACCEPTED; arquivo vazio → REJECTED

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/ingest/case_ingest.py` (função `validate_document`)  
📄 **Testes:** Testes unitários de validação

---

### Tarefa 4.2 / Task 4.2: Implementar Extração de Texto de PDF/DOCX
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 20 de Maio / May 20  
**Data Conclusão / Completion Date:** 21 de Maio / May 21  

#### Suporte / Support:
- PDF: `pdfplumber`
- DOCX: `python-docx`
- TXT: nativo Python

#### Verificações / Verification Checklist:
- [ ] Texto extraído preservando estrutura (headings, parágrafos)
- [ ] Caracteres especiais tratados (Portuguese accents)
- [ ] Teste: PDF com 10 páginas → texto extraído

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/ingest/case_ingest.py` (funções de extração)

---

### Tarefa 4.3 / Task 4.3: Implementar BM25 Sparse Index (via Whoosh ou similar)
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 21 de Maio / May 21  
**Data Conclusão / Completion Date:** 22 de Maio / May 22  

#### O que é BM25 / What is BM25:
Algoritmo de ranking de relevância keyword. Índice "esparso" significa documentos com keywords aparecem rapidamente (vs. vetor denso que precisa calcular similaridade).

#### Verificações / Verification Checklist:
- [ ] Biblioteca `whoosh` ou `rank-bm25` instalada
- [ ] BM25 index criado para chunks de caso
- [ ] Index persistido em disco (rápido para reabrir)
- [ ] Busca por keyword retorna top-K resultados

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/retrieval/hybrid_search.py` (BM25 part)

---

### Tarefa 4.4 / Task 4.4: Implementar Dense Vector Index para Case Chunks
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 22 de Maio / May 22  
**Data Conclusão / Completion Date:** 23 de Maio / May 23  

#### Similar a Semana 3 / Similar to Week 3:
Case chunks embedados com `sentence-transformers` → armazenados em LanceDB

#### Verificações / Verification Checklist:
- [ ] Case chunks embarcados (mesmo modelo que reference)
- [ ] LanceDB index para case chunks (`case_chunks` table)
- [ ] Query semântica funciona

#### Entrega / Deliverable:
📄 **Código:** Extensão de `src/maturity_check/ingest/case_ingest.py`

---

### Tarefa 4.5 / Task 4.5: Implementar Fusão Híbrida (RRF ou Score Fusion)
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 23 de Maio / May 23  
**Data Conclusão / Completion Date:** 24 de Maio / May 24  

#### Fusão Híbrida / Hybrid Fusion:
Combinar resultados de BM25 (keyword) + semantic (vetor) usando RRF (Reciprocal Rank Fusion).

#### Verificações / Verification Checklist:
- [ ] Função `hybrid_search()` implementada
- [ ] BM25 busca por query
- [ ] Dense busca por query embedding
- [ ] RRF combina rankings
- [ ] Top-K resultado final

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/retrieval/fusion.py`  
📸 **Screenshot:** Comparação keyword vs. semantic vs. hybrid resultados

---

### Tarefa 4.6 / Task 4.6: Implementar CLI para Upload de Documentos
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 24 de Maio / May 24  
**Data Conclusão / Completion Date:** 25 de Maio / May 25  

#### CLI Comando / CLI Command:
```bash
maturity-check upload-case-documents --case-id=RIO-001 --files=doc1.pdf,doc2.docx
```

#### Verificações / Verification Checklist:
- [ ] Comando aceita múltiplos arquivos
- [ ] Valida cada arquivo
- [ ] Extrai texto
- [ ] Cria chunks
- [ ] Insere em SQLite + LanceDB
- [ ] Retorna status por arquivo (ACCEPTED/WARNED/REJECTED)

#### Entrega / Deliverable:
📄 **Código:** Extensão de `src/maturity_check/cli.py`  
📸 **Screenshot:** CLI upload com múltiplos arquivos

---

## Resumo Semana 4 / Week 4 Summary

| Tarefa / Task | Status | Entrega / Deliverable |
|---------------|--------|---------------------|
| Validação Documento | ✅ Concluído | Código |
| Extração PDF/DOCX | ✅ Concluído | Código |
| BM25 Index | ✅ Concluído | Código |
| Dense Vector Index (Cases) | ✅ Concluído | Código |
| Fusão Híbrida | ✅ Concluído | Código + screenshots |
| CLI Upload | ✅ Concluído | Código + screenshots |

**Total Horas Estimadas / Estimated Hours:** 24–28h  
**Status Geral / Overall Status:** ✅ **Concluído / Complete**

---

# SEMANA 5 & FINALIZAÇÃO / WEEK 5 & MVP FINALIZATION (26 de Maio — 29 de Maio)

## Objetivo / Objective
Completar avaliação end-to-end de Ação 1, Sub-tarefa 1.1. MVP pronto em 29 de Maio.

**English:** Complete end-to-end evaluation of Action 1, Sub-task 1.1. MVP ready on May 29.

---

### Tarefa 5.1 / Task 5.1: Implementar Avaliador LLM (FR-009/FR-010)
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 26 de Maio / May 26  
**Data Conclusão / Completion Date:** 27 de Maio / May 27  

#### O que Faz / What It Does:
LLM recebe sub-tarefa + chunks relevantes → retorna present/not_present/uncertain + confidence + reasoning

#### Verificações / Verification Checklist:
- [ ] Prompt template criado (português + inglês)
- [ ] Função `evaluate_subtask()` implementada
- [ ] Chama Ollama API local
- [ ] Parseia resposta JSON
- [ ] Retorna: status, confidence, reasoning, model_id, timestamp

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/evaluation/evaluator.py`  
📸 **Screenshot:** Ollama chamado com sucesso; resposta parseada

---

### Tarefa 5.2 / Task 5.2: Implementar Assurance Pass (FR-021)
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 27 de Maio / May 27  
**Data Conclusão / Completion Date:** 27 de Maio / May 27  

#### O que Faz / What It Does:
Validação pós-geração: LLM checa sua própria resposta (temperatura=0, prompt rigoroso)

#### Verificações / Verification Checklist:
- [ ] `judge_pass()` implementado
- [ ] Usa mesmo modelo, prompt diferente, temperature=0
- [ ] Válida: lógica consistente, não-alucinação, confiança apropriada
- [ ] Se confidence < 0.70 → UNCERTAINTY flag

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/evaluation/assurance.py`

---

### Tarefa 5.3 / Task 5.3: Implementar Persistência com Evidence Links
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 27 de Maio / May 27  
**Data Conclusão / Completion Date:** 28 de Maio / May 28  

#### O que Faz / What It Does:
Salvar resultado em SQLite com links para chunks + artifacts

#### Verificações / Verification Checklist:
- [ ] Função `persist_evaluation()` implementada
- [ ] Insere em `evaluations` table
- [ ] Insere em `evidence_links` table (cada chunk referenciado)
- [ ] Insere em `audit_log` (rastreabilidade)

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/persistence/audit_log.py`

---

### Tarefa 5.4 / Task 5.4: Criar Interface Simples de Saída (Relatório)
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 28 de Maio / May 28  
**Data Conclusão / Completion Date:** 28 de Maio / May 28  

#### Formato / Format:
JSON + HTML/Markdown renderizado

```json
{
  "case_id": "RIO-001",
  "action_id": "action_1",
  "subtask_id": "subtask_1_1",
  "evaluation": {
    "status": "present",
    "confidence": 0.92,
    "reasoning": "...",
    "evidence": [
      {
        "chunk_id": "...",
        "text": "...",
        "artifact_id": "...",
        "disposition": "hit"
      }
    ],
    "flags": [],
    "timestamp": "..."
  }
}
```

#### Verificações / Verification Checklist:
- [ ] JSON export implementado
- [ ] HTML report gerado (para auditor ler)
- [ ] Evidence citations incluídos

#### Entrega / Deliverable:
📄 **Código:** `src/maturity_check/evaluation/report_generator.py`  
📸 **Screenshot:** HTML report aberto no navegador

---

### Tarefa 5.5 / Task 5.5: Pipeline End-to-End Teste (Action 1, Task 1.1)
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 28 de Maio / May 28  
**Data Conclusão / Completion Date:** 29 de Maio / May 29  

#### Teste Completo / Full Test:

```bash
# 1. Criar caso de teste
maturity-check create-case --name="Teste Ação 1" --institution="RIO" --contract="REF-2024-001"

# 2. Upload documentos de exemplo
maturity-check upload-case-documents --case-id=test-001 --files=example_docs/*.pdf

# 3. Executar avaliação Ação 1, Sub-tarefa 1.1
maturity-check evaluate-case --case-id=test-001 --action=action_1 --subtask=subtask_1_1

# 4. Ver resultado
maturity-check show-evaluation --case-id=test-001 --action=action_1 --subtask=subtask_1_1 --format=html
```

#### Verificações / Verification Checklist:
- [ ] Todas as etapas executadas com sucesso
- [ ] Resultado mostra: presente/ausente/incerto
- [ ] Confiança e raciocínio incluídos
- [ ] Evidence links funcionam
- [ ] Relatório HTML gerado e legível

#### Entrega / Deliverable:
📸 **Screenshot:** CLI mostrando pipeline completo  
📸 **Screenshot:** HTML report resultante  
📄 **Documento:** `MVP_TEST_RESULTS.md` (PT + EN)

---

### Tarefa 5.6 / Task 5.6: Documentação Final MVP + User Manual
**Status:** Backlog → Em andamento → Concluído  
**Data Início / Start Date:** 29 de Maio / May 29  
**Data Conclusão / Completion Date:** 29 de Maio / May 29  

#### Conteúdo / Content:
1. **README.md** atualizado com instruções MVP
2. **GETTING_STARTED.md** (PT + EN) — guia rápido
3. **API_REFERENCE.md** — documentação de funções
4. **DEPLOYMENT_MVP.md** — como rodar na máquina

#### Verificações / Verification Checklist:
- [ ] Documentação bilíngue
- [ ] Exemplos de uso incluídos
- [ ] Screenshots de cada etapa
- [ ] Troubleshooting section
- [ ] Links para arquivos do projeto

#### Entrega / Deliverable:
📄 **Documentos:** README.md, GETTING_STARTED.md, API_REFERENCE.md, DEPLOYMENT_MVP.md (todas PT + EN)

---

## Resumo Semana 5 / Week 5 Summary

| Tarefa / Task | Status | Entrega / Deliverable |
|---------------|--------|---------------------|
| Avaliador LLM | ✅ Concluído | Código + screenshots |
| Assurance Pass (FR-021) | ✅ Concluído | Código |
| Persistência + Evidence Links | ✅ Concluído | Código |
| Interface Relatório | ✅ Concluído | Código + screenshots |
| Pipeline E2E Teste | ✅ Concluído | Screenshots + documento |
| Documentação Final | ✅ Concluído | Documentos completos |

**Total Horas Estimadas / Estimated Hours:** 20–24h  
**Status Geral / Overall Status:** ✅ **CONCLUÍDO / COMPLETE — MVP PRONTO EM 29 DE MAIO**

---

# RESUMO EXECUTIVO FASE 1 / PHASE 1 EXECUTIVE SUMMARY

## Datas / Dates
- **Início / Start:** 28 de Abril de 2026 / April 28, 2026
- **Fim / End:** 29 de Maio de 2026 / May 29, 2026
- **Duração / Duration:** ~5 semanas / 5 weeks (200 horas estimadas / estimated 200 hours)

## MVP Entregáveis / MVP Deliverables

| Categoria / Category | Entregável / Deliverable | Status |
|-----------|----------|--------|
| **Código / Code** | Repositório Python com CLI funcional | ✅ |
| **Database / Storage** | SQLite + LanceDB estruturados | ✅ |
| **Busca / Search** | Híbrida (BM25 + semantic) | ✅ |
| **Avaliação / Evaluation** | LLM local (Ollama) + Assurance Pass | ✅ |
| **Interface / Interface** | CLI + JSON + HTML reports | ✅ |
| **Documentação / Documentation** | Arquitetura + User Manual (PT + EN) | ✅ |

## Capabilidades MVP

- ✅ Criar casos de procurement
- ✅ Upload de documentos (PDF, DOCX, TXT)
- ✅ Validação de documentos (idioma, domain)
- ✅ Busca de evidências (keyword + semântica)
- ✅ Avaliação de Ação 1, Sub-tarefa 1.1
- ✅ Resultado com confiança + citações
- ✅ Relatório auditável (JSON + HTML)

## O que Não Está em Fase 1 / NOT in Phase 1

- ❌ Web UI (CLI + arquivos de saída apenas)
- ❌ Ações 2–46 (Ação 1 apenas)
- ❌ Groq API (local Ollama apenas)
- ❌ Deployment Rio server (local dev apenas)
- ❌ Suporte multi-usuário (solo developer)

## Próximos Passos (Phase 2) / Next Steps (Phase 2)

Documento de planejamento Phase 2 segue abaixo...

---

*Documento gerado: 28 de Abril de 2026 / Generated: April 28, 2026*
