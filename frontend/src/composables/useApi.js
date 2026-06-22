import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function searchArticles(query, topN = 5) {
  const { data } = await api.get('/search', { params: { q: query, top_n: topN } })
  return data
}

export async function deepSearch(query, dir, topN = 5) {
  const { data } = await api.get('/deepsearch', { params: { query, dir, top_n: topN } })
  return data
}

export async function startScan(config = {}) {
  const { data } = await api.post('/scan', config)
  return data
}

export async function getScanStatus() {
  const { data } = await api.get('/scan/status')
  return data
}

export async function getSettings() {
  const { data } = await api.get('/settings')
  return data
}

export async function updateSettings(config) {
  const { data } = await api.put('/settings', config)
  return data
}

export async function shutdownApp() {
  const { data } = await api.post('/shutdown')
  return data
}

export async function getOllamaModels(filterFree = false) {
  const { data } = await api.get('/ollama/models', { params: { filter_free: filterFree } })
  return data
}

export async function getChatContext() {
  const { data } = await api.get('/chat/context')
  return data
}

export async function loadChatContext(filePaths) {
  const { data } = await api.post('/chat/context', { file_paths: filePaths })
  return data
}

export async function clearChatContext() {
  const { data } = await api.delete('/chat/context')
  return data
}

export async function removeChatContext(filePath) {
  const { data } = await api.delete(`/chat/context/${encodeURIComponent(filePath)}`)
  return data
}

export async function clearChatHistory() {
  const { data } = await api.delete('/chat/history')
  return data
}

export async function getChatHistory() {
  const { data } = await api.get('/chat/history')
  return data
}

export function chatMessageStream(message, onChunk, onDone, onError) {
  const controller = new AbortController()

  fetch('/api/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  }).then(response => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    function read() {
      reader.read().then(({ done, value }) => {
        if (done) {
          onDone()
          return
        }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              onDone()
              return
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.chunk) {
                onChunk(parsed.chunk)
              }
            } catch (e) { /* skip */ }
          }
        }
        read()
      }).catch(err => {
        if (err.name !== 'AbortError') {
          onError(err)
        }
      })
    }
    read()
  }).catch(err => {
    if (err.name !== 'AbortError') {
      onError(err)
    }
  })

  return controller
}
