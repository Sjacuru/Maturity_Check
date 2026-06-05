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
      </v-btn-toggle>
      <span v-if="isOverride" class="text-caption text-warning">
        Diferente do proposto ({{ proposedScore }}) — override
      </span>
    </div>

    <v-textarea
      v-if="isOverride"
      v-model="justification"
      label="Justificativa (obrigatória)"
      hint="Explique por que o score proposto não está correto."
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
      :disabled="isOverride && !justification.trim()"
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
  acoaId: Number,
})

const emit = defineEmits(['submitted'])

const selectedScore = ref(props.proposedScore)
const justification = ref('')
const submitting = ref(false)
const submitError = ref(null)

const isOverride = computed(() => selectedScore.value !== props.proposedScore)

async function submit() {
  if (isOverride.value && !justification.value.trim()) return
  submitting.value = true
  submitError.value = null

  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(props.processNumber)}/evaluations/${props.acoaId}/review`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          final_score: selectedScore.value,
          is_override: isOverride.value,
          justification: isOverride.value ? justification.value.trim() : null,
        }),
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
