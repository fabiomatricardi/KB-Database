import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function searchArticles(query, topN = 5, tags = null) {
  const params = { q: query, top_n: topN }
  if (tags) params.tags = tags
  const { data } = await api.get('/search', { params })
  return data
}

export async function deepSearch(query, dir, topN = 5, tags = null) {
  const params = { query, dir, top_n: topN }
  if (tags) params.tags = tags
  const { data } = await api.get('/deepsearch', { params })
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

export async function getTagsChanged() {
  const { data } = await api.get('/scan/tags-check')
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

export async function getGraphifyModels(backend = 'ollama') {
  const { data } = await api.get('/graphify/models', { params: { backend } })
  return data
}

export async function saveModel(model, backend) {
  const { data } = await api.post('/saved_models', { model, backend })
  return data
}

export async function deleteSavedModel(model, backend) {
  const { data } = await api.delete('/saved_models', { data: { model, backend } })
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

export async function webSearch(query, maxResults = 10) {
  const { data } = await api.get('/web/search', { params: { q: query, max_results: maxResults } })
  return data
}

export async function webFetch(url) {
  const { data } = await api.post('/web/fetch', { url })
  return data
}

export async function loadWebContext(title, url, content) {
  const { data } = await api.post('/chat/context/web', { title, url, content })
  return data
}

export async function removeWebContext(url) {
  const { data } = await api.delete('/chat/context/web', { params: { url } })
  return data
}

export async function buildGraph(config = {}) {
  const { data } = await api.post('/graph/build', config)
  return data
}

export async function getGraphStatus() {
  const { data } = await api.get('/graph/status')
  return data
}

export async function getGraphHtml() {
  const { data } = await api.get('/graph/html')
  return data
}

export async function graphQuery(question) {
  const { data } = await api.post('/graph/query', { question })
  return data
}

export async function graphExplain(concept) {
  const { data } = await api.post('/graph/explain', { concept })
  return data
}

export async function graphPathTo(start, end) {
  const { data } = await api.post('/graph/path', { start, end })
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
