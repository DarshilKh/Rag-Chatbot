import { createContext, useCallback, useEffect, useState } from 'react'
import { chatApi } from '../api/chat'

export const ChatContext = createContext(null)

// Client-side id so React has a stable key before the server round-trips —
// messages are otherwise identified by position, which breaks under re-renders.
let localIdCounter = 0
const nextLocalId = () => `local-${localIdCounter++}`

// If the backend/network hangs mid-stream with no error and no more
// tokens, isSending would otherwise stay true forever with no way for the
// user to recover short of reloading the page (audit finding M3). This is
// deliberately generous — LLM generation can legitimately take a while —
// it's a safety net for a genuinely hung connection, not a normal timeout.
const STREAM_TIMEOUT_MS = 120_000

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    chatApi
      .getHistory()
      .then((data) => {
        if (cancelled) return
        setMessages(
          data.messages.map((m) => ({
            id: nextLocalId(),
            role: m.role,
            content: m.content,
            citations: m.citations,
            timestamp: m.timestamp,
          }))
        )
      })
      .catch(() => {
        /* history is a nice-to-have on load; a failure here shouldn't block chat */
      })
      .finally(() => {
        if (!cancelled) setIsLoadingHistory(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed) return

    setError(null)
    const userMessage = {
      id: nextLocalId(),
      role: 'user',
      content: trimmed,
      citations: [],
      timestamp: new Date().toISOString(),
    }
    const assistantId = nextLocalId()
    const assistantMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      citations: [],
      timestamp: new Date().toISOString(),
      isStreaming: true,
    }
    setMessages((current) => [...current, userMessage, assistantMessage])
    setIsSending(true)

    const updateAssistant = (patch) => {
      setMessages((current) =>
        current.map((m) => (m.id === assistantId ? { ...m, ...patch(m) } : m))
      )
    }

    const controller = new AbortController()
    let timeoutId = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS)
    const resetTimeout = () => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS)
    }

    try {
      await chatApi.stream(
        trimmed,
        {
          onToken: (token) => {
            resetTimeout() // still receiving data — extend the deadline
            updateAssistant((m) => ({ content: m.content + token }))
          },
          onCitations: (citations) => updateAssistant(() => ({ citations })),
        },
        { signal: controller.signal }
      )
      updateAssistant(() => ({ isStreaming: false }))
    } catch (err) {
      const timedOut = err.name === 'AbortError'
      setError(err)
      // Remove the (likely empty or partial) assistant placeholder and
      // surface the failure as its own error bubble instead.
      setMessages((current) => [
        ...current.filter((m) => m.id !== assistantId),
        {
          id: nextLocalId(),
          role: 'error',
          content: timedOut
            ? 'The response took too long and timed out. Please try again.'
            : err.message || 'Something went wrong. Please try again.',
          citations: [],
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      clearTimeout(timeoutId)
      setIsSending(false)
    }
  }, [])

  const clearChat = useCallback(async () => {
    await chatApi.clear()
    setMessages([])
    setError(null)
  }, [])

  return (
    <ChatContext.Provider
      value={{ messages, isLoadingHistory, isSending, error, sendMessage, clearChat }}
    >
      {children}
    </ChatContext.Provider>
  )
}
