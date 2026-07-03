from __future__ import annotations

_INSTRUCTIONS = """\
Responda SEMPRE em português, mesmo que o trecho contenha termos em outro idioma.
Sua resposta deve conter APENAS uma das duas linhas abaixo, nada mais — sem \
explicações, resumos ou texto adicional:

RELEVANT: yes

ou

RELEVANT: no\
"""


def build_relevance_system_prompt(evidence_intent: str, concepts: list[str] | None = None) -> str:
    """concepts: retrieval_signal_concepts' text, the same curated sub-criteria
    hybrid.py's vector query already uses (_vector_query_text()) — without
    them, evidence_intent's framing sentence alone reads as a narrow, literal
    definition and rejects genuinely-intended evidence (e.g. "objetivos
    estratégicos" alone excludes a risk matrix, even though risk_framework is
    a documented concept for that same product). Listed as alternatives, not
    additional requirements: any one is sufficient, not all simultaneously."""
    criterion = evidence_intent
    if concepts:
        bullet_list = "\n".join(f"- {c}" for c in concepts)
        criterion = (
            f"{evidence_intent}\n\n"
            "Qualquer um dos elementos abaixo também conta como evidência válida "
            f"para este critério:\n{bullet_list}"
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
