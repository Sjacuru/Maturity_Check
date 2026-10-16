<template>
  <v-expansion-panel>
    <v-expansion-panel-title>
      <div class="d-flex align-center flex-wrap" style="gap: 8px;">
        <span class="font-weight-bold">Ação {{ evaluation.acao_id }}</span>
        <v-chip size="small" :color="scoreColor(evaluation.proposed_score)" label>
          Score: {{ evaluation.proposed_score ?? '—' }}
        </v-chip>
        <v-chip size="small" :color="evaluation.uncertainty_flag ? 'warning' : 'success'" variant="flat" label>
          <v-icon start size="small">{{ evaluation.uncertainty_flag ? 'mdi-alert' : 'mdi-check' }}</v-icon>
          Incerteza: {{ evaluation.uncertainty_flag ? 'Sim' : 'Não' }}
        </v-chip>
        <v-chip size="small" :color="evaluation.parse_failed ? 'error' : 'success'" variant="flat" label>
          <v-icon start size="small">{{ evaluation.parse_failed ? 'mdi-close-circle' : 'mdi-check' }}</v-icon>
          Parse falhou: {{ evaluation.parse_failed ? 'Sim' : 'Não' }}
        </v-chip>
        <v-chip v-if="evaluation.no_evidence_found" size="small" color="error" label>
          Sem evidência
        </v-chip>
        <v-chip v-if="review" size="small" color="success" label>
          <v-icon start size="small">mdi-check</v-icon>Revisado ({{ review.not_applicable ? 'N/A' : review.final_score }})
        </v-chip>
      </div>
    </v-expansion-panel-title>

    <v-expansion-panel-text>
      <!-- Verdict — score + label + flags, front and center -->
      <v-card variant="tonal" :color="scoreColor(evaluation.proposed_score)" class="mb-4 pa-4">
        <div class="d-flex align-center flex-wrap" style="gap: 16px;">
          <div class="text-h3 font-weight-bold" style="line-height: 1;">
            {{ evaluation.proposed_score ?? '—' }}
          </div>
          <div>
            <div class="text-subtitle-1 font-weight-medium">{{ scoreLabel(evaluation.proposed_score) }}</div>
            <div class="text-caption text-medium-emphasis">
              {{ evaluation.provider }} · {{ evaluation.model }}
            </div>
            <div v-if="productVerdicts.length" class="text-caption text-medium-emphasis">
              {{ evidencedCount }} de {{ productVerdicts.length }} Produto(s) Esperado(s) evidenciado(s)
              <span v-if="evaluation.score_source === 'computed'">· score contado em código</span>
              <span v-else class="text-warning">· score informado pelo modelo</span>
            </div>
            <!-- ADR-0070: a counted 3 capped to 1 because a prerequisite Ação
                 came out 0 / sem evidência in this run. The count stays visible. -->
            <div v-if="dependencyCap && dependencyCap.applied" class="text-caption font-weight-medium">
              Score contado: {{ dependencyCap.score_before_cap }} · limitado a
              {{ evaluation.proposed_score }} por dependência não atendida
            </div>
            <!-- The deterministic interval: same input gives the same score AND
                 the same interval, so showing it costs no reproducibility. -->
            <div v-if="showScoreInterval" class="text-caption font-weight-medium">
              Intervalo: {{ scoreBandLabel(scoreMargin.score_floor) }} —
              {{ scoreBandLabel(scoreMargin.score_ceiling) }}
            </div>
            <div
              v-if="scoreMargin && scoreMargin.band_margin !== null"
              class="text-caption text-medium-emphasis"
            >
              {{ scoreMargin.band_margin }} veredito(s) de produto mudaria(m) a faixa
              <span v-if="scoreMargin.n_fragile">
                · {{ scoreMargin.n_fragile }} produto(s) sustentado(s) por um único trecho
              </span>
            </div>
          </div>
          <v-spacer />
          <div class="d-flex flex-column align-end" style="gap: 4px;">
            <v-chip
              size="small"
              :color="evaluation.uncertainty_flag ? 'warning' : 'success'"
              variant="flat"
            >
              <v-icon start size="small">{{ evaluation.uncertainty_flag ? 'mdi-alert-circle' : 'mdi-check-circle' }}</v-icon>
              Incerteza: {{ evaluation.uncertainty_flag ? 'Sim' : 'Não' }}
            </v-chip>
            <v-chip
              size="small"
              :color="evaluation.parse_failed ? 'error' : 'success'"
              variant="flat"
            >
              <v-icon start size="small">{{ evaluation.parse_failed ? 'mdi-close-circle' : 'mdi-check-circle' }}</v-icon>
              Falha de parsing: {{ evaluation.parse_failed ? 'Sim' : 'Não' }}
            </v-chip>
            <v-chip
              size="small"
              :color="evaluation.no_evidence_found ? 'error' : 'success'"
              variant="flat"
            >
              <v-icon start size="small">{{ evaluation.no_evidence_found ? 'mdi-close-circle' : 'mdi-check-circle' }}</v-icon>
              Evidência encontrada: {{ evaluation.no_evidence_found ? 'Não' : 'Sim' }}
            </v-chip>
          </div>
        </div>
      </v-card>

      <!-- Gate failures. A truncated or unparseable gate response used to be
           indistinguishable from a substantive "not relevant" verdict, so real
           evidence could be dropped with nothing on screen to say so. -->
      <v-alert
        v-if="gateFailureCount > 0"
        type="warning"
        variant="tonal"
        density="compact"
        class="mb-4"
      >
        <strong>{{ gateFailureCount }} chamada(s) ao gate falharam</strong> — resposta truncada,
        ilegível ou recusada pelo servidor. Os trechos correspondentes foram descartados
        <em>sem julgamento de mérito</em>, então o score abaixo pode estar subestimado.
        Reexecute esta Ação antes de validar.
      </v-alert>

      <!-- score_source = "model" means the per-product verdicts were absent or
           did not cover the Ação's products, so the rubric was not counted in
           code and the model's own number was used. -->
      <v-alert
        v-if="hasGateInstrumentation && evaluation.score_source === 'model' && !evaluation.no_evidence_found && !evaluation.parse_failed"
        type="info"
        variant="tonal"
        density="compact"
        class="mb-4"
      >
        O modelo não devolveu vereditos utilizáveis por Produto Esperado, então a regra 0/1/3
        não pôde ser contada em código — o score exibido é o que o próprio modelo informou.
      </v-alert>

      <!-- ADR-0070: the dependency cap. The citing Ação cannot receive 3 when
           a prerequisite Ação was found in 0 / sem evidência — "não há revisão
           ou confirmação do que não foi feito". Arithmetic over this run's own
           scores; the scorer never sees it. -->
      <v-alert
        v-if="dependencyCap && dependencyCap.applied"
        type="warning"
        variant="tonal"
        density="compact"
        class="mb-4"
        title="Score limitado por dependência"
      >
        {{ dependencyCap.explanation }}
        <div class="text-caption mt-2">
          O score contado ({{ dependencyCap.score_before_cap }}) e os vereditos por produto
          continuam visíveis abaixo. Se a Ação citada for revisada, este teto não muda
          sozinho — decida na revisão desta Ação.
        </div>
      </v-alert>

      <!-- The auditor signal (decided 2026-10-05): review is OPTIONAL. The
           system states what happened inside its own process and the auditor
           decides whether to touch the score. Deliberately NOT an action on the
           gate — the only intervention point is the final score, below. -->
      <v-alert
        v-if="reviewRecommended"
        type="info"
        variant="tonal"
        density="compact"
        class="mb-4"
        title="Revisão sugerida (opcional)"
      >
        <div v-if="scoreMargin && scoreMargin.review_recommended">
          {{ scoreMargin.explanation }}
          <div class="text-caption mt-2">
            Aceites do gate não são constantes entre passadas, e um produto sustentado por um
            único trecho perde seu veredito se aquele trecho não for aceito. A decisão é sua:
            mantenha ou altere o score na revisão abaixo.
          </div>
        </div>
        <!-- ADR-0070: the citing Ação is a later version of the same document
             whose initial version was not evidenced — a gate inconsistency to
             look at, never a cap. -->
        <div v-if="dependencyCap && dependencyCap.review_recommended" :class="{ 'mt-2': scoreMargin && scoreMargin.review_recommended }">
          {{ dependencyCap.explanation }}
        </div>
      </v-alert>

      <!-- Per-product coverage. The 0/1/3 rubric is a count over the Expected
           Products, so this table is what the score actually rests on. -->
      <div class="mb-4" v-if="productRows.length">
        <div class="text-subtitle-2 mb-2">Cobertura por Produto Esperado</div>
        <v-table density="compact">
          <thead>
            <tr>
              <th>Produto</th>
              <th class="text-center">Evidenciado</th>
              <th class="text-center">Examinados</th>
              <th class="text-center">Aceitos</th>
              <th class="text-center">Descartados</th>
              <th class="text-center">Falhas</th>
              <th v-if="scoreMargin" class="text-center">Margem</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in productRows" :key="row.productId">
              <td class="font-weight-medium">{{ row.productId }}</td>
              <td class="text-center">
                <v-chip
                  v-if="row.evidenced !== null"
                  size="x-small"
                  :color="row.evidenced ? 'success' : 'error'"
                  variant="flat"
                >
                  {{ row.evidenced ? 'Sim' : 'Não' }}
                </v-chip>
                <span v-else class="text-medium-emphasis">—</span>
              </td>
              <td class="text-center">{{ row.nExamined ?? '—' }}</td>
              <td class="text-center">{{ row.nAccepted ?? '—' }}</td>
              <td class="text-center">{{ row.nRejected ?? '—' }}</td>
              <td class="text-center">
                <span :class="row.nFailures ? 'text-warning font-weight-bold' : ''">
                  {{ row.nFailures ?? '—' }}
                </span>
              </td>
              <!-- How many accepted chunks hold this product's `evidenced` bit,
                   as the scorer saw them. 1 on an evidenced product means the
                   bit turns off deterministically if that one chunk is not
                   accepted on the next pass. -->
              <td v-if="scoreMargin" class="text-center">
                <v-chip
                  v-if="marginByProduct.get(row.productId)?.fragile"
                  size="x-small"
                  color="warning"
                  variant="flat"
                  title="Bit evidenciado sustentado por um único trecho aceito"
                >
                  1
                </v-chip>
                <span v-else>{{ marginByProduct.get(row.productId)?.n_accepted ?? '—' }}</span>
              </td>
            </tr>
          </tbody>
        </v-table>
        <div
          v-for="row in productRows.filter((r) => r.justificativa)"
          :key="`j-${row.productId}`"
          class="text-caption text-medium-emphasis mt-2"
        >
          <strong>{{ row.productId }}:</strong> {{ row.justificativa }}
        </div>
      </div>

      <!-- AI retrieval performance — candidates examined by the relevance gate -->
      <div class="mb-4" v-if="totalExamined > 0">
        <div class="text-subtitle-2 mb-2">Atuação da IA na recuperação de evidências</div>
        <v-row dense>
          <v-col cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-h5 font-weight-bold text-primary">{{ totalExamined }}</div>
              <div class="text-caption text-medium-emphasis">Candidatos examinados</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-h5 font-weight-bold text-success">{{ acceptedCount }}</div>
              <div class="text-caption text-medium-emphasis">Aceitos pelo gate</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-h5 font-weight-bold">{{ rejectedCount }}</div>
              <div class="text-caption text-medium-emphasis">Descartados pelo gate</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-h5 font-weight-bold text-warning">{{ flaggedRejectedCount }}</div>
              <div class="text-caption text-medium-emphasis">Descartes com termo correspondente</div>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- 3. Retrieved chunks (Evidence section) -->
      <div class="mb-4">
        <div class="text-subtitle-2 mb-2">
          Evidências aceitas — {{ evaluation.retrieved_chunks.length }} chunk(s) recuperado(s)
        </div>
        <v-expansion-panels variant="accordion" density="compact">
          <v-expansion-panel
            v-for="(chunk, i) in evaluation.retrieved_chunks"
            :key="i"
          >
            <v-expansion-panel-title class="text-body-2">
              <div class="d-flex align-center flex-wrap" style="gap: 6px;">
                <span>{{ chunk.filename }} p.{{ chunk.page_number }}</span>
                <v-chip size="x-small" label>{{ chunk.cascade_step }}</v-chip>
                <v-chip
                  size="x-small"
                  :color="chunk.retrieval_mode === 'vector_fallback' ? 'secondary' : 'primary'"
                  label
                >{{ chunk.retrieval_mode }}</v-chip>
                <span v-if="chunk.rank" class="text-caption text-medium-emphasis">
                  rank {{ chunk.rank }}
                </span>
                <v-chip
                  v-for="c in chunk.matched_concepts"
                  :key="c"
                  size="x-small"
                  variant="tonal"
                  label
                >{{ c }}</v-chip>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <!-- 2. Retrieval query — per-chunk -->
              <div v-if="chunk.retrieval_query" class="mb-2">
                <span class="text-caption text-medium-emphasis">Query: </span>
                <code class="text-caption">{{ chunk.retrieval_query }}</code>
              </div>
              <pre class="text-body-2" style="white-space: pre-wrap; overflow-x: auto;">{{ chunk.text }}</pre>
              <!-- Gate reasoning per product (persisted since 2026-10-03; older rows have none) -->
              <div
                v-for="(reason, pid) in (chunk.gate_reasoning ?? {})"
                :key="pid"
                class="mt-2"
              >
                <span class="text-caption text-medium-emphasis">
                  Raciocínio do gate ({{ pid }}<span v-if="chunk.gate_source?.[pid]">, {{ sourceLabel(chunk.gate_source[pid]) }}</span>):
                </span>
                <pre class="text-caption" style="white-space: pre-wrap; overflow-x: auto;">{{ reason }}</pre>
                <v-btn
                  v-if="chunk.gate_prompt_hash?.[pid]"
                  size="x-small"
                  variant="tonal"
                  color="warning"
                  :loading="overriding === chunk.gate_prompt_hash[pid]"
                  @click="overrideGate(chunk.gate_prompt_hash[pid], false)"
                >Auditor: marcar como NÃO relevante ({{ pid }})</v-btn>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
        <v-alert
          v-if="!evaluation.retrieved_chunks.length"
          type="warning"
          density="compact"
          variant="tonal"
          class="mt-2"
        >Nenhum chunk recuperado para esta ação.</v-alert>
      </div>

      <!-- Rejected chunks — what the relevance gate discarded -->
      <div class="mb-4" v-if="rejectedCount > 0">
        <div class="text-subtitle-2 mb-2">
          Evidências descartadas pelo gate — {{ rejectedCount }} candidato(s)
        </div>
        <v-expansion-panels variant="accordion" density="compact">
          <v-expansion-panel v-for="group in rejectedByProduct" :key="group.productId">
            <v-expansion-panel-title class="text-body-2">
              <div class="d-flex align-center flex-wrap" style="gap: 6px;">
                <v-chip size="x-small" color="primary" label>{{ group.productId }}</v-chip>
                <span>{{ group.items.length }} descartado(s)</span>
                <v-chip v-if="group.flaggedCount" size="x-small" color="warning" variant="flat">
                  {{ group.flaggedCount }} com termo correspondente
                </v-chip>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-table density="compact">
                <thead>
                  <tr>
                    <th>Arquivo</th>
                    <th>Pág.</th>
                    <th>Conceitos encontrados no texto</th>
                    <th>Raciocínio do gate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, i) in group.items" :key="i">
                    <td class="text-caption">{{ item.filename }}</td>
                    <td class="text-caption">{{ item.page_number }}</td>
                    <td>
                      <v-chip
                        v-for="c in item.matched_concepts"
                        :key="c"
                        size="x-small"
                        color="warning"
                        variant="tonal"
                        label
                        class="mr-1"
                      >{{ c }}</v-chip>
                      <span
                        v-if="!item.matched_concepts.length"
                        class="text-caption text-medium-emphasis"
                      >—</span>
                    </td>
                    <td style="max-width: 520px;">
                      <pre
                        v-if="item.gate_reasoning"
                        class="text-caption"
                        style="white-space: pre-wrap; overflow-x: auto;"
                      >{{ item.gate_reasoning }}</pre>
                      <span v-else class="text-caption text-medium-emphasis">
                        {{ item.gate_failed ? 'chamada falhou — sem julgamento' : '—' }}
                      </span>
                      <div v-if="item.gate_source" class="text-caption text-medium-emphasis">
                        origem: {{ sourceLabel(item.gate_source) }}
                      </div>
                      <v-btn
                        v-if="item.gate_prompt_hash && !item.gate_failed"
                        size="x-small"
                        variant="tonal"
                        color="warning"
                        class="mt-1"
                        :loading="overriding === item.gate_prompt_hash"
                        @click="overrideGate(item.gate_prompt_hash, true)"
                      >Auditor: marcar como relevante</v-btn>
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
        <div class="text-caption text-medium-emphasis mt-2">
          Linhas com conceitos listados continham, no próprio texto, um termo da busca daquele
          produto — o gate mesmo assim classificou como não relevante. Não é necessariamente um
          erro, mas vale conferência.
        </div>
        <v-alert
          v-if="overrideMessage"
          :type="overrideError ? 'error' : 'info'"
          density="compact"
          variant="tonal"
          class="mt-2"
        >{{ overrideMessage }}</v-alert>
      </div>

      <!-- 5. LLM reasoning -->
      <div class="mb-4">
        <div class="text-subtitle-2 mb-1">Raciocínio do LLM</div>
        <v-card variant="tonal" class="pa-3">
          <pre
            class="text-body-2"
            style="white-space: pre-wrap; overflow-x: auto;"
          >{{ evaluation.reasoning || '(sem raciocínio registrado)' }}</pre>
        </v-card>
      </div>

      <!-- 1 + 4. Full Prompt (IPMP criteria + exact LLM prompt — collapsible) -->
      <v-expansion-panels class="mb-4">
        <v-expansion-panel title="Prompt completo (critérios IPMP + evidências enviadas)">
          <v-expansion-panel-text>
            <div class="text-caption text-medium-emphasis mb-1">System prompt (critérios IPMP):</div>
            <pre
              class="text-body-2 mb-4"
              style="white-space: pre-wrap; overflow-x: auto;"
            >{{ evaluation.system_prompt }}</pre>
            <v-divider class="mb-3" />
            <div class="text-caption text-medium-emphasis mb-1">
              User prompt (evidências enviadas ao LLM):
            </div>
            <pre
              class="text-body-2"
              style="white-space: pre-wrap; overflow-x: auto;"
            >{{ evaluation.user_prompt }}</pre>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <!-- Review: read-only if submitted, form if not -->
      <v-divider class="mb-4" />
      <div v-if="review">
        <div class="text-subtitle-2 mb-2">Revisão submetida</div>
        <div class="d-flex align-center flex-wrap mb-2" style="gap: 8px;">
          <v-chip v-if="review.not_applicable" color="info" label>Não aplicável</v-chip>
          <v-chip v-else :color="scoreColor(review.final_score)" label>
            Score final: {{ review.final_score }}
          </v-chip>
          <v-chip v-if="review.is_override" color="warning" size="small" label>Override</v-chip>
        </div>
        <div v-if="review.justification" class="text-body-2 text-medium-emphasis">
          {{ review.not_applicable ? 'Motivação' : 'Justificativa' }}: {{ review.justification }}
        </div>
      </div>
      <ReviewForm
        v-else
        :proposed-score="evaluation.proposed_score"
        :process-number="processNumber"
        :acao-id="evaluation.acao_id"
        @submitted="onReviewSubmitted"
      />
    </v-expansion-panel-text>
  </v-expansion-panel>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import ReviewForm from './ReviewForm.vue'

const props = defineProps({
  evaluation: Object,
  processNumber: String,
})

const emit = defineEmits(['reviewed'])

const review = ref(null)

// The case view refreshes its maturity indicator when a review lands (ADR-0075).
function onReviewSubmitted(outcome) {
  review.value = outcome
  emit('reviewed', outcome)
}
const overriding = ref(null)
const overrideMessage = ref('')
const overrideError = ref(false)

function sourceLabel(src) {
  return { model: 'modelo (nesta execução)', ledger: 'registro de vereditos', auditor: 'auditor' }[src] ?? src
}

// ADR-0067: the auditor overturns one frozen gate verdict. The stored evaluation
// is not rewritten; the new verdict applies when the case is assessed again.
async function overrideGate(promptHash, relevant) {
  const justification = window.prompt(
    `Justificativa para marcar este trecho como ${relevant ? 'RELEVANTE' : 'NÃO relevante'} (obrigatória):`
  )
  if (!justification || !justification.trim()) return
  overriding.value = promptHash
  overrideError.value = false
  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(props.processNumber)}/evaluations/${props.evaluation.acao_id}/gate-overrides`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt_hash: promptHash, relevant, justification: justification.trim() }),
      }
    )
    const data = await resp.json().catch(() => ({}))
    if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`)
    overrideMessage.value =
      `Veredito do gate substituído pelo auditor (${data.product_id}, relevante=${data.relevant}). ` +
      'Vale a partir da próxima avaliação deste caso; esta avaliação não foi reescrita.'
  } catch (e) {
    overrideError.value = true
    overrideMessage.value = `Não foi possível registrar o override: ${e.message}`
  } finally {
    overriding.value = null
  }
}

onMounted(async () => {
  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(props.processNumber)}/evaluations/${props.evaluation.acao_id}/review`
    )
    if (resp.ok) review.value = await resp.json()
  } catch {
    // no review yet — normal case
  }
})

function scoreColor(s) {
  return { 0: 'error', 1: 'warning', 3: 'success' }[s] ?? 'default'
}

function scoreLabel(s) {
  return (
    { 0: 'Não Atendido', 1: 'Parcialmente Atendido', 3: 'Atendido' }[s] ??
    'Não avaliado (falha de parsing)'
  )
}

const acceptedCount = computed(() => props.evaluation.retrieved_chunks?.length ?? 0)
const rejectedCount = computed(() => props.evaluation.rejected_chunks?.length ?? 0)
const totalExamined = computed(() => acceptedCount.value + rejectedCount.value)
const flaggedRejectedCount = computed(
  () => (props.evaluation.rejected_chunks ?? []).filter((c) => c.matched_concepts?.length).length
)

// Every field below is optional: evaluations persisted before 2026-09-27 have
// no product_verdicts / product_gate_reports / score_source, and must keep
// rendering exactly as they did.
const productVerdicts = computed(() => props.evaluation.product_verdicts ?? [])
const gateReports = computed(() => props.evaluation.product_gate_reports ?? [])

const evidencedCount = computed(() => productVerdicts.value.filter((v) => v.evidenced).length)

// Deterministic score margin (2026-10-05). Absent on rows persisted earlier, so
// every read goes through this guard and the whole block stays hidden for them.
const scoreMargin = computed(() => props.evaluation.score_margin ?? null)

// Dependency cap (ADR-0070). Absent on rows persisted before 2026-10-09 and on
// the no-evidence exit, so every read goes through this guard.
const dependencyCap = computed(() => props.evaluation.dependency_cap ?? null)

const reviewRecommended = computed(
  () =>
    Boolean(scoreMargin.value?.review_recommended) ||
    Boolean(dependencyCap.value?.review_recommended)
)

const marginByProduct = computed(() => {
  const map = new Map()
  for (const p of scoreMargin.value?.products ?? []) map.set(p.product_id, p)
  return map
})

// The interval is only worth showing when its ends differ — otherwise the score
// already says everything the margin would.
const showScoreInterval = computed(
  () =>
    scoreMargin.value !== null &&
    scoreMargin.value.attribution_complete &&
    scoreMargin.value.score_floor !== scoreMargin.value.score_ceiling
)

function scoreBandLabel(score) {
  return score === null || score === undefined ? 'sem evidência' : `score ${score}`
}

// score_source defaults to "model" on rows persisted before 2026-09-27, so it
// alone cannot tell an uncooperative model from an older evaluation. The gate
// reports only exist on runs that carry the new instrumentation.
const hasGateInstrumentation = computed(() => gateReports.value.length > 0)

const gateFailureCount = computed(() =>
  gateReports.value.reduce((total, r) => total + (r.n_gate_failures ?? 0), 0)
)

// One row per Expected Product, joining the scorer's verdict with the gate's
// own counters. A product can appear in either source alone — a gate report
// with no verdict (the model skipped it), or a verdict with no report (nothing
// was ever retrieved for it) — and both cases must stay visible.
const productRows = computed(() => {
  const rows = new Map()
  for (const r of gateReports.value) {
    rows.set(r.expected_product_id, {
      productId: r.expected_product_id,
      evidenced: null,
      justificativa: '',
      nExamined: r.n_examined,
      nAccepted: r.n_accepted,
      nRejected: r.n_rejected,
      nFailures: r.n_gate_failures ?? 0,
    })
  }
  for (const v of productVerdicts.value) {
    const row = rows.get(v.product_id) ?? {
      productId: v.product_id,
      nExamined: null,
      nAccepted: null,
      nRejected: null,
      nFailures: null,
    }
    row.evidenced = v.evidenced
    row.justificativa = v.justificativa ?? ''
    rows.set(v.product_id, row)
  }
  return [...rows.values()].sort((a, b) => a.productId.localeCompare(b.productId))
})

const rejectedByProduct = computed(() => {
  const groups = {}
  for (const item of props.evaluation.rejected_chunks ?? []) {
    const key = item.expected_product_id
    ;(groups[key] ??= []).push(item)
  }
  return Object.keys(groups)
    .sort()
    .map((productId) => ({
      productId,
      items: groups[productId],
      flaggedCount: groups[productId].filter((c) => c.matched_concepts?.length).length,
    }))
})
</script>
