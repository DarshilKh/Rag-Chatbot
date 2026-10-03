import { FileX2 } from 'lucide-react'
import DocumentItem from './DocumentItem'
import Spinner from '../common/Spinner'
import { useDocuments } from '../../hooks/useDocuments'

export default function DocumentList() {
  const { documents, isLoading, error } = useDocuments()

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center py-8">
        <Spinner size={18} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-2 py-6 text-center">
        <p className="text-xs text-[var(--color-danger)]">{error.message || 'Could not load documents.'}</p>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-2 px-4 py-8 text-center">
        <FileX2 size={22} className="text-[var(--color-ink-faint)]" />
        <p className="text-xs text-[var(--color-ink-faint)]">
          No documents yet. Upload one to start asking questions.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-1">
      {documents.map((doc) => (
        <DocumentItem key={doc.id} document={doc} />
      ))}
    </div>
  )
}
