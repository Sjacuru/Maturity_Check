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
          <v-icon start size="small">mdi-check</v-icon>Revisado ({{ review.final_score }})
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
      </div>

      <!-- 5. LLM reasoning -->
      <div class="mb-4">
        <div class="text-subtitle-2 mb-1">Raciocínio do LLM</div>
        <v-card variant="tonal" class="pa-3">
          <pre
            class="text-body-2"
            style="white-space: pre-wrap; overflow-x: auto;"
          >{{ evaluation.reasoning || '(sem raciocínio registado)' }}</pre>
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
          <v-chip :color="scoreColor(review.final_score)" label>
            Score final: {{ review.final_score }}
          </v-chip>
          <v-chip v-if="review.is_override" color="warning" size="small" label>Override</v-chip>
        </div>
        <div v-if="review.justification" class="text-body-2 text-medium-emphasis">
          Justificativa: {{ review.justification }}
        </div>
      </div>
      <ReviewForm
        v-else
        :proposed-score="evaluation.proposed_score"
        :process-number="processNumber"
        :acao-id="evaluation.acao_id"
        @submitted="review = $event"
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

const review = ref(null)

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
