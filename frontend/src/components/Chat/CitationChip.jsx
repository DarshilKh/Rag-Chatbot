import { useEffect, useRef, useState } from 'react'
import { FileText } from 'lucide-react'

// The app's signature visual element: a citation is never just prose — it's
// a small, precise, monospace-numbered marker in a color reserved
// exclusively for "this claim is grounded in a document," distinct from
// ordinary interactive blue. Clicking it reveals exactly which chunk of
// which file backs the claim, and how confident the match was.
export default function CitationChip({ index, citation }) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!isOpen) return
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    const handleEscape = (e) => e.key === 'Escape' && setIsOpen(false)
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  if (!citation) return null

  const confidencePct = Math.round(Math.max(0, citation.similarity_score) * 100)

  return (
    <span className="relative inline-block" ref={containerRef}>
      <button
        onClick={() => setIsOpen((v) => !v)}
        aria-label={`Source ${index}: ${citation.filename}, chunk ${citation.chunk_index}`}
        aria-expanded={isOpen}
        className="mx-0.5 inline-flex h-4 min-w-4 -translate-y-0.5 items-center justify-center rounded-full bg-[var(--color-citation-soft)] px-1 font-mono text-[10px] font-semibold text-[var(--color-citation)] align-super transition-transform hover:scale-110"
      >
        {index}
      </button>

      {isOpen && (
        <div
          role="dialog"
          className="animate-fade-in absolute bottom-full left-1/2 z-20 mb-2 w-64 -translate-x-1/2 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] p-3 text-left shadow-[var(--shadow-popover)]"
        >
          <div className="flex items-start gap-2">
            <FileText size={14} className="mt-0.5 shrink-0 text-[var(--color-citation)]" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-[var(--color-ink)]" title={citation.filename}>
                {citation.filename}
              </p>
              <p className="font-mono text-[10px] text-[var(--color-ink-faint)]">
                chunk {citation.chunk_index} · {confidencePct}% match
              </p>
            </div>
          </div>
          <p className="mt-2 line-clamp-4 text-[11px] leading-snug text-[var(--color-ink-muted)]">
            {citation.snippet}
          </p>
          {/* Popover arrow */}
          <div className="absolute -bottom-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 border-b border-r border-[var(--color-border)] bg-[var(--color-canvas)]" />
        </div>
      )}
    </span>
  )
}
