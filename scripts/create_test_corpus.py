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

Document 3: Caso_Teste_Acao2_Score3.pdf
  Perfect match  - all expected products (2a-2d) clearly covered: SMART
  specific objectives, measurable results/indicators per objective,
  detailed current-state diagnosis, explicit gap analysis.
  Ground truth: score = 3 (Atendido).

Document 4: Caso_Teste_Acao2_Score1.pdf
  Partial match  - 2a and 2c clearly covered; 2b describes results without
  measurable indicators; 2d names problems without an explicit current-state
  vs. objectives comparison.
  Ground truth: score = 1 (Parcialmente Atendido).

Document 5: Caso_Teste_Acao2_Score0.pdf
  No match  - pure engineering/works memorial (structure, schedule, budget),
  no diagnosis, no specific objectives, no expected results.
  Ground truth: score = 0 (Nao Atendido).
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

DOC3 = """\
ESTUDO DE VIABILIDADE TECNICA, ECONOMICA E AMBIENTAL
CONCESSAO DO PARQUE TECNOLOGICO CARIOCA
Acao 2  - Objetivos Especificos, Resultados, Diagnostico e Lacunas
Caso de Teste A2  - Score Esperado: 3 (Atendido)

SECAO 1  - OBJETIVOS ESPECIFICOS

Com base nos objetivos estrategicos definidos na Acao 1 do presente estudo \
(social, economico, ambiental, cultural-geografico e politico), foi definido \
o seguinte conjunto de objetivos especificos, elaborados segundo a \
metodologia SMART (especificos, mensuraveis, atingiveis, relevantes e \
temporizaveis):

a) Ampliar em 40 por cento o numero de empresas de base tecnologica \
instaladas no municipio no prazo de 5 anos apos a entrega do empreendimento, \
vinculado ao objetivo estrategico economico de diversificacao da base \
produtiva.

b) Gerar 3.000 empregos diretos qualificados nos primeiros 3 anos de \
operacao, com pelo menos 30 por cento destinados a egressos de programas de \
formacao profissional publica, vinculado ao objetivo estrategico social de \
ampliacao do acesso a empregos qualificados.

c) Remediar 100 por cento da area contaminada do terreno no prazo de 18 \
meses e obter certificacao ambiental LEED Gold para as edificacoes, \
vinculado ao objetivo estrategico ambiental.

d) Atrair, em ate 4 anos, ao menos 2 centros de pesquisa de instituicoes de \
ensino superior internacionais, vinculado ao objetivo estrategico cultural e \
geografico de fortalecimento do Rio de Janeiro como polo de inovacao.

Cada um destes objetivos especificos justifica o gasto de recursos publicos \
estimado em R$ 180 milhoes, na medida em que o retorno esperado em geracao \
de emprego, arrecadacao tributaria e atracao de investimento privado supera, \
conforme demonstrado na Analise de Custo-Beneficio do Relatorio Geral de \
Avaliacao, o custo de oportunidade do investimento publico.

SECAO 2  - RESULTADOS ESPERADOS

Para cada objetivo especifico definido na Secao 1, apresentam-se os \
resultados esperados e os indicadores de desempenho que evidenciam a \
resolucao dos problemas identificados no diagnostico da situacao atual:

Objetivo (a)  - Ampliacao da base tecnologica: resultado esperado e a \
instalacao de, no minimo, 120 novas empresas de base tecnologica no Parque, \
medido pelo indicador de desempenho "numero de empresas instaladas por \
semestre", com meta de desempenho de 12 empresas por semestre a partir do \
segundo ano de operacao. Este resultado evidencia a resolucao do problema de \
dispersao e insuficiencia de espaco fisico identificado no diagnostico.

Objetivo (b)  - Geracao de empregos qualificados: resultado esperado e a \
criacao de 3.000 postos de trabalho diretos, medido pelo indicador de \
desempenho "numero de vinculos empregaticios formais registrados", com meta \
de desempenho de 600 empregos por ano. Este resultado evidencia a resolucao \
do problema de escassez de empregos qualificados no setor de tecnologia \
identificado no diagnostico.

Objetivo (c)  - Remediacao ambiental: resultado esperado e a certificacao \
LEED Gold obtida no prazo de 18 meses, medido pelo indicador de desempenho \
"percentual de area remediada", com meta de desempenho de 100 por cento em \
18 meses. Este resultado evidencia a resolucao do passivo ambiental \
identificado no diagnostico.

Objetivo (d)  - Atracao de centros de pesquisa: resultado esperado e a \
assinatura de convenios com 2 instituicoes internacionais, medido pelo \
indicador de desempenho "numero de convenios de cooperacao assinados", com \
meta de desempenho de 1 convenio por ano a partir do terceiro ano. Este \
resultado evidencia a resolucao da baixa insercao internacional do \
ecossistema de inovacao identificada no diagnostico.

A comparacao entre os resultados esperados e a situacao atual (linha de \
base), descrita na Secao 3, evidencia a melhoria pretendida em todos os \
quatro eixos.

SECAO 3  - DIAGNOSTICO DA SITUACAO ATUAL

O diagnostico detalhado da situacao atual, ou seja, do cenario sem o \
projeto, aponta o seguinte:

Funcionamento, manutencao e custos do servico existente: atualmente nao ha \
infraestrutura publica dedicada a empresas de base tecnologica no \
municipio. As poucas iniciativas existentes funcionam em imoveis comerciais \
adaptados, sem manutencao especializada, com custo medio de locacao 35 por \
cento acima do praticado em polos tecnologicos consolidados de outras \
capitais.

Condicao da infraestrutura existente: o terreno destinado ao empreendimento \
e uma area de 80 mil metros quadrados anteriormente ocupada por atividade \
industrial, atualmente degradada, com contaminacao do solo identificada em \
laudo tecnico e infraestrutura viaria e de saneamento insuficiente para uso \
comercial de grande porte.

Demanda atual: levantamento junto a 340 empresas de base tecnologica \
sediadas no municipio identificou que 68 por cento delas relatam \
dificuldade para encontrar espaco fisico adequado, e a demanda reprimida \
estimada e de 150 empresas que buscariam se instalar em um parque \
tecnologico estruturado nos proximos 3 anos.

Impacto sobre partes interessadas, meio ambiente e desenvolvimento \
socioeconomico: a ausencia de um polo estruturado afeta negativamente a \
capacidade de retencao de talentos formados nas universidades locais, dos \
quais 42 por cento migram para outros estados em busca de oportunidades no \
setor de tecnologia. A area contaminada representa passivo ambiental que \
impede o uso produtivo do terreno e gera risco a saude publica do entorno. \
O desenvolvimento socioeconomico da regiao permanece limitado pela ausencia \
de atividade economica de alto valor agregado.

SECAO 4  - ANALISE DE LACUNAS

A comparacao entre a situacao atual descrita na Secao 3 (onde se esta) e os \
objetivos especificos definidos na Secao 1 (onde se quer chegar) evidencia \
as seguintes lacunas:

Lacuna 1  - Infraestrutura fisica: nao existe espaco fisico dedicado e \
adequado, enquanto o objetivo especifico (a) requer a instalacao de 120 \
novas empresas. A diferenca entre a inexistencia de espaco estruturado e a \
meta de ampliacao de 40 por cento na base tecnologica fundamenta a \
necessidade do investimento em construcao.

Lacuna 2  - Qualificacao e retencao de mao de obra: a evasao de 42 por \
cento dos talentos formados localmente contrasta com o objetivo especifico \
(b) de gerar 3.000 empregos qualificados locais, evidenciando problema \
especifico de falta de oportunidades que o projeto precisa abordar.

Lacuna 3  - Passivo ambiental: a contaminacao do solo identificada no \
diagnostico impede qualquer uso produtivo do terreno, ao passo que o \
objetivo especifico (c) exige remediacao completa e certificacao \
ambiental, o que fundamenta a necessidade de investimento em \
descontaminacao previamente a qualquer construcao.

Lacuna 4  - Insercao internacional: a inexistencia de convenios de \
cooperacao internacional hoje contrasta com o objetivo especifico (d) de \
atrair centros de pesquisa estrangeiros, evidenciando a necessidade de \
estruturacao de governanca e atratividade institucional do futuro parque.

Grau esperado de atendimento: ATENDIDO (pontuacao 3).
Todos os Produtos Esperados 2a, 2b, 2c e 2d estao claramente evidenciados.
"""

DOC4 = """\
ESTUDO DE VIABILIDADE  - PARQUE TECNOLOGICO CARIOCA
APRESENTACAO DOS OBJETIVOS E DIAGNOSTICO
Acao 2  - Caso de Teste A2  - Score Esperado: 1 (Parcialmente Atendido)

SECAO 1  - OBJETIVOS ESPECIFICOS

Com base nos objetivos estrategicos ja definidos, o Parque Tecnologico \
Carioca estabelece os seguintes objetivos especificos, formulados segundo a \
metodologia SMART:

a) Ampliar em 40 por cento o numero de empresas de base tecnologica \
instaladas no municipio no prazo de 5 anos, vinculado ao objetivo \
estrategico economico.

b) Gerar empregos qualificados no setor de tecnologia, vinculado ao \
objetivo estrategico social de ampliacao do acesso ao trabalho qualificado.

c) Remediar a area contaminada do terreno e obter certificacao ambiental, \
vinculado ao objetivo estrategico ambiental.

Estes objetivos justificam o gasto de recursos publicos estimado em R$ 180 \
milhoes, dado o retorno esperado em geracao de emprego e arrecadacao \
tributaria.

SECAO 2  - RESULTADOS ESPERADOS

O projeto espera gerar resultados positivos para a economia local. A \
instalacao de empresas de tecnologia deve contribuir para a geracao de \
emprego e renda na regiao. Espera-se tambem que a remediacao do terreno \
traga beneficios ambientais para o entorno.

A entrega do empreendimento devera atender aos objetivos tracados, \
contribuindo de forma geral para o desenvolvimento economico do municipio e \
para a modernizacao do setor de tecnologia local.

SECAO 3  - DIAGNOSTICO DA SITUACAO ATUAL

O diagnostico detalhado da situacao atual, ou seja, do cenario sem o \
projeto, aponta o seguinte:

Funcionamento, manutencao e custos do servico existente: atualmente nao ha \
infraestrutura publica dedicada a empresas de base tecnologica no \
municipio. As poucas iniciativas existentes funcionam em imoveis comerciais \
adaptados, sem manutencao especializada, com custo medio de locacao 35 por \
cento acima do praticado em polos tecnologicos consolidados de outras \
capitais.

Condicao da infraestrutura existente: o terreno destinado ao empreendimento \
e uma area de 80 mil metros quadrados anteriormente ocupada por atividade \
industrial, atualmente degradada, com contaminacao do solo identificada em \
laudo tecnico.

Demanda atual: levantamento junto a empresas de base tecnologica sediadas \
no municipio identificou dificuldade generalizada para encontrar espaco \
fisico adequado, com demanda reprimida estimada em cerca de 150 empresas \
nos proximos anos.

Impacto sobre partes interessadas, meio ambiente e desenvolvimento \
socioeconomico: a ausencia de um polo estruturado afeta a retencao de \
talentos formados localmente e a area contaminada representa passivo \
ambiental relevante para o entorno.

SECAO 4  - LACUNAS E PROBLEMAS IDENTIFICADOS

O projeto busca resolver problemas relacionados a falta de espaco fisico \
adequado para empresas de tecnologia, a evasao de talentos qualificados e o \
passivo ambiental do terreno. Esses problemas justificam a necessidade do \
investimento publico na estruturacao do Parque Tecnologico Carioca.

Grau esperado de atendimento: PARCIALMENTE ATENDIDO (pontuacao 1).
Produtos 2a e 2c evidenciados. Produto 2b nao apresenta indicadores \
mensuraveis. Produto 2d nao detalha a diferenca explicita entre a situacao \
atual e os objetivos especificos.
"""

DOC5 = """\
PROJETO PARQUE TECNOLOGICO CARIOCA
MEMORIAL DESCRITIVO DE OBRAS
Acao 2  - Caso de Teste A2  - Score Esperado: 0 (Nao Atendido)

SECAO 1  - DESCRICAO DAS OBRAS

O objetivo do presente memorial e descrever a execucao das obras do Parque \
Tecnologico Carioca, empreendimento que a Prefeitura entende como \
necessario para atender a demanda por espaco destinado a empresas de \
tecnologia no municipio. Busca-se, de forma geral, modernizar a infra- \
estrutura disponivel e contribuir para o desenvolvimento economico local.

O empreendimento consiste na construcao de um complexo composto por 4 \
edificios de escritorios com area construida total de 45 mil metros \
quadrados, 2 galpoes destinados a laboratorios com area de 12 mil metros \
quadrados cada, estacionamento subterraneo com capacidade para 800 vagas e \
areas de convivencia externas totalizando 8 mil metros quadrados.

A estrutura sera executada em concreto armado, com fundacoes em estacas do \
tipo helice continua, considerando as caracteristicas geotecnicas do \
terreno. As instalacoes prediais incluirao sistemas de climatizacao \
central, geracao de energia solar fotovoltaica para 30 por cento da \
demanda e sistema de reuso de agua pluvial.

SECAO 2  - CRONOGRAMA E ESPECIFICACOES TECNICAS

A execucao das obras esta prevista para ocorrer em 4 etapas ao longo de 36 \
meses. A primeira etapa compreende terraplenagem e fundacoes, com prazo de \
8 meses. A segunda etapa compreende a estrutura e vedacoes, com prazo de 14 \
meses. A terceira etapa compreende instalacoes e acabamentos, com prazo de \
10 meses. A quarta etapa compreende paisagismo e entrega, com prazo de 4 \
meses.

Os materiais especificados seguem as normas tecnicas da ABNT aplicaveis a \
edificacoes comerciais de grande porte, incluindo NBR 6118 para estruturas \
de concreto e NBR 15575 para desempenho de edificacoes.

SECAO 3  - ORCAMENTO

O orcamento estimado para a execucao das obras e de R$ 210 milhoes, \
distribuidos entre os itens de fundacao, estrutura, instalacoes, acabamento \
e paisagismo, conforme planilha orcamentaria detalhada em anexo.

A escolha do local e da metodologia construtiva se deu com base na \
experiencia da equipe tecnica em empreendimentos similares e na \
disponibilidade de terreno de propriedade municipal, considerado adequado \
para a implantacao do projeto.

Grau esperado de atendimento: NAO ATENDIDO (pontuacao 0).
Nenhum Produto Esperado (2a, 2b, 2c, 2d) esta evidenciado: nao ha definicao \
de objetivos especificos vinculados a objetivos estrategicos, nao ha \
resultados esperados ou indicadores de desempenho, nao ha diagnostico da \
situacao atual, e nao ha analise de lacunas.
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

    p3 = OUTPUT_DIR / "Caso_Teste_Acao2_Score3.pdf"
    p4 = OUTPUT_DIR / "Caso_Teste_Acao2_Score1.pdf"
    p5 = OUTPUT_DIR / "Caso_Teste_Acao2_Score0.pdf"
    _make_pdf(p3, DOC3)
    _make_pdf(p4, DOC4)
    _make_pdf(p5, DOC5)

    print("Done. Ground truth:")
    print("  Acao 1 Score3 - all products 1a/1b/1c/1d evidenced -> expected score 3")
    print("  Acao 1 Score1 - only 1a partial, 1b vague, 1c/1d absent -> expected score 1")
    print("  Acao 2 Score3 - all products 2a/2b/2c/2d evidenced -> expected score 3")
    print("  Acao 2 Score1 - 2a/2c evidenced, 2b no measurable indicators, 2d no explicit gap -> expected score 1")
    print("  Acao 2 Score0 - pure works memorial, no diagnosis/objectives/results -> expected score 0")
