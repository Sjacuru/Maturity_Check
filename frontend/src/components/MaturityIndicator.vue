<template>
  <v-card variant="outlined" class="mb-4">
    <v-card-text>
      <v-progress-linear v-if="loading && !indicator" indeterminate color="primary" />
      <v-alert v-else-if="fetchError" type="error" density="compact">
        Indicador de maturidade indisponível: {{ fetchError }}
      </v-alert>
      <template v-else-if="indicator">
        <div class="d-flex align-start flex-wrap" style="gap: 24px;">
          <div>
            <div class="text-caption text-medium-emphasis">Nota iPMP</div>
            <div class="text-h3 font-weight-bold" style="line-height: 1;">
              {{ formatNota(overall.nota) }}
            </div>
          </div>
          <div class="text-body-2" style="flex: 1; min-width: 240px;">
            <div>
              {{ overall.points }} de {{ overall.max_points }} pontos ·
              {{ overall.n_counted }} de {{ overall.acao_ids.length }} Ações contadas
              <v-chip v-if="!overall.complete" size="x-small" color="warning" label class="ml-1">
                parcial
              </v-chip>
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ counts.atendidas }} atendida(s) · {{ counts.parciais }} parcialmente ·
              {{ counts.naoAtendidas }} não atendida(s), {{ counts.semEvidencia }} delas sem evidência
              <span v-if="counts.naoContadas">· {{ counts.naoContadas }} sem score, fora da conta</span>
            </div>
            <div class="text-caption text-medium-emphasis">
              Revisadas pelo auditor: {{ indicator.n_reviewed }} de {{ indicator.acoes.length }}
            </div>
          </div>
        </div>

        <!-- The overall nota against the Guide's two reference limits (3.4.3). -->
        <div class="mt-4" style="position: relative;">
          <v-progress-linear
            :model-value="percent(overall.nota)"
            :color="band.color"
            height="12"
            rounded
          />
          <div
            v-for="lim in limits"
            :key="lim"
            class="limit-mark"
            :style="{ left: `${lim * 100}%` }"
          />
        </div>
        <div style="position: relative; height: 18px;">
          <span
            v-for="lim in limits"
            :key="lim"
            class="text-caption limit-label"
            :style="{ left: `${lim * 100}%` }"
          >{{ formatLimit(lim) }}</span>
        </div>
        <div class="text-caption">{{ band.text }}</div>

        <!-- ADR-0068: the nota if every fragile product fell at once. -->
        <div v-if="openReviews.length" class="text-caption mt-1">
          Piso {{ formatNota(overall.nota_floor) }} ({{ overall.floor_points }} pontos) se caírem
          os produtos frágeis das Ações com revisão sugerida:
          {{ openReviews.map((a) => `Ação ${a.acao_id} (${a.points} → ${a.floor_points})`).join(', ') }}.
        </div>

        <v-row class="mt-3" dense>
          <v-col v-for="section in sections" :key="section.title" cols="12" md="6">
            <div class="text-subtitle-2 mb-1">{{ section.title }}</div>
            <div v-for="g in section.groups" :key="g.label" class="mb-2">
              <div class="d-flex text-body-2" style="gap: 8px;">
                <span>{{ g.title }}</span>
                <v-spacer />
                <span class="text-no-wrap">{{ g.points }}/{{ g.max_points }} · {{ formatNota(g.nota) }}</span>
              </div>
              <v-progress-linear :model-value="percent(g.nota)" color="secondary" height="6" rounded />
              <div v-if="!g.complete" class="text-caption text-warning">
                {{ g.n_counted }} de {{ g.acao_ids.length }} Ações contadas
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- The approval gates of the M5D flowcharts (Figuras 3-5). -->
        <div class="text-subtitle-2 mt-2 mb-1">Pontos de transição</div>
        <div class="d-flex flex-wrap" style="gap: 6px;">
          <v-chip
            v-for="a in transitionAcoes"
            :key="a.acao_id"
            size="small"
            :color="scoreColor(a.points)"
            label
          >
            Ação {{ a.acao_id }}: {{ a.points ?? '—' }}
            <v-tooltip activator="parent" location="top">{{ a.titulo }}</v-tooltip>
          </v-chip>
        </div>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  processNumber: String,
  // Bumped by the parent on every submitted review, so the nota follows it.
  refreshKey: Number,
})

const indicator = ref(null)
const loading = ref(true)
const fetchError = ref(null)

async function load() {
  loading.value = true
  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(props.processNumber)}/maturity`
    )
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}))
      throw new Error(body.detail ?? `HTTP ${resp.status}`)
    }
    indicator.value = await resp.json()
    fetchError.value = null
  } catch (e) {
    fetchError.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.refreshKey, load)

const overall = computed(() => indicator.value.overall)
const limits = computed(() => [indicator.value.alert_below, indicator.value.satisfactory_above])

const counts = computed(() => {
  const acoes = indicator.value?.acoes ?? []
  return {
    atendidas: acoes.filter((a) => a.points === 3).length,
    parciais: acoes.filter((a) => a.points === 1).length,
    naoAtendidas: acoes.filter((a) => a.points === 0).length,
    semEvidencia: acoes.filter((a) => a.source === 'no_evidence').length,
    naoContadas: acoes.filter((a) => a.points === null).length,
  }
})

// The Guide reads only the two ends (3.4.3 and 3.4.4); the middle has no
// cut-off yet, so it gets no verdict here either.
const BANDS = {
  alert: {
    color: 'error',
    text:
      'Abaixo de 0,2: o Guia lê como alerta de fragilidades no planejamento, que pede ' +
      'revisitar as causas; não é juízo de insucesso (3.4.3).',
  },
  intermediate: {
    color: 'primary',
    text:
      'Entre 0,2 e 0,8: o Guia ainda não tem notas de corte para esta faixa (3.4.3); ' +
      'a leitura vem das Ações não atendidas e das dimensões mais baixas.',
  },
  satisfactory: {
    color: 'success',
    text: 'Acima de 0,8: o Guia lê como satisfatória, sem ser atestado de excelência (3.4.4).',
  },
}
const band = computed(() => BANDS[indicator.value.band] ?? { color: 'default', text: '' })

const openReviews = computed(() =>
  indicator.value.acoes
    .filter((a) => a.review_recommended && a.floor_points < a.points)
    .sort((x, y) => y.points - y.floor_points - (x.points - x.floor_points) || x.acao_id - y.acao_id)
)

function withRange(g) {
  const ids = g.acao_ids
  return { ...g, title: `${g.label} (Ações ${Math.min(...ids)}–${Math.max(...ids)})` }
}

const sections = computed(() => [
  {
    title: 'Por dimensão',
    groups: indicator.value.by_dimension.map((g) => ({ ...g, title: g.label })),
  },
  { title: 'Por fase', groups: indicator.value.by_phase.map(withRange) },
])

const transitionAcoes = computed(() =>
  indicator.value.acoes.filter((a) => indicator.value.transition_points.acao_ids.includes(a.acao_id))
)

function formatNota(n) {
  return n === null || n === undefined
    ? '—'
    : n.toLocaleString('pt-BR', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function formatLimit(n) {
  return n.toLocaleString('pt-BR', { minimumFractionDigits: 1 })
}

function percent(n) {
  return n === null || n === undefined ? 0 : n * 100
}

function scoreColor(s) {
  return { 0: 'error', 1: 'warning', 3: 'success' }[s] ?? 'default'
}
</script>

<style scoped>
.limit-mark {
  position: absolute;
  top: -3px;
  width: 2px;
  height: 18px;
  background: rgba(0, 0, 0, 0.55);
  transform: translateX(-1px);
}
.limit-label {
  position: absolute;
  transform: translateX(-50%);
}
</style>
