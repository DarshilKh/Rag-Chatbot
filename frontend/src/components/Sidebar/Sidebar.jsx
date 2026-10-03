import UploadZone from './UploadZone'
import DocumentList from './DocumentList'
import { useDocuments } from '../../hooks/useDocuments'

export default function Sidebar() {
  const { documents } = useDocuments()

  return (
    <aside className="flex h-full w-full flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-muted)]">
          Documents
        </h2>
        {documents.length > 0 && (
          <span className="text-[11px] text-[var(--color-ink-faint)]">{documents.length}</span>
        )}
      </div>

      <div className="px-3 pb-3">
        <UploadZone />
      </div>

      <DocumentList />
    </aside>
  )
}
