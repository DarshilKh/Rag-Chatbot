"""Request/response contracts for the /documents and /upload endpoints."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentResponse(BaseModel):
    """Public representation of an uploaded document, shown in the sidebar."""

    id: str
    filename: str = Field(..., description="Current display name (may have been renamed)")
    original_filename: str = Field(..., description="Name of the file as originally uploaded")
    extension: str
    size_bytes: int
    uploaded_at: datetime
    chunk_count: int = 0
    status: DocumentStatus = DocumentStatus.PROCESSING
    error_message: str | None = None
    summary: str | None = Field(
        default=None, description="Short auto-generated summary of the document"
    )

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str = "Document uploaded and indexed successfully."


class DocumentRenameRequest(BaseModel):
    new_filename: str = Field(..., min_length=1, max_length=255)

    @field_validator("new_filename")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Filename cannot be empty.")
        forbidden = set('/\\:*?"<>|')
        if any(ch in forbidden for ch in value):
            raise ValueError(r'Filename cannot contain any of: / \ : * ? " < > |')
        return value


class DocumentDeleteResponse(BaseModel):
    id: str
    message: str = "Document deleted successfully."
