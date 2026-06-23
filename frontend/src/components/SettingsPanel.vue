<template>
  <div>
    <div class="view-header">
      <h2>Settings</h2>
      <p>Configure application defaults</p>
    </div>

    <div class="scan-config">
      <div class="config-grid">
        <div class="form-group">
          <label>Ollama Host</label>
          <input v-model="settings.host" type="text" />
        </div>
        <div class="form-group">
          <label>Default Model</label>
          <div style="display: flex; gap: 8px;">
            <input v-model="settings.model" type="text" style="flex: 1;" />
            <button class="btn btn-secondary" @click="fetchModels" :disabled="fetchingModels" style="white-space: nowrap;">
              <i class="pi pi-refresh"></i>
              {{ fetchingModels ? 'Fetching...' : 'Fetch Models' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="ollamaModels.length > 0 || freeOnly" class="form-group" style="margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
          <label style="margin-bottom: 0;">Available Ollama Models</label>
          <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; text-transform: none; letter-spacing: 0; color: var(--text-secondary);">
            <input type="checkbox" v-model="freeOnly" @change="fetchModels" style="width: auto; accent-color: var(--accent);" />
            Free only
          </label>
        </div>
        <div class="model-list">
          <div
            v-for="model in ollamaModels"
            :key="model"
            class="model-chip"
            :class="{ active: settings.model === model }"
            @click="settings.model = model"
          >
            {{ model }}
          </div>
        </div>
      </div>

      <div v-if="ollamaError" style="color: var(--accent); font-size: 13px; margin-bottom: 12px;">
        <i class="pi pi-exclamation-triangle"></i> {{ ollamaError }}
      </div>

      <div class="config-grid">
        <div class="form-group">
          <label>Articles Directory</label>
          <input v-model="settings.articles_dir" type="text" />
        </div>
        <div class="form-group">
          <label>Database File</label>
          <input v-model="settings.database" type="text" />
        </div>
        <div class="form-group">
          <label>Server Port</label>
          <input v-model.number="settings.server_port" type="number" />
        </div>
        <div class="form-group">
          <label>Web Search Provider</label>
          <select v-model="settings.web_search_provider">
            <option value="ddgs">DuckDuckGo (free, no key)</option>
            <option value="tavily">Tavily (better results, no key)</option>
            <option value="auto">Auto (Tavily first, DDGS fallback)</option>
          </select>
        </div>
      </div>

      <div class="config-section-title">Knowledge Graph (graphify)</div>
      <div class="config-grid">
        <div class="form-group">
          <label>Graphify Backend</label>
          <select v-model="settings.graphify_backend">
            <option value="ollama">Ollama (local, free)</option>
            <option value="gemini">Gemini (free tier 20/day)</option>
            <option value="openrouter">OpenRouter / NVIDIA</option>
            <option value="openai">OpenAI</option>
          </select>
        </div>
        <div class="form-group">
          <label>Graphify Model (optional)</label>
          <input v-model="settings.graphify_model" type="text" placeholder="empty = backend default" />
        </div>
      </div>
      <div v-if="settings.graphify_backend !== 'ollama'" class="config-grid">
        <div class="form-group">
          <label>API Key</label>
          <input v-model="settings.graphify_api_key" type="password" placeholder="required for non-Ollama backends" />
        </div>
        <div v-if="settings.graphify_backend === 'openrouter' || settings.graphify_backend === 'openai'" class="form-group">
          <label>Base URL (optional)</label>
          <input v-model="settings.graphify_base_url" type="text" :placeholder="settings.graphify_backend === 'openrouter' ? 'https://openrouter.ai/api/v1' : 'https://api.openai.com/v1'" />
        </div>
      </div>
      <div class="config-grid">
        <div class="form-group">
          <label>Max Output Tokens</label>
          <input v-model.number="settings.graphify_max_output_tokens" type="number" />
        </div>
        <div class="form-group">
          <label>Max Concurrency</label>
          <input v-model.number="settings.graphify_max_concurrency" type="number" min="1" max="8" />
        </div>
      </div>

      <button class="btn btn-primary" @click="save" :disabled="saving">
        <i class="pi pi-save"></i>
        {{ saving ? 'Saving...' : 'Save Settings' }}
      </button>

      <div v-if="saved" style="margin-left: 12px; color: #27ae60; font-size: 13px; display: flex; align-items: center; gap: 6px;">
        <i class="pi pi-check"></i> Saved
      </div>
    </div>

    <div class="scan-config" style="border-color: rgba(233,69,96,0.3); margin-top: 24px;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <div style="font-weight: 600; margin-bottom: 4px;">Shutdown Application</div>
          <div style="font-size: 13px; color: var(--text-secondary);">Stops the server and closes the app</div>
        </div>
        <button class="btn btn-danger" @click="stopApp" :disabled="stopping">
          <i class="pi pi-power-off"></i>
          {{ stopping ? 'Stopping...' : 'Stop App' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings, shutdownApp, getOllamaModels } from '../composables/useApi.js'

const settings = ref({
  host: 'http://localhost:11434',
  model: 'llama3',
  articles_dir: '.\\articles\\',
  database: 'articles_db.json',
  server_port: 8000,
  web_search_provider: 'ddgs',
  graphify_backend: 'ollama',
  graphify_model: '',
  graphify_api_key: '',
  graphify_base_url: '',
  graphify_max_output_tokens: 8192,
  graphify_max_concurrency: 1,
})

const saving = ref(false)
const saved = ref(false)
const stopping = ref(false)
const ollamaModels = ref([])
const ollamaError = ref('')
const fetchingModels = ref(false)
const freeOnly = ref(true)

onMounted(async () => {
  try {
    settings.value = await getSettings()
  } catch (e) { /* use defaults */ }
})

async function fetchModels() {
  fetchingModels.value = true
  ollamaError.value = ''
  ollamaModels.value = []
  try {
    const result = await getOllamaModels(freeOnly.value)
    if (result.error) {
      ollamaError.value = 'Could not reach Ollama: ' + result.error
    } else {
      ollamaModels.value = result.models
    }
  } catch (e) {
    ollamaError.value = 'Could not reach Ollama: ' + e.message
  } finally {
    fetchingModels.value = false
  }
}

async function save() {
  saving.value = true
  saved.value = false
  try {
    await updateSettings(settings.value)
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } catch (e) {
    alert('Failed to save: ' + e.message)
  } finally {
    saving.value = false
  }
}

async function stopApp() {
  if (!confirm('Stop the application?')) return
  stopping.value = true
  try {
    await shutdownApp()
  } catch (e) {
    window.close()
  }
}
</script>
