"""Shared/generic Pydantic schemas used across multiple endpoints."""
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned for every 4xx/5xx response."""

    error_code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable error description")
    details: dict = Field(default_factory=dict, description="Optional extra context")


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    app_name: str
    version: str
    llm_provider: str
    embedding_model: str
    documents_indexed: int
