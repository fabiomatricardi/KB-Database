<template>
  <div class="graph-view">
    <div class="view-header">
      <h2>Knowledge Graph</h2>
      <p>Build and explore a knowledge graph from your articles</p>
    </div>

    <div class="graph-config-card">
      <div class="config-header">
        <i class="pi pi-cog"></i>
        <span>Graphify Configuration</span>
      </div>
      <div class="config-flags">
        <div class="config-flag">
          <span class="flag-label">Backend</span>
          <span class="flag-value" :class="'backend-' + graphifyBackend">{{ backendLabel }}</span>
        </div>
        <div class="config-flag">
          <span class="flag-label">Model</span>
          <span class="flag-value">{{ graphifyModel || '(backend default)' }}</span>
        </div>
        <div class="config-flag">
          <span class="flag-label">Max Tokens</span>
          <span class="flag-value">{{ graphifyMaxTokens }}</span>
        </div>
        <div class="config-flag">
          <span class="flag-label">Concurrency</span>
          <span class="flag-value">{{ graphifyConcurrency }}</span>
        </div>
        <div v-if="graphifyBackend !== 'ollama'" class="config-flag">
          <span class="flag-label">API Key</span>
          <span class="flag-value">{{ graphifyApiKey ? '••••••••' : '(not set)' }}</span>
        </div>
        <div v-if="graphifyBaseUrl" class="config-flag">
          <span class="flag-label">Base URL</span>
          <span class="flag-value flag-url">{{ graphifyBaseUrl }}</span>
        </div>
      </div>
    </div>

    <div class="graph-build-bar">
      <div class="build-status-text" v-if="building">
        <div class="spinner" style="width: 16px; height: 16px;"></div>
        {{ buildMessage }} <span v-if="buildProgress > 0">({{ buildProgress }}%)</span>
      </div>
      <div class="build-status-text" v-else-if="buildMessage">{{ buildMessage }}</div>
      <div class="build-status-text" v-else>Ready to build</div>
      <button class="btn btn-primary" @click="startBuild" :disabled="building">
        <i class="pi pi-play"></i>
        {{ building ? 'Building...' : 'Build / Rebuild Knowledge Graph' }}
      </button>
    </div>

    <div v-if="graphHtml && !building" class="graph-container">
      <div class="graph-frame-wrapper">
        <iframe :srcdoc="graphHtml" class="graph-iframe"></iframe>
      </div>
    </div>

    <div v-if="building" class="graph-building">
      <div class="progress-bar-container" v-if="buildProgress > 0">
        <div class="progress-bar" :style="{ width: buildProgress + '%' }"></div>
      </div>
      <div class="build-stage">{{ buildStage }}</div>
    </div>

    <div v-if="graphHtml" class="graph-tools">
      <h3><i class="pi pi-comments"></i> Graph Tools</h3>

      <div class="graph-tabs">
        <button :class="['tab-btn', { active: activeTab === 'query' }]" @click="activeTab = 'query'">Query</button>
        <button :class="['tab-btn', { active: activeTab === 'explain' }]" @click="activeTab = 'explain'">Explain</button>
        <button :class="['tab-btn', { active: activeTab === 'path' }]" @click="activeTab = 'path'">Path</button>
      </div>

      <div v-if="activeTab === 'query'" class="graph-chat-bar">
        <input
          v-model="graphQuestion"
          type="text"
          placeholder="Ask a question about the knowledge graph..."
          @keyup.enter="askGraph"
        />
        <button class="btn btn-primary btn-sm" @click="askGraph" :disabled="!graphQuestion.trim() || querying">
          <i class="pi pi-send"></i>
        </button>
      </div>

      <div v-if="activeTab === 'explain'" class="graph-chat-bar">
        <input
          v-model="explainConcept"
          type="text"
          placeholder="Enter a concept to explain..."
          @keyup.enter="askExplain"
        />
        <button class="btn btn-primary btn-sm" @click="askExplain" :disabled="!explainConcept.trim() || querying">
          <i class="pi pi-info-circle"></i>
        </button>
      </div>

      <div v-if="activeTab === 'path'" class="graph-path-bar">
        <input v-model="pathStart" type="text" placeholder="Start concept" />
        <i class="pi pi-arrow-right" style="opacity: 0.5;"></i>
        <input v-model="pathEnd" type="text" placeholder="End concept" @keyup.enter="askPath" />
        <button class="btn btn-primary btn-sm" @click="askPath" :disabled="!pathStart.trim() || !pathEnd.trim() || querying">
          <i class="pi pi-directions"></i>
        </button>
      </div>

      <div v-if="querying" class="loading" style="padding: 12px;">
        <div class="spinner"></div> Querying graph...
      </div>
      <div v-if="graphAnswer" class="graph-answer">
        <div class="field-label">Answer</div>
        <div class="field-value" style="white-space: pre-wrap;">{{ graphAnswer }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { buildGraph, getGraphStatus, getGraphHtml, graphQuery, graphExplain, graphPathTo, getSettings } from '../composables/useApi.js'

const graphHtml = ref(null)
const building = ref(false)
const buildMessage = ref('')
const buildStage = ref('')
const buildProgress = ref(0)
const activeTab = ref('query')
const graphQuestion = ref('')
const explainConcept = ref('')
const pathStart = ref('')
const pathEnd = ref('')
const querying = ref(false)
const graphAnswer = ref('')
const graphifyBackend = ref('ollama')
const graphifyModel = ref('')
const graphifyApiKey = ref('')
const graphifyBaseUrl = ref('')
const graphifyMaxTokens = ref(8192)
const graphifyConcurrency = ref(1)
let pollInterval = null

const backendLabels = { ollama: 'Ollama', gemini: 'Gemini', openrouter: 'OpenRouter', openai: 'OpenAI' }
const backendLabel = computed(() => backendLabels[graphifyBackend.value] || 'Ollama')

onMounted(async () => {
  try {
    const s = await getSettings()
    graphifyBackend.value = s.graphify_backend || 'ollama'
    graphifyModel.value = s.graphify_model || ''
    graphifyApiKey.value = s.graphify_api_key || ''
    graphifyBaseUrl.value = s.graphify_base_url || ''
    graphifyMaxTokens.value = s.graphify_max_output_tokens || 8192
    graphifyConcurrency.value = s.graphify_max_concurrency || 1
  } catch (e) { /* use defaults */ }
  await checkGraph()
  await pollStatus()
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

async function checkGraph() {
  try {
    const result = await getGraphHtml()
    if (result.available) {
      graphHtml.value = result.html
    } else {
      graphHtml.value = null
    }
  } catch (e) { /* ignore */ }
}

async function pollStatus() {
  try {
    const status = await getGraphStatus()
    if (status.running) {
      building.value = true
      buildMessage.value = status.message
      buildStage.value = status.stage
      buildProgress.value = status.progress
    }
  } catch (e) { /* ignore */ }
}

async function startBuild() {
  building.value = true
  buildMessage.value = 'Starting graph build...'
  buildProgress.value = 5
  try {
    await buildGraph()
    pollInterval = setInterval(async () => {
      const status = await getGraphStatus()
      buildMessage.value = status.message
      buildStage.value = status.stage
      buildProgress.value = status.progress
      if (!status.running) {
        clearInterval(pollInterval)
        pollInterval = null
        building.value = false
        await checkGraph()
      }
    }, 2000)
  } catch (e) {
    buildMessage.value = 'Failed to start: ' + e.message
    building.value = false
  }
}

async function askGraph() {
  if (!graphQuestion.value.trim()) return
  querying.value = true
  graphAnswer.value = ''
  try {
    const result = await graphQuery(graphQuestion.value)
    graphAnswer.value = result.answer
  } catch (e) {
    graphAnswer.value = 'Error: ' + e.message
  } finally {
    querying.value = false
  }
}

async function askExplain() {
  if (!explainConcept.value.trim()) return
  querying.value = true
  graphAnswer.value = ''
  try {
    const result = await graphExplain(explainConcept.value)
    graphAnswer.value = result.answer
  } catch (e) {
    graphAnswer.value = 'Error: ' + e.message
  } finally {
    querying.value = false
  }
}

async function askPath() {
  if (!pathStart.value.trim() || !pathEnd.value.trim()) return
  querying.value = true
  graphAnswer.value = ''
  try {
    const result = await graphPathTo(pathStart.value, pathEnd.value)
    graphAnswer.value = result.answer
  } catch (e) {
    graphAnswer.value = 'Error: ' + e.message
  } finally {
    querying.value = false
  }
}
</script>
