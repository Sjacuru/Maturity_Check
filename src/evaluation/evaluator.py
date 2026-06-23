from __future__ import annotations

import logging

from ingestion import get_ipmp_store
from retrieval.interfaces.contracts import RetrievedChunk

from evaluation._config import get_llm_client, get_model, get_provider
from evaluation.interfaces.contracts import EvaluationResult
from evaluation.parsing.response import parse_llm_response
from evaluation.prompt.builder import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)

# Warn when evidence is large; hard-cap before it crowds out the system prompt + LLM output.
# Calibrated against Mistral 7B's real 32,768-token context window (see ADR-0019 amendment,
# 2026-06-23): ~1,869 tokens system prompt + ~1,500 tokens completion + ~10% safety margin
# leaves ~25,800 tokens (~77,000 chars at 3.0 chars/token for Portuguese) for evidence.
# 50,000/35,000 are clean, conservative values well under that computed ceiling.
EVIDENCE_CHAR_WARN_THRESHOLD = 35_000
_MAX_EVIDENCE_CHARS = 50_000

_CASCADE_PRIORITY = {"filename_match": 0, "variant_match": 1, "bm25": 2, "regex": 3, "vector": 4}


def _cap_evidence(
    chunks: list[RetrievedChunk], acao_id: int, process_number: str
) -> list[RetrievedChunk]:
    total = sum(len(c.text) for c in chunks)
    if total <= _MAX_EVIDENCE_CHARS:
        return chunks
    priority_sorted = sorted(
        chunks,
        key=lambda c: (
            _CASCADE_PRIORITY[c.cascade_step],
            (c.bm25_score or 0.0) if c.cascade_step == "bm25" else 0.0,
            c.chunk_index,
        ),
    )
    kept: list[RetrievedChunk] = []
    running = 0
    for c in priority_sorted:
        if running + len(c.text) > _MAX_EVIDENCE_CHARS:
            break
        kept.append(c)
        running += len(c.text)
    logger.warning(
        "Evidence truncated: acao_id=%d process=%s dropped %d chunks (%d→%d chars)",
        acao_id,
        process_number,
        len(chunks) - len(kept),
        total,
        running,
    )
    return kept


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

    chunks = _cap_evidence(chunks, acao_id, process_number)

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
