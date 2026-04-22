# Pre-EPIC — resolved decisions (archive)

This file holds **decisions that are no longer tracked** in [pendencias_pre_epic.md](pendencias_pre_epic.md). The pendencies file lists **only unresolved** items.

Last updated: aligned with stakeholder clarifications (Rio deployment, DF+Rio as breadth for classification, `Plan/06_Models` reference PDFs).

---

## Reference materials location (`Plan/06_Models`)

All paths below are under **`Plan/06_Models/`** (no URL encoding required in the working tree).

| File | Role (short) |
|------|----------------|
| `M5D.md` | M5D guide text (dev/reference; official framework PDF remains canonical per PRD decisions) |
| `in_01_2024_TCDF.pdf` | IN 01/2024 TCDF — document/procedure patterns (DF) |
| `ManualparaPreAnaliseAvaliacaoEstruturacaoeImplementacaodePPPsvolume3.pdf` | Rio de Janeiro pre-analysis manual (Vol. 3) |
| `Estruturação de projetos de PPP e concessão no Brasil_P.pdf` | Additional PPP structuring reference |
| `Licitacoes-e-Contratos-Orientacoes-e-Jurisprudencia-do-TCU-5a-Edicao-29-08-2024.pdf` | TCU orientations / jurisprudence (5th ed.) |
| `PROC-IBR-SOCIOAMB-003_2024-Estudos-que-atestem-a-viabilidade-tecnica-economica-social-e-ambiental-v-19set.pdf` | IBR socio-environmental viability studies proc. |

---

## FR-008 — baseline classification rule (v0)

**Problem addressed**  
Procurement files often lack consistent naming; artifacts may be embedded or only titled inside a PDF.

**Agreed v0 rule**  
No mandatory “expected file name” list as the only signal. Classification **records the method used**:

1. **File name** (best case)  
2. **Title/header** extracted from the PDF  
3. **Semantic** match on content  

**Supplementary normative layer (Rio + DF)**  
DF (IN 01/2024 TCDF) and Rio (Manual) documents were developed partly from M5D. **Operational deployment is Rio**; **both sources are retained** to widen synonym and procedure coverage so irregular naming does not alone collapse scores. Cross-source comparison for **Ação 1** is captured in stakeholder analysis (DF vs Rio labels as **synonyms** for the same intent where applicable).

**Grau (Alto / Médio / Baixo)** — definition agreed  
**Grau** = how close the artifact or procedure is to the **reference pattern**, defined as **M5D** interpreted together with **Rio** and **DF** reference materials (not M5D alone).

*Implementation note (for later EPIC):* whether Grau affects **retrieval priority only**, **quality rubric**, or **numeric score** remains a product decision — see open pendencies.*

---

## Topic B — Vertical slice (decided portion)

- Start evaluation pipeline with **Ação 1**; first expansion band **Ação 1–16** (*Proposta Inicial de Investimento*).
- **Stable IDs**: use immutable keys `action_1` … `action_46` (Portuguese titles may change; keys do not).

*Open confirmation (tracked in pendencias): adopt `action_<N>` as primary key in FR-001 store.*

---

## Topic C — OQ-001: Sub-task weights (FR-002, FR-013)

**Resolved:** equal weights until custom weights are supplied.

---

## Topic F — OQ-006: UNCERTAINTY threshold (FR-015, NFR-002)

**Resolved:** confidence threshold **70%** (below → UNCERTAINTY flag).

---

## Topic G — OQ-007: Pre-M5D documents

**Resolved:** evaluate pre-M5D case documents with M5D (+ overlay) criteria to surface the **maturity gap**.

---

## Topic K — EPIC gate timing

**Resolved (process):** draft EPIC first, then walk **gates 2A–2J** in [UNIVERSAL_PHASE_GATES.md](../../UNIVERSAL_PHASE_GATES.md) one by one before locking the EPIC baseline.

---

## Topic E — OQ-004 / NFR-006: Latency

**Deferred (explicit):** no numeric response-time SLO until the flow works end-to-end.
