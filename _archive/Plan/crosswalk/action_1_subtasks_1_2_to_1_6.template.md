# Crosswalk — Ação 1 / sub-tasks 1.2 through 1.6

Same conventions as [action_1_subtask_1_1.template.md](action_1_subtask_1_1.template.md).

## How to use this file

- **Each sub-task (1.2–1.6) is a separate evaluation unit.** Even when sub-tasks share patterns, retrieval hooks, or complement logic, they are **looked at independently** and can diverge over time (different artifacts, different `grau`, different complement pointer, etc.).
- **This file is a storage convenience.** The JSON keeps a single array `units`; each element is one sub-task (`subtask` + `artifact_references`). In implementation, you may split these into separate JSON objects per sub-task without changing semantics.
- **Blueprint vs unit overrides:** any shared rule (e.g., complement linkage / default weighting) is treated as a **blueprint**, but each unit is authoritative for its own fields.

**TCDF 1.6** artifact `1.6-tcdf-003` (**Análise de Influência Cruzada**): **`grau` = `Baixo`** (decision record em [VERIFICATION_FR008_action1.md](VERIFICATION_FR008_action1.md)).

**M5D fields:** `m5d_subtask_text_pt`, `expected_output_text_pt`, `complement_text_pt` preenchidos a partir do M5D; regra de complementos em [OQ-002_action1_complement_rule.md](OQ-002_action1_complement_rule.md).

```json
{
  "schema_version": "0.2",
  "m5d_action_id": "action_1",
  "m5d_action_title_pt": "Descreva o projeto, seu contexto estratégico e objetivos estratégicos",
  "units": [
    {
      "subtask": {
        "id": "1.2",
        "m5d_subtask_text_pt": "Descrever a estratégia da Autoridade e as estratégias governamentais mais amplas relevantes para mostrar o contexto dentro do qual a Proposta de Investimento deve ser desenvolvida, incluindo a Estratégia de Infraestrutura Nacional, Estratégias Ministeriais e Estratégias de Desenvolvimento Regional.",
        "intencao": {
          "compose_order": [
            "rio_manual",
            "tcdf_in_01_2024"
          ],
          "by_source": [
            {
              "source_id": "rio_manual",
              "source_label": "Manual Rio — Pré-Análise (volume citado no mapeamento)",
              "text_pt": "Demonstrar conexão com as políticas públicas e planos de governo."
            },
            {
              "source_id": "tcdf_in_01_2024",
              "source_label": "IN 01/2024 — TCDF",
              "text_pt": "Garantir que o projeto esteja inserido no planejamento de longo prazo do ente federado."
            }
          ],
          "synthesized_text_pt": null,
          "notes": null
        },
        "expected_output_text_pt": "Como o projeto se encaixa no contexto estratégico mais amplo do governo — segundo marcador de «Qual deve ser o resultado?» (Ação 1, M5D).",
        "complement_text_pt": "QUADRO 11 (M5D, Cap. 3, Ação 1): diretrizes e planos orientadores dos investimentos em infraestrutura — internacionais (ODS); nacionais (EFD, Dec. 10.531/2020, NDCs); regionais (política nacional de desenvolvimento regional, PRDNE/PRDA/PRDCO, PDUI); locais (Planos Diretores e planos setoriais); setoriais (PNL, PNSH, PNE, PERT, PLANARES, PLANSAB, etc.). Texto integral no M5D (Cap. 3, Ação 1, Quadro 11).",
        "weight": null,
        "notes": "Complemento = Quadro 11 (OQ-002_action1_complement_rule.md).",
        "m5d_source_ref": "M5D.md — Cap. 3, Ação 1, item ii; Quadro 11."
      },
      "artifact_references": [
        {
          "artifact_id": "1.2-rio-001",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Direta",
          "document_name_pt": "Plano Estratégico Municipal",
          "procedimento_pt": "Consulta e enquadramento estratégico",
          "descricao_pt": "O projeto deve ser submetido à análise baseada no Plano Estratégico vigente.",
          "referencia_pt": "Etapa 1 (p. 7/20)",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.2-rio-002",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Direta",
          "document_name_pt": "Parecer da Casa Civil (CVL)",
          "procedimento_pt": "Análise de conveniência e mérito",
          "descricao_pt": "Manifestação sobre o enquadramento do projeto nas políticas públicas municipais.",
          "referencia_pt": "Quadro 12 (p. 47/117)",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.2-rio-003",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Indireta",
          "document_name_pt": "Decreto de Inclusão no PROPAR-RIO",
          "procedimento_pt": "Edição de ato pelo Prefeito",
          "descricao_pt": "Decreto que oficializa a inclusão do projeto no programa de parcerias estratégico.",
          "referencia_pt": "Etapa 9 (p. 11/30)",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.2-tcdf-001",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Direta",
          "document_name_pt": "Demonstrativo de Compatibilidade com o PPA",
          "procedimento_pt": "Verificação de conformidade orçamentária",
          "descricao_pt": "Comprovação de que a solução está alinhada às diretrizes e metas do Plano Plurianual.",
          "referencia_pt": "Anexo I, item 26",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.2-tcdf-002",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Indireta",
          "document_name_pt": "Relatório de Admissibilidade",
          "procedimento_pt": "Parecer jurídico e técnico inicial",
          "descricao_pt": "Avaliação sobre a forma de desestatização e seu enquadramento legal.",
          "referencia_pt": "Art. 4º, I, \"g\"",
          "grau": "Médio",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        }
      ]
    },
    {
      "subtask": {
        "id": "1.3",
        "m5d_subtask_text_pt": "Definir os Objetivos Estratégicos que a Proposta de Investimento apoia e que devem estar alinhados com os objetivos da Autoridade em questões sociais, ambientais, culturais, geográficas, éticas ou políticas (lista exemplificativa de critérios no M5D, item iii).",
        "intencao": {
          "compose_order": [
            "rio_manual",
            "tcdf_in_01_2024"
          ],
          "by_source": [
            {
              "source_id": "rio_manual",
              "source_label": "Manual Rio",
              "text_pt": "Estabelecer metas SMART e ganhos para a população."
            },
            {
              "source_id": "tcdf_in_01_2024",
              "source_label": "IN 01/2024 — TCDF",
              "text_pt": "Definir resultados esperados e melhorias qualitativas e quantitativas."
            }
          ],
          "synthesized_text_pt": null,
          "notes": null
        },
        "expected_output_text_pt": "Um conjunto de Objetivos Estratégicos — terceiro marcador de «Qual deve ser o resultado?» (Ação 1, M5D).",
        "complement_text_pt": null,
        "weight": null,
        "notes": "Complemento null (OQ-002); critérios em lista no M5D, não em quadro separado nesta ação.",
        "m5d_source_ref": "M5D.md — Cap. 3, Ação 1, item iii."
      },
      "artifact_references": [
        {
          "artifact_id": "1.3-rio-001",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Direta",
          "document_name_pt": "Relatório de Avaliação de Benefícios",
          "procedimento_pt": "Análise de mérito social pelo CGP",
          "descricao_pt": "Análise específica sobre os benefícios que o projeto trará para a população.",
          "referencia_pt": "Etapa 8 (p. 10/22)",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.3-rio-002",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Indireta",
          "document_name_pt": "Especificações de Desempenho",
          "procedimento_pt": "Definição de metas contratuais",
          "descricao_pt": "Tradução dos objetivos estratégicos em requerimentos de performance técnica.",
          "referencia_pt": "Item 10 (p. 44/109)",
          "grau": "Médio",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.3-tcdf-001",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Direta",
          "document_name_pt": "Relatório de Objetivos e Resultados",
          "procedimento_pt": "Definição de metas e indicadores",
          "descricao_pt": "Indicação preliminar dos resultados, ganhos globais e vantagens da contratação.",
          "referencia_pt": "Art. 4º, I, \"c\"",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.3-tcdf-002",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Direta",
          "document_name_pt": "Planilha de Melhorias Esperadas",
          "procedimento_pt": "Quantificação de benefícios",
          "descricao_pt": "Detalhamento de melhorias em termos de economia, eficiência e eficácia.",
          "referencia_pt": "Anexo I, item 9",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        }
      ]
    },
    {
      "subtask": {
        "id": "1.4",
        "m5d_subtask_text_pt": "Mostrar como os Objetivos Estratégicos promovem o desenvolvimento sustentável, especialmente em relação ao gênero e à inclusão, e como estão alinhados com os compromissos internacionais, como os Objetivos de Desenvolvimento Sustentável (ODS) da ONU ou as Contribuições Nacionalmente Determinadas (NDCs).",
        "intencao": {
          "compose_order": [
            "rio_manual",
            "tcdf_in_01_2024"
          ],
          "by_source": [
            {
              "source_id": "rio_manual",
              "source_label": "Manual Rio",
              "text_pt": "Integrar sustentabilidade social, ambiental e inclusão."
            },
            {
              "source_id": "tcdf_in_01_2024",
              "source_label": "IN 01/2024 — TCDF",
              "text_pt": "Integrar compromissos internacionais e ações de equidade no projeto."
            }
          ],
          "synthesized_text_pt": null,
          "notes": null
        },
        "expected_output_text_pt": "Trecho do relatório breve sobre sustentabilidade, gênero, inclusão e alinhamento a ODS/NDCs (Ação 1, item iv, M5D).",
        "complement_text_pt": "Anexo 4 do M5D — Estrutura de Gênero e Inclusão; citado nos itens iv e v da Ação 1. Consultar o anexo no PDF oficial do guia para cláusulas, declarações de impacto e níveis de ambição.",
        "weight": null,
        "notes": "Complemento remete ao Anexo 4 onde o item v o exige explicitamente; item iv cita ODS/NDCs (OQ-002).",
        "m5d_source_ref": "M5D.md — Cap. 3, Ação 1, item iv; remissões a ODS/NDCs."
      },
      "artifact_references": [
        {
          "artifact_id": "1.4-rio-001",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Indireta",
          "document_name_pt": "Plano Ambiental",
          "procedimento_pt": "Gestão de impactos ambientais",
          "descricao_pt": "Parte da proposta técnica que detalha a conformidade com normas ambientais.",
          "referencia_pt": "Item 7.3.1 (p. 33/88)",
          "grau": "Médio",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.4-rio-002",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Contextual",
          "document_name_pt": "Análise de Performance Social",
          "procedimento_pt": "Verificação de viabilidade técnica",
          "descricao_pt": "Consideração de aspectos de performance e impacto social na estruturação.",
          "referencia_pt": "Item 10 (p. 44/109)",
          "grau": "Baixo",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.4-tcdf-001",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Direta",
          "document_name_pt": "Checklist de ODS e Padrões IFC",
          "procedimento_pt": "Verificação de sustentabilidade",
          "descricao_pt": "Declaração se a solução atende aos critérios dos Objetivos de Desenvolvimento Sustentável.",
          "referencia_pt": "Anexo I, item 17",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.4-tcdf-002",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Direta",
          "document_name_pt": "Relatório de Impacto Social (Gênero)",
          "procedimento_pt": "Avaliação de inclusão social",
          "descricao_pt": "Descrição de como o projeto melhora oportunidades para mulheres e grupos vulneráveis.",
          "referencia_pt": "Anexo I, item 11",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.4-tcdf-003",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Indireta",
          "document_name_pt": "Minuta de Edital/Contrato",
          "procedimento_pt": "Inclusão de cláusulas afirmativas",
          "descricao_pt": "Previsão de obrigações contratuais ligadas à igualdade de gênero e inclusão.",
          "referencia_pt": "Anexo I, item 82",
          "grau": "Médio",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        }
      ]
    },
    {
      "subtask": {
        "id": "1.5",
        "m5d_subtask_text_pt": "Incluir uma declaração que resuma, em alto nível, os possíveis impactos ambientais e sociais e a ambição geral do projeto (consulte o Anexo 4), e uma declaração que determine o nível de ambição do projeto em relação à Estrutura de Gênero e Inclusão (Anexo 4).",
        "intencao": {
          "compose_order": [
            "rio_manual",
            "tcdf_in_01_2024"
          ],
          "by_source": [
            {
              "source_id": "rio_manual",
              "source_label": "Manual Rio",
              "text_pt": "Listar potenciais impactos e o nível de mitigação esperado."
            },
            {
              "source_id": "tcdf_in_01_2024",
              "source_label": "IN 01/2024 — TCDF",
              "text_pt": "Identificar riscos socioambientais precocemente para mitigação."
            }
          ],
          "synthesized_text_pt": null,
          "notes": null
        },
        "expected_output_text_pt": "Trecho do relatório breve sobre impactos socioambientais, ambição geral e ambição em relação à Estrutura de Gênero e Inclusão (Ação 1, item v, M5D).",
        "complement_text_pt": "Anexo 4 do M5D — Estrutura de Gênero e Inclusão; citado nos itens iv e v da Ação 1. Consultar o anexo no PDF oficial do guia para cláusulas, declarações de impacto e níveis de ambição.",
        "weight": null,
        "notes": "Complemento = Anexo 4 (OQ-002).",
        "m5d_source_ref": "M5D.md — Cap. 3, Ação 1, item v; Anexo 4."
      },
      "artifact_references": [
        {
          "artifact_id": "1.5-rio-001",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Direta",
          "document_name_pt": "Licença Ambiental Prévia (ou Diretrizes)",
          "procedimento_pt": "Protocolo junto ao órgão ambiental",
          "descricao_pt": "Documento obrigatório para o lançamento da licitação de PPP.",
          "referencia_pt": "Quadro 12 (p. 48/118)",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.5-rio-002",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Indireta",
          "document_name_pt": "Due Diligence Ambiental",
          "procedimento_pt": "Investigação de riscos técnicos",
          "descricao_pt": "Análise de passivos e riscos que podem inviabilizar a implementação.",
          "referencia_pt": "Item 2 (p. 14/42)",
          "grau": "Médio",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.5-tcdf-001",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Direta",
          "document_name_pt": "Avaliação de Impacto Ambiental e Social (AIAS)",
          "procedimento_pt": "Estudo técnico de impactos",
          "descricao_pt": "Documento que fundamenta os riscos e a solução escolhida sob a ótica ambiental.",
          "referencia_pt": "Anexo I, item 18",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.5-tcdf-002",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Direta",
          "document_name_pt": "Cópia da Licença Ambiental Prévia",
          "procedimento_pt": "Licenciamento formal",
          "descricao_pt": "Licença ou diretrizes fixadas pelo órgão ambiental competente para a licitação.",
          "referencia_pt": "Art. 4º, III",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        }
      ]
    },
    {
      "subtask": {
        "id": "1.6",
        "m5d_subtask_text_pt": "Descrever como quaisquer programas e projetos existentes podem influenciar o projeto.",
        "intencao": {
          "compose_order": [
            "rio_manual",
            "tcdf_in_01_2024"
          ],
          "by_source": [
            {
              "source_id": "rio_manual",
              "source_label": "Manual Rio",
              "text_pt": "Identificar projetos ou programas que afetam a proposta."
            },
            {
              "source_id": "tcdf_in_01_2024",
              "source_label": "IN 01/2024 — TCDF",
              "text_pt": "Mapear interdependências e organizações afetadas pelo empreendimento."
            }
          ],
          "synthesized_text_pt": null,
          "notes": null
        },
        "expected_output_text_pt": "Trecho do relatório breve sobre influência de programas/projetos existentes (Ação 1, item vi, M5D), no mesmo documento dos três marcadores de «Qual deve ser o resultado?».",
        "complement_text_pt": null,
        "weight": null,
        "notes": "Complemento null (OQ-002).",
        "m5d_source_ref": "M5D.md — Cap. 3, Ação 1, item vi."
      },
      "artifact_references": [
        {
          "artifact_id": "1.6-rio-001",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Indireta",
          "document_name_pt": "Data Room de Licitação",
          "procedimento_pt": "Mapeamento de passivos e sucessões",
          "descricao_pt": "Disponibilização de dados sobre contratos anteriores ou influências externas.",
          "referencia_pt": "Item 7.1.4 (p. 27/68)",
          "grau": "Médio",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.6-rio-002",
          "jurisdiction_layer": "rio_manual",
          "tipo": "Contextual",
          "document_name_pt": "Due Diligence Regulatória",
          "procedimento_pt": "Verificação de riscos de falha",
          "descricao_pt": "Análise legal sobre propriedade de terrenos ou riscos técnicos que afetam o escopo.",
          "referencia_pt": "Item 10 (p. 44/110)",
          "grau": "Médio",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.6-tcdf-001",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Direta",
          "document_name_pt": "Matriz de Organizações Afetadas",
          "procedimento_pt": "Mapeamento de stakeholders",
          "descricao_pt": "Identificação de quais organizações ou órgãos são envolvidos ou afetados pelo projeto.",
          "referencia_pt": "Anexo I, item 4",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.6-tcdf-002",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Indireta",
          "document_name_pt": "Relatório de Interdependências",
          "procedimento_pt": "Análise de interface regional",
          "descricao_pt": "Identificação de dependências locais ou regionais que podem limitar benefícios.",
          "referencia_pt": "Anexo I, item 14",
          "grau": "Alto",
          "retrieval_notes_pt": null,
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        },
        {
          "artifact_id": "1.6-tcdf-003",
          "jurisdiction_layer": "tcdf_in_01_2024",
          "tipo": "Contextual",
          "document_name_pt": "Análise de Influência Cruzada",
          "procedimento_pt": "Verificação de conflitos de projetos",
          "descricao_pt": "Avaliação de impacto em outros projetos em desenvolvimento pelo Poder Concedente.",
          "referencia_pt": "Art. 16, IV",
          "grau": "Baixo",
          "retrieval_notes_pt": "Contextual + Art. 16, IV: apoio a conflitos/interdependências entre projetos; grau Baixo para não dominar o pool Rio+TCDF (TCDF como expansor lexical). Alternativas: Médio se quiser peso igual a outros Indiretos; Alto apenas se priorizar recall agressivo de conflitos cruzados.",
          "equivalence_group_id": null,
          "match_hints": {
            "filename_candidates": [],
            "heading_candidates": [],
            "notes": null
          }
        }
      ]
    }
  ],
  "_field_guide": {
    "tcdf_1_6_grau": "Confirmado: Análise de Influência Cruzada (1.6-tcdf-003) com grau Baixo — alinhado a tipo Contextual e papel de hook TCDF; ver VERIFICATION_FR008_action1.md."
  }
}
```
