from __future__ import annotations

_INSTRUCTIONS = """\
Avalie o trecho de texto fornecido e responda em até dois blocos:

1. Se o trecho for relevante ao critério acima, copie o texto do trecho \
removendo apenas elementos de ruído: cabeçalhos e rodapés repetidos (nome \
do órgão, endereço), nomes próprios irrelevantes ao critério, e frases \
duplicadas. Não resuma, não reescreva, não altere nenhuma palavra mantida \
— apenas remova trechos de ruído, preservando o restante caractere por \
caractere, exatamente como no original.

2. Bloco sentinela final (últimas linhas da resposta, sem texto após):
RELEVANT: <yes ou no>
CLEANED:
<texto limpo, apenas quando RELEVANT: yes; omita este bloco quando RELEVANT: no>\
"""


def build_relevance_system_prompt(evidence_intent: str) -> str:
    return (
        "Você é um classificador de relevância de evidências para auditoria de "
        "processos de Parceria Público-Privada (PPP), avaliados segundo o "
        "framework IPMP.\n\n"
        f"## Critério de relevância para este Produto Esperado\n\n{evidence_intent}"
        f"\n\n---\n\n{_INSTRUCTIONS}"
    )


def build_relevance_user_prompt(chunk_text: str) -> str:
    return f"[Trecho a avaliar]\n{chunk_text}"
