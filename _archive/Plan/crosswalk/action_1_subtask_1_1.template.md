# Crosswalk template — Ação 1 / sub-task 1.1

This document is **machine-readable JSON** embedded in Markdown so it can live in the repo without a separate `.json` path (rename or extract the block to `action_1_subtask_1_1.json` when your tooling requires it).

**Conventions:** `jurisdiction_layer` labels **anchor vs expander** metadata, not a mandatory “search Rio hooks then stop before TCDF” pipeline. **PRD FR-008A** requires **pooled** retrieval hooks per sub-task with ranking/aggregation. **`intencao.compose_order`** (JSON field) is only the order for **assembling intenção text in prompts** (Rio first, then TCDF). **Evaluated cases are Rio only.** `grau` is **retrieval weighting only**. `tipo` drives retrieval tier. See [Plan/07_RETRIEVAL/retrieval_satisficing_rules.md](../../07_RETRIEVAL/retrieval_satisficing_rules.md).

```json
{
  "schema_version": "0.2",
  "scope_note": "v0 implementation and crosswalk are anchored on M5D Ação 1. Full PRD remains multi-action; later actions may reuse schema with partial or full row changes.",
  "m5d_action_id": "action_1",
  "m5d_action_title_pt": "Descreva o projeto, seu contexto estratégico e objetivos estratégicos",
  "subtask": {
    "id": "1.1",
    "m5d_subtask_text_pt": "Escrever uma descrição breve e concisa do motivo pelo qual o projeto é necessário.",
    "intencao": {
      "compose_order": ["rio_manual", "tcdf_in_01_2024"],
      "by_source": [
        {
          "source_id": "rio_manual",
          "source_label": "Manual de Pré-Análise e Avaliação Estruturada — Município do Rio de Janeiro (volume citado no mapeamento)",
          "text_pt": "Justificar a existência do projeto e o problema a ser resolvido."
        },
        {
          "source_id": "tcdf_in_01_2024",
          "source_label": "Instrução Normativa nº 01/2024 — TCDF",
          "text_pt": "Estabelecer a fundamentação do projeto com base em uma carência real e diagnosticada."
        }
      ],
      "synthesized_text_pt": null,
      "notes": "compose_order orders intenção text in prompts only (Rio then TCDF). Artifact retrieval uses the full pooled set per FR-008A; see retrieval_satisficing_rules.md."
    },
    "expected_output_text_pt": "Porque o projeto é necessário — primeiro elemento do resultado esperado da Ação 1 («Um breve relatório estabelecendo…», M5D).",
    "complement_text_pt": null,
    "weight": null,
    "m5d_source_ref": "M5D.md — Cap. 3, Ação 1, item i e «Qual deve ser o resultado?» (primeiro marcador).",
    "notes": "Complemento null por OQ-002 regra Ação 1.1 — ver OQ-002_action1_complement_rule.md. Peso (FR-002) igual até definição externa."
  },
  "artifact_references": [
    {
      "artifact_id": "1.1-rio-001",
      "jurisdiction_layer": "rio_manual",
      "tipo": "Direta",
      "document_name_pt": "Publicação de Justificativa",
      "procedimento_pt": "Ato de publicação formal da justificativa",
      "descricao_pt": "Publicação contendo identificação do objeto e valor estimado da contratação.",
      "referencia_pt": "Quadro 12 (p. 47/116)",
      "grau": "Alto",
      "retrieval_notes_pt": "Primary Rio target for necessity / justification evidence.",
      "equivalence_group_id": null,
      "match_hints": {
        "filename_candidates": [],
        "heading_candidates": [],
        "notes": "Leave hints empty unless stable patterns exist in Rio case files."
      }
    },
    {
      "artifact_id": "1.1-rio-002",
      "jurisdiction_layer": "rio_manual",
      "tipo": "Indireta",
      "document_name_pt": "Aprovação de Estudos Técnicos",
      "procedimento_pt": "Validação interna da necessidade",
      "descricao_pt": "Aprovação pelo órgão promotor fundamentada em estudos técnicos prévios.",
      "referencia_pt": "Quadro 12 (p. 47/115)",
      "grau": "Alto",
      "retrieval_notes_pt": "Secondary Rio target; supports demonstrated technical validation of need.",
      "equivalence_group_id": null,
      "match_hints": {
        "filename_candidates": [],
        "heading_candidates": [],
        "notes": null
      }
    },
    {
      "artifact_id": "1.1-rio-003",
      "jurisdiction_layer": "rio_manual",
      "tipo": "Contextual",
      "document_name_pt": "Relatório de Viabilidade",
      "procedimento_pt": "Diagnóstico situacional",
      "descricao_pt": "Documento originado na fase de Avaliação que detalha a viabilidade técnica.",
      "referencia_pt": "Item 3 (p. 15/43)",
      "grau": "Médio",
      "retrieval_notes_pt": "Supporting / contextual evidence for necessity narrative.",
      "equivalence_group_id": null,
      "match_hints": {
        "filename_candidates": [],
        "heading_candidates": [],
        "notes": null
      }
    },
    {
      "artifact_id": "1.1-tcdf-001",
      "jurisdiction_layer": "tcdf_in_01_2024",
      "tipo": "Direta",
      "document_name_pt": "Relatório Diagnóstico da Situação Atual",
      "procedimento_pt": "Levantamento de dados de demanda e oferta",
      "descricao_pt": "Documento que descreve as necessidades a satisfazer e as condições técnicas atuais.",
      "referencia_pt": "Art. 4º, I, \"a\"",
      "grau": "Alto",
      "retrieval_notes_pt": "Apply after Rio tier in semantic expansion; synonym bridge for diagnostic necessity wording.",
      "equivalence_group_id": "necessity_diagnostic",
      "match_hints": {
        "filename_candidates": [],
        "heading_candidates": [],
        "notes": "Optional: link to Rio artifact via equivalence_group_id when cross-source merge is curated."
      }
    },
    {
      "artifact_id": "1.1-tcdf-002",
      "jurisdiction_layer": "tcdf_in_01_2024",
      "tipo": "Direta",
      "document_name_pt": "Resumo Executivo (Questionário)",
      "procedimento_pt": "Consolidação da fundamentação",
      "descricao_pt": "Item específico exigindo a descrição breve e concisa do motivo do projeto.",
      "referencia_pt": "Anexo I, item 2",
      "grau": "Alto",
      "retrieval_notes_pt": "Secondary TCDF direct tier; overlaps executive justification intent.",
      "equivalence_group_id": null,
      "match_hints": {
        "filename_candidates": [],
        "heading_candidates": [],
        "notes": null
      }
    },
    {
      "artifact_id": "1.1-tcdf-003",
      "jurisdiction_layer": "tcdf_in_01_2024",
      "tipo": "Indireta",
      "document_name_pt": "Relatório Fundamentado de Justificativa",
      "procedimento_pt": "Análise de conveniência e oportunidade",
      "descricao_pt": "Justificativa da escolha do projeto considerando a política pública setorial.",
      "referencia_pt": "Art. 4º, I, \"d\"",
      "grau": "Alto",
      "retrieval_notes_pt": "TCDF indirect tier; use for semantic recall when Rio labels differ.",
      "equivalence_group_id": null,
      "match_hints": {
        "filename_candidates": [],
        "heading_candidates": [],
        "notes": null
      }
    }
  ],
  "_field_guide": {
    "omit_from_v0_if_not_needed": [
      "synthesized_text_pt (keep null unless you approve a merged intenção line)",
      "equivalence_group_id (populate when Rio↔TCDF rows are explicitly paired)"
    ],
    "embedding_text_assembly_suggestion": "For dense retrieval queries, order intencao.by_source using intencao.compose_order, then add procedimento_pt + descricao_pt per artifact; dedupe and cap per tokenizer policy. Retrieval uses pooled hooks (FR-008A), not compose_order alone.",
    "removed_from_schema_v0": [
      "exact_file_name as a required column (unreliable in Rio case files; use match_hints when patterns are known)",
      "standalone information_chunk (redundant with descricao + procedimento + intenção; generate at ingest if needed)"
    ]
  }
}
```
