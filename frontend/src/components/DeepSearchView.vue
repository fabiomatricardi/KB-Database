<template>
  <div>
    <div class="view-header">
      <h2>Deep Search</h2>
      <p>Full-text BM25 search across all files in a directory</p>
    </div>

    <div class="search-bar">
      <input
        v-model="query"
        type="text"
        placeholder="Deep search... e.g. 'llama.cpp', 'transformer'"
        @keyup.enter="doSearch"
      />
      <input
        v-model="dir"
        type="text"
        placeholder="Directory path"
        style="max-width: 200px;"
      />
      <input
        v-model="tagFilter"
        type="text"
        placeholder="Filter by tags"
        style="max-width: 180px;"
      />
      <div class="top-n-control">
        <label>Top</label>
        <input v-model.number="topN" type="number" min="1" max="50" />
      </div>
      <button class="btn btn-primary" :disabled="!query.trim() || loading" @click="doSearch">
        <i class="pi pi-directions"></i>
        Deep Search
      </button>
    </div>

    <div v-if="availableTags.length > 0" class="available-tags">
      <span class="field-label">Tags:</span>
      <span
        v-for="tag in availableTags"
        :key="tag"
        class="tag-badge"
        :class="{ active: tagFilter.includes(tag) }"
        @click="toggleTag(tag)"
      >#{{ tag }}</span>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      Indexing and searching files...
    </div>

    <div v-else-if="results" class="results-container">
      <div class="stats-bar">
        <span>Found: <span class="count">{{ results.total_found }}</span></span>
        <span>Indexed: <span class="count">{{ results.total_indexed }}</span></span>
        <span>Query: <span class="count">"{{ results.query }}"</span></span>
      </div>

      <div v-if="results.results.length > 0" style="margin-bottom: 16px;">
        <button class="btn btn-primary" @click="loadAllToChat" :disabled="loadingChat">
          <i class="pi pi-comments"></i>
          {{ loadingChat ? 'Loading...' : 'Load All to Chat' }}
        </button>
        <span v-if="chatLoaded" style="margin-left: 12px; color: #27ae60; font-size: 13px;">
          <i class="pi pi-check"></i> {{ chatLoaded }}
        </span>
      </div>

      <div v-if="results.results.length === 0" class="empty-state">
        <i class="pi pi-directions"></i>
        <p>No matches found in any file</p>
      </div>

      <ResultCard
        v-for="item in results.results"
        :key="item.rank"
        :rank="item.rank"
        :score="item.score"
        :title="item.title || item.filename"
        :subtitle="item.subheading || item.snippet"
        :tags="item.tags || []"
        @tag-click="toggleTag"
      >
        <div v-if="item.summary" class="field-label">Summary</div>
        <div v-if="item.summary" class="field-value">{{ item.summary }}</div>

        <div v-if="item.toc && item.toc.length" class="field-label">Table of Contents</div>
        <ul v-if="item.toc && item.toc.length" class="toc-list">
          <li v-for="(heading, i) in item.toc" :key="i">{{ heading }}</li>
        </ul>

        <div v-if="item.url && item.url !== 'None'" class="field-label">URL</div>
        <a
          v-if="item.url && item.url !== 'None'"
          :href="item.url"
          class="field-value url"
          target="_blank"
        >{{ item.url }}</a>

        <div v-if="!item.title" class="field-label">Preview</div>
        <div v-if="!item.title" class="field-value">{{ item.snippet }}</div>

        <div class="field-label">Source File</div>
        <div class="field-value file-path">{{ item.file_path }}</div>

        <button class="btn btn-secondary btn-sm" @click="loadSingleToChat(item.file_path)" style="margin-top: 8px;">
          <i class="pi pi-comments"></i> Load to Chat
        </button>
      </ResultCard>
    </div>

    <div v-else class="empty-state">
      <i class="pi pi-directions"></i>
      <p>Enter a query and directory to search through all files</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { deepSearch, loadChatContext } from '../composables/useApi.js'
import ResultCard from './ResultCard.vue'

const query = ref('')
const dir = ref('.\\articles\\')
const tagFilter = ref('')
const topN = ref(5)
const loading = ref(false)
const results = ref(null)
const loadingChat = ref(false)
const chatLoaded = ref('')
const availableTags = ref([])

function toggleTag(tag) {
  const tags = tagFilter.value.split(',').map(t => t.trim()).filter(Boolean)
  const idx = tags.indexOf(tag)
  if (idx >= 0) {
    tags.splice(idx, 1)
  } else {
    tags.push(tag)
  }
  tagFilter.value = tags.join(', ')
}

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  chatLoaded.value = ''
  try {
    const tags = tagFilter.value.trim() || null
    results.value = await deepSearch(query.value, dir.value, topN.value, tags)
    if (results.value.available_tags) {
      availableTags.value = results.value.available_tags
    }
  } catch (e) {
    results.value = { query: query.value, top_n: topN.value, results: [], total_indexed: 0, total_found: 0, error: e.message }
  } finally {
    loading.value = false
  }
}

async function loadAllToChat() {
  if (!results.value || !results.value.results.length) return
  loadingChat.value = true
  chatLoaded.value = ''
  try {
    const paths = results.value.results.map(r => r.file_path)
    const res = await loadChatContext(paths)
    chatLoaded.value = `Loaded ${res.loaded} article${res.loaded > 1 ? 's' : ''}`
    setTimeout(() => { chatLoaded.value = '' }, 4000)
  } catch (e) {
    alert('Failed to load: ' + e.message)
  } finally {
    loadingChat.value = false
  }
}

async function loadSingleToChat(filePath) {
  try {
    const res = await loadChatContext([filePath])
    chatLoaded.value = `Loaded ${res.loaded} article`
    setTimeout(() => { chatLoaded.value = '' }, 4000)
  } catch (e) {
    alert('Failed to load: ' + e.message)
  }
}
</script>
