"""
Custom exception hierarchy.

Using typed exceptions instead of raising HTTPException deep inside services
keeps the service layer framework-agnostic (services shouldn't know about
HTTP status codes). Route handlers catch these and translate them to the
correct HTTP response via the exception handlers registered in main.py.
"""


class AppError(Exception):
    """Base class for all application-specific errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DocumentNotFoundError(AppError):
    status_code = 404
    error_code = "document_not_found"


class UnsupportedFileTypeError(AppError):
    status_code = 415
    error_code = "unsupported_file_type"


class FileTooLargeError(AppError):
    status_code = 413
    error_code = "file_too_large"


class EmptyDocumentError(AppError):
    """Raised when a document contains no extractable text."""

    status_code = 422
    error_code = "empty_document"


class DocumentParsingError(AppError):
    status_code = 422
    error_code = "document_parsing_failed"


class VectorStoreError(AppError):
    status_code = 500
    error_code = "vector_store_error"


class NoDocumentsIndexedError(AppError):
    """Raised when a chat request comes in but no documents have been uploaded."""

    status_code = 400
    error_code = "no_documents_indexed"


class ChatBusyError(AppError):
    """Raised when a second chat request arrives while one is still being
    processed. The app intentionally serializes access to its single shared
    conversation (see chat_service.py) rather than silently interleaving
    concurrent requests and corrupting turn ordering."""

    status_code = 429
    error_code = "chat_busy"


class LLMProviderError(AppError):
    """Raised when the configured LLM provider (Groq/OpenAI) fails or times out."""

    status_code = 502
    error_code = "llm_provider_error"


class InvalidConfigurationError(AppError):
    status_code = 500
    error_code = "invalid_configuration"
