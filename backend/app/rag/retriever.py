"""
Retrieval layer: wraps VectorStoreManager.similarity_search with the
configured TOP_K / SIMILARITY_THRESHOLD, and converts raw FAISS results
into CitationRef objects ready to attach to a chat response.
"""
from app.core.logging import logger
from app.models.chat import CitationRef
from app.rag.vectorstore import get_vector_store_manager
from app.utils.text_utils import make_snippet

# Above this word-overlap ratio, a lower-ranked chunk is treated as a
# near-duplicate of a higher-ranked one already kept, and dropped — this
# happens naturally with CHUNK_OVERLAP (adjacent chunks sharing text) and
# when the same content exists in more than one uploaded document. Kept
# conservative (0.75) so genuinely distinct-but-adjacent chunks, which
# share only their overlap region and are otherwise different, aren't
# accidentally dropped.
_DUPLICATE_OVERLAP_THRESHOLD = 0.75


def _word_overlap_ratio(text_a: str, text_b: str) -> float:
    """Cheap (no embeddings, no extra model call) duplicate-content check:
    fraction of the smaller text's words that also appear in the other."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / min(len(words_a), len(words_b))


def _deduplicate(citations: list[CitationRef]) -> list[CitationRef]:
    """Drop citations that substantially overlap a higher-ranked citation
    already kept. Assumes citations are pre-sorted by relevance (highest
    first) — always keeps the higher-scoring one of any duplicate pair."""
    kept: list[CitationRef] = []
    for citation in citations:
        if any(
            _word_overlap_ratio(citation.full_text, k.full_text) >= _DUPLICATE_OVERLAP_THRESHOLD
            for k in kept
        ):
            continue
        kept.append(citation)
    return kept


def retrieve_relevant_chunks(
    query: str,
    top_k: int,
    similarity_threshold: float,
    document_ids: list[str] | None = None,
) -> list[CitationRef]:
    """
    Run semantic search and return citation-ready results above the
    configured similarity threshold, most relevant first, with
    near-duplicate chunks removed.
    """
    vsm = get_vector_store_manager()
    results = vsm.similarity_search(query, top_k=top_k, document_ids=document_ids)

    logger.debug(
        f"RETRIEVAL query={query!r} top_k={top_k} threshold={similarity_threshold} "
        f"document_ids={document_ids} -> {len(results)} raw candidate(s) before threshold filtering"
    )
    for document, score in results:
        kept = score >= similarity_threshold
        logger.debug(
            f"  candidate doc={document.metadata.get('document_id')} "
            f"chunk={document.metadata.get('chunk_index')} score={score:.4f} "
            f"{'KEPT' if kept else 'DROPPED (below threshold)'} "
            f"text={document.page_content[:120]!r}..."
        )

    citations: list[CitationRef] = []
    for document, score in results:
        if score < similarity_threshold:
            continue
        citations.append(
            CitationRef(
                document_id=document.metadata.get("document_id", "unknown"),
                filename=document.metadata.get("filename", "unknown"),
                chunk_index=document.metadata.get("chunk_index", -1),
                snippet=make_snippet(document.page_content),
                similarity_score=round(float(score), 4),
                full_text=document.page_content,
            )
        )

    # vsm.similarity_search already returns results sorted by cosine
    # similarity descending, but re-sort defensively since we filtered.
    citations.sort(key=lambda c: c.similarity_score, reverse=True)

    before_dedup = len(citations)
    citations = _deduplicate(citations)
    if len(citations) < before_dedup:
        logger.debug(
            f"RETRIEVAL deduplication: dropped {before_dedup - len(citations)} "
            f"near-duplicate chunk(s) (>{_DUPLICATE_OVERLAP_THRESHOLD:.0%} word overlap "
            "with a higher-ranked chunk already kept)"
        )

    logger.debug(f"RETRIEVAL final: {len(citations)} chunk(s) passed to the LLM as context")

    return citations