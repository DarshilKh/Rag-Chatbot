"""Routes for document upload, listing, renaming, and deletion."""
from fastapi import APIRouter, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.schemas.common import ErrorResponse
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentRenameRequest,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

_error_responses = {
    404: {"model": ErrorResponse, "description": "Document not found"},
    413: {"model": ErrorResponse, "description": "File exceeds MAX_UPLOAD_SIZE_MB"},
    415: {"model": ErrorResponse, "description": "Unsupported file type or empty file"},
    422: {"model": ErrorResponse, "description": "Validation error (parsing failed, empty document, or invalid rename)"},
}


def _to_response(record) -> DocumentResponse:
    return DocumentResponse(
        id=record.id,
        filename=record.filename,
        original_filename=record.original_filename,
        extension=record.extension,
        size_bytes=record.size_bytes,
        uploaded_at=record.uploaded_at,
        chunk_count=record.chunk_count,
        status=record.status,
        error_message=record.error_message,
        summary=record.summary,
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={413: _error_responses[413], 415: _error_responses[415], 422: _error_responses[422]},
)
async def upload_document(file: UploadFile) -> DocumentUploadResponse:
    record = await document_service.upload_document(file)
    return DocumentUploadResponse(document=_to_response(record))


@router.get("", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    records = document_service.list_documents()
    return DocumentListResponse(
        documents=[_to_response(r) for r in records],
        total=len(records),
    )


@router.get("/{document_id}", response_model=DocumentResponse, responses={404: _error_responses[404]})
async def get_document(document_id: str) -> DocumentResponse:
    record = document_service.get_document(document_id)
    return _to_response(record)


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={404: _error_responses[404], 422: _error_responses[422]},
)
async def rename_document(document_id: str, payload: DocumentRenameRequest) -> DocumentResponse:
    record = document_service.rename_document(document_id, payload.new_filename)
    return _to_response(record)


@router.delete("/{document_id}", response_model=DocumentDeleteResponse, responses={404: _error_responses[404]})
async def delete_document(document_id: str) -> DocumentDeleteResponse:
    # Deletion triggers a FAISS index rewrite (save_local), which scales
    # with total index size and is blocking I/O/CPU work — offloaded so it
    # doesn't stall other concurrent requests (audit finding C1).
    await run_in_threadpool(document_service.delete_document, document_id)
    return DocumentDeleteResponse(id=document_id)
