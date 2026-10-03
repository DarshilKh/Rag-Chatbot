import { FileText } from 'lucide-react'

// Full-source footer, complementing the inline numbered CitationChip markers:
// a scannable "here's everything this answer drew from" strip, in the same
// reserved citation-cyan accent.
export default function CitationList({ citations }) {
  if (!citations || citations.length === 0) return null

  return (
    <div className="mt-2.5 flex flex-wrap gap-1.5 border-t border-[var(--color-border)] pt-2.5">
      {citations.map((citation, i) => (
        <span
          key={`${citation.document_id}-${citation.chunk_index}`}
          title={citation.snippet}
          className="inline-flex max-w-[220px] items-center gap-1.5 rounded-full bg-[var(--color-citation-soft)] px-2.5 py-1 text-[11px] text-[var(--color-citation)]"
        >
          <span className="flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full bg-[var(--color-citation)] font-mono text-[9px] font-bold text-[var(--color-canvas)]">
            {i + 1}
          </span>
          <FileText size={11} className="shrink-0" />
          <span className="truncate font-mono">
            {citation.filename} · #{citation.chunk_index}
          </span>
        </span>
      ))}
    </div>
  )
}
