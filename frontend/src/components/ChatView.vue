<template>
  <div class="chat-layout" :class="{ 'web-panel-open': showWebPanel }">
    <div class="chat-main">
      <div class="view-header">
        <h2>Chat</h2>
        <p>Ask questions about your loaded articles and web sources</p>
        <button class="btn-icon web-toggle" :class="{ active: showWebPanel }" @click="showWebPanel = !showWebPanel" title="Web Tools">
          <i class="pi pi-globe"></i>
        </button>
      </div>

      <div v-if="contextFiles.length > 0 || webContexts.length > 0" class="context-bar">
        <div class="context-header">
          <i class="pi pi-file"></i>
          <span>{{ contextFiles.length }} article{{ contextFiles.length > 1 ? 's' : '' }}</span>
          <span v-if="webContexts.length > 0" style="margin-left: 8px;">
            <i class="pi pi-globe"></i>
            {{ webContexts.length }} web source{{ webContexts.length > 1 ? 's' : '' }}
          </span>
          <button class="btn-link" @click="saveChat" v-if="messages.length > 0">
            <i class="pi pi-download"></i> Save Chat
          </button>
          <button class="btn-link" @click="clearContext">Clear All</button>
        </div>
        <div class="context-files">
          <div v-for="file in contextFiles" :key="file" class="context-chip">
            <i class="pi pi-file"></i>
            <span>{{ shortName(file) }}</span>
            <i class="pi pi-times" @click="removeFile(file)"></i>
          </div>
          <div v-for="w in webContexts" :key="w.url" class="context-chip web-chip">
            <i class="pi pi-globe"></i>
            <span>{{ w.title || w.url }}</span>
            <i class="pi pi-times" @click="removeWebCtx(w.url)"></i>
          </div>
        </div>
      </div>

      <div v-else class="context-bar empty-context">
        <i class="pi pi-info-circle"></i>
        <span>No articles loaded. Use Deep Search to load articles, or the Web panel to load web content.</span>
      </div>

      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0 && !streaming" class="empty-state">
          <i class="pi pi-comments"></i>
          <p v-if="contextFiles.length > 0 || webContexts.length > 0">Context loaded. Ask a question or type <strong>"Summarize these articles"</strong> to start.</p>
          <p v-else>Load articles from Deep Search or web content from the Web panel to start a conversation.</p>
        </div>

      <div v-for="(msg, i) in messages" :key="i" class="message" :class="msg.role">
        <div v-if="msg.role !== 'system'" class="message-role">{{ msg.role === 'user' ? 'You' : 'Assistant' }}</div>
        <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
      </div>

        <div v-if="streaming" class="message assistant">
          <div class="message-role">Assistant</div>
          <div class="message-content" v-html="renderMarkdown(streamingText)"></div>
          <div class="streaming-indicator"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
        </div>
      </div>

      <div class="chat-input-bar">
        <div class="input-row">
          <textarea
            v-model="input"
            placeholder="Ask a question about the loaded articles..."
            :disabled="streaming"
            @keydown.enter.exact.prevent="sendMessage"
            rows="2"
          ></textarea>
          <button class="btn btn-primary" @click="sendMessage" :disabled="!input.trim() || streaming">
            <i class="pi pi-send"></i>
          </button>
        </div>
        <label class="auto-search-toggle">
          <input type="checkbox" v-model="autoSearchWeb" />
          <span>Search web before sending</span>
        </label>
        <div v-if="webContexts.length > 0" class="web-context-indicator">
          <i class="pi pi-globe"></i>
          {{ webContexts.length }} web source{{ webContexts.length > 1 ? 's' : '' }} will be included with your message
        </div>
      </div>
    </div>

    <div v-if="showWebPanel" class="web-panel">
      <div class="web-panel-header">
        <h3><i class="pi pi-globe"></i> Web Tools</h3>
        <button class="btn-icon" @click="showWebPanel = false"><i class="pi pi-times"></i></button>
      </div>

      <div class="web-tabs">
        <button :class="{ active: webTab === 'search' }" @click="webTab = 'search'">Search</button>
        <button :class="{ active: webTab === 'fetch' }" @click="webTab = 'fetch'">Fetch URL</button>
      </div>

      <div v-if="webTab === 'search'" class="web-tab-content">
        <div class="web-search-bar">
          <input
            v-model="webQuery"
            type="text"
            placeholder="Search the web..."
            @keyup.enter="doWebSearch"
          />
          <button class="btn btn-primary btn-sm" @click="doWebSearch" :disabled="!webQuery.trim() || webSearching">
            <i class="pi pi-search"></i>
          </button>
        </div>

        <div v-if="webSearching" class="web-loading">
          <div class="spinner"></div> Searching...
        </div>

        <div v-if="webSearchResults.length > 0" class="web-results">
          <div v-for="(r, i) in webSearchResults" :key="i" class="web-result-card">
            <div class="web-result-title">{{ r.title }}</div>
            <a :href="r.url" target="_blank" class="web-result-url">{{ r.url }}</a>
            <div class="web-result-snippet">{{ r.snippet }}</div>
            <div class="web-result-actions">
              <button class="btn btn-secondary btn-sm" @click="fetchAndLoad(r.url, r.title)">
                <i class="pi pi-download"></i> Fetch &amp; Load
              </button>
            </div>
          </div>
        </div>

        <div v-else-if="!webSearching && webSearched" class="web-empty">
          No results found.
        </div>
      </div>

      <div v-if="webTab === 'fetch'" class="web-tab-content">
        <div class="web-search-bar">
          <input
            v-model="fetchUrl"
            type="url"
            placeholder="https://example.com/article"
            @keyup.enter="doWebFetch"
          />
          <button class="btn btn-primary btn-sm" @click="doWebFetch" :disabled="!fetchUrl.trim() || webFetching">
            <i class="pi pi-cloud-download"></i>
          </button>
        </div>

        <div v-if="webFetching" class="web-loading">
          <div class="spinner"></div> Fetching...
        </div>

        <div v-if="fetchResult" class="web-fetch-preview">
          <div class="web-result-title">{{ fetchResult.title }}</div>
          <div class="web-result-url">{{ fetchResult.url }}</div>
          <div class="web-fetch-meta">{{ fetchResult.char_count.toLocaleString() }} characters</div>
          <div class="web-fetch-content">{{ fetchResult.content.substring(0, 1000) }}{{ fetchResult.content.length > 1000 ? '...' : '' }}</div>
          <button class="btn btn-primary btn-sm" @click="loadFetchResult">
            <i class="pi pi-download"></i> Load to Chat
          </button>
        </div>

        <div v-else-if="!webFetching && fetchTried" class="web-empty">
          Failed to fetch URL.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import {
  getChatContext,
  loadChatContext,
  clearChatContext,
  removeChatContext,
  clearChatHistory,
  getChatHistory,
  chatMessageStream,
  webSearch,
  webFetch,
  loadWebContext,
  removeWebContext,
} from '../composables/useApi.js'

marked.setOptions({
  breaks: true,
  gfm: true,
})

const contextFiles = ref([])
const webContexts = ref([])
const messages = ref([])
const input = ref('')
const streaming = ref(false)
const streamingText = ref('')
const messagesContainer = ref(null)
let streamController = null

const showWebPanel = ref(false)
const webTab = ref('search')
const webQuery = ref('')
const webSearching = ref(false)
const webSearchResults = ref([])
const webSearched = ref(false)
const fetchUrl = ref('')
const webFetching = ref(false)
const fetchResult = ref(null)
const fetchTried = ref(false)
const autoSearchWeb = ref(false)

onMounted(async () => {
  await refreshContext()
  await loadHistory()
})

async function refreshContext() {
  try {
    const ctx = await getChatContext()
    contextFiles.value = ctx.files || []
    webContexts.value = ctx.web_contexts || []
  } catch (e) { /* ignore */ }
}

async function loadHistory() {
  try {
    const result = await getChatHistory()
    if (result.history && result.history.length > 0) {
      messages.value = result.history
    }
  } catch (e) { /* ignore */ }
}

function shortName(path) {
  return path.split(/[/\\]/).pop()
}

async function removeFile(file) {
  try {
    await removeChatContext(file)
    await refreshContext()
  } catch (e) { /* ignore */ }
}

async function removeWebCtx(url) {
  try {
    await removeWebContext(url)
    await refreshContext()
  } catch (e) { /* ignore */ }
}

async function clearContext() {
  try {
    await clearChatContext()
    contextFiles.value = []
    webContexts.value = []
    messages.value = []
  } catch (e) { /* ignore */ }
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function doWebSearch() {
  if (!webQuery.value.trim()) return
  webSearching.value = true
  webSearched.value = false
  webSearchResults.value = []
  try {
    const data = await webSearch(webQuery.value, 10)
    webSearchResults.value = data.results || []
  } catch (e) {
    webSearchResults.value = [{ title: 'Error', url: '', snippet: e.message }]
  } finally {
    webSearching.value = false
    webSearched.value = true
  }
}

async function fetchAndLoad(url, title) {
  if (!url) return
  webFetching.value = true
  try {
    const result = await webFetch(url)
    if (result.content) {
      await loadWebContext(result.title || title || url, result.url || url, result.content)
      await refreshContext()
      messages.value.push({ role: 'system', content: `🌐 Loaded: ${result.title || title || url}. Ask a follow-up question.` })
      scrollToBottom()
    }
  } catch (e) {
    alert('Failed to fetch: ' + e.message)
  } finally {
    webFetching.value = false
  }
}

async function doWebFetch() {
  if (!fetchUrl.value.trim()) return
  webFetching.value = true
  fetchTried.value = false
  fetchResult.value = null
  try {
    fetchResult.value = await webFetch(fetchUrl.value)
  } catch (e) {
    fetchResult.value = null
  } finally {
    webFetching.value = false
    fetchTried.value = true
  }
}

async function loadFetchResult() {
  if (!fetchResult.value) return
  try {
    await loadWebContext(fetchResult.value.title, fetchResult.value.url, fetchResult.value.content)
    await refreshContext()
    messages.value.push({ role: 'system', content: `🌐 Loaded: ${fetchResult.value.title}. Ask a follow-up question.` })
    scrollToBottom()
    fetchResult.value = null
    fetchTried.value = false
  } catch (e) {
    alert('Failed to load: ' + e.message)
  }
}

async function autoSearchAndSend(msg) {
  webSearching.value = true
  try {
    const data = await webSearch(msg, 5)
    const results = data.results || []
    let loaded = 0
    for (const r of results) {
      if (r.url) {
        try {
          const fetched = await webFetch(r.url)
          if (fetched.content) {
            await loadWebContext(fetched.title || r.title, fetched.url || r.url, fetched.content)
            loaded++
          }
        } catch (e) { /* skip failed fetches */ }
      }
    }
    await refreshContext()
    if (loaded > 0) {
      messages.value.push({ role: 'system', content: `🌐 ${loaded} web source${loaded > 1 ? 's' : ''} loaded. Ask a follow-up question about them.` })
      scrollToBottom()
    }
  } catch (e) { /* ignore */ }
  finally {
    webSearching.value = false
  }
}

async function sendMessage() {
  const msg = input.value.trim()
  if (!msg || streaming.value) return

  input.value = ''

  if (autoSearchWeb.value) {
    await autoSearchAndSend(msg)
  }

  messages.value.push({ role: 'user', content: msg })
  streaming.value = true
  streamingText.value = ''
  scrollToBottom()

  streamController = chatMessageStream(
    msg,
    (chunk) => {
      streamingText.value += chunk
      scrollToBottom()
    },
    () => {
      messages.value.push({ role: 'assistant', content: streamingText.value })
      streamingText.value = ''
      streaming.value = false
      streamController = null
      scrollToBottom()
    },
    (err) => {
      streamingText.value += '\n[Error: ' + err.message + ']'
      messages.value.push({ role: 'assistant', content: streamingText.value })
      streamingText.value = ''
      streaming.value = false
      streamController = null
    }
  )
}

async function saveChat() {
  const now = new Date()
  const dateStr = now.toISOString().slice(0, 16).replace('T', ' ')
  const fileNames = contextFiles.value.map(f => shortName(f)).join(', ')
  const webNames = webContexts.value.map(w => w.title || w.url).join(', ')

  let md = `# ArticleDatabase Chat\n`
  md += `**Date:** ${dateStr}\n`
  md += `**Articles:** ${fileNames || 'None'}\n`
  md += `**Web Sources:** ${webNames || 'None'}\n\n---\n\n`

  for (const msg of messages.value) {
    const role = msg.role === 'user' ? '## You' : '## Assistant'
    md += `${role}\n\n${msg.content}\n\n---\n\n`
  }

  const blob = new Blob([md], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-${dateStr.replace(/[: ]/g, '-')}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>
