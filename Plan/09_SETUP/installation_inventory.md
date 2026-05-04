# Installation inventory (dev machine)

This page tracks **what must be installed** to work on this repo and what is **already installed** on the current machine.  
Update it as you go so setup is reproducible.

---

## How to use (quick)

- For each item below, set **Status** to one of: `installed` / `pending` / `optional` / `n/a`.
- Paste the output (or a short note) into **Evidence**.
- Commands are provided for **CMD** (preferred) and **PowerShell** where it matters.

---

## 1) System baseline

### Required

- **Git**
  - **Status**: installed
  - **Verify (CMD / PowerShell)**: `git --version`
  - **Evidence**:

- **Python 3.11+ (64-bit)**
  - **Status**: installed
  - **Verify (CMD / PowerShell)**: `python --version`
  - **Evidence**:

- **Pip + (venv or Conda)**
  - **Status**: installed
  - **Verify (CMD / PowerShell)**:
    - `python -m pip --version`
    - `python -m venv --help`
    - If using Conda: `conda --version`
  - **Evidence**:

### Recommended

- **VS Code / Cursor**
  - **Status**: installed
  - **Evidence**:

- **Windows Terminal**
  - **Status**: installed
  - **Evidence**:

---

## 2) Repo structure & data directories (local-only)

### Required

- **Writable local data folder**
  - This repo writes local artifacts by default:
    - `data/framework.sqlite`
    - `data/lancedb/reference/`
    - `data/crosswalk/` (generated JSON extracts) 
  - **Status**: pending
  - **Verify (CMD)**:
    - `mkdir data`
    - `mkdir data\\lancedb\\reference`
    - `mkdir data\\crosswalk`
  - **Verify (PowerShell)**:
    - `New-Item -ItemType Directory -Force data, data\\lancedb\\reference, data\\crosswalk | Out-Null`
  - **Evidence**:

### Recommended (safety)

- **`.env` / secrets discipline** 
  - **Status**: pending
  - **Verify**: confirm secrets are not committed (repo `.gitignore`)
  - **Evidence**:

---

## 3) Python project environment (this repo)

This repository is a Python package with a CLI: `maturity-check` (see `pyproject.toml`).

### Required

- **Create a virtual environment**
  - **Status**: pending
  - **Option A — venv (recommended for consistency with repo)**
    - **CMD**:
      - `python -m venv .venv`
      - `.venv\\Scripts\\activate.bat`
    - **PowerShell**:
      - `python -m venv .venv`
      - `.\.venv\Scripts\Activate.ps1`
  - **Option B — Conda (OK if you prefer it)**
    - **CMD / PowerShell**:
      - `conda create -n maturity-check python=3.11 -y`
      - `conda activate maturity-check`
  - **Evidence**:

- **Install the package**
  - **Status**: pending
  - **Commands (CMD / PowerShell)**:
    - `python -m pip install -U pip`
    - `python -m pip install -e .`
  - **Evidence**:

- **Verify CLI works**
  - **Status**: pending
  - **Verify (CMD / PowerShell)**: `maturity-check --help`
  - **Evidence**:

### Dependency notes (why these exist)

- **SQLite** is used as a local store (bundled with Python).
- **LanceDB + PyArrow** provide local vector storage/search.
- **sentence-transformers** generates local embeddings for Portuguese-capable semantic search.

---

## 4) Database / vector stack (local reference corpus)

### Required (Phase 0 / spikes already in repo)

- **SQLite runtime**
  - **Status**: pending
  - **Verify (CMD / PowerShell)**: `python -c "import sqlite3; print(sqlite3.sqlite_version)"`
  - **Evidence**:

- **LanceDB + PyArrow import check**
  - **Status**: pending
  - **Verify**:
    - **CMD / PowerShell**: `python -c "import lancedb, pyarrow; print('ok')"`
  - **Evidence**:

- **sentence-transformers import check**
  - **Status**: pending
  - **Verify**:
    - **CMD / PowerShell**: `python -c "from sentence_transformers import SentenceTransformer; print('ok')"`
  - **Evidence**:

### Smoke test (optional but useful)

- **Ingest M5D into SQLite + LanceDB**
  - **Status**: optional
  - **Command**:
    - `maturity-check ingest-m5d`
  - **Evidence**:

- **Vector search reference chunks**
  - **Status**: optional
  - **Command**:
    - `maturity-check search-ref-vector "exemplo de consulta" --limit 3`
  - **Evidence**:

---

## 5) Local LLM (future EPIC/MDAP work; not required for current repo code)

### Optional (Phase 1 MVP path)

- **Ollama**
  - **Status**: pending
  - **Verify**:
    - **CMD / PowerShell**: `ollama --version`
    - **CMD / PowerShell**: `ollama list`
  - **Evidence**:

- **Local model pulled**
  - **Status**: pending
  - **Verify**: `ollama list` shows your chosen model (e.g., `mistral`)
  - **Evidence**:

---

## 6) External LLM (production-gated; keep off by default)

### Optional (Phase 2+, explicitly configured)

- **Groq API key present (DO NOT COMMIT)**
  - **Status**: optional
  - **Verify (CMD)**: `echo %GROQ_API_KEY%`
  - **Verify (PowerShell)**: `echo $env:GROQ_API_KEY`
  - **Evidence**:

- **Audit log path writable**
  - **Status**: optional
  - **Verify (CMD)**: `mkdir logs`
  - **Verify (PowerShell)**: `New-Item -ItemType Directory -Force logs | Out-Null`
  - **Evidence**:

---

## 7) What’s installed on this machine (fill as you go)

Paste a short snapshot here after you install/verify items above.

- **Date**:
- **Machine**:
- **Notes**:

