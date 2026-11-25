from __future__ import annotations

import logging
from collections.abc import Mapping

from ingestion import get_dependency_store, get_ipmp_store
from retrieval.interfaces.contracts import RetrievedChunk

from evaluation._config import get_llm_client, get_model, get_provider
from evaluation.dependency_cap import apply_dependency_cap, compute_dependency_cap
from evaluation.interfaces.contracts import (
    EvaluationResult,
    ProductGateReport,
    ProductVerdict,
    RejectedChunk,
)
from evaluation.margin import compute_score_margin
from evaluation.parsing.response import combine_votes, parse_llm_response
from evaluation.progress import report
from evaluation.prompt.builder import build_system_prompt, build_user_prompt
from evaluation.schemas import SCORER_SCHEMA

logger = logging.getLogger(__name__)

# Warn when evidence is large; hard-cap before it crowds out the system prompt + LLM output.
#
# 21,000 -> 40,000 (2026-09-28). The old value was never derived from a context
# window: it was sized against Groq's on-demand tier rate limit of 12,000
# tokens/minute. Groq has been unwired since ADR-0059, so that constraint is
# gone, but the number it produced was still dropping real gated evidence —
# Run 1 lost 2 chunks on Ação 15 (24,406 -> 20,487 chars).
#
# Re-derived from this server, measured rather than assumed
# (scripts/diagnostics/measure_context_budget.py + measure_scorer_output.py):
#   * per-slot n_ctx = 32,000 (GET /props; 4 slots, 32,000 each)
#   * worst system prompt of all 46 Ações = 1,715 tokens (Ação 31)
#   * real corpus tokenizes at 3.11 chars/token (the old comment assumed 2.87)
#   * at 40,000 chars the worst-case prompt (Ação 31, 9 products, so the most
#     per-product block overhead) = 15,791 tokens
#   * scorer output over 10 real calls (5 Ações x 2 caps) = 988-1,649 tokens,
#     finish_reason=stop every time; it barely grows with evidence volume
#     because the reasoning channel dominates, not the per-product verdicts
# Worst case therefore lands at 15,791 + 1,649 = 17,440 of 32,000, leaving 45%
# of the slot spare. 40,000 covers the largest evidence set yet observed
# (24,406 chars) with 64% headroom, without pre-spending the context that
# raising _MAX_EXAMINED would need.
#
# The scorer client has no max_tokens (llamacpp.py), so this margin is what
# stands between a verbose reasoning burst and a truncated score.
# 40,000 -> 70,000 (2026-10-06), re-measured with the server's own tokenizer
# now that the prompts carry the sibling contrast (ADR-0064), the polarity
# sentence (ADR-0066) and _MAX_EXAMINED=16. At the worst Ação (31, 9 products):
# cap 40,000 = 15,717 prompt tokens; 60,000 = 21,842; 70,000 = 25,406;
# 80,000 = 28,727; 90,000 = 31,473; 100,000 overflows the 32,000-token slot.
# 70,000 leaves 6,594 tokens for the scorer's output, about 4x the worst of the
# 10 measured calls (988-1,649) — 80,000 would leave only 2x, and the scorer
# has no max_tokens, so a verbose reasoning burst would truncate the score.
# The largest real evidence set observed across five full passes is 33,891
# chars (Ação 4), so this cap is a safety net, not a working limit.
EVIDENCE_CHAR_WARN_THRESHOLD = 55_000
_MAX_EVIDENCE_CHARS = 70_000

# Repeated scorer calls on the same prompt, combined per Expected Product by
# combine_votes(). Deliberately 1: voting was implemented, measured over 20
# full passes and reverted — see ADR-0063. The votes are made back-to-back on a
# byte-identical prompt, which is the one condition under which this engine
# reproduces itself, so they come out near-copies of each other (verdicts split
# in 2 of 10 passes on Ação 3, 0 of 10 on Ação 14) and a majority over
# near-copies cannot reduce variance. Modal agreement did not move (Ação 3
# 90% -> 90%, Ação 14 50% -> 40%) and a pass cost +45% / +7%.
#
# combine_votes() and its tests stay in the tree, unwired at exactly this line:
# raising this number is all it takes to re-run the experiment.
_SCORER_VOTES = 1


def _truncation_order(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Round-robin over Expected Products: every product keeps its best chunk
    before any product keeps a second one.

    The score is a count over products (ADR-0058), so dropping a product's only
    chunk changes the score while dropping its third usually does not. The
    previous rule sorted by cascade step and put "vector" last, which penalised
    a lane ADR-0049 made co-equal to BM25 — with the fused RRF order already
    encoded in the list, a lane is no longer a priority signal.

    Chunks with no product attribution (the document-focused route, which
    bypasses the gate) come first: that route has no per-product structure to
    balance.
    """
    by_product: dict[str, list[RetrievedChunk]] = {}
    order: list[RetrievedChunk] = []
    seen: set[tuple[str, int, int]] = set()

    for c in chunks:
        if not c.expected_product_ids:
            key = (c.filename, c.page_number, c.chunk_index)
            if key not in seen:
                seen.add(key)
                order.append(c)
            continue
        for product_id in c.expected_product_ids:
            by_product.setdefault(product_id, []).append(c)

    for round_index in range(max((len(v) for v in by_product.values()), default=0)):
        for product_id in sorted(by_product):
            bucket = by_product[product_id]
            if round_index >= len(bucket):
                continue
            c = bucket[round_index]
            key = (c.filename, c.page_number, c.chunk_index)
            if key not in seen:
                seen.add(key)
                order.append(c)
    return order


def _cap_evidence(
    chunks: list[RetrievedChunk], acao_id: int, process_number: str
) -> list[RetrievedChunk]:
    total = sum(len(c.text) for c in chunks)
    if total <= _MAX_EVIDENCE_CHARS:
        return chunks
    priority_sorted = _truncation_order(chunks)
    kept: list[RetrievedChunk] = []
    running = 0
    for c in priority_sorted:
        if running + len(c.text) > _MAX_EVIDENCE_CHARS:
            break
        kept.append(c)
        running += len(c.text)
    # Membership is decided by the round-robin; the order the scorer reads is
    # still the assembled one (anchors in RRF order, per product block).
    kept_keys = {(c.filename, c.page_number, c.chunk_index) for c in kept}
    kept = [c for c in chunks if (c.filename, c.page_number, c.chunk_index) in kept_keys]
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
    product_gate_reports: list[ProductGateReport] | None = None,
    prior_results: Mapping[int, EvaluationResult] | None = None,
) -> EvaluationResult:
    """Evaluate one Ação.

    `prior_results` are the Ações already evaluated in this run, keyed by id;
    the dependency cap (ADR-0070) is derived from them. Callers that evaluate a
    single Ação in isolation may omit it — the cap is then not computed and the
    result says so (`dependency_cap is None`), which is NOT the same as "no cap
    applied": a measurement that must reproduce production has to pass them.
    """
    client = get_llm_client()  # raises if configure_llm_client() not called
    provider = get_provider()
    model = get_model()
    rejected_chunks = rejected_chunks or []
    product_gate_reports = product_gate_reports or []

    store = get_ipmp_store()
    if acao_id not in store.acoes:
        raise ValueError(
            f"acao_id {acao_id} not found in IPMPStore. "
            "Ensure the corresponding source-of-truth artifact is loaded."
        )

    # Hoisted above the no-evidence return so both exits can report a margin
    # over the same product set.
    expected_product_ids = [p.id for p in store.acoes[acao_id].produtos_esperados if p.scored]

    chunks = _cap_evidence(chunks, acao_id, process_number)

    if not chunks:
        return EvaluationResult(
            acao_id=acao_id,
            process_number=process_number,
            provider=provider,
            model=model,
            retrieved_chunks=[],
            rejected_chunks=rejected_chunks,
            product_gate_reports=product_gate_reports,
            score_margin=compute_score_margin(
                verdicts=[],
                chunks=[],
                expected_product_ids=expected_product_ids,
                proposed_score=None,
            ),
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

    # Sequential, not concurrent: the votes must be independent samples of the
    # same prompt, and putting them in flight together would add exactly the
    # kind of slot contention that the 2026-08-27 gate forensics identified as
    # a source of divergence. Three calls at ~8-10s each cost little next to
    # the gate work that precedes them.
    candidates = []
    actual_provider, actual_model = provider, model
    for vote in range(1, _SCORER_VOTES + 1):
        raw = client.complete(system_prompt, user_prompt, schema=SCORER_SCHEMA)
        # Prefer the client's own reporting of what served the call: the
        # model name the server returned (LlamaCppClient.last_model_used).
        actual_provider = getattr(client, "last_provider_used", None) or provider
        actual_model = getattr(client, "last_model_used", None) or model
        candidates.append(parse_llm_response(raw, expected_product_ids=expected_product_ids))
        if _SCORER_VOTES > 1:
            report(
                "chamando_llm",
                f"Ação {acao_id}: chamada {vote} de {_SCORER_VOTES} do avaliador "
                f"({actual_provider}).",
                "waiting",
            )

    report("validando_resposta", f"Resposta recebida ({actual_provider}) — validando formato.")
    parsed, n_verdict_splits = combine_votes(candidates, expected_product_ids)
    product_verdicts = [
        ProductVerdict(
            product_id=v.product_id,
            evidenced=v.evidenced,
            justificativa=v.justificativa,
        )
        for v in parsed.product_verdicts
    ]
    score_margin = compute_score_margin(
        verdicts=product_verdicts,
        chunks=chunks,
        expected_product_ids=expected_product_ids,
        proposed_score=parsed.proposed_score,
    )
    # ADR-0070: the cap is arithmetic over the scores already produced in this
    # run; it is applied AFTER the counted score and never touches the prompt.
    dependency_cap = None
    final_score = parsed.proposed_score
    if prior_results is not None and not parsed.parse_failed:
        dependency_cap = compute_dependency_cap(
            acao_id,
            parsed.proposed_score,
            prior_results,
            get_dependency_store(),
            product_verdicts=product_verdicts,
        )
        final_score, score_margin = apply_dependency_cap(
            parsed.proposed_score, score_margin, dependency_cap
        )
    if parsed.parse_failed:
        report(
            "validando_resposta",
            f"Resposta da Ação {acao_id} não pôde ser interpretada — marcada como falha de parsing.",
            "error",
        )
    else:
        if parsed.score_source == "computed":
            evidenced = sum(1 for v in parsed.product_verdicts if v.evidenced)
            detail = f" ({evidenced} de {len(parsed.product_verdicts)} produtos evidenciados)"
        else:
            detail = " (score informado pelo modelo — vereditos por produto inutilizáveis)"
        if n_verdict_splits:
            detail += (
                f"; as {_SCORER_VOTES} chamadas divergiram em {n_verdict_splits} "
                "produto(s) — incerteza sinalizada"
            )
        if score_margin.review_recommended:
            floor = (
                "sem evidência"
                if score_margin.score_floor is None
                else f"score {score_margin.score_floor}"
            )
            detail += (
                f"; {score_margin.n_fragile} produto(s) com margem 1 — o score cairia "
                f"para {floor} se não tivessem se sustentado (revisão sugerida)"
            )
        if dependency_cap is not None and (
            dependency_cap.applied or dependency_cap.review_recommended
        ):
            detail += f"; {dependency_cap.explanation}"
        report(
            "validando_resposta",
            f"Ação {acao_id} avaliada — score {final_score}{detail}"
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
        product_gate_reports=product_gate_reports,
        product_verdicts=product_verdicts,
        score_source=parsed.score_source,
        score_margin=score_margin,
        dependency_cap=dependency_cap,
        n_scorer_votes=len(candidates),
        n_verdict_splits=n_verdict_splits,
        evidence_char_count=evidence_char_count,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        raw_llm_response=parsed.raw_llm_response,
        reasoning=parsed.reasoning,
        proposed_score=final_score,
        uncertainty_flag=parsed.uncertainty_flag,
        parse_failed=parsed.parse_failed,
        no_evidence_found=False,
    )
