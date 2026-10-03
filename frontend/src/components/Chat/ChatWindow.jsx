import { useState } from 'react'
import { Trash2, Download, FileUp } from 'lucide-react'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import SuggestedQuestions from './SuggestedQuestions'
import Modal from '../common/Modal'
import Button from '../common/Button'
import Spinner from '../common/Spinner'
import { useChat } from '../../hooks/useChat'
import { useDocuments } from '../../hooks/useDocuments'
import { useToast } from '../../hooks/useToast'
import { downloadConversation } from '../../utils/downloadConversation'

export default function ChatWindow() {
  const { messages, isLoadingHistory, isSending, sendMessage, clearChat } = useChat()
  const { readyDocuments, isLoading: isLoadingDocuments } = useDocuments()
  const { notify } = useToast()
  const [isClearOpen, setIsClearOpen] = useState(false)

  const hasReadyDocuments = readyDocuments.length > 0
  const isBusy = isLoadingHistory || isLoadingDocuments

  const handleClear = async () => {
    try {
      await clearChat()
      setIsClearOpen(false)
      notify('Conversation cleared.', 'success')
    } catch (err) {
      notify(err.message || 'Could not clear the conversation.', 'error')
    }
  }

  const handleDownload = () => {
    downloadConversation(messages)
    notify('Conversation downloaded.', 'success')
  }

  if (isBusy) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner size={22} />
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {messages.length > 0 && (
        <div className="flex items-center justify-end gap-1 border-b border-[var(--color-border)] px-4 py-2">
          <Button variant="ghost" size="sm" onClick={handleDownload}>
            <Download size={13} /> Download
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setIsClearOpen(true)}>
            <Trash2 size={13} /> Clear chat
          </Button>
        </div>
      )}

      {messages.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-accent-soft)] text-[var(--color-accent)]">
            <FileUp size={26} />
          </div>
          {hasReadyDocuments ? (
            <>
              <div>
                <h1 className="text-base font-semibold text-[var(--color-ink)]">Ask away</h1>
                <p className="mt-1 max-w-sm text-sm text-[var(--color-ink-muted)]">
                  {readyDocuments.length} document{readyDocuments.length === 1 ? '' : 's'} indexed
                  and ready. Answers are grounded in their content, with citations back to source.
                </p>
              </div>
              <SuggestedQuestions onSelect={sendMessage} />
            </>
          ) : (
            <div>
              <h1 className="text-base font-semibold text-[var(--color-ink)]">Upload a document to begin</h1>
              <p className="mt-1 max-w-sm text-sm text-[var(--color-ink-muted)]">
                Add a PDF, DOCX, TXT, or Markdown file from the sidebar. Once it's indexed, you can
                ask questions grounded in its content.
              </p>
            </div>
          )}
        </div>
      ) : (
        <MessageList messages={messages} />
      )}

      <ChatInput
        onSend={sendMessage}
        disabled={!hasReadyDocuments || isSending}
        disabledReason={
          hasReadyDocuments ? undefined : 'Upload a document to start chatting…'
        }
      />

      <Modal
        isOpen={isClearOpen}
        onClose={() => setIsClearOpen(false)}
        title="Clear conversation?"
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setIsClearOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" onClick={handleClear}>
              Clear
            </Button>
          </>
        }
      >
        <p className="text-sm text-[var(--color-ink-muted)]">
          This deletes the current conversation history. This can't be undone.
        </p>
      </Modal>
    </div>
  )
}
