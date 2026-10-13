from __future__ import annotations

from evaluation._config import (
    configure_gate_ledger,
    configure_gate_llm,
    configure_gate_llm_client,
    configure_llm,
    configure_llm_client,
)
from evaluation.gate_ledger import GateLedger
from evaluation.evaluator import evaluate
from evaluation.evidence_selection import (
    GATE_MAX_IN_FLIGHT,
    EvidenceSelectionResult,
    filter_focal_document,
    select_evidence,
)
from evaluation.interfaces.contracts import (
    EvaluationResult,
    ProductGateReport,
    ProductMargin,
    ProductVerdict,
    RejectedChunk,
    ScoreMargin,
)

__all__ = [
    "GATE_MAX_IN_FLIGHT",
    "configure_llm",
    "configure_gate_llm",
    "configure_llm_client",
    "configure_gate_llm_client",
    "configure_gate_ledger",
    "GateLedger",
    "evaluate",
    "select_evidence",
    "filter_focal_document",
    "EvidenceSelectionResult",
    "EvaluationResult",
    "ProductGateReport",
    "ProductMargin",
    "ProductVerdict",
    "RejectedChunk",
    "ScoreMargin",
]
