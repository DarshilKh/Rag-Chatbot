import { useEffect, useState } from 'react'
import { MessageSquareText, Menu, Sun, Moon, Circle } from 'lucide-react'
import { healthApi } from '../../api/health'
import { useTheme } from '../../hooks/useTheme'

export default function Header({ onToggleSidebar }) {
  const { theme, toggleTheme } = useTheme()
  const [status, setStatus] = useState('checking') // checking | online | offline

  useEffect(() => {
    let cancelled = false

    const check = async () => {
      try {
        await healthApi.check()
        if (!cancelled) setStatus('online')
      } catch {
        if (!cancelled) setStatus('offline')
      }
    }

    check()
    const interval = setInterval(check, 30_000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const statusConfig = {
    checking: { color: 'text-[var(--color-ink-faint)]', label: 'Checking…' },
    online: { color: 'text-[var(--color-success)]', label: 'Connected' },
    offline: { color: 'text-[var(--color-danger)]', label: 'Backend offline' },
  }[status]

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-canvas)] px-4">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle documents sidebar"
          className="rounded-md p-1.5 text-[var(--color-ink-muted)] hover:bg-[var(--color-surface-hover)] lg:hidden"
        >
          <Menu size={18} />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-accent)] text-white">
            <MessageSquareText size={15} />
          </div>
          <span className="text-sm font-semibold text-[var(--color-ink)]">Document Chat</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-1.5 sm:flex" title={statusConfig.label}>
          <Circle size={7} className={`${statusConfig.color} fill-current`} />
          <span className="text-xs text-[var(--color-ink-faint)]">{statusConfig.label}</span>
        </div>
        <button
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="rounded-md p-1.5 text-[var(--color-ink-muted)] hover:bg-[var(--color-surface-hover)]"
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  )
}
