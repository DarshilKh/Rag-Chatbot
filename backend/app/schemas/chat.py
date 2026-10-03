"""Request/response contracts for the /chat endpoints."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Citation(BaseModel):
    """A single source citation backing (part of) an answer."""

    document_id: str
    filename: str
    chunk_index: int = Field(..., description="0-based index of the chunk within the document")
    snippet: str = Field(..., description="Short excerpt of the cited chunk")
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    citations: list[Citation] = Field(default_factory=list)
    timestamp: datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    document_ids: list[str] | None = Field(
        default=None,
        description="Restrict retrieval to these document IDs. Omit to search all documents.",
    )
    top_k: int | None = Field(default=None, ge=1, le=20)


class ChatResponse(BaseModel):
    message: str
    citations: list[Citation] = Field(default_factory=list)
    conversation_length: int = Field(..., description="Number of turns in the conversation so far")


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]


class ClearChatResponse(BaseModel):
    message: str = "Conversation cleared."


class SuggestedQuestionsResponse(BaseModel):
    questions: list[str]
