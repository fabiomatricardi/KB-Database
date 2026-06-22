<template>
  <div class="chat-layout">
    <div class="view-header">
      <h2>Chat</h2>
      <p>Ask questions about your loaded articles</p>
    </div>

    <div v-if="contextFiles.length > 0" class="context-bar">
      <div class="context-header">
        <i class="pi pi-file"></i>
        <span>{{ contextFiles.length }} article{{ contextFiles.length > 1 ? 's' : '' }} loaded</span>
        <button class="btn-link" @click="saveChat" v-if="messages.length > 0">
          <i class="pi pi-download"></i> Save Chat
        </button>
        <button class="btn-link" @click="clearContext">Clear All</button>
      </div>
      <div class="context-files">
        <div v-for="file in contextFiles" :key="file" class="context-chip">
          <span>{{ shortName(file) }}</span>
          <i class="pi pi-times" @click="removeFile(file)"></i>
        </div>
      </div>
    </div>

    <div v-else class="context-bar empty-context">
      <i class="pi pi-info-circle"></i>
      <span>No articles loaded. Go to Deep Search and click "Load to Chat".</span>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0 && !streaming" class="empty-state">
        <i class="pi pi-comments"></i>
        <p v-if="contextFiles.length > 0">Articles loaded. Ask a question or type <strong>"Summarize these articles"</strong> to start.</p>
        <p v-else>Load articles from Deep Search to start a conversation.</p>
      </div>

      <div v-for="(msg, i) in messages" :key="i" class="message" :class="msg.role">
        <div class="message-role">{{ msg.role === 'user' ? 'You' : 'Assistant' }}</div>
        <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
      </div>

      <div v-if="streaming" class="message assistant">
        <div class="message-role">Assistant</div>
        <div class="message-content" v-html="renderMarkdown(streamingText)"></div>
        <div class="streaming-indicator"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
      </div>
    </div>

    <div class="chat-input-bar">
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
} from '../composables/useApi.js'

marked.setOptions({
  breaks: true,
  gfm: true,
})

const contextFiles = ref([])
const messages = ref([])
const input = ref('')
const streaming = ref(false)
const streamingText = ref('')
const messagesContainer = ref(null)
let streamController = null

onMounted(async () => {
  await refreshContext()
  await loadHistory()
})

async function refreshContext() {
  try {
    const ctx = await getChatContext()
    contextFiles.value = ctx.files || []
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

async function clearContext() {
  try {
    await clearChatContext()
    contextFiles.value = []
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

function sendMessage() {
  const msg = input.value.trim()
  if (!msg || streaming.value) return

  messages.value.push({ role: 'user', content: msg })
  input.value = ''
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

  let md = `# ArticleDatabase Chat\n`
  md += `**Date:** ${dateStr}\n`
  md += `**Articles:** ${fileNames || 'None'}\n\n---\n\n`

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
