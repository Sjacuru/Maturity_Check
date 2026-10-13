"""Legacy `real_world` query terms (ADR-0073) classified by canonicity.

The user's rule (2026-10-10): a query term must never be tailored to the
document it searches; a term from outside the IPMP is allowed when it is
canonical. The test applied term by term: is it general vocabulary of the
product's IPMP concept (or of the legislation / official manual that concept
relies on), valid for any document of any type? The 56 legacy terms (Ações 1,
3, 4, 5, 28) were added from the SMG-040 case documents in earlier Stage B
passes; their source is irrelevant, only canonicity decides.

- MANTER: canonical. Kept and relabelled `canonical`, source named.
- REMOVER: tailored. Removed. These terms carry this case's own phrasing, its
  goals, or its economic study and benchmarking read as the 1b panorama.
- SETORIAL: sector vocabulary not named by the criterion. It becomes
  `synthetic` and experimental with a sector_hint (ADR-0056). Experimental
  terms never reach BM25, so the retrieval effect equals removal.

Only REMOVER/SETORIAL terms that are `active` change retrieval (the BM25 lane;
the vector query is evidence_intent + concepts and does not read terms). All
15 such terms are in Ação 1 (1a, 1b, 1c, 1d). The gate prompt never contains
terms, so it is unchanged.

    reproducibility.py --runs 1 --acoes 1 --candidates THIS_FILE --apply 1a,1b,1c,1d

removes/demotes them in memory, so the change is measured across independent
processes before anything is written. It is adopted only if it measures as
more consistent (the user, 2026-10-10).
"""

# (term label, class, source or reason). The label is the phrase text, or
# "NEAR(tok, tok, ...)" for NEAR terms, exactly as in the profile.
CLASSIFICACAO = {
    "1a": [
        ("obsolescência", "MANTER", "IPMP (Ação 4); the concept text itself (existing_problem)"),
        ("NEAR(serviço, ineficiente)", "MANTER", "general deficiency vocabulary"),
        ("NEAR(serviço, deficiente)", "MANTER", "general deficiency vocabulary"),
        ("NEAR(falhas, prestação)", "MANTER", "IPMP (Ações 9, 24, 36, 42); 1a canonical 'falhas na prestação'"),
        ("NEAR(limitações, operacionais)", "MANTER", "IPMP (Ação 10)"),
        ("requalificação", "MANTER", "IPMP (Ações 19, 32, 36); stays experimental"),
        ("NEAR(demanda, crescente)", "MANTER", "1a canonical 'demanda crescente'; the concept text (public_demand)"),
        ("NEAR(continuidade, serviço)", "MANTER", "continuity of public service, Lei 8.987/1995 art. 6 par. 1; IPMP (Ação 46); stays experimental"),
        ("término da vigência", "MANTER", "general contract vocabulary for a re-procurement motive; same concept as 1a canonical 'vencimento contratual'"),
        ("NEAR(contrato, vencimento)", "MANTER", "same; 1a canonical 'vencimento contratual'"),
        ("NEAR(término, vigência)", "MANTER", "same"),
        ("NEAR(encerramento, contrato)", "MANTER", "same; 1a canonical 'encerramento contratual'"),
        ("NEAR(nova, contratação)", "MANTER", "same; 1a canonical 'necessidade de nova contratação'"),
        ("harmonização contratual", "REMOVER", "this case's own phrase; the general concept is covered by 1a canonical 'fragmentação contratual' / 'reorganização da gestão'"),
        ("NEAR(harmonização, contratual)", "REMOVER", "same"),
    ],
    "1b": [
        ("NEAR(panorama, econômico)", "MANTER", "the IPMP 1b criterion's own word; Rio Manual (socioeconomic annex, maps to 1b)"),
        ("estudo econômico de referência", "REMOVER", "the name of this edital's annex; the Rio Manual maps the socioeconomic annex, not this one, to 1b"),
        ("fluxo de caixa descontado", "REMOVER", "finance vocabulary of this case's economic study, read as 1b; not 1b's concept (the broader panorama)"),
        ("viabilidade econômico-financeira", "REMOVER", "same"),
        ("premissas básicas", "REMOVER", "same"),
        ("fluxo de caixa livre", "REMOVER", "same (experimental)"),
        ("receita projetada", "REMOVER", "same (experimental)"),
        ("custos operacionais", "REMOVER", "same (experimental)"),
        ("CAPEX", "REMOVER", "investment sizing of this case, not 1b's panorama; the Rio Manual lists CAPEX as project-description data (experimental)"),
        ("projetos análogos", "REMOVER", "this case's benchmarking; not in 1b's criterion"),
        ("NEAR(entes, federativos)", "REMOVER", "same benchmarking"),
        ("NEAR(investimentos, estimativa)", "REMOVER", "investment sizing of this case; not 1b's panorama"),
    ],
    "1c": [
        ("objetivos estratégicos", "MANTER", "the IPMP 1c criterion's own words"),
        ("NEAR(objetivos, projeto)", "MANTER", "IPMP wording"),
        ("segurança pública", "REMOVER", "one of this case's own goals; 1c names dimensions, not goals"),
        ("atualização tecnológica", "REMOVER", "one of this case's own goals"),
        ("NEAR(renovação, tecnológica)", "REMOVER", "one of this case's own goals"),
    ],
    "1d": [
        ("NEAR(alinhamento, política)", "MANTER", "IPMP (Ações 1, 39): consonance with public policies"),
        ("Lei Complementar Municipal", "MANTER", "Rio Manual (LC 105/2009, the municipal PPP law listed for Ação 1)"),
        ("NEAR(concessão, serviço, público)", "REMOVER", "this case's contracting model; not 1d's policy-alignment concept"),
        ("mobilidade urbana", "SETORIAL", "sector policy (Lei 12.587/2012) not named by 1d; sector transporte_publico"),
        ("NEAR(integração, mobilidade)", "SETORIAL", "same"),
    ],
    "3a": [
        ("parcelamento da solução", "MANTER", "Lei 14.133/2021 art. 18 par. 1 VIII (every ETP)"),
        ("NEAR(parcelamento, lotes)", "MANTER", "same"),
        ("parcelamento da contratação", "MANTER", "same"),
        ("NEAR(divisão, objeto, lotes)", "MANTER", "same (division of the object into lots); stays experimental"),
        ("estimativa de quantitativo", "MANTER", "Lei 14.133/2021 art. 18 par. 1 IV (estimated quantities)"),
        ("viabilidade técnica", "MANTER", "IPMP (Ações 4, 33)"),
        ("proposta inicial", "MANTER", "general synonym of a preliminary scope; stays experimental"),
        ("objeto pretendido", "MANTER", "procurement vocabulary; stays experimental"),
        ("NEAR(contratação, pretendida)", "MANTER", "procurement vocabulary; stays experimental"),
    ],
    "4a": [
        ("qualidade de vida", "MANTER", "IPMP (Ações 1, 19, 36); the concept text (social_benefits)"),
        ("NEAR(acessibilidade, segurança)", "MANTER", "the concept text (social_benefits); stays experimental"),
        ("sustentabilidade", "MANTER", "the concept text (environmental_benefits); stays experimental"),
    ],
    "4c": [
        ("restrições e condicionantes", "MANTER", "general wording of 4c's limiting factors"),
        ("bens tombados", "MANTER", "heritage protection, Decreto-Lei 25/1937: a standard legal restriction"),
        ("restrições urbanísticas", "MANTER", "urban-planning law restricts any project in a city, any sector"),
    ],
    "4d": [
        ("contratações correlatas", "MANTER", "Lei 14.133/2021 art. 18 par. 1 XI"),
        ("NEAR(contratações, correlatas, interdependentes)", "MANTER", "same"),
    ],
    "5b": [
        ("sustentabilidade financeira", "MANTER", "IPMP (Ações 10, 40, 43); stays experimental"),
    ],
    "28.3": [
        ("Lei de Responsabilidade Fiscal", "MANTER", "LC 101/2000, named LRF by the IPMP 28.3 criterion"),
    ],
}

ACAO = {"1a": 1, "1b": 1, "1c": 1, "1d": 1, "3a": 3, "4a": 4, "4c": 4, "4d": 4, "5b": 5, "28.3": 28}
SETOR = {"mobilidade urbana": "transporte_publico", "NEAR(integração, mobilidade)": "transporte_publico"}

# Case vocabulary inside a canonical field the search reads (concepts enter the
# vector query and the gate prompt). A scan of every intent and concept for
# words absent from all IPMP and Rio Manual texts and present in >= 20 chunks
# of the case found one case noun: "mobiliário" (307 chunks; sector
# mobiliario_urbano), in the 3a concept below. The rewrite takes the 3a
# intent's own wording ("os elementos, tipos de solução, lotes ou etapas").
CONCEITOS = {
    "3a": {
        "concrete_solution_description": (
            "Descrição concreta do que o projeto entregará ou executará — elementos, "
            "tipos de solução, lotes ou etapas —, com ou sem quantidades e custos"
        ),
    },
}

# What reproducibility.py --candidates reads: per product, the labels to
# remove, the labels to demote to synthetic/experimental, and concept texts
# to replace.
CANDIDATOS = {
    pid: {
        "acao": ACAO[pid],
        "remover_termos": [t for t, c, _ in linhas if c == "REMOVER"],
        "rebaixar_termos": [t for t, c, _ in linhas if c == "SETORIAL"],
        "conceitos_texto": CONCEITOS.get(pid, {}),
    }
    for pid, linhas in CLASSIFICACAO.items()
}
