import { createContext, useCallback, useState } from 'react'
import { CheckCircle2, XCircle, Info, X } from 'lucide-react'

export const ToastContext = createContext(null)

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
}

const ACCENT_CLASSES = {
  success: 'border-l-4 border-l-[var(--color-success)] text-[var(--color-success)]',
  error: 'border-l-4 border-l-[var(--color-danger)] text-[var(--color-danger)]',
  info: 'border-l-4 border-l-[var(--color-accent)] text-[var(--color-accent)]',
}

let idCounter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((t) => t.id !== id))
  }, [])

  const notify = useCallback(
    (message, type = 'info', duration = 4000) => {
      const id = idCounter++
      setToasts((current) => [...current, { id, message, type }])
      if (duration) {
        setTimeout(() => dismiss(id), duration)
      }
      return id
    },
    [dismiss]
  )

  return (
    <ToastContext.Provider value={{ notify, dismiss }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-full max-w-sm px-4 sm:px-0">
        {toasts.map((toast) => {
          const Icon = ICONS[toast.type]
          return (
            <div
              key={toast.id}
              role="status"
              className={`animate-fade-in flex items-start gap-3 rounded-lg bg-[var(--color-canvas)] px-4 py-3 shadow-[var(--shadow-popover)] ${ACCENT_CLASSES[toast.type]}`}
            >
              <Icon size={18} className="mt-0.5 shrink-0" />
              <p className="flex-1 text-sm text-[var(--color-ink)]">{toast.message}</p>
              <button
                onClick={() => dismiss(toast.id)}
                aria-label="Dismiss notification"
                className="shrink-0 text-[var(--color-ink-faint)] hover:text-[var(--color-ink)]"
              >
                <X size={16} />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
