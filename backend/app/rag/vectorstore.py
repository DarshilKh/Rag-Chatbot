"""
FAISS vector store management: create, load, persist, add chunks, delete
by document ID, and run similarity search.

Design notes:
- The index is created lazily on the first document upload (an empty FAISS
  index isn't meaningfully constructible without at least one vector), then
  persisted to disk and reloaded on every process restart.
- A small sidecar JSON file (`id_map.json`) tracks which FAISS-internal
  vector IDs belong to which document, so deleting a document only removes
  its own chunks rather than requiring a full index rebuild from scratch.
- Similarity scoring: we deliberately do NOT use LangChain's
  `similarity_search_with_relevance_scores` / `DistanceStrategy.COSINE`.
  In the installed langchain-community version, `DistanceStrategy.COSINE`
  silently falls back to a plain `IndexFlatL2` index (see its own comment,
  "currently other metric types not initialized"), and the paired
  `_cosine_relevance_score_fn` treats the raw *squared* L2 distance FAISS
  returns as if it were a bounded cosine distance — the resulting "score"
  is actually `2*cos_sim - 1`, which is unbounded below and would silently
  miscalibrate SIMILARITY_THRESHOLD. Since embeddings are L2-normalized
  (see rag/embeddings.py), squared L2 distance relates to cosine similarity
  exactly: `cos_sim = 1 - squared_L2_distance / 2`. We use
  `similarity_search_with_score` (raw distance) and apply that formula
  ourselves, which is correct and version-independent.
"""
import json
import threading
from functools import lru_cache
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import settings
from app.core.exceptions import VectorStoreError
from app.core.logging import logger
from app.models.document import DocumentChunk
import app.rag.embeddings as embeddings_module

_lock = threading.Lock()


def _squared_l2_to_cosine_similarity(squared_l2_distance: float) -> float:
    """Exact for unit-normalized embeddings: ||a-b||^2 = 2 - 2*cos_sim."""
    cos_sim = 1.0 - (squared_l2_distance / 2.0)
    return max(-1.0, min(1.0, cos_sim))  # clamp for float rounding at the extremes


class VectorStoreManager:
    """Owns the on-disk FAISS index and exposes a small, typed interface over it."""

    def __init__(self):
        self.index_dir = settings.VECTORSTORE_DIR / "faiss_index"
        self.id_map_path = settings.VECTORSTORE_DIR / "id_map.json"
        self.embeddings = embeddings_module.get_embedding_model()
        self._store: FAISS | None = None
        self._id_map: dict[str, list[str]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self.index_dir.exists() and any(self.index_dir.iterdir()):
            try:
                self._store = FAISS.load_local(
                    str(self.index_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info(f"Loaded existing FAISS index from {self.index_dir}")
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to load FAISS index, starting fresh: {exc}")
                self._store = None

        if self.id_map_path.exists():
            try:
                self._id_map = json.loads(self.id_map_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self._id_map = {}

    def persist(self) -> None:
        if self._store is not None:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            self._store.save_local(str(self.index_dir))
        self.id_map_path.write_text(json.dumps(self._id_map, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return

        texts = [c.text for c in chunks]
        metadatas = [
            {"document_id": c.document_id, "chunk_index": c.chunk_index, "filename": c.filename}
            for c in chunks
        ]
        document_id = chunks[0].document_id

        with _lock:
            try:
                if self._store is None:
                    self._store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
                    new_ids = list(self._store.index_to_docstore_id.values())
                else:
                    new_ids = self._store.add_texts(texts, metadatas=metadatas)
            except Exception as exc:  # noqa: BLE001
                raise VectorStoreError(f"Failed to add document to vector store: {exc}") from exc

            self._id_map[document_id] = list(new_ids)
            self.persist()

        logger.info(f"Indexed {len(chunks)} chunks for document {document_id}")

    def delete_document(self, document_id: str) -> None:
        with _lock:
            ids = self._id_map.pop(document_id, [])
            if ids and self._store is not None:
                try:
                    self._store.delete(ids)
                except Exception as exc:  # noqa: BLE001
                    raise VectorStoreError(f"Failed to remove document from vector store: {exc}") from exc
            self.persist()
        logger.info(f"Removed {len(ids)} chunks for document {document_id} from vector store")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def similarity_search(
        self,
        query: str,
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[tuple[Document, float]]:
        """Returns (Document, cosine_similarity) pairs, unfiltered by threshold,
        sorted most-similar first. cosine_similarity is in [-1, 1] (in practice
        close to [0, 1] for genuinely related text)."""
        if self._store is None:
            return []

        filter_fn = None
        fetch_k = 20  # langchain-community's own default
        if document_ids:
            allowed = set(document_ids)
            filter_fn = lambda metadata: metadata.get("document_id") in allowed  # noqa: E731

            # `similarity_search_with_score(..., filter=...)` fetches the top
            # `fetch_k` nearest neighbors *globally first*, then filters —
            # it does not filter before searching. With the default
            # fetch_k=20, a `document_ids`-scoped query can silently return
            # fewer results than requested (or none) once the index holds
            # more than ~20 chunks across other documents, even when the
            # targeted document clearly contains relevant content. Widening
            # fetch_k to the full index size when filtering is active makes
            # the filter actually consider every candidate (audit finding C2).
            fetch_k = max(fetch_k, self._store.index.ntotal)

        try:
            raw_results = self._store.similarity_search_with_score(
                query, k=top_k, filter=filter_fn, fetch_k=fetch_k
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Similarity search failed: {exc}") from exc

        return [
            (doc, _squared_l2_to_cosine_similarity(distance)) for doc, distance in raw_results
        ]

    @property
    def is_empty(self) -> bool:
        return self._store is None

    def get_all_chunks(self, document_ids: list[str] | None = None) -> list[Document]:
        """
        Return every chunk currently indexed, optionally scoped to specific
        document_ids, ordered by (document_id, chunk_index).

        Used for non-similarity-based context building — e.g. "summarize
        this document" — where semantic search over a narrow query
        embedding is the wrong tool: the reader wants the whole document,
        not whichever chunks happen to embed close to the literal words
        "summarize the key points."
        """
        if self._store is None:
            return []

        if document_ids:
            vector_ids: list[str] = []
            for doc_id in document_ids:
                vector_ids.extend(self._id_map.get(doc_id, []))
        else:
            vector_ids = list(self._store.index_to_docstore_id.values())

        documents = []
        for vector_id in vector_ids:
            doc = self._store.docstore.search(vector_id)
            if isinstance(doc, Document):  # docstore.search returns a str on a miss
                documents.append(doc)

        documents.sort(
            key=lambda d: (d.metadata.get("document_id", ""), d.metadata.get("chunk_index", 0))
        )
        return documents


@lru_cache
def get_vector_store_manager() -> VectorStoreManager:
    """Process-wide singleton — FAISS index + embeddings model loaded once."""
    return VectorStoreManager()