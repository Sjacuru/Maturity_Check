from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

_VALID_SCORES = {0, 1, 3}


class ReviewOutcome(BaseModel):
    acao_id: int
    process_number: str
    final_score: int
    is_override: bool
    justification: str | None
    evidence_references: list[int] | None
    created_at: datetime

    @field_validator("final_score")
    @classmethod
    def _validate_score(cls, v: int) -> int:
        if v not in _VALID_SCORES:
            raise ValueError(f"final_score must be one of {_VALID_SCORES}, got {v}")
        return v

    @model_validator(mode="after")
    def _validate_override_invariants(self) -> ReviewOutcome:
        if self.is_override:
            if not self.justification:
                raise ValueError(
                    "justification is required and must be non-empty when is_override=True"
                )
        else:
            if self.justification is not None:
                raise ValueError(
                    "justification must be None when is_override=False"
                )
        return self
