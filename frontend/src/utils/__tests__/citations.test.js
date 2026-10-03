import { describe, it, expect } from 'vitest'
import { linkifySourceMarkers, parseCitationHref } from '../citations'

describe('linkifySourceMarkers', () => {
  it('converts a single source marker into a markdown link', () => {
    const result = linkifySourceMarkers('We use PostgreSQL [Source 1].')
    expect(result).toBe('We use PostgreSQL [Source 1](#citation-1).')
  })

  it('converts multiple distinct source markers', () => {
    const result = linkifySourceMarkers('A [Source 1] and B [Source 2].')
    expect(result).toContain('[Source 1](#citation-1)')
    expect(result).toContain('[Source 2](#citation-2)')
  })

  it('is case-insensitive, normalizing to "Source" in the output', () => {
    const result = linkifySourceMarkers('See [source 3] for details.')
    expect(result).toBe('See [Source 3](#citation-3) for details.')
  })

  it('leaves text with no source markers unchanged', () => {
    const text = 'This has no citations at all.'
    expect(linkifySourceMarkers(text)).toBe(text)
  })

  it('handles repeated references to the same source', () => {
    const result = linkifySourceMarkers('[Source 1] ... and again [Source 1].')
    expect(result).toBe('[Source 1](#citation-1) ... and again [Source 1](#citation-1).')
  })
})

describe('parseCitationHref', () => {
  it('extracts the numeric index from a citation anchor', () => {
    expect(parseCitationHref('#citation-1')).toBe(1)
    expect(parseCitationHref('#citation-42')).toBe(42)
  })

  it('returns null for non-citation hrefs', () => {
    expect(parseCitationHref('https://example.com')).toBe(null)
    expect(parseCitationHref('#some-other-anchor')).toBe(null)
  })

  it('returns null for missing/empty href', () => {
    expect(parseCitationHref(undefined)).toBe(null)
    expect(parseCitationHref('')).toBe(null)
  })
})
