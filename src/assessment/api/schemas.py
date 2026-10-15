from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

_VALID_SCORES = {0, 1, 3}


class GateOverrideRequest(BaseModel):
    """Write-side body for POST /evaluations/{acao_id}/gate-overrides (ADR-0067):
    the auditor overturns one recorded gate verdict, identified by the ledger
    key shown on the chunk. Takes effect on the next assessment of the case."""

    prompt_hash: str
    relevant: bool
    justification: str

    @field_validator("prompt_hash")
    @classmethod
    def _validate_hash(cls, v: str) -> str:
        if len(v) != 64 or any(c not in "0123456789abcdef" for c in v):
            raise ValueError("prompt_hash must be a 64-char lowercase hex SHA-256")
        return v

    @field_validator("justification")
    @classmethod
    def _validate_justification(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("justification is required and must be non-empty")
        return v.strip()


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

    @field_validator("justification")
    @classmethod
    def _strip_justification(cls, v: str | None) -> str | None:
        # A note of blanks is no note (ADR-0023): strip it, so the invariant
        # below sees it empty, and store the text without the padding.
        return v.strip() if v is not None else None

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
