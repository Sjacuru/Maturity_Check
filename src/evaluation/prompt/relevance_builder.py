from __future__ import annotations

_INSTRUCTIONS = """\
Responda SEMPRE em português, mesmo que o trecho contenha termos em outro idioma.
Não resuma, não traduza, não reescreva, não explique o conteúdo. Sua resposta \
deve conter APENAS o bloco sentinela abaixo, nada mais.

Se o trecho NÃO for relevante ao critério acima, responda exatamente:
RELEVANT: no

Se o trecho FOR relevante ao critério acima, copie o texto do trecho removendo \
apenas elementos de ruído (cabeçalhos e rodapés repetidos, nome do órgão, \
endereço, nomes próprios irrelevantes ao critério, frases duplicadas), \
preservando todo o restante caractere por caractere, exatamente como no \
original — e responda exatamente:
RELEVANT: yes
CLEANED:
<aqui o texto limpo>

Não use a palavra "yes" ou "no" entre os símbolos < >: escreva apenas a \
palavra escolhida. Não inclua nenhum texto antes ou depois deste bloco.

Exemplo de resposta válida para um trecho relevante:
RELEVANT: yes
CLEANED:
O contrato vigente encontra-se próximo do término de sua vigência.

Exemplo de resposta válida para um trecho não relevante:
RELEVANT: no\
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
