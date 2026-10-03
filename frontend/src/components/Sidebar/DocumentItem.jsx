import { useState, useRef, useEffect } from 'react'
import { FileText, Pencil, Trash2, Check, X } from 'lucide-react'
import StatusBadge from '../common/StatusBadge'
import Modal from '../common/Modal'
import Button from '../common/Button'
import { useDocuments } from '../../hooks/useDocuments'
import { useToast } from '../../hooks/useToast'
import { formatFileSize, formatRelativeDate } from '../../utils/formatters'

export default function DocumentItem({ document }) {
  const { rename, remove } = useDocuments()
  const { notify } = useToast()
  const [isEditing, setIsEditing] = useState(false)
  const [draftName, setDraftName] = useState(document.filename)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    if (isEditing) inputRef.current?.focus()
  }, [isEditing])

  const startEditing = () => {
    setDraftName(document.filename)
    setIsEditing(true)
  }

  const saveRename = async () => {
    const trimmed = draftName.trim()
    if (!trimmed || trimmed === document.filename) {
      setIsEditing(false)
      return
    }
    setIsSaving(true)
    try {
      await rename(document.id, trimmed)
      setIsEditing(false)
    } catch (err) {
      notify(err.message || 'Could not rename document.', 'error')
    } finally {
      setIsSaving(false)
    }
  }

  const confirmDelete = async () => {
    setIsDeleting(true)
    try {
      await remove(document.id)
      notify(`"${document.filename}" deleted.`, 'success')
      setIsDeleteOpen(false)
    } catch (err) {
      notify(err.message || 'Could not delete document.', 'error')
      setIsDeleting(false)
    }
  }

  return (
    <>
      <div className="group relative rounded-lg border border-transparent px-2.5 py-2.5 hover:border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] transition-colors">
        <div className="flex items-start gap-2.5">
          <FileText size={16} className="mt-0.5 shrink-0 text-[var(--color-ink-faint)]" />
          <div className="min-w-0 flex-1">
            {isEditing ? (
              <div className="flex items-center gap-1">
                <input
                  ref={inputRef}
                  value={draftName}
                  onChange={(e) => setDraftName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveRename()
                    if (e.key === 'Escape') setIsEditing(false)
                  }}
                  className="min-w-0 flex-1 rounded-md border border-[var(--color-accent)] bg-[var(--color-canvas)] px-1.5 py-0.5 text-sm text-[var(--color-ink)] outline-none"
                />
                <button
                  onClick={saveRename}
                  disabled={isSaving}
                  aria-label="Save name"
                  className="p-1 text-[var(--color-success)] hover:bg-[var(--color-success-soft)] rounded"
                >
                  <Check size={14} />
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  aria-label="Cancel rename"
                  className="p-1 text-[var(--color-ink-faint)] hover:bg-[var(--color-surface-hover)] rounded"
                >
                  <X size={14} />
                </button>
              </div>
            ) : (
              <p className="truncate text-sm font-medium text-[var(--color-ink)]" title={document.filename}>
                {document.filename}
              </p>
            )}
            <div className="mt-1 flex items-center gap-2 text-[11px] text-[var(--color-ink-faint)]">
              <span>{formatFileSize(document.size_bytes)}</span>
              <span aria-hidden="true">·</span>
              <span>{formatRelativeDate(document.uploaded_at)}</span>
            </div>
            <div className="mt-1.5 flex items-center gap-2">
              <StatusBadge status={document.status} />
              {document.status === 'ready' && (
                <span className="text-[11px] text-[var(--color-ink-faint)]">
                  {document.chunk_count} chunk{document.chunk_count === 1 ? '' : 's'}
                </span>
              )}
            </div>
            {document.status === 'failed' && document.error_message && (
              <p className="mt-1 text-[11px] text-[var(--color-danger)]">{document.error_message}</p>
            )}
          </div>

          {!isEditing && (
            <div className="flex shrink-0 gap-0.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
              <button
                onClick={startEditing}
                aria-label={`Rename ${document.filename}`}
                className="p-1.5 text-[var(--color-ink-faint)] hover:text-[var(--color-accent)] hover:bg-[var(--color-accent-soft)] rounded-md"
              >
                <Pencil size={13} />
              </button>
              <button
                onClick={() => setIsDeleteOpen(true)}
                aria-label={`Delete ${document.filename}`}
                className="p-1.5 text-[var(--color-ink-faint)] hover:text-[var(--color-danger)] hover:bg-[var(--color-danger-soft)] rounded-md"
              >
                <Trash2 size={13} />
              </button>
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Delete document?"
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" isLoading={isDeleting} onClick={confirmDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-[var(--color-ink-muted)]">
          This removes <span className="font-medium text-[var(--color-ink)]">"{document.filename}"</span> and
          all of its indexed content. This can't be undone.
        </p>
      </Modal>
    </>
  )
}
