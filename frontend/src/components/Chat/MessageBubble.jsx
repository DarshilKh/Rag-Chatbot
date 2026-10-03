import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import PrismLight from 'react-syntax-highlighter/dist/esm/prism-light'
import js from 'react-syntax-highlighter/dist/esm/languages/prism/javascript'
import jsx from 'react-syntax-highlighter/dist/esm/languages/prism/jsx'
import ts from 'react-syntax-highlighter/dist/esm/languages/prism/typescript'
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python'
import bash from 'react-syntax-highlighter/dist/esm/languages/prism/bash'
import json from 'react-syntax-highlighter/dist/esm/languages/prism/json'
import sql from 'react-syntax-highlighter/dist/esm/languages/prism/sql'
import yaml from 'react-syntax-highlighter/dist/esm/languages/prism/yaml'
import markdown from 'react-syntax-highlighter/dist/esm/languages/prism/markdown'
import { oneLight, oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, AlertTriangle } from 'lucide-react'
import { useTheme } from '../../hooks/useTheme'
import { linkifySourceMarkers, parseCitationHref } from '../../utils/citations'
import CitationChip from './CitationChip'
import CitationList from './CitationList'
import TypingIndicator from './TypingIndicator'

PrismLight.registerLanguage('javascript', js)
PrismLight.registerLanguage('jsx', jsx)
PrismLight.registerLanguage('typescript', ts)
PrismLight.registerLanguage('python', python)
PrismLight.registerLanguage('bash', bash)
PrismLight.registerLanguage('json', json)
PrismLight.registerLanguage('sql', sql)
PrismLight.registerLanguage('yaml', yaml)
PrismLight.registerLanguage('markdown', markdown)

function CodeBlock({ className, children }) {
  const { theme } = useTheme()
  const language = /language-(\w+)/.exec(className || '')?.[1]

  if (!language) {
    return (
      <code className="rounded bg-[var(--color-surface-hover)] px-1.5 py-0.5 font-mono text-[13px]">
        {children}
      </code>
    )
  }

  return (
    <PrismLight
      language={language}
      style={theme === 'dark' ? oneDark : oneLight}
      customStyle={{
        borderRadius: '0.5rem',
        fontSize: '13px',
        margin: '0.5rem 0',
        border: '1px solid var(--color-border)',
      }}
    >
      {String(children).replace(/\n$/, '')}
    </PrismLight>
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <button
      onClick={handleCopy}
      aria-label="Copy response"
      className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-[11px] text-[var(--color-ink-faint)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-ink)]"
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  const isError = message.role === 'error'
  const isStreamingEmpty = message.isStreaming && !message.content

  if (isError) {
    return (
      <div className="flex items-start gap-2 rounded-lg border border-[var(--color-danger)]/30 bg-[var(--color-danger-soft)] px-3.5 py-2.5 text-sm text-[var(--color-danger)] animate-fade-in">
        <AlertTriangle size={16} className="mt-0.5 shrink-0" />
        <p>{message.content}</p>
      </div>
    )
  }

  return (
    <div className={`flex animate-fade-in ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`group max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed sm:max-w-[75%] ${
          isUser
            ? 'bg-[var(--color-accent)] text-white rounded-br-sm'
            : 'bg-[var(--color-surface)] text-[var(--color-ink)] rounded-bl-sm border border-[var(--color-border)]'
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : isStreamingEmpty ? (
          <TypingIndicator />
        ) : (
          <>
            <div>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code: ({ className, children }) => (
                    <CodeBlock className={className}>{children}</CodeBlock>
                  ),
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="mb-2 list-disc pl-5 last:mb-0">{children}</ul>,
                  ol: ({ children }) => <ol className="mb-2 list-decimal pl-5 last:mb-0">{children}</ol>,
                  a: ({ children, href }) => {
                    const citationIndex = parseCitationHref(href)
                    if (citationIndex) {
                      return <CitationChip index={citationIndex} citation={message.citations?.[citationIndex - 1]} />
                    }
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[var(--color-accent)] underline underline-offset-2"
                      >
                        {children}
                      </a>
                    )
                  },
                }}
              >
                {linkifySourceMarkers(message.content)}
              </ReactMarkdown>
              {message.isStreaming && (
                <span
                  className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-[var(--color-ink-faint)] align-middle"
                  aria-hidden="true"
                />
              )}
            </div>
            {!message.isStreaming && <CitationList citations={message.citations} />}
            {!message.isStreaming && (
              <div className="mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <CopyButton text={message.content} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
