"""Internal domain models for chat/conversation state."""
from dataclasses import dataclass, field
from datetime import datetime

from app.models.document import utcnow


@dataclass
class CitationRef:
    # `full_text` is the untruncated chunk content, used to build the LLM's
    # context — NOT the same as `snippet` (a short, truncated preview meant
    # only for citation UI display). Conflating these two was a real bug:
    # every chunk sent to the LLM was silently cut to ~220 characters
    # regardless of CHUNK_SIZE, so any fact appearing after that point in a
    # chunk was invisible to the model even though it had been correctly
    # retrieved.
    document_id: str
    filename: str
    chunk_index: int
    snippet: str
    similarity_score: float
    full_text: str = ""


@dataclass
class ConversationTurn:
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=utcnow)
    citations: list[CitationRef] = field(default_factory=list)