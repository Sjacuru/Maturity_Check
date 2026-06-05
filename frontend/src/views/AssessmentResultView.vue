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
})
</script>
