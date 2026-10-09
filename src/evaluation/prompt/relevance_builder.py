from __future__ import annotations

from typing import TYPE_CHECKING

from rapidfuzz import fuzz

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ingestion.ipmp import AcaoIPMP

# The polarity sentence (2026-10-03, ADR-0066): the model read "evidência DESTE
# Produto" as evidence THAT the product is satisfied, so a parecer stating that
# the required declaration was NOT met (Ação 26, p.136) was rejected 4/4 and the
# only place the process treated the criterion never reached the scorer or the
# auditor. Measured as variant P1 at serial+low on 26 (must flip) and on
# 14/22/3 (must not move) before shipping; see the ADR for the numbers.
_INSTRUCTIONS = """\
Considere o trecho em português, mesmo que contenha termos em outro idioma. \
Um trecho que trate diretamente do que este critério pede é relevante mesmo \
quando registra que o item NÃO foi atendido, não foi elaborado ou não se \
aplica a este processo — julgar o cumprimento é da etapa seguinte, não deste \
classificador; isso não torna relevante um trecho que apenas mencione o tema \
sem tratar do elemento exigido. Preencha o campo "relevant" do objeto JSON \
de resposta com true (relevante) ou false (não relevante). Nenhum outro \
campo é esperado.\
"""

# The gate judged a criterion without ever being told which Ação or which
# Expected Product it belonged to — the header said "este Produto Esperado"
# and never named it. Sibling products of one Ação share vocabulary almost by
# construction (Ação 15's six products are all about risk), so an unanchored
# criterion leaves the model no way to tell "evidence for THIS product" from
# "evidence for this Ação in general". Consistent with that, the 2026-09-29
# instability probe found 5 of Ação 15's 9 unstable chunks concentrated in one
# product, 15e.
#
# Stated abstractly, the rule is not enough: across 640 captured gate reasoning
# traces (2026-10-02) it was engaged in 0.8% of them, and the model named the
# wrong sibling in 62%. The concrete form — listing the sibling products as NOT
# under evaluation, see _sibling_contrast() — is what the model actually uses.
_SCOPE_RULE = """\
O trecho só é relevante se for evidência DESTE Produto Esperado. Evidência que \
sirva a outro Produto Esperado da mesma Ação, ou à Ação em geral, não conta aqui.\
"""

# Sibling product texts are quoted whole up to this length; the IPMP's longer
# ones (14a runs to ~300 chars) are cut so a 9-product Ação (31, 35) does not
# triple the prompt. The id and the opening clause carry the contrast.
_SIBLING_TEXT_MAX = 140


# A retrieval profile's evidence_intent is an operationalisation of the IPMP's
# own produto_esperado text, and for many products it simply restates it: over
# the 164 scored products, partial_ratio between the two has a median of 84 and
# reaches 100. Quoting the product text in the identity block AND again as the
# criterion would then send the same sentence twice. Above this threshold the
# criterion already carries the IPMP wording verbatim, so the quote is dropped
# and the block keeps only what the criterion cannot supply: which Ação this is,
# which of its products, and how many siblings it is competing with.
_INTENT_RESTATES_PRODUCT = 90

# The same idea one level down. A product's retrieval_signal_concepts are meant
# to list FORMS the required element may take; for 22 of the 164 products the
# list is a single entry that is the evidence_intent again (fuzz.ratio >= 90),
# and the prompt then said "Qualquer um dos elementos abaixo também conta" about
# a sentence identical to the criterion — one captured accepting trace quoted
# exactly that line to read the restatement as a looser criterion (ADR-0064).
# When every concept restates the intent the list is omitted; a list with at
# least one distinct concept is kept whole. Measured as variant V4 on
# 2026-10-02 (Ação 14: 1/40 oscillating vs 2/40 base, no accept gained).
_CONCEPT_RESTATES_INTENT = 90


def _concepts_restate_intent(concepts: list[str], evidence_intent: str) -> bool:
    def norm(t: str) -> str:
        return " ".join(t.split()).rstrip(".").lower()

    return bool(concepts) and all(
        fuzz.ratio(norm(c), norm(evidence_intent)) >= _CONCEPT_RESTATES_INTENT
        for c in concepts
    )


def _identity_block(acao: AcaoIPMP, product_id: str, evidence_intent: str) -> str:
    scored = [p for p in acao.produtos_esperados if p.scored]
    texto = next((p.texto for p in scored if p.id == product_id), "")
    position = (
        f", um dos {len(scored)} Produtos Esperados avaliados nesta Ação"
        if len(scored) > 1
        else ", o único Produto Esperado avaliado nesta Ação"
    )
    quote = ""
    if texto:
        a = " ".join(texto.split()).lower()
        b = " ".join(evidence_intent.split()).lower()
        if fuzz.partial_ratio(a, b) < _INTENT_RESTATES_PRODUCT:
            quote = f"\n«{texto}»"
    return (
        "## O que está sendo avaliado\n\n"
        f"Ação {acao.acao_id} — {acao.titulo}\n"
        f"Dimensão {acao.dimensao}, fase {acao.fase}.\n"
        f"Produto Esperado {product_id}{position}.{quote}"
        f"{_sibling_contrast(scored, product_id)}\n\n"
        f"{_SCOPE_RULE}"
    )


def _sibling_contrast(scored: list, product_id: str) -> str:
    """The scope rule made concrete: name every OTHER scored product of the
    Ação, with its IPMP text, as explicitly not under evaluation.

    Measured 2026-10-02 against the production configuration (4 calls in
    flight, 8 passes): on Ação 14 the gate went from 2/40 oscillating chunks
    and 6 accepts (all false positives, per the 2026-09-08 audit) to 0/40 and
    0; on Ação 22, which has genuine evidence, from 4/32 oscillating to 2/32
    with the risk matrix (p.774) and the insurance clauses (p.921) still
    accepted 6/6 and a previously oscillating chunk (p.193) now stable. The
    generic alternatives tried in the same session — a decision procedure, a
    tiebreak rule, reframing the concept list — were REJECTED: each turned the
    genuine p.774 risk matrix into an oscillating chunk, because "generic
    contractual obligations do not count" is wrong for Dimensão Comercial
    products whose evidence IS a contract annex. See ADR-0064.

    Returns "" for a single-product Ação, which has nothing to contrast."""
    siblings = [p for p in scored if p.id != product_id]
    if not siblings:
        return ""
    lines = []
    for p in siblings:
        text = " ".join(p.texto.split())
        if len(text) > _SIBLING_TEXT_MAX:
            text = text[: _SIBLING_TEXT_MAX - 1].rstrip() + "…"
        lines.append(f"- {p.id} — {text}")
    return (
        "\n\nOs demais Produtos Esperados desta Ação, que NÃO estão em avaliação aqui "
        "(evidência que sirva a eles não conta):\n" + "\n".join(lines)
    )


def build_relevance_system_prompt(
    evidence_intent: str,
    concepts: list[str] | None = None,
    negative_patterns: list[str] | None = None,
    *,
    acao: AcaoIPMP | None = None,
    product_id: str | None = None,
) -> str:
    """concepts: retrieval_signal_concepts' text, the same curated sub-criteria
    hybrid.py's vector query already uses (_vector_query_text()) — without
    them, evidence_intent's framing sentence alone reads as a narrow, literal
    definition and rejects genuinely-intended evidence (e.g. "objetivos
    estratégicos" alone excludes a risk matrix, even though risk_framework is
    a documented concept for that same product). Listed as alternatives, not
    additional requirements: any one is sufficient, not all simultaneously.

    negative_patterns: retrieval_signal_concepts' sibling field
    negative_evidence_patterns — populated in the retrieval profile schema
    since ADR-0047 but never wired into this prompt until it was found
    (2026-08-27) to explain gate instability on tangentially-worded but
    off-topic candidates (e.g. a contract's sanctions/appeal clauses
    accepted as Ação 2 product 2c's "situação atual" evidence). Listed as
    explicit exclusions, applied after the positive concepts above.

    A concept list that only restates the intent is omitted (see
    _concepts_restate_intent): it adds no form the criterion does not already
    state, and the "também conta" framing invited a looser reading of it."""
    criterion = evidence_intent
    if concepts and _concepts_restate_intent(concepts, evidence_intent):
        concepts = []
    if concepts:
        bullet_list = "\n".join(f"- {c}" for c in concepts)
        criterion = (
            f"{evidence_intent}\n\n"
            "Qualquer um dos elementos abaixo também conta como evidência válida "
            f"para este critério:\n{bullet_list}"
        )
    if negative_patterns:
        negative_list = "\n".join(f"- {p}" for p in negative_patterns)
        criterion = (
            f"{criterion}\n\n"
            "Os padrões abaixo NÃO contam como evidência válida para este critério, "
            f"mesmo que mencionem termos ou o contexto do projeto relacionados:\n{negative_list}"
        )
    header = (
        "Você é um classificador de relevância de evidências para auditoria de "
        "processos de Parceria Público-Privada (PPP), avaliados segundo o "
        "framework IPMP.\n\n"
    )
    if acao is not None and product_id is not None:
        header = f"{header}{_identity_block(acao, product_id, evidence_intent)}\n\n"
    return (
        f"{header}"
        f"## Critério de relevância para este Produto Esperado\n\n{criterion}"
        f"\n\n---\n\n{_INSTRUCTIONS}"
    )


def build_relevance_user_prompt(chunk_text: str, product_id: str | None = None) -> str:
    """The product id is repeated next to the chunk — the system prompt names
    it once, ~2,000 chars earlier, and the captured reasoning showed the model
    labelling the wrong sibling in 62% of traces. Measured together with
    _sibling_contrast() (see there); the two were not separated in the
    measurement, so they ship together."""
    tag = f"[Produto Esperado {product_id} — avalie SOMENTE este critério]\n" if product_id else ""
    return f"{tag}[Trecho a avaliar]\n{chunk_text}"
