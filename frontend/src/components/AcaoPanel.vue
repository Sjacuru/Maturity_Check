<template>
  <v-expansion-panel>
    <v-expansion-panel-title>
      <div class="d-flex align-center flex-wrap" style="gap: 8px;">
        <span class="font-weight-bold">Ação {{ evaluation.acao_id }}</span>
        <v-chip size="small" :color="scoreColor(evaluation.proposed_score)" label>
          Score: {{ evaluation.proposed_score }}
        </v-chip>
        <v-chip v-if="evaluation.uncertainty_flag" size="small" color="warning" label>
          <v-icon start size="small">mdi-alert</v-icon>Incerteza
        </v-chip>
        <v-chip v-if="evaluation.parse_failed" size="small" color="error" label>Parse falhou</v-chip>
        <v-chip v-if="evaluation.no_evidence_found" size="small" color="error" label>
          Sem evidência
        </v-chip>
        <v-chip v-if="review" size="small" color="success" label>
          <v-icon start size="small">mdi-check</v-icon>Revisado ({{ review.final_score }})
        </v-chip>
      </div>
    </v-expansion-panel-title>

    <v-expansion-panel-text>
      <!-- 6. Uncertainty flag — prominent in-panel display -->
      <v-alert
        v-if="evaluation.uncertainty_flag"
        type="warning"
        variant="tonal"
        class="mb-4"
        density="compact"
        icon="mdi-alert-circle"
      >
        Avaliação marcada com <strong>flag de incerteza</strong>. Revise as evidências com atenção.
      </v-alert>

      <!-- 7. Proposed score — read-only above review form -->
      <div class="mb-4 d-flex align-center" style="gap: 8px;">
        <span class="text-subtitle-2 text-medium-emphasis">Score proposto:</span>
        <v-chip :color="scoreColor(evaluation.proposed_score)" label>
          {{ evaluation.proposed_score }}
        </v-chip>
        <span class="text-caption text-medium-emphasis">
          ({{ evaluation.provider }} / {{ evaluation.model }})
        </span>
      </div>

      <!-- 3. Retrieved chunks (Evidence section) -->
      <div class="mb-4">
        <div class="text-subtitle-2 mb-2">
          Evidências — {{ evaluation.retrieved_chunks.length }} chunk(s) recuperado(s)
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
import { ref, onMounted } from 'vue'
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
</script>
