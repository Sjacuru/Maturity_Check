from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from retrieval.interfaces.contracts import RetrievedChunk

_VALID_SCORES = {0, 1, 3}


class EvaluationResult(BaseModel):
    acao_id: int
    process_number: str
    provider: str
    model: str
    retrieved_chunks: list[RetrievedChunk]
    evidence_char_count: int
    system_prompt: str | None
    user_prompt: str | None
    raw_llm_response: str | None
    reasoning: str | None
    proposed_score: int | None
    uncertainty_flag: bool
    parse_failed: bool
    no_evidence_found: bool

    @field_validator("proposed_score")
    @classmethod
    def _validate_score(cls, v: int | None) -> int | None:
        if v is not None and v not in _VALID_SCORES:
            raise ValueError(f"proposed_score must be one of {_VALID_SCORES} or None, got {v}")
        return v

    @model_validator(mode="after")
    def _validate_flag_invariants(self) -> EvaluationResult:
        if self.no_evidence_found:
            violations = []
            if self.system_prompt is not None:
                violations.append("system_prompt must be None when no_evidence_found=True")
            if self.user_prompt is not None:
                violations.append("user_prompt must be None when no_evidence_found=True")
            if self.raw_llm_response is not None:
                violations.append("raw_llm_response must be None when no_evidence_found=True")
            if self.reasoning is not None:
                violations.append("reasoning must be None when no_evidence_found=True")
            if self.proposed_score is not None:
                violations.append("proposed_score must be None when no_evidence_found=True")
            if self.uncertainty_flag:
                violations.append("uncertainty_flag must be False when no_evidence_found=True")
            if self.parse_failed:
                violations.append("parse_failed must be False when no_evidence_found=True")
            if violations:
                raise ValueError("; ".join(violations))
        if self.parse_failed:
            if self.reasoning is not None:
                raise ValueError("reasoning must be None when parse_failed=True")
            if self.proposed_score is not None:
                raise ValueError("proposed_score must be None when parse_failed=True")
        return self
