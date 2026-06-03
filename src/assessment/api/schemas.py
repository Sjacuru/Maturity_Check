from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

_VALID_SCORES = {0, 1, 3}


class ReviewSubmission(BaseModel):
    """Write-side request body for POST /evaluations/{acao_id}/review."""

    final_score: int
    is_override: bool
    justification: str | None = None
    evidence_references: list[int] | None = None

    @field_validator("final_score")
    @classmethod
    def _validate_score(cls, v: int) -> int:
        if v not in _VALID_SCORES:
            raise ValueError(f"final_score must be one of {_VALID_SCORES}, got {v}")
        return v

    @model_validator(mode="after")
    def _validate_override_invariants(self) -> ReviewSubmission:
        if self.is_override:
            if not self.justification:
                raise ValueError(
                    "justification is required and must be non-empty when is_override=True"
                )
        else:
            if self.justification is not None:
                raise ValueError("justification must be None when is_override=False")
        return self
