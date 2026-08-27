from __future__ import annotations

_INSTRUCTIONS = """\
Considere o trecho em português, mesmo que contenha termos em outro idioma. \
Preencha o campo "relevant" do objeto JSON de resposta com true (relevante) \
ou false (não relevante). Nenhum outro campo é esperado.\
"""


def build_relevance_system_prompt(
    evidence_intent: str,
    concepts: list[str] | None = None,
    negative_patterns: list[str] | None = None,
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
    explicit exclusions, applied after the positive concepts above."""
    criterion = evidence_intent
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
    return (
        "Você é um classificador de relevância de evidências para auditoria de "
        "processos de Parceria Público-Privada (PPP), avaliados segundo o "
        "framework IPMP.\n\n"
        f"## Critério de relevância para este Produto Esperado\n\n{criterion}"
        f"\n\n---\n\n{_INSTRUCTIONS}"
    )


def build_relevance_user_prompt(chunk_text: str) -> str:
    return f"[Trecho a avaliar]\n{chunk_text}"
