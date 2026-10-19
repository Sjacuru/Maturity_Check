<template>
  <v-container class="py-6" max-width="1100">
    <div class="d-flex align-center mb-4">
      <v-btn variant="text" icon="mdi-arrow-left" @click="router.push('/')" />
      <span class="text-h6 ml-2">Avaliação — {{ processNumber }}</span>
    </div>

    <MaturityIndicator
      v-if="!loading && evaluations.length"
      :process-number="processNumber"
      :refresh-key="reviewsLanded"
    />

    <!-- ADR-0078: the auditor's gate overrides enter the score only when the
         Ação is re-evaluated, from the documents already indexed. -->
    <v-card v-if="!loading && evaluations.length" variant="outlined" class="mb-4">
      <v-card-text>
        <div class="text-subtitle-2 mb-1">Reavaliação</div>
        <div v-if="pendingAcoes.length" class="text-body-2 mb-3">
          {{ pendingOverrides.length }} override(s) do gate ainda fora do score:
          Ação(ões) {{ pendingAcoes.join(', ') }}. Reavalie para que entrem na avaliação.
        </div>
        <div v-else class="text-body-2 text-medium-emphasis mb-3">
          Nenhum override do gate pendente. Marque trechos nas Ações e reavalie ao final.
        </div>
        <div class="d-flex flex-wrap" style="gap: 8px;">
          <v-btn
            color="primary"
            :disabled="!pendingAcoes.length || reevaluating"
            :loading="reevaluating && reevalMode === 'pending'"
            @click="reevaluate(pendingAcoes, 'pending')"
          >
            Reavaliar Ações com override pendente
          </v-btn>
          <v-btn
            variant="outlined"
            color="warning"
            :disabled="reevaluating"
            :loading="reevaluating && reevalMode === 'all'"
            @click="reevaluate(evaluations.map((e) => e.acao_id), 'all')"
          >
            Reavaliar todas as Ações
          </v-btn>
        </div>
        <v-list v-if="reevaluating && reevalEvents.length" density="compact" class="mt-2">
          <v-list-item v-for="ev in reevalEvents.slice(-5)" :key="ev.seq" class="py-0">
            <v-list-item-title class="text-caption" style="white-space: normal;">
              {{ ev.message }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
        <v-alert
          v-if="reevalMessage"
          :type="reevalError ? 'error' : 'success'"
          variant="tonal"
          density="compact"
          class="mt-3"
          style="white-space: pre-line;"
        >
          {{ reevalMessage }}
        </v-alert>
      </v-card-text>
    </v-card>

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
        :key="`${ev.acao_id}-${reloads}`"
        :evaluation="ev"
        :process-number="processNumber"
        :pending-override="pendingAcoes.includes(ev.acao_id)"
        @reviewed="reviewsLanded++"
        @overridden="loadPending"
      />
    </v-expansion-panels>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AcaoPanel from '../components/AcaoPanel.vue'
import MaturityIndicator from '../components/MaturityIndicator.vue'

const route = useRoute()
const router = useRouter()
const processNumber = route.params.processNumber

const loading = ref(true)
const fetchError = ref(null)
const evaluations = ref([])
const routeEvents = ref([])
// Bumped on every submitted review, so the indicator refetches (ADR-0075).
const reviewsLanded = ref(0)

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

const caseUrl = `/api/cases/${encodeURIComponent(processNumber)}`

async function loadEvaluations() {
  const resp = await fetch(`${caseUrl}/evaluations`)
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  const rows = await resp.json()
  evaluations.value = rows.sort((a, b) => a.acao_id - b.acao_id)
}

// ── Re-evaluation (ADR-0078) ─────────────────────────────────────────────────
const pendingOverrides = ref([])
const pendingAcoes = computed(() => [...new Set(pendingOverrides.value.map((o) => o.acao_id))])
const reevaluating = ref(false)
const reevalMode = ref(null)
const reevalEvents = ref([])
const reevalMessage = ref('')
const reevalError = ref(false)
// Bumped after a re-evaluation so every panel remounts and reloads its review.
const reloads = ref(0)

async function loadPending() {
  try {
    const resp = await fetch(`${caseUrl}/reevaluation/pending`)
    if (resp.ok) pendingOverrides.value = (await resp.json()).overrides
  } catch {
    // The list is a convenience; the buttons still work without it.
  }
}

function postReevaluation(acaoIds, deleteReviews) {
  return fetch(`${caseUrl}/reevaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ acao_ids: acaoIds, delete_reviews: deleteReviews }),
  })
}

function describeReport(report) {
  const line = (c) =>
    `Ação ${c.acao_id}: ${c.before} → ${c.after}${c.review_deleted ? ' (revisão apagada)' : ''}`
  const parts = []
  if (report.reevaluated?.length) parts.push('Reavaliadas:\n' + report.reevaluated.map(line).join('\n'))
  if (report.dependents?.length) {
    parts.push('Dependentes recalculadas (teto por dependência):\n' + report.dependents.map(line).join('\n'))
  }
  if (report.failed?.length) parts.push(`Falharam (avaliação e revisão mantidas): ${report.failed.join(', ')}`)
  if (report.not_reached?.length) parts.push(`Não reavaliadas: ${report.not_reached.join(', ')}`)
  if (report.interrupted) parts.unshift(report.interrupted)
  return parts.join('\n\n') || 'Nada mudou.'
}

async function reevaluate(acaoIds, mode) {
  if (!acaoIds.length) return
  if (
    mode === 'all' &&
    !window.confirm(
      `Reavaliar as ${acaoIds.length} Ações deste processo? Os documentos já indexados são ` +
        'reaproveitados e o gate repete os vereditos gravados, com os overrides do auditor; ' +
        'o avaliador roda de novo e pode dar outro score. As revisões das Ações reavaliadas ' +
        'serão apagadas.'
    )
  ) {
    return
  }
  reevaluating.value = true
  reevalMode.value = mode
  reevalEvents.value = []
  reevalMessage.value = ''
  reevalError.value = false
  let since = 0
  const timer = setInterval(async () => {
    try {
      const r = await fetch(`${caseUrl}/assess/progress?since=${since}`)
      if (!r.ok) return
      const body = await r.json()
      reevalEvents.value.push(...body.events)
      since = body.next_since
    } catch {
      // Progress is a convenience; the request itself reports the outcome.
    }
  }, 1500)
  try {
    let resp = await postReevaluation(acaoIds, false)
    if (resp.status === 409) {
      const detail = (await resp.json()).detail ?? {}
      const targets = detail.reviewed_targets ?? []
      const dependents = detail.reviewed_dependents ?? []
      let text = ''
      if (targets.length) {
        text += `As revisões das Ações ${targets.join(', ')} serão apagadas: ` +
          'referem-se a uma avaliação que deixará de existir.'
      }
      if (dependents.length) {
        text += `${text ? '\n\n' : ''}As revisões das Ações dependentes ${dependents.join(', ')} ` +
          'serão apagadas se o score delas mudar com o recálculo do teto.'
      }
      if (!window.confirm(`${text}\n\nContinuar?`)) {
        reevalMessage.value = 'Reavaliação cancelada; nada foi alterado.'
        return
      }
      resp = await postReevaluation(acaoIds, true)
    }
    const data = await resp.json().catch(() => ({}))
    if (!resp.ok) {
      reevalError.value = true
      reevalMessage.value =
        typeof data.detail === 'object' && data.detail
          ? describeReport(data.detail)
          : `Não foi possível reavaliar: ${data.detail || `HTTP ${resp.status}`}`
    } else {
      reevalMessage.value = describeReport(data)
    }
    // A partial run (server lost midway) also changed stored evaluations.
    if (resp.ok || resp.status === 503) {
      await loadEvaluations()
      reloads.value++
      reviewsLanded.value++
    }
  } catch (e) {
    reevalError.value = true
    reevalMessage.value = `Não foi possível reavaliar: ${e.message}`
  } finally {
    clearInterval(timer)
    reevaluating.value = false
    reevalMode.value = null
    await loadPending()
  }
}

onMounted(async () => {
  try {
    await loadEvaluations()
  } catch (e) {
    fetchError.value = e.message
  } finally {
    loading.value = false
  }
  await loadPending()

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
