from __future__ import annotations

import logging

from ingestion import get_ipmp_store
from retrieval.interfaces.contracts import RetrievedChunk

from evaluation._config import get_llm_client, get_model, get_provider
from evaluation.interfaces.contracts import EvaluationResult, RejectedChunk
from evaluation.parsing.response import parse_llm_response
from evaluation.progress import report
from evaluation.prompt.builder import build_system_prompt, build_user_prompt
from evaluation.schemas import SCORER_SCHEMA

logger = logging.getLogger(__name__)

# Warn when evidence is large; hard-cap before it crowds out the system prompt + LLM output.
# Bounded by whichever provider's limit is tighter (see ADR-0019 amendment, 2026-06-23).
# Mistral's 32,768-token context allows ~77,000 chars of evidence, but Groq's on-demand
# account tier caps requests at 12,000 tokens/minute — measured at ~2.87 chars/token for
# this system prompt + evidence mix, that's the actual binding constraint: ~2,180 tokens
# system prompt + ~1,500 completion + ~10% margin leaves ~7,100 tokens (~21,000 chars).
EVIDENCE_CHAR_WARN_THRESHOLD = 15_000
_MAX_EVIDENCE_CHARS = 21_000

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
    rejected_chunks: list[RejectedChunk] | None = None,
) -> EvaluationResult:
    client = get_llm_client()  # raises if configure_llm() not called
    provider = get_provider()
    model = get_model()
    rejected_chunks = rejected_chunks or []

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
            rejected_chunks=rejected_chunks,
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

    report(
        "construindo_prompt",
        f"Montando prompt de avaliação da Ação {acao_id} ({len(chunks)} evidências).",
    )
    system_prompt = build_system_prompt(acao_id)
    user_prompt = build_user_prompt(chunks, acao_id=acao_id)
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

    report(
        "chamando_llm",
        f"Chamando avaliador (Ação {acao_id}) — {provider}/{model}...",
        "waiting",
    )
    raw = client.complete(system_prompt, user_prompt, schema=SCORER_SCHEMA)
    # Prefer the client's own reporting of what actually served the call —
    # matters when client is a FallbackLLMClient (ADR-0054) that may have
    # served this specific call from its secondary provider.
    actual_provider = getattr(client, "last_provider_used", None) or provider
    actual_model = getattr(client, "last_model_used", None) or model

    report("validando_resposta", f"Resposta recebida ({actual_provider}) — validando formato.")
    parsed = parse_llm_response(raw)
    if parsed.parse_failed:
        report(
            "validando_resposta",
            f"Resposta da Ação {acao_id} não pôde ser interpretada — marcada como falha de parsing.",
            "error",
        )
    else:
        report(
            "validando_resposta",
            f"Ação {acao_id} avaliada — score {parsed.proposed_score}"
            f"{' (incerteza sinalizada)' if parsed.uncertainty_flag else ''}.",
            "success",
        )

    return EvaluationResult(
        acao_id=acao_id,
        process_number=process_number,
        provider=actual_provider,
        model=actual_model,
        retrieved_chunks=chunks,
        rejected_chunks=rejected_chunks,
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
