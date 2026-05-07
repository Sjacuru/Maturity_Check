# PRD — PDF to Retrieval-Optimized Markdown Converter
# PRD — Conversor de PDF para Markdown Otimizado para Recuperação

**Version:** 1.0  
**Date:** 2026-05-07  
**Author:** Salim (sjacuru@gmail.com)  
**Context:** M5D Evaluation System — document ingestion pipeline  

---

## 1. Purpose / Propósito

Build a tool that converts a structured policy/guidance PDF document into a clean, retrieval-optimized Markdown file. The output will be ingested into a RAG (Retrieval-Augmented Generation) system that scores procurement case documents against the M5D framework.

The target documents are structured Brazilian public-sector guidance PDFs (e.g., M5D framework, Rio Manual, TCDF IN). They share a common layout pattern: chapter headings, numbered action items, numbered subtasks, sidebar boxes, footnotes, and page-level running headers that repeat on every page.

The goal is **not** a generic PDF-to-Markdown converter. The goal is a clean, structured Markdown file where every heading level carries semantic meaning for a retrieval system. The output must be suitable for direct ingestion with zero manual post-processing.

---

## 2. Problem Description — What Goes Wrong with Raw PDF Conversion

The following problems were identified during ingestion of `M5D.md` (converted from PDF using a standard tool):

### 2.1 Running Headers on Every Page
Every page contains a repeated book-title line and a repeated chapter heading line that have nothing to do with the content of that page.

**Example artifacts:**
```
Estruturação de Propostas de Investimento em Infraestrutura - Modelo de 5 Dimensões 39
Capítulo 3: Proposta Inicial de Investimento – Dimensão Estratégica
```
These appear between paragraphs, interrupting the content flow. The chapter heading appears once legitimately at the start of a section and then as a running header on every subsequent page.

**Impact:** Chunks contain irrelevant repeated text; heading detection logic must deduplicate manually.

### 2.2 Table of Contents Entries Mixed with Body Content
The TOC at the start of the document uses the same text as body headings but with trailing underscores and page numbers:
```
Ação 1: Descreva o projeto, seu contexto estratégico e objetivos estratégicos _________ 38
```
These appear again in the body as legitimate headings without the underscore+page pattern:
```
Ação 1: Descreva o projeto, seu contexto estratégico e objetivos estratégicos
```

**Impact:** TOC entries are ingested as content chunks, polluting retrieval results.

### 2.3 Annex Headings Split Across Multiple Lines
Long annex titles wrap across 2–3 lines without trailing space markers:
```
Anexo 6 – Explicação de Alto Nível da
Rota de Desenvolvimento do Projeto e BIM
```
Or with trailing space on the first line:
```
Anexo 3 – Colaboração com os Bancos 
Multilaterais de Desenvolvimento
```

**Impact:** Chunks receive truncated heading paths that don't match the full title.

### 2.4 Sidebar / Diagram Content Embedded Inline
Visual elements (flowcharts, sidebars, dimension maps) are converted as plain text and injected in the middle of paragraphs:
```
...tais como:
 diversidade;
 coesão;
Ação 1
Descreva o 
projeto, seu 
contexto e 
objetivos 
estratégicos
Ação 2
Determine os 
objetivos, 
resultados, ...
Dimensão Estratégica

 empoderamento e inclusão de mulheres...
```

**Impact:** Chunk text contains irrelevant repeated action names mid-paragraph, reducing semantic clarity.

### 2.5 Footnote URLs Injected Mid-Paragraph
Footnote references appear inline between paragraphs rather than at the bottom:
```
 conformidade (cumprimento dos requisitos legais ou do financiador);
46 https://www.gov.br/produtividade-e-comercio-exterior/...
47 https://unece.org/...
 substituição (substituição de um serviço que está prestes a expirar);
```

**Impact:** Chunk text is interrupted; retrieval for "conformidade" returns text contaminated with URLs.

### 2.6 Subtask Items Not Marked as Headings
Each Ação contains numbered subtasks using Roman numerals (`i.`, `ii.`, `iii.`...) that are semantically distinct evaluation criteria. In the raw conversion these appear as plain paragraphs with no heading marker:
```
i. Escrever uma descrição breve e concisa do motivo pelo qual o projeto é necessário.
ii. Descrever a estratégia da Autoridade e as estratégias governamentais mais amplas 
relevantes...
```

**Impact:** All subtasks of one Ação land in the same chunk, making subtask-level retrieval impossible.

### 2.7 Structural Section Headers Not Marked
Each Ação has three structural sections that appear as plain text:
- `Quem deve trabalhar nisto?`
- `O que você deve fazer?`
- `Qual deve ser o resultado?`

**Impact:** These sections cannot be queried independently; the "expected result" section gets mixed with subtask content.

### 2.8 Missing Content (Graphics and Tables)
Some sections consist primarily of graphics, diagrams, or tables that the PDF converter cannot extract as text. These sections appear as nearly empty chunks or are omitted entirely.

**Example:** Ação 15 (Gerencial) — section exists in TOC but produces no readable text content.

---

## 3. Target Output Format

The output `.md` file must follow this exact heading hierarchy:

```
# [Document Title]                          ← H1, appears once

## Capítulo N: [Title]                      ← H2, one per chapter

### Ação N: [Title]                         ← H3, one per action

#### Quem deve trabalhar nisto?             ← H4, structural section
#### O que você deve fazer?                 ← H4, structural section
#### Qual deve ser o resultado?             ← H4, structural section
#### QUADRO N: [Title]                      ← H4, informational box
#### Foco ESG N: [Title]                    ← H4, ESG focus box

##### i. [Subtask description]              ← H5, subtask item
##### ii. [Subtask description]
##### iii. [Subtask description]
...
```

### 3.1 Example — Ideal Output for Ação 1

```markdown
## Capítulo 3: Proposta Inicial de Investimento – Dimensão Estratégica

### Ação 1: Descreva o projeto, seu contexto estratégico e objetivos estratégicos

#### Quem deve trabalhar nisto?

- O Diretor e Gerente de Projeto
- Representantes (servidores e funcionários públicos) da Autoridade e outras partes interessadas
- Consultores Ambientais e Sociais

#### O que você deve fazer?

##### i. Escrever uma descrição breve e concisa do motivo pelo qual o projeto é necessário.

##### ii. Descrever a estratégia da Autoridade e as estratégias governamentais mais amplas relevantes para mostrar o contexto dentro do qual a Proposta de Investimento deve ser desenvolvida, incluindo a Estratégia de Infraestrutura Nacional, Estratégias Ministeriais e Estratégias de Desenvolvimento Regional.

##### iii. Definir os Objetivos Estratégicos que a Proposta de Investimento apoia e que devem estar alinhados com os objetivos da Autoridade em questões sociais, ambientais, culturais, geográficas, éticas ou políticas, tais como:

- diversidade
- coesão
- empoderamento e inclusão de mulheres e/ou outros grupos desfavorecidos
- conservação / patrimônio cultural
- saúde / bem-estar
- sustentabilidade
- meio ambiente / social
- transparência / anticorrupção
- criação de empregos
- oportunidades da economia circular

##### iv. Mostrar como os Objetivos Estratégicos promovem o desenvolvimento sustentável, especialmente em relação ao gênero e à inclusão, e como estão alinhados com os compromissos internacionais, como os ODS da ONU ou as NDCs.

##### v. Inclua uma declaração que resuma, em alto nível, os possíveis impactos ambientais e sociais e a ambição geral do projeto, e uma declaração sobre o nível de ambição em relação à Estrutura de Gênero e Inclusão.

##### vi. Descrever como quaisquer programas e projetos existentes podem influenciar o projeto.

#### Qual deve ser o resultado?

Um breve relatório estabelecendo:
- Por que o projeto é necessário
- Como o projeto se encaixa no contexto estratégico mais amplo do governo
- Um conjunto de Objetivos Estratégicos

#### QUADRO 11: Diretrizes e planos orientadores dos investimentos em infraestrutura

[full box content, clean text only]

#### Foco ESG 1: Crescimento e infraestrutura inclusivos

[full ESG section content]
```

---

## 4. Functional Requirements

### FR-01 — Running Header Removal
The tool MUST detect and remove all repeated running headers:
- Book-title running headers (appear on every page, contain title + page number)
- Chapter running headers (repeat the chapter heading on pages after the chapter start)
- Annex running headers (repeat the annex title on pages within the annex)

**Detection rule:** A line that (a) matches a heading pattern AND (b) has appeared before at the same heading level → remove all occurrences after the first.

### FR-02 — TOC Removal
The tool MUST detect and remove the Table of Contents section entirely. The TOC starts after the cover pages and ends before the first chapter body content.

**Detection rule:** Lines matching a heading pattern followed by underscores and a page number (e.g., `_______ 38`) are TOC entries → remove them.

### FR-03 — Heading Hierarchy Construction
The tool MUST assign the correct heading level to each detected heading:

| Pattern | Heading Level |
|---------|---------------|
| Document title | H1 |
| `Capítulo N:` | H2 |
| `Ação N:` | H3 |
| `Quem deve trabalhar nisto?` | H4 |
| `O que você deve fazer?` | H4 |
| `Qual deve ser o resultado?` | H4 |
| `QUADRO N:` | H4 |
| `Foco ESG N:` | H4 |
| `Anexo N –` | H2 |
| Roman numeral subtasks `i.`, `ii.`, ... | H5 |

### FR-04 — Multi-Line Heading Reconstruction
The tool MUST join heading lines that wrap across multiple lines into a single heading. Detection: the heading pattern matches the first line, and the next line(s) do not match any heading pattern and are not blank.

### FR-05 — Sidebar / Diagram Removal
The tool MUST detect and remove visual element artifacts embedded inline. These appear as short isolated text fragments that reference action names, dimension names, or page-layout labels without forming grammatical sentences.

**Detection heuristics:**
- A block of lines where each line is fewer than 30 characters
- The block contains action names (`Ação N`) or dimension names (`Dimensão Estratégica` etc.)
- The block appears mid-paragraph (surrounded by grammatical text on both sides)
- The block does not contain a verb or complete sentence

### FR-06 — Footnote Relocation
The tool MUST detect inline footnote references (lines that start with a number followed by a URL or bibliographic reference) and relocate them to a `#### Referências` subsection at the end of the nearest enclosing Ação or Chapter section.

**Detection rule:** Line starts with `\d+ https?://` or `\d+ [A-Z]` where the leading number matches a footnote marker in the preceding text.

### FR-07 — Subtask Boundary Preservation
Each Roman numeral subtask item (`i.`, `ii.`, `iii.`...) MUST be promoted to H5 and its complete text (including multi-line wrap and bullet lists) MUST be preserved as the body of that H5 section.

**Critical:** If a subtask is a single line, the line text MUST appear as both the heading and the first line of body content so that the chunk is not empty when split at heading boundaries.

### FR-08 — Missing Content Marking
Where a section contains primarily graphic or tabular content that cannot be extracted as text, the tool MUST insert a placeholder:

```markdown
> ⚠️ *Esta seção contém principalmente conteúdo visual (gráficos, tabelas ou diagramas) que não pôde ser extraído como texto.*
```

### FR-09 — Bullet List Normalization
Lines that begin with a Unicode bullet character (` `, `•`, `-`, `–`) or a letter/number followed by `.` (sub-items `a.`, `b.`, `c.`) MUST be converted to standard Markdown list syntax (`- `).

### FR-10 — Output Validation
After conversion, the tool MUST output a validation report containing:
- Total H3 headings found (= number of Ações detected)
- List of any Ação numbers from 1–46 that were NOT found
- Total H5 headings found (= total subtask items)
- Count of sidebar blocks removed
- Count of footnotes relocated
- Count of running headers removed

---

## 5. Technical Requirements

### TR-01 — Input Format
- Input: PDF file path
- PDF version: any (target documents are standard text PDFs, not scanned images)
- Language: Portuguese (Brazilian) with occasional English terms

### TR-02 — PDF Extraction
- Use a library that preserves reading order and can distinguish columns (e.g., `pdfplumber`, `PyMuPDF`/`fitz`, or `pdfminer.six`)
- Do NOT use OCR — all target documents are text-based PDFs
- Column layout: the target documents are single-column body text with occasional two-column layouts in sidebar boxes

### TR-03 — Output Format
- Output: UTF-8 encoded `.md` file
- Encoding: no BOM, Unix line endings (`\n`)
- File name: derived from input PDF name, e.g., `m5d_clean.md`

### TR-04 — Configuration
The tool MUST accept a configuration file (YAML or JSON) that defines document-specific patterns:

```yaml
document:
  title: "Estruturação de Propostas de Investimento em Infraestrutura"
  book_title_pattern: "Estruturação de Propostas.*Modelo de 5 Dimensões"
  chapter_pattern: "^Capítulo\\s+\\d+:"
  action_pattern: "^Ação\\s+\\d+:"
  annex_pattern: "^Anexo\\s+\\d+"
  subtask_pattern: "^(i{{1,3}}|iv|vi{{0,3}}|ix|xi{{0,3}}|xiv|xv)\\."
  structural_sections:
    - "Quem deve trabalhar nisto?"
    - "O que você deve fazer?"
    - "Qual deve ser o resultado?"
  box_patterns:
    - "^QUADRO\\s+\\d+:"
    - "^Foco ESG\\s+\\d+:"
  toc_trailing_pattern: "_{2,}\\s*\\d+\\s*$|\\s+\\d+\\s*$"
```

This makes the tool reusable for Rio Manual and TCDF IN with different config files.

### TR-05 — Language
- Tool implementation language: Python 3.11+
- No external AI/LLM calls during conversion — purely deterministic rule-based processing

### TR-06 — Performance
- Must process the M5D PDF (≈285 pages) in under 60 seconds on a modern laptop

---

## 6. Known Edge Cases (from M5D ingestion experience)

| Edge Case | Description | Required Handling |
|-----------|-------------|-------------------|
| "G20" false positive | Headings ending in "G20" match digit-trailing TOC pattern | TOC detection for annexes requires underscores, not bare trailing digits |
| 3-line heading wrap | Some annex headings span 3 lines, middle lines have no trailing space | Join all continuation lines until next heading or blank line |
| Ação 15 | Section exists in TOC but has almost no text (mostly diagrams) | Insert FR-08 placeholder; do NOT omit the heading |
| Ação 46 | Last action before annexes; content is short but annexes MUST NOT fall under it | Ensure annex headings are detected as H2, closing the Ação 46 section |
| Sub-items `a.`, `b.`, `c.` | Appear within Roman numeral subtasks; they are list items, NOT separate headings | Convert to `  - a.` nested list, do not promote to heading |
| Footnotes mid-list | Footnote references sometimes appear between bullet list items, breaking the list | Collect footnotes, close list, continue list after footnote |
| Running headers with page variants | Some running headers include slightly different text per page (e.g., sub-section name added) | Match by prefix (first N chars) rather than exact string |
| Sidebar column layout | Some pages have a narrow sidebar column alongside the main text | Detect narrow-column text by character width and remove it as sidebar |

---

## 7. Validation Criteria — Acceptance Tests

The output `.md` file is accepted when ALL of the following are true:

1. **Zero running headers** — no line in the output matches the book-title pattern or any chapter heading that appears more than once
2. **Zero TOC entries** — no line ends with `___` + digits
3. **46 H3 headings** (or 45 if Ação 15 is confirmed absent from source) — one per M5D action
4. **All Ação sections have H5 subtasks** — every H3 is followed by at least one H5 within its section
5. **No sidebar artifacts** — no isolated action-name fragments appear mid-paragraph
6. **No inline footnotes** — no line matching `^\d+ https?://` appears in the body; all footnotes are in a `#### Referências` section
7. **Clean bullet lists** — all list items use `- ` prefix, no Unicode bullet characters remain
8. **Ação 15 placeholder present** — the section exists as an H3 with the FR-08 visual-content placeholder
9. **Annexes are H2** — Anexo 1 through Anexo 10 each have their own H2 heading
10. **Round-trip test** — extract all H3 and H5 heading texts, compare against the M5D reference list (`Plan/06_Models/M5D_reference.md`); all 45 Ação titles must match

---

## 8. Out of Scope

- OCR of scanned PDFs
- Extraction of image content (figures, charts) — use placeholder (FR-08)
- Translation of content (document remains in Portuguese)
- Conversion of tables to Markdown table syntax (treat table text as plain text paragraphs for now)
- Automatic summarization or paraphrasing of content
- Support for non-PDF input formats
- GUI or web interface — CLI only

---

## 9. Deliverable

A Python CLI tool accepting:
```
python pdf_to_md.py --input m5d.pdf --config m5d_config.yaml --output m5d_clean.md --validate
```

And producing:
- `m5d_clean.md` — the clean, retrieval-optimized Markdown file
- `m5d_conversion_report.txt` — the validation report (FR-10)
