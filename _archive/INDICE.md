# _archive/ — índice

Material que saiu do desenvolvimento ativo e foi guardado, não apagado.
Nada aqui é lido pelo sistema nem pelos testes. Para recuperar um item,
`git mv` de volta ao caminho de origem.

| Caminho aqui | Origem | Arquivado em | Por quê |
|---|---|---|---|
| `PROMPTS/`, `Plan/`, `root_files/` | raiz e planejamento inicial | 2026-05-26 | planos e prompts da primeira arquitetura, anteriores aos ADRs |
| `scripts/*.py` (5 arquivos soltos) | `scripts/` | 2026-05-26 | inspeção de stores das primeiras versões |
| `scripts/apresentacoes/create_slides.py` | `scripts/` | 2026-11-15 | gera o deck de apresentação de junho (`docs/PPP_Maturity_Check_Slides.pptx`); não faz parte do sistema |
| `scripts/apresentacoes/create_professor_slides.py` | `scripts/` | 2026-11-15 | gera os 5 slides de andamento de julho para o orientador |
| `scripts/inspecao_por_acao/a3_inspect_retrieval_acao{3,4,5}.py` | `scripts/` | 2026-11-15 | cópias do modelo da Ação 2 que só trocam `ACAO_ID`; o rastreador `scripts/validation/rastreia_evidencia.py` cobre qualquer Ação e produto |
| `scripts/inspecao_por_acao/a4_inspect_evaluation_acao{3,4,5}.py` | `scripts/` | 2026-11-15 | idem, para o gate e o avaliador |
| `scripts/inspecao_por_acao/a3_inspect_retrieval.py`, `a4_inspect_evaluation.py` | `scripts/` | 2026-11-15 | o par da Ação 1, registro da arquitetura anterior ao gate, mantido sem alteração; o `a4` chamava `configure_llm(provider="ollama")`, função apagada com os clientes Groq e Ollama |

Ficou em `scripts/` só o par da Ação 2 (o modelo que
`docs/prompts/05_retrieval-profile-validation.md` manda copiar).
