export function downloadConversation(messages) {
  const lines = messages
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => {
      const speaker = m.role === 'user' ? 'You' : 'Assistant'
      const citationLines = (m.citations || [])
        .map((c) => `  Source: ${c.filename} (chunk ${c.chunk_index}, similarity ${c.similarity_score})`)
        .join('\n')
      return `${speaker}:\n${m.content}${citationLines ? `\n${citationLines}` : ''}`
    })

  const content = lines.join('\n\n---\n\n')
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `conversation-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
