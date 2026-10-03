"""
Internal domain models for documents.

These are distinct from `app/schemas/document.py`: schemas are the API
contract (what clients see), models are the internal representation used
by services and the RAG pipeline (may carry fields we never expose, like
the on-disk storage path).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DocumentRecord:
    """Full internal record of an uploaded document."""

    id: str
    filename: str
    original_filename: str
    extension: str
    size_bytes: int
    stored_path: str
    uploaded_at: datetime
    chunk_count: int = 0
    status: str = "processing"
    error_message: str | None = None
    summary: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "stored_path": self.stored_path,
            "uploaded_at": self.uploaded_at.isoformat(),
            "chunk_count": self.chunk_count,
            "status": self.status,
            "error_message": self.error_message,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentRecord":
        payload = dict(data)
        payload["uploaded_at"] = datetime.fromisoformat(payload["uploaded_at"])
        return cls(**payload)


@dataclass
class DocumentChunk:
    """A single chunk of a parsed document, ready for embedding."""

    document_id: str
    chunk_index: int
    text: str
    filename: str
    metadata: dict = field(default_factory=dict)

    @property
    def vector_id(self) -> str:
        """Stable, unique identifier for this chunk inside the vector store."""
        return f"{self.document_id}::{self.chunk_index}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
