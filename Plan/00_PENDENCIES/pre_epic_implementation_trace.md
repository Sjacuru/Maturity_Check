# Pre-EPIC implementation trace (reconcile with EPIC later)

Use this file so **early spikes** do not get lost when you run the **EPIC prompt**. After EPIC is written, walk this list and either (a) map each item to an EPIC story/MDAP task, or (b) mark it superseded.

| Area | What exists in repo | Intended EPIC home (suggested) | Notes |
|------|---------------------|--------------------------------|-------|
| M5D reference ingest | `maturity-check ingest-m5d` → SQLite `reference_*` | Module 1 / reference corpus | Chunks + hashes; optional LanceDB |
| Reference keyword search | `maturity-check search-ref-sqlite` | Module 1 / dev tooling → later API | `LIKE` on `reference_chunks.text` |
| Reference vector search | `maturity-check search-ref-vector` | Module 1 / reference RAG | LanceDB + local `sentence-transformers` |
| Crosswalk templates | `Plan/06_Models/crosswalk/*.template.md` (JSON-in-MD) | Module 1 overlay + Module 3 retrieval policy | **FR-008A hook list** lives here; not yet wired into retrieval code |
| Crosswalk JSON extract | `maturity-check extract-crosswalk-md` → `data/crosswalk/*.json` | Same | Optional export for loaders/tests (`data/` gitignored) |
| Case hybrid FR-008D | Not implemented yet | Module 2–3 | BM25 + dense + RRF on **case** segments |

**Process:** When EPIC lands, add a column “EPIC ID” or link to your tracker; do not delete this file until every row is mapped or closed.

---

## Model weights vs LanceDB

- **Downloaded weights** (Hugging Face Hub cache, e.g. `%USERPROFILE%\.cache\huggingface\hub` on Windows) are the **SentenceTransformer** model files.
- **LanceDB** stores **per-chunk vectors** produced *by* that model at ingest time, plus `chunk_id`, `text`, etc.
- **Not the only interaction:** the model also runs at **query time** to embed the search string. SQLite keyword search does **not** use the model or LanceDB.

## Crosswalk “sequence” in **current** Python code

**There is no FR-008A/B/C retrieval sequence implemented in code yet.** The pipeline today is only:

1. Read `M5D.md` → chunk → SQLite (`reference_chunks`).
2. Optionally embed chunks → LanceDB.
3. Search reference by substring (SQLite) or by vector (LanceDB).

The **crosswalk** defines the future ordering policy (**pooled hooks**, `tipo` / `grau` tiers, staged floor, etc.) in **Markdown + embedded JSON**; that policy is specified in [Plan/07_RETRIEVAL/retrieval_satisficing_rules.md](../07_RETRIEVAL/retrieval_satisficing_rules.md) and the PRD (**FR-008A–D**). Wiring hooks → queries → fusion → evidence packets is **post–reference-spike** work.

---

## Suggested next pre-EPIC engineering steps

1. **Load extracted JSON** in Python (validate `schema_version`, list `artifact_id` per sub-task).
2. **Join crosswalk text** with `reference_chunks` or a future normative segment store (Rio/TCDF PDFs when ingested).
3. **Prototype FR-008D** on a **case** segment index (sparse + dense + RRF), then apply overlay weighting from crosswalk metadata.
