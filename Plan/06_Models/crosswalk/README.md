# Crosswalk data (`Plan/06_Models/crosswalk`)

Machine-readable overlays that link **M5D** sub-tasks to **Rio Manual** and **IN 01/2024 TCDF** artifacts for retrieval and FR-008 classification.

## Conventions

- **`schema_version`**: bump when breaking structure changes.
- **`jurisdiction_layer`**: `rio_manual` (Rio **authority anchor**) and `tcdf_in_01_2024` (**vocabulary / semantic expansion**). Evaluated **cases** are **Rio** only. **Retrieval is from a pooled set of hooks per sub-task** (PRD **FR-008A**): do not treat “all Rio artifacts before any TCDF” as the required semantics unless a **staged** strategy meets FR-008A equivalence rules.
- **`tipo`**: `Direta` | `Indireta` | `Contextual` — retrieval tier (primary → secondary → supporting).
- **`grau`**: `Alto` | `Médio` | `Baixo` — **retrieval weighting only** (not a direct change to PRD numeric score formula).
- **`match_hints`**: optional strings for filename or heading hints; often **empty** in real cases (v0 still uses FR-008 steps 1–3). When a case-type manifest is available, `match_hints` will carry a **`document_registry_ids`** array pointing to entries in that manifest (see [Case-Type Manifest](#case-type-manifest) below).
- **Sub-task independence**: even when a “blueprint” applies across sub-tasks, each sub-task is **evaluated and maintained separately** and can diverge (artifacts, `grau`, complements).

## Files

| File | Purpose |
|------|---------|
| [action_1_subtask_1_1.template.md](action_1_subtask_1_1.template.md) | **Ação 1 / sub-task 1.1** — JSON (Rio + TCDF artifacts). |
| [action_1_subtasks_1_2_to_1_6.template.md](action_1_subtasks_1_2_to_1_6.template.md) | **Ação 1 / sub-tasks 1.2–1.6** — stored as one JSON `units` array for convenience; each unit is a **separate** sub-task evaluation object. |
| [VERIFICATION_FR008_action1.md](VERIFICATION_FR008_action1.md) | Checklist vs FR-008; M5D field gaps and TCDF 1.6 `grau` decision. |
| [OQ-002_action1_complement_rule.md](OQ-002_action1_complement_rule.md) | OQ-002: which sub-tasks carry **Quadro 11** / **Anexo 4** complements (Ação 1). |

## Case-Type Manifest

A companion file at [`../case_type_manifest/rio_ppp_v1.json`](../case_type_manifest/rio_ppp_v1.json) declares the **expected document types** for Rio PPP cases (not specific filenames — patterns and headings that work for any case of this type).

### Purpose
Improves FR-008 step 1 (exact/approximate filename match) and step 2 (heading match) without requiring pre-enumeration of per-case filenames. Works for both:
- **Individual files** — one physical file per document type → matched via `filename_patterns`
- **Combined file** — one large PDF/DOCX containing multiple document types as sections → matched via `heading_patterns` and `combined_file_section_hints`

### `document_registry_ids` field (future — not yet in templates)
Each artifact row's `match_hints` block will gain a `document_registry_ids` array once the manifest is stable:

```json
"match_hints": {
  "document_registry_ids": ["rio-LicAmbiental-001"],
  "filename_candidates": [],
  "heading_candidates": [],
  "notes": "..."
}
```

This lets the retrieval engine look up `filename_patterns`, `heading_patterns`, and `combined_file_section_hints` from the manifest at runtime, rather than duplicating them across artifact rows that reference the same physical document. **Crosswalk templates are not modified until the manifest schema reaches v1.0 and pilot results confirm pattern quality.**

### Cross-jurisdiction documents
Some physical documents are required by both Rio Manual and TCDF IN 01/2024 (e.g., Licença Ambiental Prévia). These appear **once** in the manifest under their primary `jurisdiction_layer` with a `cross_jurisdiction_note` field. Both TCDF and Rio artifact rows will reference the same `document_id`.

## Tooling (extract JSON for scripts)

Templates stay authoritative in Markdown. To emit standalone `.json` under `data/crosswalk/` (gitignored with `data/`):

```bash
python -m maturity_check.cli extract-crosswalk-md \
  Plan/06_Models/crosswalk/action_1_subtask_1_1.template.md \
  Plan/06_Models/crosswalk/action_1_subtasks_1_2_to_1_6.template.md
```
