"""Padrão de produto que acompanha a variante G2 do gate (14/10/2026).

Origem: medição de direção de G, em 13/10/2026 (gate_positioning.py).
  - Sem G, o gate rejeitava 18b `_1` p.185 (0 de 20 nos ciclos 3 e 4).
  - Com G, ele aceitou em 2 de 3 passadas: "inclui estimativa de receita e
    custo operacional, isso é parte da análise de custo-benefício".
  - O trecho é a projeção de receita de publicidade da concessão, isto é, o
    modelo financeiro do parceiro privado (território da Ação 27, "Construa um
    modelo financeiro").
  - Antes de G, o motivo da rejeição era a falta de taxa de desconto, de custo
    de risco e de Valor Público: certo, pelo motivo errado.
  - O motivo certo é o objeto. A regra de G "de outro Produto Esperado" não o
    pega, porque o gate só vê os irmãos da mesma Ação.

O padrão diz o objeto, com uma marca que o próprio trecho decide: de quem são as
receitas e os custos. É canônico: separa a análise financeira do contrato, do
ponto de vista do parceiro privado, da análise de custo-benefício para a
sociedade, a do IPMP. Vale para qualquer concessão ou PPP.

Auditoria de sobreajuste: "viabilidade financeira do contrato" estava em 8 trechos do
corpus e foi trocado por "se o negócio é viável para ele".

Medido em memória, só na condição g2 de measure_gate_positioning.py e com
reproducibility.py --candidates ... --apply 18b. Não gravado no perfil.

Resultado (14/10/2026, posicao_g2_direcao.json): ignorado. Com o padrão, 18b
`_1` p.185 foi aceito nas 3 passadas (G sem o padrão, no mesmo processo: FFF):
"the criterion says any of the elements: benefits estimate, costs estimate...
So it's relevant". O próprio G não repetiu em 14/10 o aceite de 13/10 (FTT ->
FFF): o par é uma moeda, e o padrão não a resolveu. Não gravado.
"""

_IPMP_18 = ("Produto 18b: 'Análise de custo-benefício detalhada para cada opção, incluindo: "
            "estimativa dos Benefícios Públicos (separados em classes e com aplicação da taxa "
            "de desconto e ajuste para viés de otimismo); estimativa dos Custos (...); "
            "estimativa dos Riscos (...); cálculo do Valor Público para cada opção.'")

CANDIDATOS: dict[str, dict] = {
    "18b": {
        "acao": 18,
        "direcao": "rejeicao",
        "alvos": [("_1", 185), ("_2", 638)],
        "resumo": "receita, custos ou fluxo de caixa do parceiro privado (modelo financeiro) "
                  "não são os benefícios e custos para a sociedade da análise de custo-benefício.",
        "ipmp": _IPMP_18,
        "negativo": (
            "Receitas, custos de operação ou fluxo de caixa previstos para o parceiro "
            "privado — a contratada ou concessionária — para avaliar se o negócio é viável "
            "para ele não são a estimativa dos Benefícios Públicos e dos "
            "Custos de cada opção para a sociedade, que a análise de custo-benefício pede. "
            "Verifique no texto: de quem são as receitas e os custos? Se são do parceiro "
            "privado, o trecho trata de outro elemento."
        ),
    },
}
