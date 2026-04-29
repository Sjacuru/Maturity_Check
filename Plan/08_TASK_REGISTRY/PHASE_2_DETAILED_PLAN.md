# FASE 2 — Plano Detalhado (29 de Maio — 20 de Novembro de 2026) / PHASE 2 — Detailed Plan (May 29 — November 20, 2026)

## Objetivo / Objective
**Português:** Expandir o sistema do MVP (Ação 1) para toda a framework M5D (46 ações), otimizar para deployment em servidor Rio municipal, e preparar para produção.

**English:** Expand MVP (Action 1) to full M5D framework (46 actions), optimize for Rio municipal server deployment, and prepare for production.

---

## Escopo Fase 2 / Phase 2 Scope

### Incluso / Included:
- ✅ Ações 2–16 (Proposta Inicial de Investimento — PIIPI)
- ✅ Ações 17–46 (Estruturação e Implementação)
- ✅ Web UI para auditor (dashboard + interface avançada)
- ✅ Groq API integração (opcional, código pronto para production)
- ✅ Performance optimization + caching
- ✅ Multi-tenancy para múltiplas instituições Rio
- ✅ Deployment em servidor Rio municipal (on-premises)
- ✅ Testes extensivos com casos Rio reais
- ✅ Documentação production-ready

### Não Incluso / NOT Included:
- ❌ Outras jurisdições (DF, SP, etc.) — fase 3+
- ❌ Mobile app
- ❌ Multi-language além Portuguese/English

---

## Timeline Fase 2 / Phase 2 Timeline

**Período / Period:** 29 de Maio — 20 de Novembro de 2026 (176 dias / 26 semanas)

| Bloco / Block | Semanas / Weeks | Foco / Focus |
|-----------|---------|------|
| **I** | Semana 1-4 (Jun 1-28) | Ações 2–5 + CLI optimization |
| **II** | Semana 5-8 (Jul 1-28) | Ações 6–10 + Web UI estrutura |
| **III** | Semana 9-12 (Ago 1-28) | Ações 11–16 + Web UI advanced |
| **IV** | Semana 13-16 (Set 1-28) | Ações 17–25 + Groq integration |
| **V** | Semana 17-20 (Out 1-28) | Ações 26–36 + Performance tuning |
| **VI** | Semana 21-24 (Nov 1-14) | Ações 37–46 + Testing |
| **VII** | Semana 25-26 (Nov 15-20) | Production readiness + deployment |

---

# BLOCO I / BLOCK I: Ações 2–5 & Otimizações (29 de Maio — 28 de Junho)

## Objetivo Semanal Bloco I / Block I Weekly Objective
Expandir de Ação 1 para Ações 2–5. Refatorar código para suportar múltiplas ações facilmente.

---

### Semana 1-2 / Week 1-2 (Jun 1-14): Ação 2 — Análise de Influência

#### Tarefa I.1 / Task I.1: Desenhar Crosswalk para Ação 2
**Data:** Jun 1-3  
**Verificações:**
- [ ] Crosswalk Rio + TCDF para Ação 2 (7 sub-tarefas)
- [ ] Artifact references mapeados
- [ ] JSON schema validado

**Entrega:**
📄 `Plan/06_Models/crosswalk/action_2_subtasks.template.md` (PT + EN)

#### Tarefa I.2 / Task I.2: Ingestão Ação 2 em Banco de Dados
**Data:** Jun 4-7  
**Verificações:**
- [ ] Framework M5D Ação 2 parseada
- [ ] Sub-tarefas inseridas em `reference_chunks`
- [ ] Crosswalk JSON carregado

**Entrega:**
📄 Código: Extensão de `ingest/m5d_ingest.py`  
📸 Screenshot: Ação 2 data no SQLite

#### Tarefa I.3 / Task I.3: Teste Avaliação Ação 2
**Data:** Jun 8-14  
**Verificações:**
- [ ] Avaliação end-to-end Ação 2
- [ ] Relatório com evidências
- [ ] Comparação com Ação 1 funcionalidade

**Entrega:**
📸 Screenshot: Relatório Ação 2  
📄 Documento: `AÇÃO_2_VERIFICATION.md` (PT + EN)

---

### Semana 3 / Week 3 (Jun 15-21): Ações 3–4

#### Tarefa I.4 / Task I.4: Ação 3 Implementação
**Data:** Jun 15-18  
**Verificações:** (Similar a Ação 2)

**Entrega:**
📄 Crosswalk + código  
📸 Screenshot: Relatório Ação 3

#### Tarefa I.5 / Task I.5: Ação 4 Implementação
**Data:** Jun 18-21  
**Verificações:** (Similar)

**Entrega:**
📄 Crosswalk + código  
📸 Screenshot: Relatório Ação 4

---

### Semana 4 / Week 4 (Jun 22-28): Ação 5 & Refatoração CLI

#### Tarefa I.6 / Task I.6: Ação 5 Implementação
**Data:** Jun 22-24  
**Verificações:** (Similar)

**Entrega:** Crosswalk + código + screenshot

#### Tarefa I.7 / Task I.7: Refatorar CLI para Batch Evaluation
**Data:** Jun 25-28  
**Verificações:**
- [ ] Novo comando: `maturity-check evaluate-all-actions --case-id=RIO-001`
- [ ] Avalia Ações 1–5 em sequência
- [ ] Gera relatório consolidado (JSON + HTML)
- [ ] Progress bar mostrando status

**Entrega:**
📄 Código: Extensão `cli.py`  
📸 Screenshot: Batch evaluation rodando

---

## Resumo Bloco I / Block I Summary

| Ação / Action | Crosswalk | Código | Teste | Status |
|-------|---------|--------|-------|--------|
| 1 | ✅ MVP | ✅ MVP | ✅ MVP | ✅ Complete |
| 2 | ✅ New | ✅ New | ✅ New | ✅ Complete |
| 3 | ✅ New | ✅ New | ✅ New | ✅ Complete |
| 4 | ✅ New | ✅ New | ✅ New | ✅ Complete |
| 5 | ✅ New | ✅ New | ✅ New | ✅ Complete |

**Total Horas Bloco I / Block I Hours:** 80–100h  
**Deliverables:** 5 relatórios funcionais + código refatorado

---

# BLOCO II / BLOCK II: Ações 6–10 & Web UI Base (Jun 29 — Jul 28)

## Objetivo / Objective
Ações 6–10 implementadas. Web UI estrutura criada (Django ou FastAPI + Vue.js).

---

### Semana 5 / Week 5 (Jun 29-Jul 5): Framework Web UI

#### Tarefa II.1 / Task II.1: Escolher e Configurar Web Framework
**Data:** Jun 29-Jul 1  
**Opções:**
- FastAPI (Python, rápido, JSON-first)
- Django (Python, full-featured, admin panel)
- Recomendação: **FastAPI** (leve para Phase 2)

**Verificações:**
- [ ] Framework instalado e rodando
- [ ] Rota básica `/api/cases` funciona
- [ ] CORS configurado
- [ ] Database connection testada

**Entrega:**
📄 `src/maturity_check/api/main.py` (FastAPI app)  
📸 Screenshot: FastAPI docs (`/docs` endpoint)

#### Tarefa II.2 / Task II.2: Implementar Endpoints API Básicos
**Data:** Jul 1-5  
**Endpoints:**
```
GET    /api/cases                    # List all cases
POST   /api/cases                    # Create case
GET    /api/cases/{case_id}          # Get case details
POST   /api/cases/{case_id}/upload   # Upload documents
GET    /api/cases/{case_id}/evaluations  # Get evaluations
POST   /api/cases/{case_id}/evaluate # Trigger evaluation
GET    /api/actions                  # List M5D actions
GET    /api/actions/{action_id}      # Get action details
```

**Verificações:**
- [ ] Endpoints testados com curl/Postman
- [ ] Responses JSON bem-formados
- [ ] Error handling implementado
- [ ] Documentação automática via Swagger

**Entrega:**
📄 Código: `src/maturity_check/api/routes.py`  
📸 Screenshot: Postman testar endpoints  
📄 Documento: `API_ENDPOINTS.md` (PT + EN)

---

### Semana 6-7 / Week 6-7 (Jul 6-21): Ações 6–8 & Frontend Base

#### Tarefa II.3 / Task II.3: Ações 6, 7, 8 Implementação
**Data:** Jul 6-19  
**Similar a Bloco I:** Crosswalk + código + teste

**Entrega:** Documentação por ação

#### Tarefa II.4 / Task II.4: Frontend Base (Vue.js ou React)
**Data:** Jul 15-21  
**Recomendação: Vue.js 3** (mais simples para MVP web)

**Componentes:**
- Case List view
- Case Detail view
- Document upload form
- Evaluation results view

**Verificações:**
- [ ] Vue.js instalado e rodando
- [ ] Components criados
- [ ] API calls (axios/fetch) funcionam
- [ ] UI responsiva (desktop + tablet)

**Entrega:**
📄 Código: `frontend/src/components/`  
📸 Screenshot: Case List page  
📸 Screenshot: Upload form

---

### Semana 8 / Week 8 (Jul 22-28): Ação 9–10 & UI Integration

#### Tarefa II.5 / Task II.5: Ações 9–10 Implementação
**Data:** Jul 22-26  
**Entrega:** Código + teste

#### Tarefa II.6 / Task II.6: Integração API + Frontend Completa
**Data:** Jul 26-28  
**Fluxo Completo:**
1. User abre frontend
2. Vê lista de casos
3. Clica em um caso
4. Faz upload de documento
5. Sistema valida
6. User clica "Avaliar Ação 6"
7. Resultado aparece em tempo real (ou com loading bar)

**Verificações:**
- [ ] E2E flow funciona
- [ ] Sem erros de CORS
- [ ] UI responsiva
- [ ] Feedback visual (loading, success, error)

**Entrega:**
📸 Screenshot: Full flow funcionando  
📄 Documento: `WEB_UI_USER_FLOW.md` (PT + EN)

---

## Resumo Bloco II / Block II Summary

| Item | Status | Entrega |
|------|--------|---------|
| Ações 6–10 | ✅ Complete | Código + testes |
| Web Framework (FastAPI) | ✅ Complete | API funcionando |
| Frontend Base (Vue.js) | ✅ Complete | Pages + forms |
| API-Frontend Integration | ✅ Complete | E2E flow |

**Total Horas Bloco II / Block II Hours:** 120–140h

---

# BLOCO III / BLOCK III: Ações 11–16 & UI Avançada (Jul 29 — Ago 28)

## Objetivo / Objective
Ações 11–16 (fim de PIIPI) implementadas. Web UI com edição/anotações.

---

### Semana 9-10 / Week 9-10 (Jul 29-Ago 11): Ações 11–13

#### Tarefa III.1 / Task III.1: Ações 11–13 Implementação
**Data:** Jul 29-Ago 11  
**Similar pattern:** Crosswalk → código → teste

**Entrega:** Código + documentação

---

### Semana 11-12 / Week 11-12 (Ago 12-25): Ações 14–16 & Anotações

#### Tarefa III.2 / Task III.2: Ações 14–16 Implementação
**Data:** Ago 12-22  
**Entrega:** Código + teste

#### Tarefa III.3 / Task III.3: Sistema de Anotações (Auditor Review)
**Data:** Ago 22-25  

**Funcionalidade:**
- Auditor vê resultado (present/absent/uncertain)
- Auditor pode editar score
- Auditor pode adicionar notas/comentários
- Mudanças são rastreadas em audit log
- Resultado final é "approved" por auditor

**Schema:**
```sql
CREATE TABLE annotations (
  annotation_id TEXT PRIMARY KEY,
  eval_id TEXT REFERENCES evaluations(eval_id),
  auditor_id TEXT,
  original_status TEXT,
  modified_status TEXT,
  notes TEXT,
  timestamp TEXT
);
```

**Verificações:**
- [ ] Anotações salvas em database
- [ ] UI permite edição de score
- [ ] Audit trail mostra mudanças
- [ ] Relatório final mostra versão aprovada

**Entrega:**
📄 Código: Database + API + frontend  
📸 Screenshot: Annotation UI

---

### Semana 13 / Week 13 (Ago 26-28): Teste Integrado Ações 1–16

#### Tarefa III.4 / Task III.4: Teste PIIPI Completo
**Data:** Ago 26-28  
**Teste:**
- Criar caso com 10+ documentos
- Avaliar Ações 1–16 (16 sub-tarefas principais)
- Auditor revisa e anota
- Gera relatório final consolidado

**Entrega:**
📸 Screenshot: Dashboard mostrando 16 ações  
📄 Documento: `PIIPI_TEST_REPORT.md` (PT + EN)

---

## Resumo Bloco III / Block III Summary

| Item | Status |
|------|--------|
| Ações 11–16 | ✅ Complete |
| Anotações + Audit Trail | ✅ Complete |
| PIIPI Teste E2E | ✅ Complete |

**Total Horas Bloco III / Block III Hours:** 100–120h

---

# BLOCO IV / BLOCK IV: Ações 17–25 & Groq Integration (Set 1 — Set 28)

## Objetivo / Objective
Ações 17–25 (Estruturação inicial) implementadas. Groq API integração testada.

---

### Semana 14-16 / Week 14-16 (Set 1-21): Ações 17–23

#### Tarefa IV.1 / Task IV.1: Ações 17–23 Implementação
**Data:** Set 1-21  
**Pattern familiar:** Crosswalk → código → teste

**Entrega:** Código por ação

---

### Semana 17 / Week 17 (Set 22-28): Groq API Integration

#### Tarefa IV.2 / Task IV.2: Implementar Groq Fallback
**Data:** Set 22-25  

**Funcionalidade:**
- Se Ollama indisponível, fallback para Groq
- Config via `config/llm_backends.json`
- Audit log rastreia chamadas Groq
- Teste: disable Ollama, verificar se Groq é usado

**Verificações:**
- [ ] Config permite habilitar Groq
- [ ] API key via environment variable
- [ ] Query anonimizado antes de enviar
- [ ] Resposta parseada igual a Ollama
- [ ] Latency melhor que Ollama? (esperado)

**Entrega:**
📄 Código: `src/maturity_check/evaluation/llm_backends.py`  
📸 Screenshot: Groq fallback funcionando  
📄 Documento: `GROQ_INTEGRATION.md` (PT + EN)

#### Tarefa IV.3 / Task IV.3: Performance Benchmarking
**Data:** Set 26-28  

**Testes:**
- Ollama latency: [X ms] por sub-tarefa
- Groq latency: [Y ms] por sub-tarefa
- Local vs. Groq accuracy: testes de 10 casos
- Relatório: quando usar qual?

**Entrega:**
📄 Documento: `PERFORMANCE_BENCHMARKS.md` (PT + EN)

---

### Ações 24–25 / Actions 24–25

#### Tarefa IV.4 / Task IV.4: Ações 24–25
**Data:** Set 1-21 (paralelo)

**Entrega:** Código + teste

---

## Resumo Bloco IV / Block IV Summary

| Item | Status |
|------|--------|
| Ações 17–25 | ✅ Complete |
| Groq API Integration | ✅ Complete |
| Performance Benchmarking | ✅ Complete |

**Total Horas Bloco IV / Block IV Hours:** 100–120h

---

# BLOCO V / BLOCK V: Ações 26–36 & Performance Tuning (Out 1 — Out 28)

## Objetivo / Objective
Ações 26–36 (Estruturação meio-termo) implementadas. Otimizações de performance completadas.

---

### Semana 18-20 / Week 18-20 (Out 1-20): Ações 26–35

#### Tarefa V.1 / Task V.1: Ações 26–35 Implementação
**Data:** Out 1-20  
**Pattern familiar**

**Entrega:** Código por ação

---

### Semana 21 / Week 21 (Out 21-28): Ação 36 & Performance Optimization

#### Tarefa V.2 / Task V.2: Ação 36 Implementação
**Data:** Out 21-25  
**Entrega:** Código + teste

#### Tarefa V.3 / Task V.3: Caching & Query Optimization
**Data:** Out 24-28  

**Otimizações:**
- Redis caching para queries comuns
- LanceDB query optimization
- BM25 index tuning
- Batch processing para múltiplas ações

**Verificações:**
- [ ] Cache miss rate < 20%
- [ ] Query tempo reduzido em 30%+
- [ ] Memory usage aceitável (<1GB)

**Entrega:**
📄 Código: Caching layer  
📄 Documento: `OPTIMIZATION_RESULTS.md` (PT + EN)

---

## Resumo Bloco V / Block V Summary

| Item | Status |
|------|--------|
| Ações 26–36 | ✅ Complete |
| Performance Optimization | ✅ Complete |

**Total Horas Bloco V / Block V Hours:** 100–120h

---

# BLOCO VI / BLOCK VI: Ações 37–46 & Testes Extensivos (Nov 1 — Nov 14)

## Objetivo / Objective
Todas as 46 ações implementadas e testadas com casos Rio reais.

---

### Semana 22-23 / Week 22-23 (Nov 1-10): Ações 37–46

#### Tarefa VI.1 / Task VI.1: Ações 37–46 Implementação
**Data:** Nov 1-10  
**Pattern:** Crosswalk → código → teste (9 ações)

**Entrega:** Código por ação

---

### Semana 24 / Week 24 (Nov 11-14): Teste Integrado Completo

#### Tarefa VI.2 / Task VI.2: Teste E2E com Casos Rio Reais
**Data:** Nov 11-14  

**Teste:**
- 5 casos Rio completos
- Todas 46 ações avaliadas
- Resultados validados manualmente vs. automated
- Performance aceitável (< 5min por caso)

**Verificações:**
- [ ] Todas ações retornam resultados
- [ ] Sem crashes ou erros
- [ ] Audit log completo
- [ ] Relatório final OK

**Entrega:**
📸 Screenshots: Dashboard mostrando 46 ações  
📄 Documento: `FULL_SYSTEM_VALIDATION_REPORT.md` (PT + EN)

---

## Resumo Bloco VI / Block VI Summary

| Item | Status |
|------|--------|
| Ações 37–46 | ✅ Complete |
| Full System Testing | ✅ Complete |

**Total Horas Bloco VI / Block VI Hours:** 80–100h

---

# BLOCO VII / BLOCK VII: Production Readiness & Deployment (Nov 15 — Nov 20)

## Objetivo / Objective
Sistema pronto para deployment em servidor Rio municipal.

---

### Semana 25-26 / Week 25-26 (Nov 15-20): Finalização

#### Tarefa VII.1 / Task VII.1: Security Hardening
**Data:** Nov 15-16  

**Checklist:**
- [ ] SQL injection prevention (parameterized queries)
- [ ] CSRF tokens em forms
- [ ] Password hashing (se multi-user)
- [ ] API rate limiting
- [ ] Audit logging completo
- [ ] Secrets management (.env)

**Entrega:**
📄 Documento: `SECURITY_CHECKLIST.md` (PT + EN)

#### Tarefa VII.2 / Task VII.2: Deployment Documentation & Runbook
**Data:** Nov 16-18  

**Conteúdo:**
- Como instalar em servidor Rio
- Database setup
- Ollama setup (ou Groq config)
- Nginx/Apache reverse proxy
- SSL certificates
- Backup strategy
- Recovery procedures

**Entrega:**
📄 Documento: `DEPLOYMENT_RUNBOOK.md` (PT + EN, 50+ páginas)

#### Tarefa VII.3 / Task VII.3: User Training Materials
**Data:** Nov 18-19  

**Materiais:**
- Auditor user manual (pdf)
- Admin manual (for Rio IT)
- Video tutorials (capturas de tela com narração PT)
- FAQ

**Entrega:**
📄 PDFs + videos

#### Tarefa VII.4 / Task VII.4: Final Integration Test
**Data:** Nov 19-20  

**Teste:**
- Deploy em staging server (simulando Rio environment)
- Full workflow test
- Performance under load (10+ concurrent users)
- 24h uptime test

**Verificações:**
- [ ] Tudo funciona em production environment
- [ ] Sem hardcoded paths ou localhost references
- [ ] Database backups funcionam
- [ ] Recovery procedures testadas

**Entrega:**
📄 Documento: `FINAL_TEST_REPORT.md` (PT + EN)

---

## Resumo Bloco VII / Block VII Summary

| Item | Status |
|------|--------|
| Security Hardening | ✅ Complete |
| Deployment Documentation | ✅ Complete |
| User Training Materials | ✅ Complete |
| Final Integration Test | ✅ Complete |

**Total Horas Bloco VII / Block VII Hours:** 60–80h

---

# RESUMO EXECUTIVO FASE 2 / PHASE 2 EXECUTIVE SUMMARY

## Datas / Dates
- **Início / Start:** 29 de Maio de 2026 / May 29, 2026
- **Fim / End:** 20 de Novembro de 2026 / November 20, 2026
- **Duração / Duration:** ~26 semanas / 26 weeks (~1000 horas / 1000 hours estimated)

## Entregáveis Fase 2 / Phase 2 Deliverables

| Item | Status |
|------|--------|
| Todas 46 ações M5D implementadas | ✅ Complete |
| Web UI para auditor | ✅ Complete |
| API REST completa | ✅ Complete |
| Groq integration (optional) | ✅ Complete |
| Performance otimizado | ✅ Complete |
| Deployment documentation | ✅ Complete |
| User training materials | ✅ Complete |
| Production-ready system | ✅ Complete |

## Metrics Esperadas / Expected Metrics

- **Latency:** < 5 min por caso completo (46 ações)
- **Accuracy:** > 90% match com avaliação manual
- **Uptime:** 99%+ (after Phase 2)
- **Documentation:** 200+ páginas (PT + EN)
- **Code coverage:** 80%+ (testes)

## Capabilidades Finais / Final Capabilities

- ✅ Avaliar 46 ações de procurement
- ✅ Multi-institutional support (múltiplas instituições Rio)
- ✅ Web UI com edição de resultados
- ✅ Groq API opcional (mais rápido)
- ✅ Audit trail completo
- ✅ Performance otimizado para 100+ casos simultâneos
- ✅ On-premises deployment (servidor Rio)

## O que Não Está / NOT Included

- ❌ Mobile app
- ❌ Outras jurisdições
- ❌ Machine learning retraining
- ❌ Advanced analytics/dashboards

---

# PRÓXIMOS PASSOS / NEXT STEPS

Após 20 de Novembro de 2026:
1. **Phase 3 (Future):** Expansão para DF, SP, outros estados
2. **Phase 4 (Future):** Mobile app + advanced analytics
3. **Maintenance (Ongoing):** Bug fixes, model updates

---

*Documento gerado: 28 de Abril de 2026 / Generated: April 28, 2026*
