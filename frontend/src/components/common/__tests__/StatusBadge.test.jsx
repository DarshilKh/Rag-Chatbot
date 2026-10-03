import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusBadge from '../StatusBadge'

describe('StatusBadge', () => {
  it('renders "Ready" for a ready document', () => {
    render(<StatusBadge status="ready" />)
    expect(screen.getByText('Ready')).toBeInTheDocument()
  })

  it('renders "Processing" for a processing document', () => {
    render(<StatusBadge status="processing" />)
    expect(screen.getByText('Processing')).toBeInTheDocument()
  })

  it('renders "Failed" for a failed document', () => {
    render(<StatusBadge status="failed" />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('falls back to "Processing" for an unrecognized status', () => {
    render(<StatusBadge status="something-unexpected" />)
    expect(screen.getByText('Processing')).toBeInTheDocument()
  })
})
