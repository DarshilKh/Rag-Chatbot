/**
 * Rewrites literal "[Source N]" references (which the backend's system
 * prompt instructs the LLM to emit) into markdown link syntax pointing at
 * a `#citation-N` anchor. MessageBubble's custom `a` renderer intercepts
 * that anchor pattern and swaps in a real, clickable CitationChip —
 * turning a citation from something the model *says* into something the
 * reader can actually inspect.
 */
export function linkifySourceMarkers(text) {
  return text.replace(/\[Source (\d+)\]/gi, (_, num) => `[Source ${num}](#citation-${num})`)
}

/** Extracts the 1-based citation index from a chip anchor href, or null if it doesn't match. */
export function parseCitationHref(href) {
  const match = /^#citation-(\d+)$/.exec(href || '')
  return match ? Number(match[1]) : null
}
