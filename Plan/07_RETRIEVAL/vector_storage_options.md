# Vector and structured storage options (Rio v1)

**Policy:** [NFR-008](../01_PRD/prd.md) — case document text stays **local by default**; cloud is **opt-in** with explicit configuration.

**Deployment boundary (v1 baseline):** [nfr_008_deployment_boundary.md](nfr_008_deployment_boundary.md) — what may leave the environment, default local inference for case text, and how EPIC should branch on OQ-005.

**Architecture (approved):**

1. **Structured overlay** — Crosswalk + FR-001 data in **SQLite or Postgres** (JSON/JSONB columns or sidecar files). Source of truth for `tipo`, `grau`, citations.
2. **Case vector index** — Embeddings over **uploaded procurement PDF chunks** (primary retrieval).
3. **Reference vector index (optional)** — Embeddings over **M5D / Rio manual / IN TCDF** chunks for definitions and Q&A; **does not replace** the crosswalk.

---

## Option matrix (local first test vs employer cloud)

| Approach | Best for | NFR-008 / data | Notes |
|----------|----------|----------------|--------|
| **A. Local — LanceDB or Chroma + SQLite** | First dev laptop test, air-gapped demos | Strong — vectors on disk, no upload | **LanceDB** (file-based) or **Chroma** (persistent dir). Pair with **sentence-transformers** or **Ollama** embeddings locally. |
| **B. Local — Qdrant or Milvus (Docker)** | Team wanting a “real” vector server on LAN | Strong if Docker stays on-prem | More ops than A; good if you outgrow embedded DBs. |
| **C. Postgres + pgvector** | One DB for **rows + vectors** | Strong on-prem | Single stack; good when you already want Postgres for cases and audit logs. |
| **D. Azure AI Search (vector)** | Employer standard contract, managed service | **Opt-in** — procurement text leaves boundary unless you deploy **isolated** tenant / private link + legal sign-off | Fits “Azure signatures”; enable only after boundary doc (Topic H). |
| **E. Hugging Face Hub** | **Downloading embedding models** only | N/A for vectors (models are files) | Use **HF only to pull model weights** (e.g. `sentence-transformers`), not to store case embeddings. **Do not** send case PDFs to public HF Inference API under NFR-008 default. |
| **F. Hugging Face + private** | Rare: enterprise private hub | Possible with enterprise agreement | Usually overkill for v1; still treat case index as **your** deployment. |

---

## Recommendation for your situation

**Selected for this project (v0 / Phase 0):** **Option A** — **LanceDB** *or* **Chroma** on disk + **SQLite** for structured / crosswalk rows + **local** embedding model (e.g. multilingual MiniLM / BGE via `sentence-transformers` or **Ollama**). EPIC chooses LanceDB *vs* Chroma as a single implementation detail; default bias: **LanceDB** for a simple embedded file store.

1. **Phase 0 (first tests):** As above. No Hugging Face **API** for case text.
2. **Phase 1 (pilot with IT):** If the city mandates Azure, add **Azure AI Search** or **Postgres Flexible Server + pgvector** in a **dedicated** resource group, with **documented** opt-in (Topic H).
3. **Hugging Face:** Keep as **model registry**, not the **vector database** for case evidence.

---

## `retrieval_floor_stage2` (link to PRD)

Staged Rio-first retrieval must use **retrieval_floor_stage2** per **FR-008A** in the PRD. Calibrate the numeric value in **MDAP** within the **0.35–0.50** band (or justify another value with pilot metrics). See [retrieval_satisficing_rules.md](retrieval_satisficing_rules.md).
