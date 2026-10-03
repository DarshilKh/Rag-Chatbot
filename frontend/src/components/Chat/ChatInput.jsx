import { useRef, useState, useEffect } from 'react'
import { SendHorizontal } from 'lucide-react'

export default function ChatInput({ onSend, disabled, disabledReason }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [value])

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-[var(--color-border)] bg-[var(--color-canvas)] px-4 py-3 sm:px-6">
      <div className="mx-auto flex max-w-2xl items-end gap-2">
        <div className="flex-1 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 py-2.5 focus-within:border-[var(--color-accent)] transition-colors">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={1}
            placeholder={disabled ? disabledReason : 'Ask a question about your documents…'}
            aria-label="Chat message"
            className="w-full resize-none bg-transparent text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)] outline-none disabled:cursor-not-allowed"
          />
        </div>
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-accent)] text-white transition-colors hover:bg-[var(--color-accent-hover)] disabled:opacity-40 disabled:hover:bg-[var(--color-accent)]"
        >
          <SendHorizontal size={17} />
        </button>
      </div>
      <p className="mx-auto mt-1.5 max-w-2xl text-[11px] text-[var(--color-ink-faint)]">
        Enter to send · Shift+Enter for a new line
      </p>
    </div>
  )
}
