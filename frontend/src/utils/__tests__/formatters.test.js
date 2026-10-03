import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatFileSize, formatRelativeDate, truncate } from '../formatters'

describe('formatFileSize', () => {
  it('formats zero bytes', () => {
    expect(formatFileSize(0)).toBe('0 B')
  })

  it('formats bytes without decimals', () => {
    expect(formatFileSize(512)).toBe('512 B')
  })

  it('formats kilobytes with one decimal', () => {
    expect(formatFileSize(1536)).toBe('1.5 KB')
  })

  it('formats megabytes', () => {
    expect(formatFileSize(5 * 1024 * 1024)).toBe('5.0 MB')
  })
})

describe('formatRelativeDate', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-31T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows "just now" for very recent timestamps', () => {
    expect(formatRelativeDate('2026-07-31T11:59:45Z')).toBe('just now')
  })

  it('shows minutes ago', () => {
    expect(formatRelativeDate('2026-07-31T11:45:00Z')).toBe('15m ago')
  })

  it('shows hours ago', () => {
    expect(formatRelativeDate('2026-07-31T09:00:00Z')).toBe('3h ago')
  })

  it('shows days ago', () => {
    expect(formatRelativeDate('2026-07-28T12:00:00Z')).toBe('3d ago')
  })

  it('falls back to a full date for anything older than a week', () => {
    const result = formatRelativeDate('2026-01-01T12:00:00Z')
    expect(result).toMatch(/2026/)
    expect(result).not.toMatch(/ago/)
  })
})

describe('truncate', () => {
  it('returns short text unchanged', () => {
    expect(truncate('short text', 60)).toBe('short text')
  })

  it('truncates long text with an ellipsis', () => {
    const long = 'a'.repeat(100)
    const result = truncate(long, 60)
    expect(result.length).toBeLessThanOrEqual(61)
    expect(result.endsWith('…')).toBe(true)
  })

  it('passes through null/undefined unchanged', () => {
    expect(truncate(null)).toBe(null)
    expect(truncate(undefined)).toBe(undefined)
  })
})
