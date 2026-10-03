"""Health check endpoint — used by uptime monitors and the frontend's connectivity check."""
from fastapi import APIRouter

from app.config import settings
from app.schemas.common import HealthResponse
from app.services.document_service import document_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    documents_indexed = len(
        [d for d in document_service.list_documents() if d.status == "ready"]
    )
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        llm_provider=settings.LLM_PROVIDER,
        embedding_model=settings.EMBEDDING_MODEL,
        documents_indexed=documents_indexed,
    )
