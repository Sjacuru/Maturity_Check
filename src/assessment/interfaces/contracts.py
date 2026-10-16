from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

_VALID_SCORES = {0, 1, 3}

# The Ações the auditor may mark "não aplicável" (ADR-0076). The Guide keeps it an
# absolute exception (4.1) and names its typical case: Ações 45 and 46, the
# selection of the winning bidder and the signing of the contract, in a project
# that has not reached that stage yet. The user scoped it to those two.
NOT_APPLICABLE_ACOES = frozenset({45, 46})


class ReviewOutcome(BaseModel):
    acao_id: int
    process_number: str
    # None only when the auditor marks the Ação not applicable (ADR-0076).
    final_score: int | None
    is_override: bool
    justification: str | None
    evidence_references: list[int] | None
    created_at: datetime
    # The auditor's "não aplicável" (ADR-0076): no score, out of the nota's
    # denominator, and the motivation the Guide asks for in `justification`.
    # Missing evidence is never this: it stays "não atendida" (Guide 4.1).
    not_applicable: bool = False

    @field_validator("final_score")
    @classmethod
    def _validate_score(cls, v: int | None) -> int | None:
        if v is not None and v not in _VALID_SCORES:
            raise ValueError(f"final_score must be one of {_VALID_SCORES}, got {v}")
        return v

    @model_validator(mode="after")
    def _validate_override_invariants(self) -> ReviewOutcome:
        if self.not_applicable:
            if self.acao_id not in NOT_APPLICABLE_ACOES:
                raise ValueError(
                    f"not_applicable is admitted only for Ações {sorted(NOT_APPLICABLE_ACOES)}"
                )
            if self.final_score is not None or self.is_override:
                raise ValueError(
                    "a not-applicable review has no final_score and is not an override"
                )
            if not self.justification or not self.justification.strip():
                raise ValueError(
                    "justification is required and must be non-empty when not_applicable=True"
                )
            return self
        if self.final_score is None:
            raise ValueError("final_score is required unless not_applicable=True")
        if self.is_override:
            if not self.justification or not self.justification.strip():
                raise ValueError(
                    "justification is required and must be non-empty when is_override=True"
                )
        else:
            if self.justification is not None:
                raise ValueError(
                    "justification must be None when is_override=False"
                )
        return self


class AcaoPoints(BaseModel):
    """One Ação's contribution to the maturity indicator (ADR-0075)."""

    acao_id: int
    titulo: str
    dimensao: str
    fase: str
    ponto_transicao: bool
    # The points counted: the auditor's final score when a review exists, else
    # the proposed score (after the dependency cap, ADR-0070), else 0 for
    # `sem evidência`. None when there is nothing to count yet, and for an Ação
    # the auditor marked not applicable, which leaves the count (ADR-0076).
    points: int | None
    source: Literal[
        "review", "not_applicable", "proposed", "no_evidence", "unscored", "not_evaluated"
    ]
    # ADR-0068's optional-review signal while it is still open: the Ação has no
    # review and a fragile product falling would move its band.
    review_recommended: bool = False
    # The points if every fragile product fell at once (the ADR-0068 floor,
    # `sem evidência` counting 0); equal to `points` when no review is open.
    floor_points: int | None


class MaturityGroup(BaseModel):
    """The nota over a set of Ações: the whole case, one dimension, one phase
    or the transition points."""

    label: str
    acao_ids: list[int]
    n_counted: int
    # Marked not applicable by the auditor (ADR-0076): out of the count, and
    # not a gap, so the group stays complete.
    n_not_applicable: int
    points: int
    max_points: int  # 3 x n_counted
    nota: float | None  # points / max_points; None when nothing is counted
    floor_points: int
    nota_floor: float | None
    complete: bool  # every Ação of the group is counted or not applicable


class MaturityIndicator(BaseModel):
    """The IPMP nota of one case and its breakdowns (ADR-0075)."""

    process_number: str
    overall: MaturityGroup
    # The Guide's reading of the overall nota against its two reference limits.
    band: Literal["alert", "intermediate", "satisfactory"] | None
    alert_below: float
    satisfactory_above: float
    by_dimension: list[MaturityGroup]
    by_phase: list[MaturityGroup]
    transition_points: MaturityGroup
    n_reviewed: int
    acoes: list[AcaoPoints]
