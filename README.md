# Maturity Check (M5D Evaluation System)

Repository for the **M5D Evaluation System** — tooling to support public auditors in evaluating procurement case documents against the **Modelo de Cinco Dimensões (M5D)** framework (Brazilian public procurement context).

## Current state

At this stage the repo mainly holds **planning and reference material**:

- **[Plan/01_PRD/prd.md](Plan/01_PRD/prd.md)** — Product requirements
- **[Plan/00_PENDENCIES/pendencias_pre_epic.md](Plan/00_PENDENCIES/pendencias_pre_epic.md)** — Open decisions before EPIC
- **[UNIVERSAL_PHASE_GATES.md](UNIVERSAL_PHASE_GATES.md)** — Governance for PRD → EPIC → MDAP → architecture
- **[M5D.md](M5D.md)** — Secondary/dev copy of the M5D guide text (canonical source for framework ingest is the official PDF per project decisions)

Application code (Python, LangGraph, local LLM integration, etc.) will be added as the implementation phase proceeds.

## How to use this repository

1. **Clone**

   ```bash
   git clone https://github.com/<your-org>/Maturity_Check.git
   cd Maturity_Check
   ```

2. **Read the PRD and pendências** before contributing or running future tooling.

3. **Run the project** — There is no single runnable application yet. When code is added (e.g. `requirements.txt`, `pyproject.toml`, or a `src/` package), this README will be updated with install and run commands (virtual environment, local LLM setup, and any PDF ingestion pipeline).

## Contributing

- Follow the phase gates in `UNIVERSAL_PHASE_GATES.md` (human review between planning artifacts).
- Do not commit secrets (`.env` is ignored — see `.gitignore`).

## License

Add a `LICENSE` file when you choose a license for this repository.
