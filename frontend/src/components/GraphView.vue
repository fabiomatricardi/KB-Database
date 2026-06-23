<template>
  <div class="graph-view">
    <div class="view-header">
      <h2>Knowledge Graph</h2>
      <p>Build and explore a knowledge graph from your articles</p>
    </div>

    <div v-if="graphHtml" class="graph-container">
      <div class="graph-frame-wrapper">
        <iframe :srcdoc="graphHtml" class="graph-iframe"></iframe>
      </div>
    </div>

    <div v-else-if="building" class="graph-building">
      <div class="loading">
        <div class="spinner"></div>
        {{ buildMessage }}
      </div>
      <div class="progress-bar-container" v-if="buildProgress > 0">
        <div class="progress-bar" :style="{ width: buildProgress + '%' }"></div>
      </div>
      <div class="build-stage">{{ buildStage }}</div>
    </div>

    <div v-else class="graph-empty">
      <i class="pi pi-chart" style="font-size: 48px; opacity: 0.3; margin-bottom: 16px; display: block;"></i>
      <p style="margin-bottom: 20px; color: var(--text-secondary);">
        Build a knowledge graph from your articles using Ollama for entity extraction.
      </p>
      <button class="btn btn-primary" @click="startBuild" :disabled="building">
        <i class="pi pi-play"></i> Build Knowledge Graph
      </button>
      <p v-if="buildMessage && !building" style="margin-top: 12px; color: var(--text-secondary); font-size: 13px;">
        {{ buildMessage }}
      </p>
    </div>

    <div v-if="graphHtml" class="graph-chat">
      <h3><i class="pi pi-comments"></i> Graph Chat</h3>
      <div class="graph-chat-bar">
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
import { ref, onMounted, onUnmounted } from 'vue'
import { buildGraph, getGraphStatus, getGraphHtml, graphQuery } from '../composables/useApi.js'

const graphHtml = ref(null)
const building = ref(false)
const buildMessage = ref('')
const buildStage = ref('')
const buildProgress = ref(0)
const graphQuestion = ref('')
const querying = ref(false)
const graphAnswer = ref('')
let pollInterval = null

onMounted(async () => {
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
</script>
