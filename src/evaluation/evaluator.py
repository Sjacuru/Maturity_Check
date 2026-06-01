from __future__ import annotations

import logging

from ingestion import get_ipmp_store
from retrieval.interfaces.contracts import RetrievedChunk

from evaluation._config import get_llm_client, get_model, get_provider
from evaluation.interfaces.contracts import EvaluationResult
from evaluation.parsing.response import parse_llm_response
from evaluation.prompt.builder import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)

# Sits below Mistral 7B's 32K context window after accounting for the system prompt (~3-4k chars).
EVIDENCE_CHAR_WARN_THRESHOLD = 15_000


def evaluate(
    acao_id: int,
    process_number: str,
    chunks: list[RetrievedChunk],
) -> EvaluationResult:
    client = get_llm_client()  # raises if configure_llm() not called
    provider = get_provider()
    model = get_model()

    store = get_ipmp_store()
    if acao_id not in store.acoes:
        raise ValueError(
            f"acao_id {acao_id} not found in IPMPStore. "
            "Ensure the corresponding source-of-truth artifact is loaded."
        )

    if not chunks:
        return EvaluationResult(
            acao_id=acao_id,
            process_number=process_number,
            provider=provider,
            model=model,
            retrieved_chunks=[],
            evidence_char_count=0,
            system_prompt=None,
            user_prompt=None,
            raw_llm_response=None,
            reasoning=None,
            proposed_score=None,
            uncertainty_flag=False,
            parse_failed=False,
            no_evidence_found=True,
        )

    system_prompt = build_system_prompt(acao_id)
    user_prompt = build_user_prompt(chunks)
    evidence_char_count = sum(len(c.text) for c in chunks)

    logger.info(
        "evaluate acao_id=%d process=%s evidence_chars=%d chunks=%d",
        acao_id,
        process_number,
        evidence_char_count,
        len(chunks),
    )
    if evidence_char_count > EVIDENCE_CHAR_WARN_THRESHOLD:
        logger.warning(
            "evidence_char_count %d exceeds EVIDENCE_CHAR_WARN_THRESHOLD %d "
            "for acao_id=%d process=%s",
            evidence_char_count,
            EVIDENCE_CHAR_WARN_THRESHOLD,
            acao_id,
            process_number,
        )

    raw = client.complete(system_prompt, user_prompt)
    parsed = parse_llm_response(raw)

    return EvaluationResult(
        acao_id=acao_id,
        process_number=process_number,
        provider=provider,
        model=model,
        retrieved_chunks=chunks,
        evidence_char_count=evidence_char_count,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        raw_llm_response=parsed.raw_llm_response,
        reasoning=parsed.reasoning,
        proposed_score=parsed.proposed_score,
        uncertainty_flag=parsed.uncertainty_flag,
        parse_failed=parsed.parse_failed,
        no_evidence_found=False,
    )
