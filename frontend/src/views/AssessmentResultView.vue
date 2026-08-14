<template>
  <v-container class="py-6" max-width="1100">
    <div class="d-flex align-center mb-4">
      <v-btn variant="text" icon="mdi-arrow-left" @click="router.push('/')" />
      <span class="text-h6 ml-2">Avaliação — {{ processNumber }}</span>
    </div>

    <v-progress-circular
      v-if="loading"
      indeterminate
      color="primary"
      class="d-block mx-auto my-8"
    />
    <v-alert v-else-if="fetchError" type="error">{{ fetchError }}</v-alert>
    <v-alert v-else-if="!evaluations.length" type="info">
      Nenhuma avaliação encontrada para este processo.
    </v-alert>

    <v-expansion-panels v-else multiple>
      <v-expansion-panel v-if="routeEvents.length">
        <v-expansion-panel-title>
          <div class="d-flex align-center" style="gap: 8px;">
            <v-icon size="small">mdi-routes</v-icon>
            <span class="font-weight-bold">Rota de execução</span>
            <span class="text-caption text-medium-emphasis">
              ({{ routeEvents.length }} evento(s))
            </span>
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-list density="compact">
            <v-list-item v-for="ev in routeEvents" :key="ev.seq" class="py-1">
              <template #prepend>
                <v-icon size="16" :color="levelColor(ev.level)" class="mr-1">
                  {{ levelIcon(ev.level) }}
                </v-icon>
              </template>
              <v-list-item-title class="text-body-2" style="white-space: normal;">
                {{ ev.message }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-expansion-panel-text>
      </v-expansion-panel>

      <AcaoPanel
        v-for="ev in evaluations"
        :key="ev.acao_id"
        :evaluation="ev"
        :process-number="processNumber"
      />
    </v-expansion-panels>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AcaoPanel from '../components/AcaoPanel.vue'

const route = useRoute()
const router = useRouter()
const processNumber = route.params.processNumber

const loading = ref(true)
const fetchError = ref(null)
const evaluations = ref([])
const routeEvents = ref([])

// Same event log the live progress panel (UploadView) polled during the run
// (ADR-0055) — the backend keeps it in memory until the next assessment for
// this process_number starts, so it's fetched once here as a static recap.
const LEVEL_META = {
  info: { color: 'primary', icon: 'mdi-information-outline' },
  waiting: { color: 'warning', icon: 'mdi-timer-sand' },
  warning: { color: 'warning', icon: 'mdi-alert' },
  error: { color: 'error', icon: 'mdi-close-circle' },
  success: { color: 'success', icon: 'mdi-check-circle' },
}
function levelColor(level) {
  return LEVEL_META[level]?.color ?? 'primary'
}
function levelIcon(level) {
  return LEVEL_META[level]?.icon ?? 'mdi-circle-small'
}

onMounted(async () => {
  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(processNumber)}/evaluations`
    )
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    evaluations.value = await resp.json()
  } catch (e) {
    fetchError.value = e.message
  } finally {
    loading.value = false
  }

  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(processNumber)}/assess/progress?since=0`
    )
    if (resp.ok) {
      const body = await resp.json()
      routeEvents.value = body.events
    }
  } catch {
    // Recap is a convenience, not load-bearing — the evaluation results
    // above already fetched successfully regardless of this outcome.
  }
})
</script>
