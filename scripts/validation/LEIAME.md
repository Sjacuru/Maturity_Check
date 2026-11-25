# scripts/validation/

Instrumentos para validar os scores com um caso novo e com especialistas.
Os três são só leitura: não chamam modelo, não precisam da GPU e não gravam
no banco. Rode com o ambiente `rel_voto`, a partir da raiz do repositório.

| script | responde |
|---|---|
| `mapa_cobertura.py --process P` | Em que etapa parou cada um dos 164 produtos pontuados na última avaliação: evidenciado, recusado pelo avaliador, recusado pelo gate, só texto de instrumento, busca vazia ou documento focal. É a lista de perguntas para o especialista. |
| `rastreia_evidencia.py --process P --acao N --produto ID --arquivo _2 --pagina 973` | O especialista diz "a evidência está nesta página". O script mostra onde ela se perdeu: indexação, rota focal, gênero, ruído, posição nas raias BM25 e vetorial, pool fundido, corte dos 16 examinados, veredito do gate (com o raciocínio) e entrega ao avaliador. |
| `relatorio_concordancia.py --process P [--csv f.csv]` | Quanto o especialista concordou com o sistema: aceites, overrides para cima e para baixo por dimensão, distância média em pontos, Ações com o sinal de revisão sugerida e trechos marcados no gate. |

## Protocolo

1. **Caso novo.** Use um número de processo novo e rode a avaliação pela
   interface. Antes de qualquer execução na GPU, faça a checagem de uso do
   servidor. As revisões de teste de um caso (justificativas como "f") devem
   ser apagadas antes de medir a concordância: uma reavaliação forçada as
   apaga (ADR-0026).
2. **Revisão na interface.** Para cada Ação, o especialista aceita o score ou
   o altera, com justificativa obrigatória (ADR-0023). Para um trecho que o
   gate julgou errado, marca relevante ou não relevante (ADR-0067); para
   aplicar, reavalia as Ações com override pendente (ADR-0078). "Não
   aplicável" só vale para as Ações 45 e 46 (ADR-0076).
3. **Evidência que o sistema não achou.** O especialista anota Ação,
   produto, arquivo e página. `rastreia_evidencia.py` diz a etapa da perda.
4. **Medida.** `mapa_cobertura.py` e `relatorio_concordancia.py`, com
   `--csv` para guardar o resultado do caso.

## Da descoberta à melhoria

Um achado de validação vira mudança só por estas regras do projeto:

- Termos de busca são canônicos (ADR-0073): vêm do texto do IPMP, da lei ou
  do manual em que o conceito se apoia, ou de vocabulário geral, nunca do
  documento do caso. O caso testa o perfil; não o escreve.
- Texto de instrumento (contrato, edital, TR) não volta ao gate como regra
  geral (ADR-0074), e não se escrevem padrões negativos feitos sob medida
  para páginas de um caso.
- Uma mudança por vez, medida em processos completos com
  `scripts/diagnostics/reproducibility.py --runs 10`, com o critério escrito
  antes da primeira chamada ao modelo. Uma rodada é uma única invocação.
- A mudança entra se não piorar a constância nem as confusões, nos dois
  casos, e trouxer ao menos um alvo legítimo (regra do ADR-0077), e só com a
  aprovação do usuário.
