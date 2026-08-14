from __future__ import annotations

from evaluation._config import (
    configure_gate_llm,
    configure_gate_llm_client,
    configure_llm,
    configure_llm_client,
)
from evaluation.evaluator import evaluate
from evaluation.evidence_selection import EvidenceSelectionResult, select_evidence
from evaluation.interfaces.contracts import EvaluationResult, RejectedChunk

__all__ = [
    "configure_llm",
    "configure_gate_llm",
    "configure_llm_client",
    "configure_gate_llm_client",
    "evaluate",
    "select_evidence",
    "EvidenceSelectionResult",
    "EvaluationResult",
    "RejectedChunk",
]
