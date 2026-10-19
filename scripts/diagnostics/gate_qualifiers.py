"""Variante Q do prompt do gate: os qualificadores do critério são do scorer (2026-10-18).

Pedido do usuário (79ª passada): "O gate ainda julga suficiência... trata-se de
alteração do prompt"; a seguir, "Um ciclo para a variante estreita do gate".

O que a variante corrige. No ciclo 8, o gate rejeita trechos que tratam do
elemento pedido porque eles não têm a forma ou o grau que o critério descreve.
Alguns exemplos, com o raciocínio gravado:
  - 14a `_1` p.3: a justificativa enumera os benefícios (i a v), rejeitada 10/10
    por "not categorized or structured";
  - 13c `_1` p.3: as mudanças do projeto (transição entre concessionárias,
    gestão por tipo de mobiliário, novos encargos) e a estratégia de antecipar a
    licitação para evitar interrupção, aceita 1/11. Quando aceita (processo 7),
    o scorer leu certo: "parcialmente evidenciado";
  - 2c `_1` p.3: o estado atual (cerca de 3 000 equipamentos, contratos até
    12/2026, áreas não cobertas), rejeitada 10/10 por "not detailed";
  - 42a `_2` p.144: rejeitada 10/10 por suficiência.

Diferença em relação a G (descartada em 14/10/2026). G trocava a abertura do
prompt por uma seção sobre o lugar do gate no processo e tirava o motivo
"faltam detalhes" sem dar o motivo certo; ponteiros e regras futuras passaram
(ADR-0071, ciclo 5). Q não mexe na abertura, no título do critério, no bloco de
identidade, nos padrões negativos nem no prompt de usuário. Acrescenta uma frase
às instruções, logo depois da cláusula que já diz que "apenas mencionar o tema"
não basta, e essa cláusula continua imediatamente antes.

Muda os 164 prompts de sistema (a instrução é comum a todos), então só ciclos de
processos completos a medem (memória feedback_prompt_wide_variant_noise).
Usada por: reproducibility.py --gate-variant qualificadores.
"""

from __future__ import annotations

# Fim da cláusula de polaridade de relevance_builder._INSTRUCTIONS (ADR-0066),
# exatamente como o builder a produz; qualifica() confere a presença, então uma
# mudança no builder aborta a medição em vez de medir outra coisa.
ANCORA = "sem tratar do elemento exigido. "

FRASE = (
    "As palavras do critério que qualificam o elemento, como completo, "
    "detalhado, categorizado, estruturado, monetizado, formal ou fundamentado, "
    "dizem como a etapa seguinte vai julgar o cumprimento; aqui não são "
    "condição: um trecho que trate do elemento pedido é relevante mesmo sem "
    "esse grau de detalhe ou essa forma. "
)


def qualifica(system: str) -> str:
    """O prompt de sistema de produção com FRASE logo depois de ANCORA."""
    assert system.count(ANCORA) == 1, "cláusula de polaridade mudou no builder"
    return system.replace(ANCORA, ANCORA + FRASE, 1)
