import { useCallback, useRef, useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { useDocuments } from '../../hooks/useDocuments'
import { useToast } from '../../hooks/useToast'

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']
const MAX_SIZE_MB = 20

function getExtension(filename) {
  const idx = filename.lastIndexOf('.')
  return idx === -1 ? '' : filename.slice(idx).toLowerCase()
}

export default function UploadZone() {
  const { upload } = useDocuments()
  const { notify } = useToast()
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const inputRef = useRef(null)

  const handleFiles = useCallback(
    async (fileList) => {
      const files = Array.from(fileList)
      for (const file of files) {
        const extension = getExtension(file.name)
        if (!ALLOWED_EXTENSIONS.includes(extension)) {
          notify(`"${file.name}" isn't a supported type. Use PDF, DOCX, TXT, or MD.`, 'error')
          continue
        }
        if (file.size > MAX_SIZE_MB * 1024 * 1024) {
          notify(`"${file.name}" is over the ${MAX_SIZE_MB}MB limit.`, 'error')
          continue
        }

        setIsUploading(true)
        setProgress(0)
        try {
          const document = await upload(file, (event) => {
            if (event.total) {
              setProgress(Math.round((event.loaded / event.total) * 100))
            }
          })
          // The backend can return a successful HTTP response (upload itself
          // succeeded) with status: 'failed' if *indexing* subsequently
          // failed (e.g. a corrupt/encrypted PDF) — checking only for a
          // thrown error here previously showed a false "uploaded and
          // indexed" success toast even when indexing had failed.
          if (document.status === 'failed') {
            notify(
              document.error_message || `"${file.name}" was uploaded, but indexing failed.`,
              'error'
            )
          } else {
            notify(`"${file.name}" uploaded and indexed.`, 'success')
          }
        } catch (err) {
          notify(err.message || `Failed to upload "${file.name}".`, 'error')
        } finally {
          setIsUploading(false)
          setProgress(0)
        }
      }
    },
    [upload, notify]
  )

  const onDrop = useCallback(
    (e) => {
      e.preventDefault()
      setIsDragging(false)
      if (e.dataTransfer.files?.length) {
        handleFiles(e.dataTransfer.files)
      }
    },
    [handleFiles]
  )

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
      aria-label="Upload a document"
      className={`group flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed px-4 py-6 text-center transition-colors duration-150 ${
        isDragging
          ? 'border-[var(--color-accent)] bg-[var(--color-accent-soft)]'
          : 'border-[var(--color-border-strong)] hover:border-[var(--color-accent)] hover:bg-[var(--color-accent-soft)]/40'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED_EXTENSIONS.join(',')}
        multiple
        className="hidden"
        onChange={(e) => e.target.files?.length && handleFiles(e.target.files)}
      />
      <UploadCloud
        size={22}
        className={`transition-colors ${isDragging ? 'text-[var(--color-accent)]' : 'text-[var(--color-ink-faint)] group-hover:text-[var(--color-accent)]'}`}
      />
      {isUploading ? (
        <div className="w-full">
          <p className="text-xs font-medium text-[var(--color-ink)]">Uploading… {progress}%</p>
          <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-border)]">
            <div
              className="h-full rounded-full bg-[var(--color-accent)] transition-all duration-150"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : (
        <>
          <p className="text-xs font-medium text-[var(--color-ink)]">
            Drop a file or <span className="text-[var(--color-accent)]">browse</span>
          </p>
          <p className="text-[11px] text-[var(--color-ink-faint)]">PDF, DOCX, TXT, MD · up to {MAX_SIZE_MB}MB</p>
        </>
      )}
    </div>
  )
}
