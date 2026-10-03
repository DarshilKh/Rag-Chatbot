import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ChatInput from '../ChatInput'

describe('ChatInput', () => {
  it('sends the trimmed message on Enter', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} disabled={false} />)

    const textarea = screen.getByLabelText('Chat message')
    fireEvent.change(textarea, { target: { value: '  What is this document about?  ' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })

    expect(onSend).toHaveBeenCalledWith('What is this document about?')
  })

  it('does not send on Shift+Enter (allows a newline instead)', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} disabled={false} />)

    const textarea = screen.getByLabelText('Chat message')
    fireEvent.change(textarea, { target: { value: 'line one' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })

    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not send an empty/whitespace-only message', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} disabled={false} />)

    const textarea = screen.getByLabelText('Chat message')
    fireEvent.change(textarea, { target: { value: '   ' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })

    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not send while disabled', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} disabled={true} disabledReason="Upload a document first" />)

    const textarea = screen.getByLabelText('Chat message')
    fireEvent.change(textarea, { target: { value: 'hello' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })

    expect(onSend).not.toHaveBeenCalled()
  })

  it('clears the input after sending', () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} disabled={false} />)

    const textarea = screen.getByLabelText('Chat message')
    fireEvent.change(textarea, { target: { value: 'hello' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })

    expect(textarea.value).toBe('')
  })
})
