"""
Document service — orchestrates upload, listing, renaming, and deletion of
documents. This is the only layer that touches both `core.storage` (metadata)
and `rag.pipeline` (indexing); routes never call either directly.
"""
import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.config import settings
from app.core.exceptions import DocumentNotFoundError
from app.core.logging import logger
from app.core.storage import document_store
from app.models.document import DocumentRecord, utcnow
from app.rag import pipeline as rag_pipeline
from app.utils.file_utils import (
    generate_stored_filename,
    read_upload_within_limit,
    sanitize_filename,
    validate_extension,
)


class DocumentService:
    """Business logic for document lifecycle management."""

    def list_documents(self) -> list[DocumentRecord]:
        records = document_store.get_all()
        documents = [DocumentRecord.from_dict(data) for data in records.values()]
        return sorted(documents, key=lambda d: d.uploaded_at, reverse=True)

    def get_document(self, document_id: str) -> DocumentRecord:
        data = document_store.get(document_id)
        if data is None:
            raise DocumentNotFoundError(f"No document found with id '{document_id}'.")
        return DocumentRecord.from_dict(data)

    async def upload_document(self, file: UploadFile) -> DocumentRecord:
        original_filename = sanitize_filename(file.filename or "untitled")
        extension = validate_extension(original_filename)

        # Reads in bounded chunks and aborts as soon as the configured limit
        # is exceeded, instead of buffering an arbitrarily large upload into
        # memory before ever checking its size (see audit finding C3).
        contents = await read_upload_within_limit(file, settings.max_upload_size_bytes)

        document_id = str(uuid.uuid4())
        stored_filename = generate_stored_filename(original_filename)
        stored_path = settings.UPLOAD_DIR / stored_filename

        # Blocking disk I/O — offloaded to a thread so it doesn't stall the
        # event loop (see audit finding C1).
        await run_in_threadpool(_write_file, stored_path, contents)

        record = DocumentRecord(
            id=document_id,
            filename=original_filename,
            original_filename=original_filename,
            extension=extension,
            size_bytes=len(contents),
            stored_path=str(stored_path),
            uploaded_at=utcnow(),
            status="processing",
        )
        document_store.set(document_id, record.to_dict())
        logger.info(f"Stored upload '{original_filename}' ({len(contents)} bytes) as {document_id}")

        # Chunking, embedding, and FAISS indexing are all CPU/IO-bound
        # synchronous work — offloaded to a thread so a large document
        # doesn't block every other concurrent request (audit finding C1).
        await run_in_threadpool(self._index_document, record)
        return record

    def _index_document(self, record: DocumentRecord) -> None:
        """Run the RAG indexing pipeline and persist the resulting status.

        Runs on a worker thread (see upload_document) — synchronous by
        design, do not add `await` here.
        """
        try:
            chunk_count, summary = rag_pipeline.index_document(
                document_id=record.id,
                filename=record.filename,
                file_path=record.stored_path,
                extension=record.extension,
            )
            record.chunk_count = chunk_count
            record.summary = summary
            record.status = "ready"
        except Exception as exc:  # noqa: BLE001 — surfaced via status, not raised
            logger.error(f"Indexing failed for '{record.filename}': {exc}")
            record.status = "failed"
            record.error_message = str(exc)
        finally:
            document_store.set(record.id, record.to_dict())

    def rename_document(self, document_id: str, new_filename: str) -> DocumentRecord:
        record = self.get_document(document_id)
        record.filename = sanitize_filename(new_filename)
        document_store.set(document_id, record.to_dict())
        logger.info(f"Renamed document {document_id} -> '{record.filename}'")
        return record

    def delete_document(self, document_id: str) -> None:
        record = self.get_document(document_id)

        rag_pipeline.remove_document(document_id)

        stored_path = Path(record.stored_path)
        if stored_path.exists():
            stored_path.unlink()

        document_store.delete(document_id)
        logger.info(f"Deleted document {document_id} ('{record.filename}')")


def _write_file(path: Path, contents: bytes) -> None:
    with open(path, "wb") as f:
        f.write(contents)


document_service = DocumentService()
