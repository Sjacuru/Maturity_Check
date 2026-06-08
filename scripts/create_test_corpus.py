"""
Create synthetic test corpus for Phase A  - Reasoning Chain Validation.

Document 1: Caso_Teste_Acao1_Score3.pdf
  Perfect match  - all expected products (1a-1d) clearly covered.
  Uses exact BM25 hint phrases and law regex patterns from Rio Manual.
  Ground truth: score = 3 (Atendido).

Document 2: Caso_Teste_Acao1_Score1.pdf
  Partial match  - 1a weakly covered, 1b briefly mentioned, 1c/1d absent.
  No specific legal phrases or planning instrument references.
  Ground truth: score = 1 (Parcialmente Atendido).
"""
from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF  - already a project dependency

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "test_corpus"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

W, H, M = 595, 842, 60          # A4, 60 pt margins
CHARS_PER_PAGE = 2000            # empirical limit: 2500 causes overflow; keep margin
FONTNAME = "helv"
FONTSIZE = 11


# ---------------------------------------------------------------------------
# Document content
# ---------------------------------------------------------------------------

DOC1 = """\
ESTUDO DE VIABILIDADE TECNICA, ECONOMICA E AMBIENTAL
CONCESSAO DO PARQUE TECNOLOGICO CARIOCA
Caso de Teste A2  - Score Esperado: 3 (Atendido)

SECAO 1  - NECESSIDADE E DESCRICAO DO PROJETO

O presente documento constitui o Relatorio de Pre-Analise para a concessao \
do Parque Tecnologico Carioca, empreendimento que a Prefeitura do Municipio \
do Rio de Janeiro pretende estruturar sob a modalidade de Parceria \
Publico-Privada, nos termos da Lei Complementar n. 105/2009 e da Lei Federal \
n. 11.079/2004.

A necessidade que justifica o projeto decorre da insuficiencia da \
infraestrutura publica de apoio a inovacao tecnologica no municipio. \
O Rio de Janeiro carece de um espaco integrado que articule pesquisa, \
desenvolvimento e transferencia de tecnologia em escala capaz de sustentar \
a diversificacao da base economica local. A natureza do empreendimento e a \
prestacao de servico publico de apoio a inovacao mediante a construcao, \
manutencao e operacao de infraestrutura dedicada ao ecossistema de ciencia \
e tecnologia.

A conveniencia e oportunidade do projeto estao fundamentadas no diagnostico \
de que o municipio dispoe de capital humano qualificado e demanda latente por \
parte das empresas de base tecnologica, mas carece de ambiente fisico e \
institucional adequado. O efetivo interesse publico e demonstrado pela \
expectativa de geracao de empregos qualificados, atracao de investimentos \
privados e fortalecimento da capacidade de inovacao do setor publico municipal.

SECAO 2  - CONTEXTO ECONOMICO, SOCIAL E AMBIENTAL

O panorama economico em que o projeto se insere e marcado pela transicao da \
economia carioca em direcao a setores de maior valor agregado, apos decadas \
de dependencia do petroleo e do turismo como vetores principais de crescimento.

No plano social, o municipio enfrenta desigualdade na distribuicao espacial \
das oportunidades de trabalho qualificado. A analise de impacto economico e \
beneficios socioeconomicos do projeto indica que a concentracao de empresas \
de tecnologia em um polo dedicado tende a gerar externalidades positivas para \
os bairros do entorno, incluindo valorizacao imobiliaria, incremento do \
comercio local e melhoria da mobilidade urbana.

No plano ambiental, o terreno escolhido e uma area anteriormente degradada \
por atividade industrial, cuja remediacao esta prevista como condicao de \
implantacao. A reutilizacao contribui para os objetivos municipais de \
requalificacao urbana e reducao do passivo ambiental.

A viabilidade socioeconomica do projeto foi avaliada por Analise de \
Custo-Beneficio (ACB), conforme metodologia recomendada no Relatorio Geral \
de Avaliacao, considerando beneficios quantificaveis e nao quantificaveis.

SECAO 3  - OBJETIVOS ESTRATEGICOS

O projeto busca alcancar os seguintes objetivos estrategicos:

a) Social: ampliar o acesso a empregos qualificados para a populacao carioca, \
com enfase em grupos historicamente excluidos do mercado de trabalho de alta \
remuneracao, e fomentar a formacao de talentos locais em parceria com \
universidades publicas.

b) Economico: diversificar a base produtiva municipal, reduzindo a dependencia \
de setores expostos a ciclos de commodities, e atrair investimentos privados \
nacionais e internacionais em tecnologia e inovacao.

c) Ambiental: promover a remediacao de area degradada, incorporar padroes de \
construcao sustentavel (certificacao LEED) e criar espacos verdes integrados.

d) Cultural e Geografico: fortalecer a identidade do Rio de Janeiro como polo \
de inovacao na America Latina, aproveitando a concentracao de instituicoes de \
ensino superior e centros de pesquisa existentes na regiao.

e) Politico: demonstrar a capacidade do Municipio de estruturar parcerias \
publico-privadas complexas de forma transparente e eficiente, fortalecendo a \
governanca municipal e a credibilidade institucional junto a investidores.

A definicao desses objetivos estrategicos e consistente com as diretrizes \
governamentais estabelecidas para o setor de ciencia, tecnologia e inovacao.

SECAO 4  - ALINHAMENTO COM POLITICAS PUBLICAS E PLANEJAMENTO GOVERNAMENTAL

O projeto esta em plena conformidade com as politicas gerais do Municipio e \
com os planos estrategicos do Municipio vigentes, conforme demonstrado abaixo.

4.1 Plano Estrategico Municipal
O Plano Estrategico da Cidade do Rio de Janeiro contempla, entre seus eixos \
prioritarios, o fomento a economia criativa e a inovacao tecnologica. O \
Parque Tecnologico Carioca esta alinhado com a diretriz de diversificacao \
economica e com a meta de posicionamento do Rio de Janeiro como hub \
tecnologico regional.

4.2 Plano Plurianual (PPA)
O projeto esta incluido no Plano Plurianual 2026-2029 (Lei Municipal n. \
9.275/2026), na acao referente ao desenvolvimento do ecossistema de inovacao, \
conforme exigido pelo art. 10, VII, da Lei Complementar n. 105/2009 e pelo \
art. 10, I, alineas b e c, da Lei Federal n. 11.079/2004.

4.3 Lei Orcamentaria Anual (LOA)
A Lei Orcamentaria Anual 2026 (Lei n. 9.276/2026) preve dotacao orcamentaria \
para as despesas de estruturacao da PPP, em conformidade com o art. 10, VII, \
da Lei Complementar n. 105/2009.

4.4 Lei de Diretrizes Orcamentarias (LDO)
A Lei de Diretrizes Orcamentarias 2026 (Lei n. 8.411/2025) estabelece \
diretrizes para a utilizacao de mecanismos de parceria publico-privada como \
instrumento de politica de desenvolvimento urbano.

4.5 Lei Organica Municipal e Legislacao Federal
O projeto observa as disposicoes da Lei Organica Municipal do Rio de Janeiro \
e esta em conformidade com a Lei Complementar n. 105/2009 (art. 10, I, que \
exige demonstracao de efetivo interesse publico e observancia das diretrizes \
governamentais) e com a Lei Federal n. 11.079/2004.

A vantagem economica e operacional da proposta de concessao em relacao a \
execucao direta pelo Poder Publico e demonstrada no Relatorio Geral de \
Avaliacao  - Anexo de Analise Socioeconomica, onde se conclui que o modelo \
de PPP permite transferencia de risco com ganhos de eficiencia estimados em \
18 por cento em relacao ao modelo de contratacao tradicional.

Grau esperado de atendimento: ATENDIDO (pontuacao 3).
Todos os Produtos Esperados 1a, 1b, 1c e 1d estao claramente evidenciados.
"""

DOC2 = """\
ESTUDO DE VIABILIDADE  - PARQUE TECNOLOGICO CARIOCA
APRESENTACAO PRELIMINAR DO PROJETO
Caso de Teste A2  - Score Esperado: 1 (Parcialmente Atendido)

SECAO 1  - APRESENTACAO DO PROJETO

O Parque Tecnologico Carioca e uma iniciativa da Prefeitura Municipal do Rio \
de Janeiro para criar um espaco dedicado a inovacao e ao desenvolvimento \
tecnologico. O projeto consiste na construcao e operacao de um complexo com \
laboratorios, escritorios e espacos de convivencia para empresas de \
tecnologia, startups e pesquisadores.

O empreendimento visa resolver a falta de infraestrutura adequada para o \
setor tecnologico no municipio, que nao conta com um polo estruturado capaz \
de concentrar atividades de pesquisa e desenvolvimento. A Prefeitura considera \
que uma PPP seria a forma mais adequada de viabilizar o projeto.

SECAO 2  - CONTEXTO DO PROJETO

O Rio de Janeiro passa por um processo de transformacao economica. O declinio \
da industria do petroleo e a necessidade de criar novas fontes de emprego tem \
levado o governo municipal a buscar alternativas. O setor de tecnologia e \
visto como uma oportunidade promissora.

O projeto podera gerar empregos e atrair investimentos. Ha tambem a \
possibilidade de recuperar uma area subutilizada, o que seria positivo do \
ponto de vista urbanistico.

A Prefeitura entende que o projeto esta alinhado com os objetivos de \
desenvolvimento do municipio e com as politicas governamentais voltadas para \
a modernizacao da economia carioca.

Grau esperado de atendimento: PARCIALMENTE ATENDIDO (pontuacao 1).
Produto 1a parcialmente evidenciado. Produtos 1b, 1c e 1d nao evidenciados \
de forma clara ou especifica.
"""


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def _make_pdf(path: Path, content: str) -> None:
    doc = fitz.open()
    rect = fitz.Rect(M, M, W - M, H - M)

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    page_buf: list[str] = []
    page_chars = 0

    def flush(buf: list[str]) -> None:
        if not buf:
            return
        page = doc.new_page(width=W, height=H)
        page.insert_textbox(rect, "\n\n".join(buf), fontname=FONTNAME, fontsize=FONTSIZE)

    for para in paragraphs:
        if page_chars + len(para) > CHARS_PER_PAGE and page_buf:
            flush(page_buf)
            page_buf, page_chars = [], 0
        page_buf.append(para)
        page_chars += len(para)

    flush(page_buf)
    page_count = doc.page_count
    doc.save(str(path))
    doc.close()
    print(f"Created: {path.name}  ({page_count} pages)")


if __name__ == "__main__":
    p1 = OUTPUT_DIR / "Caso_Teste_Acao1_Score3.pdf"
    p2 = OUTPUT_DIR / "Caso_Teste_Acao1_Score1.pdf"
    _make_pdf(p1, DOC1)
    _make_pdf(p2, DOC2)
    print("Done. Ground truth:")
    print("  Score3 - all products 1a/1b/1c/1d evidenced -> expected score 3")
    print("  Score1 - only 1a partial, 1b vague, 1c/1d absent -> expected score 1")
