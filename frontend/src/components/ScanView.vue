<template>
  <div>
    <div class="view-header">
      <h2>Scan &amp; Extract</h2>
      <p>Scan article files and extract metadata using Ollama LLM</p>
    </div>

    <div class="scan-config">
      <div v-if="tagsWarning" class="alert-banner" style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; font-size: 13px;">
        <i class="pi pi-exclamation-triangle" style="color: #f59e0b; font-size: 16px;"></i>
        <div>
          <strong>Tags configuration changed.</strong>
          A full rescan is recommended to update article tags with the new categories.
        </div>
      </div>
      <div class="config-grid">
        <div class="form-group">
          <label>Ollama Host</label>
          <input v-model="config.host" type="text" placeholder="http://localhost:11434" />
        </div>
        <div class="form-group">
          <label>Model</label>
          <input v-model="config.model" type="text" placeholder="llama3" />
        </div>
        <div class="form-group">
          <label>Articles Directory</label>
          <input v-model="config.articles_dir" type="text" placeholder=".\articles\" />
        </div>
        <div class="form-group">
          <label>Database File</label>
          <input v-model="config.database" type="text" placeholder="articles_db.json" />
        </div>
      </div>

      <button class="btn btn-primary" :disabled="scanning" @click="doScan">
        <i class="pi pi-play"></i>
        {{ scanning ? 'Scanning...' : 'Start Scan' }}
      </button>
    </div>

    <div v-if="scanStatus" class="scan-status">
      <div class="status-row">
        <div class="status-dot" :class="{ running: scanStatus.running }"></div>
        <span>{{ scanStatus.message || 'Idle' }}</span>
      </div>

      <div v-if="scanStatus.total > 0" class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: ((scanStatus.processed / scanStatus.total) * 100) + '%' }"
        ></div>
      </div>

      <div v-if="scanStatus.total > 0" class="stats-bar">
        <span>Progress: <span class="count">{{ scanStatus.processed }} / {{ scanStatus.total }}</span></span>
        <span v-if="scanStatus.current_file">Current: <span class="count">{{ scanStatus.current_file }}</span></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getSettings, startScan, getScanStatus, getTagsChanged } from '../composables/useApi.js'

const config = ref({
  host: 'http://localhost:11434',
  model: 'llama3',
  articles_dir: '.\\articles\\',
  database: 'articles_db.json',
})

const scanning = ref(false)
const scanStatus = ref(null)
const tagsWarning = ref(false)
let pollInterval = null

onMounted(async () => {
  try {
    const settings = await getSettings()
    config.value = settings
  } catch (e) { /* use defaults */ }

  try {
    scanStatus.value = await getScanStatus()
    if (scanStatus.value.running) startPolling()
  } catch (e) { /* ignore */ }

  try {
    const tagsCheck = await getTagsChanged()
    tagsWarning.value = tagsCheck.changed || tagsCheck.never_scanned
  } catch (e) { /* ignore */ }
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

function startPolling() {
  scanning.value = true
  pollInterval = setInterval(async () => {
    try {
      scanStatus.value = await getScanStatus()
      if (!scanStatus.value.running) {
        clearInterval(pollInterval)
        pollInterval = null
        scanning.value = false
        tagsWarning.value = false
      }
    } catch (e) { /* ignore */ }
  }, 1000)
}

async function doScan() {
  if (scanning.value) return
  try {
    const result = await startScan(config.value)
    if (result.error) {
      alert(result.error)
      return
    }
    scanStatus.value = await getScanStatus()
    startPolling()
  } catch (e) {
    alert('Failed to start scan: ' + e.message)
  }
}
</script>
