from __future__ import annotations

from evaluation._config import configure_llm
from evaluation.evaluator import evaluate
from evaluation.interfaces.contracts import EvaluationResult

__all__ = ["configure_llm", "evaluate", "EvaluationResult"]
