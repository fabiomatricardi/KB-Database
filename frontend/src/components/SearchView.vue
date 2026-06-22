<template>
  <div>
    <div class="view-header">
      <h2>Search Database</h2>
      <p>Search article metadata (title, subheading, summary) using BM25 ranking</p>
    </div>

    <div class="search-bar">
      <input
        v-model="query"
        type="text"
        placeholder="Search articles... e.g. 'RAG', 'llama.cpp', 'OpenCode'"
        @keyup.enter="doSearch"
      />
      <div class="top-n-control">
        <label>Top</label>
        <input v-model.number="topN" type="number" min="1" max="50" />
      </div>
      <button class="btn btn-primary" :disabled="!query.trim() || loading" @click="doSearch">
        <i class="pi pi-search"></i>
        Search
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      Searching...
    </div>

    <div v-else-if="results" class="results-container">
      <div class="stats-bar">
        <span>Results: <span class="count">{{ results.total_found }}</span></span>
        <span>Query: <span class="count">"{{ results.query }}"</span></span>
      </div>

      <div v-if="results.results.length === 0" class="empty-state">
        <i class="pi pi-search"></i>
        <p>No matches found for "{{ results.query }}"</p>
      </div>

      <ResultCard
        v-for="item in results.results"
        :key="item.rank"
        :rank="item.rank"
        :score="item.score"
        :title="item.article.title"
        :subtitle="item.article.subheading"
      >
        <div class="field-label">Summary</div>
        <div class="field-value">{{ item.article.summary }}</div>

        <div v-if="item.article.url && item.article.url !== 'None'" class="field-label">URL</div>
        <a
          v-if="item.article.url && item.article.url !== 'None'"
          :href="item.article.url"
          class="field-value url"
          target="_blank"
        >{{ item.article.url }}</a>

        <div class="field-label">Source File</div>
        <div class="field-value file-path">{{ item.article.file_path }}</div>
      </ResultCard>
    </div>

    <div v-else class="empty-state">
      <i class="pi pi-search"></i>
      <p>Type a query and press Search to find articles</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchArticles } from '../composables/useApi.js'
import ResultCard from './ResultCard.vue'

const query = ref('')
const topN = ref(5)
const loading = ref(false)
const results = ref(null)

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  try {
    results.value = await searchArticles(query.value, topN.value)
  } catch (e) {
    results.value = { query: query.value, top_n: topN.value, results: [], total_found: 0, error: e.message }
  } finally {
    loading.value = false
  }
}
</script>
