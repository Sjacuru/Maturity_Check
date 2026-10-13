"""Ação 1: 1b's concepts and 1d's first negative pattern made canonical (ADR-0073).

Found on 2026-10-10 (62nd pass) and accepted by the user the same day:

- 1b. Three of its four concepts were written in Ação 1's Stage B from this
  case's own economic study (economic_viability_study, benchmarking,
  investment_scale). The IPMP 1b criterion asks for "o panorama mais amplo em
  que o projeto se insere, considerando os cenários econômico, social e
  ambiental relevantes", and the Ação's description says "Contextualizar o
  panorama econômico, social e ambiental em que o projeto se enquadra". They are
  replaced, in place, by the criterion's three scenarios. The fourth concept
  (socioeconomic_panorama) is already general and stays.
- 1d. Its first negative pattern names this case's sector ("sem
  correspondência com o setor de mobiliário urbano (PNL, PDE, Plansab, PNLP são
  inaplicáveis a este setor)"). For a sanitation project it would tell the gate
  to reject the Plansab, an instrument 1d's own criterion lists. It is rewritten
  sector-neutral on the criterion's own qualifier, "quando for aplicável".

Concepts reach the gate prompt and the vector query as text only, in list
order (relevance_builder; retrieval/query/hybrid.py), never by key. Measuring
with the old keys and the new texts (conceitos_texto) therefore builds the same
prompts and the same vector query as the written profile, where the keys are
renamed in the same positions (CHAVES_1B). The 1d replacement keeps the
pattern's position (negativos_substitui).

    reproducibility.py --runs 1 --acoes 1 --candidates THIS_FILE --apply 1b,1d

LOGICA holds the matching rewrites of evidence_logic_patterns. They are
written together with the rest so the profile stays coherent. They are not
measured: no consumer reads that field (src/ingestion/retrieval_profile.py
declares it; nothing else does).

Measured across independent processes on 2026-10-10, ledger off, through the
SSH tunnel to the owner's instance (scratchpad/acc/a1can_*, a1d_cand*). The
gate walks 1a, 1b, 1c and 1d in that order, and each product has its own
pool, so one joint run separates the two changes:

- 1b, NOT applied. Five current and five candidate processes, interleaved
  (--apply 1b,1d). The scenario texts change 1b's vector query and so its
  examined pool: 11 chunks enter and 10 leave. One entrant, the edital's
  justification of the procurement (_1 p.2), was accepted for 1b in 1 of 5
  processes; the reasoning took 1b for 1a's IPMP text, and the same process
  accepted the page for 1c. Score 1 in all ten, but the identical batch per
  pair of processes fell from 100 % to 30 %. Less constant, so it is not
  written under the user's rule; canonicity against this measured cost is the
  user's decision, as for the 3a concept.
- 1d, applied. Its pool did not change and its 16 examined chunks were
  rejected in every process. Five more processes with --apply 1d alone gave
  the same batch in all five, equal to that of eleven current-state processes,
  and 16/16 rejections for 1d. Written by textual edit together with its two
  LOGICA notes; only 1d's gate prompt changed, and the written profile builds
  the same 164 gate prompts as this candidate applied in memory.
"""

CONCEITOS_1B = {
    "economic_viability_study": (
        "Cenário econômico em que o projeto se insere: dados e condições da "
        "economia da região ou do setor afetado (atividade econômica, renda, emprego)"
    ),
    "benchmarking": (
        "Cenário social em que o projeto se insere: população atendida ou "
        "afetada pelo projeto e suas condições sociais"
    ),
    "investment_scale": (
        "Cenário ambiental em que o projeto se insere: condições, recursos e "
        "restrições ambientais da área da intervenção"
    ),
}
CHAVES_1B = {
    "economic_viability_study": "economic_scenario",
    "benchmarking": "social_scenario",
    "investment_scale": "environmental_scenario",
}

NEGATIVO_1D_ANTIGO = (
    "Citação isolada de planos nacionais setoriais sem correspondência com o "
    "setor de mobiliário urbano (PNL, PDE, Plansab, PNLP são inaplicáveis a este setor)"
)
NEGATIVO_1D_NOVO = (
    "Citação isolada de instrumento oficial de planejamento federal de setor "
    "diferente do setor do projeto, sem correspondência com o objeto: o "
    "instrumento só demonstra aderência quando for aplicável ao setor do próprio projeto"
)

# evidence_logic_patterns (dormant): old text -> new text, per product.
LOGICA = {
    "1b": {
        "Estudo econômico-financeiro de referência com modelagem de fluxo de caixa, CAPEX, estrutura de receitas e custos operacionais": (
            "Seção de contextualização que descreve o cenário econômico, social "
            "e/ou ambiental em que o projeto se insere, com dados do contexto da intervenção"
        ),
        "Análise comparativa com concessões de porte similar realizadas por outros entes federativos": (
            "Diagnóstico do contexto regional ou setorial afetado pelo projeto "
            "(população, atividade econômica, condições ambientais), anterior à definição da solução"
        ),
        "Seção que contextualiza o mercado setorial: dimensionamento da receita esperada, benchmarks de custo, estrutura de tributação": (
            "Contextualização da intervenção com dados confiáveis do cenário em "
            "que o projeto se desenvolve"
        ),
    },
    "1d": {
        "Menção à integração com programas de mobilidade urbana municipal como BRT, bicicletas compartilhadas ou sistema de transporte integrado": (
            "Menção à integração do projeto com programas setoriais vigentes do "
            "ente responsável, do mesmo setor do projeto"
        ),
        "Nota: para concessões de mobiliário urbano, o alinhamento é com planejamento municipal — a ausência de referências a planos nacionais setoriais (PNL, PDE, Plansab) é esperada e não configura não atendimento": (
            "Nota: quando nenhum instrumento oficial de planejamento federal for "
            "aplicável ao setor do projeto, o alinhamento é demonstrado com o "
            "planejamento regional ou local (PPA, LOA, LDO, plano estratégico do "
            "ente) — a ausência de planos nacionais setoriais é então esperada e "
            "não configura não atendimento"
        ),
    },
}

CANDIDATOS = {
    "1b": {"acao": 1, "conceitos_texto": CONCEITOS_1B},
    "1d": {"acao": 1, "negativos_substitui": {NEGATIVO_1D_ANTIGO: NEGATIVO_1D_NOVO}},
}
