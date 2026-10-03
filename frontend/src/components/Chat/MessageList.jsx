import { Suspense, lazy, useEffect, useRef } from 'react'

const MessageBubble = lazy(() => import('./MessageBubble'))

export default function MessageList({ messages }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-6">
      <div className="mx-auto flex max-w-2xl flex-col gap-3">
        <Suspense fallback={null}>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </Suspense>
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
