<template>
  <v-container class="py-8" max-width="700">
    <v-card>
      <v-card-title class="text-h5 pa-4">PPP Maturity Check</v-card-title>
      <v-card-text>
        <v-text-field
          v-model="processNumber"
          label="Número do Processo"
          placeholder="0023.001234/2024-01"
          :disabled="loading"
          class="mb-2"
        />
        <v-file-input
          v-model="files"
          label="Documentos (PDF)"
          accept="application/pdf"
          multiple
          :disabled="loading"
          class="mb-2"
        />
        <v-alert
          v-if="error"
          type="error"
          class="mb-4"
          closable
          @click:close="error = null"
        >{{ error }}</v-alert>
      </v-card-text>
      <v-card-actions class="pa-4 pt-0">
        <v-btn
          color="primary"
          :disabled="!canSubmit"
          :loading="loading"
          @click="runAssessment"
        >
          Executar Avaliação
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Live progress panel -->
    <v-card v-if="loading || events.length" class="mt-4">
      <v-card-title class="pa-4 d-flex align-center" style="gap: 10px;">
        <v-progress-circular
          v-if="loading"
          indeterminate
          size="20"
          width="2"
          :color="statusColor"
        />
        <v-icon v-else :color="statusColor">{{ levelIcon(lastEvent?.level) }}</v-icon>
        <span class="text-subtitle-1" style="line-height: 1.3;">{{ statusHeadline }}</span>
        <v-spacer />
        <span
          v-if="loading && secondsSinceUpdate > 0"
          class="text-caption"
          :class="secondsSinceUpdate > 45 ? 'text-warning' : 'text-medium-emphasis'"
        >
          {{ secondsSinceUpdate }}s sem atualização
        </span>
      </v-card-title>

      <v-alert
        v-if="fallbackActive"
        type="warning"
        variant="tonal"
        density="compact"
        class="mx-4 mb-3"
      >
        <v-icon start size="small">mdi-server-network-off</v-icon>
        <strong>Usando LLM local (fallback)</strong> — {{ lastFallbackReason }}
      </v-alert>

      <v-list density="compact" class="px-2 pb-3" style="max-height: 320px; overflow-y: auto;">
        <v-list-item v-for="ev in reversedEvents" :key="ev.seq" class="py-1">
          <template #prepend>
            <v-icon size="16" :color="levelColor(ev.level)" class="mr-1">
              {{ levelIcon(ev.level) }}
            </v-icon>
          </template>
          <v-list-item-title class="text-body-2" style="white-space: normal;">
            {{ ev.message }}
          </v-list-item-title>
        </v-list-item>
        <v-list-item v-if="!events.length" class="py-1">
          <v-list-item-title class="text-body-2 text-medium-emphasis">
            Preparando execução...
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-card>

    <v-card v-if="documents.length" class="mt-4">
      <v-card-title class="text-subtitle-1 pa-4">Documentos processados</v-card-title>
      <v-list density="compact">
        <v-list-item
          v-for="doc in documents"
          :key="doc.filename"
          :title="doc.filename"
        >
          <template #append>
            <v-chip :color="dispositionColor(doc.disposition)" size="small" label>
              {{ doc.disposition }}
            </v-chip>
          </template>
        </v-list-item>
      </v-list>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const processNumber = ref('')
const files = ref([])
const loading = ref(false)
const error = ref(null)
const documents = ref([])

// ── Live progress (ADR-0055) ────────────────────────────────────────────
// Polls GET /assess/progress while the (still-synchronous) POST /assess is
// in flight, so a multi-minute wait (LLM retry/fallback cycles in
// particular) is never a silent blank screen.

const events = ref([])
const nextSince = ref(0)
const lastUpdateAt = ref(null)
const nowTick = ref(Date.now())
let pollTimer = null
let tickTimer = null

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

const canSubmit = computed(
  () => processNumber.value.trim() && files.value.length > 0 && !loading.value
)

function dispositionColor(d) {
  return { new: 'success', reused: 'info', replaced: 'warning' }[d] ?? 'default'
}

const reversedEvents = computed(() => [...events.value].reverse())
const lastEvent = computed(() => events.value[events.value.length - 1] ?? null)

// True from a "fallback" event until the next "concluido"/"erro" — i.e. for
// the rest of the run, since ADR-0054's circuit breaker keeps using the
// fallback for a cooldown window rather than reverting call-by-call.
const fallbackActive = computed(() => {
  for (let i = events.value.length - 1; i >= 0; i--) {
    const ev = events.value[i]
    if (ev.stage === 'fallback') return true
    if (ev.stage === 'concluido' || ev.stage === 'erro') return false
  }
  return false
})

const lastFallbackReason = computed(() => {
  for (let i = events.value.length - 1; i >= 0; i--) {
    if (events.value[i].stage === 'fallback') return events.value[i].message
  }
  return ''
})

const statusColor = computed(() => levelColor(lastEvent.value?.level))

const statusHeadline = computed(() => {
  if (lastEvent.value) return lastEvent.value.message
  return loading.value ? 'Iniciando avaliação...' : 'Concluído.'
})

const secondsSinceUpdate = computed(() => {
  if (!lastUpdateAt.value) return 0
  return Math.max(0, Math.round((nowTick.value - lastUpdateAt.value) / 1000))
})

function resetProgress() {
  events.value = []
  nextSince.value = 0
  lastUpdateAt.value = Date.now()
}

async function pollProgress(pn) {
  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(pn)}/assess/progress?since=${nextSince.value}`
    )
    if (resp.ok) {
      const body = await resp.json()
      if (body.events.length) {
        events.value.push(...body.events)
        lastUpdateAt.value = Date.now()
      }
      nextSince.value = body.next_since
    }
  } catch {
    // Transient polling hiccup — retried on the next tick, not surfaced as
    // a user-facing error (the assessment itself is unaffected).
  }
}

function startPolling(pn) {
  stopPolling()
  pollTimer = setInterval(() => pollProgress(pn), 1500)
  tickTimer = setInterval(() => {
    nowTick.value = Date.now()
  }, 1000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (tickTimer) {
    clearInterval(tickTimer)
    tickTimer = null
  }
}

onUnmounted(stopPolling)

async function runAssessment() {
  error.value = null
  documents.value = []
  resetProgress()
  loading.value = true

  const pn = processNumber.value.trim()
  const form = new FormData()
  for (const file of files.value) {
    form.append('files', file)
  }

  startPolling(pn)

  try {
    const resp = await fetch(`/api/cases/${encodeURIComponent(pn)}/assess`, {
      method: 'POST',
      body: form,
    })
    await pollProgress(pn) // catch any trailing events emitted right before completion
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({ detail: resp.statusText }))
      throw new Error(detail.detail ?? `HTTP ${resp.status}`)
    }
    const body = await resp.json()
    documents.value = body.documents ?? []
    stopPolling()
    await router.push(`/cases/${encodeURIComponent(pn)}`)
  } catch (e) {
    await pollProgress(pn)
    stopPolling()
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
