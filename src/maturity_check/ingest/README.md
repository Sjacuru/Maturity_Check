# Ingestion (v0 slice)

This folder starts the first implementation slice: ingesting **M5D** as a static reference document.

## What is implemented

- **M5D markdown ingestion** into:
  - **SQLite** (`reference_documents`, `reference_chunks`) for deterministic storage and audit.
  - **LanceDB** table for a **reference vector index** (definitions/citations), enabled by default (disable with `--no-embed`).

## Run

From repo root:

```bash
python -m pip install -e .
maturity-check ingest-m5d
```

Outputs:
- `data/framework.sqlite`
- `data/lancedb/reference/` (unless `--no-embed`)

## Notes

- This is **reference ingestion**, not case-document ingestion.
- Case-document segmentation and FR-008D hybrid retrieval are implemented later, but this provides the static corpus required for “reference RAG” and for consistent citations.

## Hugging Face warning (`HF_TOKEN` / unauthenticated requests)

With `--embed`, **sentence-transformers** downloads **model weights** from the [Hugging Face Hub](https://huggingface.co/) the first time you use a model id (e.g. `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`). That is typically **free** for public model downloads; many orgs use it without a paid plan.

- **You are not sending your M5D text or case PDFs to Hugging Face** for this step — only **HTTP downloads** of weight files into your local cache.
- **`HF_TOKEN`** is **optional**: it can **increase** Hub rate limits and is required for some private/gated models. If you see throttling, create a token and set `HF_TOKEN` in your environment (see Hugging Face docs).
- **NFR-008:** case document text still must follow your deployment boundary doc; model downloads are not the same as sending procurement content to an inference API.

### Where the model weights live on disk

**sentence-transformers** / **huggingface_hub** cache downloads under your user profile (override with **`HF_HOME`** or **`HUGGINGFACE_HUB_CACHE`**). Typical locations:

- **Windows:** `%USERPROFILE%\.cache\huggingface\hub` (unless `HF_HOME` points elsewhere).
- **macOS / Linux:** `~/.cache/huggingface/hub`.

Those files are the **neural network weights** (and tokenizer assets). They are **not** stored inside LanceDB.

### How weights relate to LanceDB (reference index)

1. **Ingest with `--embed`:** the model runs **locally**, converts each reference chunk’s text into a **vector** (e.g. 384 floats), and LanceDB **persists those vectors** plus chunk metadata in the `reference_m5d_chunks` table.
2. **Vector search:** the same model encodes your **query** string into a vector; LanceDB does **similarity search** against the stored vectors.

So LanceDB holds **embeddings and metadata**; the **model weights** stay in the Hugging Face cache and are loaded whenever you construct `SentenceTransformer(...)`. Keyword search (`search-ref-sqlite`) uses **only SQLite** and never loads the embedding model.
