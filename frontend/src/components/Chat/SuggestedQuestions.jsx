import { Sparkles } from 'lucide-react'

// Static, sensible-default question starters. A backend-generated variant
// (tailored to actual document content) can replace this via GET
// /chat/suggested-questions without changing this component's contract.
const DEFAULT_QUESTIONS = [
  'What are the main topics covered in these documents?',
  'Summarize the key points in a few bullets.',
  'Are there any dates, numbers, or deadlines I should know about?',
]

export default function SuggestedQuestions({ onSelect }) {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center gap-3 px-4">
      <div className="flex items-center gap-1.5 text-xs font-medium text-[var(--color-ink-faint)]">
        <Sparkles size={13} />
        Try asking
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {DEFAULT_QUESTIONS.map((question) => (
          <button
            key={question}
            onClick={() => onSelect(question)}
            className="rounded-full border border-[var(--color-border)] bg-[var(--color-canvas)] px-3.5 py-1.5 text-xs text-[var(--color-ink-muted)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
