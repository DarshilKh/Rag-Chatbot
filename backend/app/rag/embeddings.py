"""
Embedding model wrapper around Sentence Transformers (via LangChain's
HuggingFaceEmbeddings), shared by both the indexing and retrieval paths.

The model is loaded once per process (lru_cache) since loading it from
disk/HF hub is the single most expensive operation in the whole pipeline —
every request reusing the same instance is what keeps latency reasonable.
"""
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings
from app.core.logging import logger


@lru_cache
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Return a process-wide singleton embeddings model."""
    logger.info(f"Loading embedding model '{settings.EMBEDDING_MODEL}' on {settings.EMBEDDING_DEVICE}...")
    model = HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={"device": settings.EMBEDDING_DEVICE},
        # Normalizing embeddings lets us use cosine similarity cleanly, which
        # is what SIMILARITY_THRESHOLD in .env is calibrated against.
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.info("Embedding model loaded.")
    return model
