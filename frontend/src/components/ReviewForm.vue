<template>
  <div>
    <div class="text-subtitle-2 mb-3">Revisão do Auditor</div>

    <div class="d-flex align-center flex-wrap mb-3" style="gap: 8px;">
      <span class="text-body-2">Score final:</span>
      <v-btn-toggle v-model="selectedScore" mandatory density="compact" rounded="lg">
        <v-btn
          v-for="s in [0, 1, 3]"
          :key="s"
          :value="s"
          :color="s === proposedScore ? 'primary' : undefined"
          size="small"
        >
          {{ s }}
          <v-tooltip v-if="s === proposedScore" activator="parent" location="top">
            Score proposto
          </v-tooltip>
        </v-btn>
        <v-btn v-if="admitsNotApplicable" :value="NA" size="small">
          N/A
          <v-tooltip activator="parent" location="top">
            Não aplicável: etapa futura que o empreendimento comprovadamente ainda não
            alcançou (Guia, 4.1)
          </v-tooltip>
        </v-btn>
      </v-btn-toggle>
      <span v-if="notApplicable" class="text-caption text-warning">
        Não aplicável — sai da nota. Falta de evidência não é isto: segue "não atendida".
      </span>
      <span v-else-if="isOverride" class="text-caption text-warning">
        {{ proposedScore == null
          ? 'Sem score proposto (sem evidência) — atribuição do auditor'
          : `Diferente do proposto (${proposedScore}) — override` }}
      </span>
    </div>

    <v-textarea
      v-if="needsNote"
      v-model="justification"
      :label="notApplicable ? 'Motivação da dispensa (obrigatória)' : 'Justificativa (obrigatória)'"
      :hint="notApplicable
        ? 'Registre a motivação técnica e documental: que etapa ainda não foi alcançada, e onde os documentos param (Guia, 4.1).'
        : 'Explique por que o score proposto não está correto.'"
      persistent-hint
      rows="3"
      class="mb-3"
    />

    <v-alert v-if="submitError" type="error" density="compact" class="mb-3">
      {{ submitError }}
    </v-alert>

    <v-btn
      color="primary"
      :loading="submitting"
      :disabled="selectedScore == null || (needsNote && !justification.trim())"
      @click="submit"
    >
      Submeter revisão
    </v-btn>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  proposedScore: Number,
  processNumber: String,
  acaoId: Number,
})

const emit = defineEmits(['submitted'])

const selectedScore = ref(props.proposedScore)
const justification = ref('')
const submitting = ref(false)
const submitError = ref(null)

// The Ações that admit "não aplicável" (ADR-0076); mirrors NOT_APPLICABLE_ACOES
// in src/assessment/interfaces/contracts.py, which the route enforces.
const NOT_APPLICABLE_ACOES = [45, 46]
const NA = 'na'

const admitsNotApplicable = computed(() => NOT_APPLICABLE_ACOES.includes(props.acaoId))
const notApplicable = computed(() => selectedScore.value === NA)
const isOverride = computed(
  () => !notApplicable.value && selectedScore.value !== props.proposedScore
)
const needsNote = computed(() => isOverride.value || notApplicable.value)

function reviewBody() {
  if (notApplicable.value) {
    return {
      final_score: null,
      is_override: false,
      not_applicable: true,
      justification: justification.value.trim(),
    }
  }
  return {
    final_score: selectedScore.value,
    is_override: isOverride.value,
    justification: isOverride.value ? justification.value.trim() : null,
  }
}

async function submit() {
  if (selectedScore.value == null) return
  if (needsNote.value && !justification.value.trim()) return
  submitting.value = true
  submitError.value = null

  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(props.processNumber)}/evaluations/${props.acaoId}/review`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reviewBody()),
      }
    )
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({ detail: resp.statusText }))
      throw new Error(detail.detail ?? `HTTP ${resp.status}`)
    }
    emit('submitted', await resp.json())
  } catch (e) {
    submitError.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>
