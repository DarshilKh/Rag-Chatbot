"""Small, stateless helpers for file handling — no business logic here."""
import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError

# Read in bounded chunks rather than a single file.read() — lets us abort as
# soon as the configured size limit is exceeded instead of buffering an
# arbitrarily large upload into memory/disk first (audit finding C3).
_READ_CHUNK_SIZE = 1024 * 1024  # 1MB


def validate_extension(filename: str) -> str:
    """Return the lowercase extension if allowed, else raise."""
    extension = Path(filename).suffix.lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension or 'unknown'}'. Allowed types: {allowed}"
        )
    return extension


async def read_upload_within_limit(file: UploadFile, max_bytes: int) -> bytes:
    """
    Read an UploadFile in bounded chunks, raising as soon as `max_bytes` is
    exceeded rather than reading the entire body first and checking after.

    This matters even behind nginx (which enforces its own, separately
    configured `client_max_body_size`) because the backend can also be hit
    directly — docker-compose exposes it on its own port — where no such
    upfront limit exists otherwise.
    """
    total = 0
    chunks: list[bytes] = []
    while True:
        chunk = await file.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FileTooLargeError(
                f"File exceeds the {max_bytes // (1024 * 1024)}MB limit."
            )
        chunks.append(chunk)

    if total == 0:
        raise UnsupportedFileTypeError("Uploaded file is empty.")

    return b"".join(chunks)


def sanitize_filename(filename: str) -> str:
    """Strip path components and unsafe characters, keep it human-readable."""
    name = Path(filename).name
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name.strip() or "untitled"


def generate_stored_filename(original_filename: str) -> str:
    """Prefix with a short UUID so re-uploads of the same filename never collide on disk."""
    safe_name = sanitize_filename(original_filename)
    unique_prefix = uuid.uuid4().hex[:8]
    return f"{unique_prefix}_{safe_name}"


def format_size(size_bytes: int) -> str:
    """Human-readable file size, e.g. 1536000 -> '1.5 MB'."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
