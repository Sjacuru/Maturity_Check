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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const processNumber = ref('')
const files = ref([])
const loading = ref(false)
const error = ref(null)
const documents = ref([])

const canSubmit = computed(
  () => processNumber.value.trim() && files.value.length > 0 && !loading.value
)

function dispositionColor(d) {
  return { new: 'success', reused: 'info', replaced: 'warning' }[d] ?? 'default'
}

async function runAssessment() {
  error.value = null
  documents.value = []
  loading.value = true

  const form = new FormData()
  for (const file of files.value) {
    form.append('files', file)
  }

  try {
    const resp = await fetch(
      `/api/cases/${encodeURIComponent(processNumber.value.trim())}/assess`,
      { method: 'POST', body: form }
    )
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({ detail: resp.statusText }))
      throw new Error(detail.detail ?? `HTTP ${resp.status}`)
    }
    const body = await resp.json()
    documents.value = body.documents ?? []
    await router.push(`/cases/${encodeURIComponent(processNumber.value.trim())}`)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
