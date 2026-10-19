"""Teto por dependência (ADR-0070): sem 3 quando um pré-requisito não foi feito.

Regra do usuário (2026-10-09): "Ações que citam uma ou mais ações nas quais tais
ações não tiveram evidências ou não tiveram pontuação maior que zero não podem
receber pontuação 3, pois não há revisão ou confirmação do que não foi feito."

O que entra e o que não entra foi decidido aresta a aresta a partir da frase do
IPMP (data/ipmp/dependencias.json):

  * só as dependências `pre` limitam o score; `fraco` ("recomenda-se"),
    `sucessora`, `contraste`, `delega`, `sequencia` e `lacuna` (43: o exemplo
    Atendido do IPMP tem a Ação 28 não feita e a 43 a fazendo) não têm efeito;
  * `artefato` (a citante é a versão posterior do MESMO documento) não limita:
    o corpus não tem eixo de tempo, a versão final evidenciaria as duas Ações,
    e "citada vazia + citante cheia" é inconsistência do gate, não um estado do
    processo — vira revisão sugerida;
  * a base é o score PROPOSTO da mesma corrida (a citada precede a citante na
    ordem 1..46). Um ReviewOutcome da citada não se propaga: o score proposto
    da citante é imutável depois de persistido, e o auditor da citante decide
    com o teto à vista. Medido em 2026-10-09 (ADR-0070 §risco).
  * uma dependência não avaliada (falha, corrida parcial, parse_failed) não
    engata o teto: só a citada conhecidamente em 0 / sem evidência.
  * quando uma citada é REAVALIADA (ADR-0078), o seu score proposto muda e o
    teto das citantes é recalculado sobre os resultados gravados
    (`recompute_dependency_cap`): mesma evidência, mesmos vereditos, só a
    aritmética de novo. A revisão continua sem se propagar.

É aritmética sobre dados já existentes: mesma entrada, mesmo teto. Nada vai
para o prompt do scorer (decisão 4 de 2026-10-05).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from evaluation.interfaces.contracts import (
    DependencyCap,
    DependencyOutcome,
    EvaluationResult,
    ProductVerdict,
    ScoreMargin,
)
from evaluation.margin import compute_score_margin
from ingestion import get_ipmp_store
from ingestion.dependencias import Dependencia, DependencyStore

_CAP = 1


def _estado(prior: EvaluationResult | None) -> tuple[str, int | None]:
    if prior is None or prior.parse_failed:
        return "desconhecida", None
    if prior.no_evidence_found or prior.proposed_score == 0:
        return "baixa", prior.proposed_score
    if prior.proposed_score is None:
        return "desconhecida", None
    return "ok", prior.proposed_score


def _citante_evidenciou(
    d: Dependencia,
    proposed_score: int | None,
    verdicts: Sequence[ProductVerdict],
) -> bool:
    """Did the citing Ação evidence the part that is the later version of the
    cited artefact? Scoped edges look at their products; others at the score."""
    if d.produtos_citante:
        escopo = set(d.produtos_citante)
        return any(v.evidenced for v in verdicts if v.product_id in escopo)
    return proposed_score is not None and proposed_score >= 1


def compute_dependency_cap(
    acao_id: int,
    proposed_score: int | None,
    prior_results: Mapping[int, EvaluationResult],
    store: DependencyStore,
    product_verdicts: Sequence[ProductVerdict] = (),
) -> DependencyCap | None:
    """The cap for `acao_id` given the Ações already evaluated in this run.

    Returns None when the Ação has no dependency with effect — nothing to say.
    """
    deps = store.com_efeito(acao_id)
    if not deps:
        return None

    outcomes: list[DependencyOutcome] = []
    for d in deps:
        estado, score = _estado(prior_results.get(d.citada))
        outcomes.append(DependencyOutcome(
            acao_id=d.citada, tipo=d.tipo, estado=estado, proposed_score=score,
        ))

    baixas_pre = [o for o in outcomes if o.tipo == "pre" and o.estado == "baixa"]
    desconhecidas = [o for o in outcomes if o.estado == "desconhecida"]
    # review: the cited artefact's initial version was not evidenced while this
    # Ação evidenced its later version — per edge, honouring the product scope
    # (35.1 is the later version of Ação 14; 35.2a-g of Ação 15: a risk-plan
    # accept says nothing about the benefits plan).
    baixas_art = [
        o for o, d in zip(outcomes, deps)
        if d.tipo == "artefato" and o.estado == "baixa"
        and _citante_evidenciou(d, proposed_score, product_verdicts)
    ]

    applied = proposed_score == 3 and bool(baixas_pre)
    review = bool(baixas_art)

    partes: list[str] = []
    if applied:
        partes.append(
            f"Score limitado a {_CAP} (contado: 3): "
            + _lista("pré-requisito", baixas_pre)
            + " — não há revisão ou confirmação do que não foi feito."
        )
    elif baixas_pre:
        partes.append(
            "Teto não aplicado (score contado abaixo de 3), mas "
            + _lista("pré-requisito", baixas_pre) + "."
        )
    if review:
        partes.append(
            "Revisão sugerida: esta Ação é a versão posterior de documento cuja versão "
            "inicial não foi evidenciada — " + _lista("artefato", baixas_art)
            + " — verificar se o gate aplicou teste de estágio à versão inicial ou "
            "se a evidência desta é um falso positivo."
        )
    if desconhecidas:
        partes.append(
            "Dependência(s) não avaliada(s) nesta corrida: "
            + ", ".join(f"Ação {o.acao_id}" for o in desconhecidas)
            + " — o teto não engata sobre o desconhecido."
        )

    return DependencyCap(
        applied=applied,
        score_before_cap=proposed_score if applied else None,
        review_recommended=review,
        dependencies=outcomes,
        explanation=" ".join(partes),
    )


def apply_dependency_cap(
    proposed_score: int | None,
    score_margin: ScoreMargin | None,
    cap: DependencyCap | None,
) -> tuple[int | None, ScoreMargin | None]:
    """The score and the interval after the cap. Pure; never raises a score."""
    if cap is None or not cap.applied:
        return proposed_score, score_margin
    new_score = min(proposed_score, _CAP) if proposed_score is not None else None
    if score_margin is None:
        return new_score, None
    # ADR-0068's interval describes the COUNT; under a cap neither end can sit
    # above the cap. Nothing else about the margin changes: the fragile bits
    # and the band margin are still facts about the evidence.
    clip = lambda v: None if v is None else min(v, _CAP)  # noqa: E731
    return new_score, score_margin.model_copy(update={
        "score_floor": clip(score_margin.score_floor),
        "score_ceiling": clip(score_margin.score_ceiling),
    })


def recompute_dependency_cap(
    result: EvaluationResult,
    prior_results: Mapping[int, EvaluationResult],
    store: DependencyStore,
) -> EvaluationResult:
    """The stored `result` with its cap computed again against `prior_results`.

    Used after a cited Ação is re-evaluated (ADR-0078). The evidence and the
    scorer's verdicts of this Ação do not change, only the arithmetic over the
    scores it cites: the counted score is recovered from the stored cap, the
    margin is rebuilt from the stored evidence and verdicts exactly as
    evaluate() built it, and the new cap is applied. A no-evidence or
    parse-failed result never carries a cap and is returned unchanged.
    """
    if result.no_evidence_found or result.parse_failed:
        return result
    old = result.dependency_cap
    counted = old.score_before_cap if old is not None and old.applied else result.proposed_score
    expected = [
        p.id for p in get_ipmp_store().acoes[result.acao_id].produtos_esperados if p.scored
    ]
    margin = compute_score_margin(
        verdicts=list(result.product_verdicts),
        chunks=list(result.retrieved_chunks),
        expected_product_ids=expected,
        proposed_score=counted,
    )
    cap = compute_dependency_cap(
        result.acao_id, counted, prior_results, store,
        product_verdicts=result.product_verdicts,
    )
    score, margin = apply_dependency_cap(counted, margin, cap)
    return result.model_copy(update={
        "proposed_score": score, "score_margin": margin, "dependency_cap": cap,
    })


def _lista(rotulo: str, outcomes: list[DependencyOutcome]) -> str:
    def um(o: DependencyOutcome) -> str:
        estado = "sem evidência" if o.proposed_score is None else f"score {o.proposed_score}"
        return f"Ação {o.acao_id} ({estado})"
    return f"{rotulo}: " + ", ".join(um(o) for o in outcomes)
