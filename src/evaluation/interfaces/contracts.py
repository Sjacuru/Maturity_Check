from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from retrieval.interfaces.contracts import RetrievedChunk

_VALID_SCORES = {0, 1, 3}


class RejectedChunk(BaseModel):
    """A candidate the relevance gate (ADR-0050) classified as not relevant.

    Recorded for auditor visibility into what was found and discarded per
    product. matched_concepts lists concept keys whose query terms appeared in
    the chunk text even though the gate rejected it — a non-empty list is a
    signal worth auditor review (possible gate miss or marginal relevance).
    """

    filename: str
    page_number: int
    chunk_index: int
    expected_product_id: str
    matched_concepts: list[str] = []

    # Whether the gate actually reached a verdict on this chunk. True means the
    # call broke (unparseable response, token-cap truncation, transport error)
    # and the chunk was dropped WITHOUT being judged — not that it was found
    # irrelevant. Until 2026-09-27 the two were conflated, so a broken call
    # looked exactly like a rejection; 65% of (Ação, product) pairs in the
    # 2026-09-07 run rejected 100% of their candidates and there was no way to
    # tell how much of that was real. Defaults preserve older persisted rows.
    gate_failed: bool = False
    gate_failure_reason: str | None = None

    # Which provider/model actually decided. EvaluationResult.provider is the
    # SCORER's, so before these fields a gate served by a different model left
    # no trace at all in the audit trail.
    gate_provider: str | None = None
    gate_model: str | None = None

    # The gate model's reasoning channel for this call, verbatim. With a
    # one-boolean schema this is the only justification a rejection has; the
    # 2026-10-02 study read 1 749 of these to find the confounds that became
    # canonical profile fixes. None when the call failed or the model has no
    # reasoning channel; absent on rows persisted before 2026-10-03.
    gate_reasoning: str | None = None

    # ADR-0067: "model" | "ledger" | "auditor", and the ledger key the auditor
    # overrides by. None on failed calls, when no ledger is configured, and on
    # rows persisted before 2026-10-03.
    gate_source: str | None = None
    gate_prompt_hash: str | None = None


class ProductVerdict(BaseModel):
    """The scorer's judgement on one Expected Product.

    The 0/1/3 rubric is a count over these, so recording them makes the score
    auditable: the auditor can see which product the model considered evidenced
    and why, instead of only a single number and a prose paragraph.
    """

    product_id: str
    evidenced: bool
    justificativa: str = ""


class ProductGateReport(BaseModel):
    """Per-Expected-Product gate telemetry for one evaluation.

    Makes "this product had no evidence" a first-class, auditable outcome
    instead of something inferred from the absence of chunks. n_candidates vs
    n_examined shows how much of the retrieved pool _MAX_EXAMINED discarded
    before any judgement; n_gate_failures separates broken calls from real
    rejections; providers/models record who decided.
    """

    expected_product_id: str
    n_candidates: int          # after the genre filter and pre-gate near-duplicate removal
    n_examined: int            # actually sent to the gate (<= _MAX_EXAMINED)
    n_accepted: int            # anchors accepted for this product
    n_rejected: int            # judged and found irrelevant
    n_gate_failures: int = 0   # call broke — NOT a rejection
    providers: list[str] = []  # distinct provider labels that served this product
    models: list[str] = []     # distinct model labels that served this product
    n_ledger_hits: int = 0     # verdicts answered from the gate ledger (ADR-0067)
    # ADR-0074: candidates removed before the cut because their document is
    # instrument text (always 0 for a genre-exempt product), and neighbours of
    # accepted chunks not gated for the same reason (any product, exempt ones
    # included). Both 0 when the genre filter is off.
    n_genre_excluded: int = 0
    n_neighbors_genre_excluded: int = 0

    @property
    def no_evidence(self) -> bool:
        return self.n_accepted == 0


class ProductMargin(BaseModel):
    """How much accepted evidence holds one Expected Product's `evidenced` bit.

    n_accepted counts the accepted chunks the SCORER actually saw attributed to
    this product — after pre-gate dedup, post-gate dedup and _cap_evidence, so
    it is the real support, not the gate's gross count.

    `fragile` marks the one case the chain makes deterministic: an evidenced
    product supported by exactly ONE accepted chunk. Lose that chunk and
    build_user_prompt emits "NENHUMA evidência foi recuperada para este Produto
    Esperado", so the bit necessarily turns off — no judgement involved. With
    two or more accepts, losing one leaves evidence and the bit depends on the
    scorer, which is not deterministic and is therefore not claimed here.

    Why it matters (measured 2026-10-04 over two independent cold runs of the
    same frozen configuration): the gate's rejections are near-deterministic
    (1.7 % flip) but its ACCEPTS are close to coin-flips (38.5 %), and only
    48 % of ever-accepted chunks were accepted by both runs. 8 of the 13
    product-bit flips observed came from products held by a single accept.
    """

    product_id: str
    evidenced: bool
    n_accepted: int
    fragile: bool = False


class ScoreMargin(BaseModel):
    """The deterministic uncertainty around a counted score (ADR-0058).

    Two margins, as decided 2026-10-05: per product (how many accepts hold the
    bit, in `products`) and per Ação (`band_margin` — how many bits must flip to
    change the 0/1/3 band, in either direction).

    `score_floor` is the reported interval's lower end: the score obtained when
    every fragile bit turns off at once, or None when nothing accepted would
    remain (i.e. the Ação would come out `sem evidência`, not 0). `score_ceiling`
    is the current score — no upward claim is made, because a rejection flipping
    to accept is not deterministic from one pass.

    Same input gives the same score AND the same interval, so this does not
    touch the reproducibility constraint. Nothing here is fed to the scorer
    (ADR-0058 deliberately took the count out of the model's judgement); it is
    reported beside the score and read by the auditor.
    """

    products: list[ProductMargin] = []
    n_products: int = 0
    n_evidenced: int = 0
    n_fragile: int = 0
    # Steps to the nearest band change, counting bit flips in either direction.
    # None when there are no scored products to count over.
    band_margin: int | None = None
    score_floor: int | None = None
    score_ceiling: int | None = None
    # False when the evidence carries no per-product attribution at all — the
    # document-focused Step A/B route bypasses the gate (ADR-0050), so there is
    # nothing to count accepts against and the per-product margin does not
    # apply. Stated rather than silently reported as zero.
    attribution_complete: bool = True
    # The auditor's signal (optional review, decided 2026-10-05): True only when
    # a fragile bit falling would actually move the band. Measured volume is
    # under 10 per case, so it stays legible.
    review_recommended: bool = False
    # One deterministic sentence naming what happened in the system's own
    # process, for the auditor to read beside the score.
    explanation: str = ""


class DependencyOutcome(BaseModel):
    """One dependency of this Ação and the state the cited Ação was found in."""

    acao_id: int
    tipo: str                     # "pre" | "artefato"
    # "baixa" (0 or sem evidência), "ok" (>= 1), "desconhecida" (not evaluated,
    # parse failure, or absent from the run).
    estado: str
    proposed_score: int | None = None


class DependencyCap(BaseModel):
    """ADR-0070: the score cap derived from the cited Ações' outcomes.

    Deterministic arithmetic over scores that already exist when this Ação is
    evaluated (the run walks the Ações in order 1..46): an Ação with a `pre`
    dependency found in 0 / sem evidência cannot receive 3, so a counted 3 is
    recorded in `score_before_cap` and `proposed_score` becomes 1. An `artefato`
    dependency in that state does NOT cap — the citing Ação is a later version
    of the same document and the corpus has no time axis — it recommends review
    instead. Nothing here reaches the scorer prompt.
    """

    applied: bool = False
    score_before_cap: int | None = None
    review_recommended: bool = False
    dependencies: list[DependencyOutcome] = []
    explanation: str = ""


class EvaluationResult(BaseModel):
    acao_id: int
    process_number: str
    provider: str
    model: str
    retrieved_chunks: list[RetrievedChunk]
    rejected_chunks: list[RejectedChunk] = []
    # One entry per scored Expected Product the gate examined. Empty for
    # document-focused (Step A/B) routing, which bypasses the gate entirely,
    # and for rows persisted before 2026-09-27.
    product_gate_reports: list[ProductGateReport] = []
    # Per-product verdicts the score was computed from, plus which of the two
    # paths produced proposed_score. Empty / "model" for rows persisted before
    # 2026-09-27 and whenever the model's verdicts were unusable.
    product_verdicts: list[ProductVerdict] = []
    score_source: str = "model"

    # Deterministic uncertainty around the counted score: how many accepts hold
    # each product's bit, how far the Ação sits from a band change, and the
    # resulting score interval. Computed in code from the verdicts and the
    # accepted chunks — no model call, no extra cost. None for rows persisted
    # before 2026-10-05; the read path is json.loads(raw_json) (ADR-0031) and
    # does not re-validate, so older rows keep serving unchanged.
    score_margin: ScoreMargin | None = None
    # ADR-0070. None for rows persisted before 2026-10-09, for the no-evidence
    # exit, and when the caller had no prior results to derive it from.
    dependency_cap: DependencyCap | None = None

    # How many scorer calls were combined, and on how many Expected Products
    # they disagreed. A split is the auditor's signal that the model did not
    # agree with itself on this Ação — information a single call discards
    # entirely. Defaulted so rows persisted before 2026-09-29 still validate;
    # the read path is json.loads(raw_json) (ADR-0031) and does not re-validate.
    n_scorer_votes: int = 1
    n_verdict_splits: int = 0
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
