import apiClient from './client'

export const chatApi = {
  send: (message, options = {}) =>
    apiClient
      .post('/chat', {
        message,
        document_ids: options.documentIds ?? null,
        top_k: options.topK ?? null,
      })
      .then((r) => r.data),

  getHistory: () => apiClient.get('/chat/history').then((r) => r.data),

  clear: () => apiClient.delete('/chat').then((r) => r.data),

  /**
   * Streams a chat response over SSE using fetch + a manual reader, since
   * EventSource doesn't support POST bodies. Calls `handlers.onToken(text)`
   * as tokens arrive, `handlers.onCitations(citations)` once (after the last
   * token), and resolves when the stream ends. Throws on network/HTTP errors
   * or a backend-emitted `error` SSE event, so callers can catch it like any
   * other rejected promise.
   */
  async stream(message, handlers = {}, options = {}) {
    const baseURL = apiClient.defaults.baseURL || ''
    const response = await fetch(`${baseURL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        document_ids: options.documentIds ?? null,
        top_k: options.topK ?? null,
      }),
      signal: options.signal,
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      const err = new Error(body.message || `Request failed with status ${response.status}`)
      err.status = response.status
      err.errorCode = body.error_code
      throw err
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE events are separated by a blank line; parse each complete block.
      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        const rawEvent = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        boundary = buffer.indexOf('\n\n')

        const eventLine = rawEvent.split('\n').find((l) => l.startsWith('event:'))
        const dataLine = rawEvent.split('\n').find((l) => l.startsWith('data:'))
        if (!eventLine || !dataLine) continue

        const eventType = eventLine.slice('event:'.length).trim()
        const data = JSON.parse(dataLine.slice('data:'.length).trim())

        if (eventType === 'token') handlers.onToken?.(data.content)
        else if (eventType === 'citations') handlers.onCitations?.(data.citations)
        else if (eventType === 'error') throw new Error(data.message || 'The assistant hit an error.')
        else if (eventType === 'done') return
      }
    }
  },
}
