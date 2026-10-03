"""
Lightweight JSON-backed metadata storage.

This app deliberately doesn't pull in a full SQL database — FAISS already
holds the vectors, and document *metadata* (filename, size, upload date,
chunk count...) is small, simple, and read far more than it's written. A
JSON file behind a small repository class keeps things simple without
sacrificing a clean interface; swapping this for SQLite/Postgres later only
means rewriting this one file.
"""
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.logging import logger

_lock = threading.Lock()


class JSONMetadataStore:
    """A minimal, thread-safe key-value JSON store for document metadata."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        if not self.file_path.exists():
            self._write({})

    def _read(self) -> dict[str, Any]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # A corrupt/truncated file here previously meant silently losing
            # every document record with only a warning logged — atomic
            # writes (below) are what actually prevent this file from ever
            # being left in a truncated state, but this log is upgraded to
            # make it unmissable if it ever does happen (audit finding M2).
            logger.error(
                f"Metadata file {self.file_path} is missing or corrupt — "
                "reinitializing as empty. Any document records in it are lost "
                "(the underlying uploaded files and FAISS index are unaffected)."
            )
            return {}

    def _write(self, data: dict[str, Any]) -> None:
        """Write atomically: to a temp file in the same directory, then
        rename into place. `os.replace` is atomic on POSIX and Windows, so a
        crash or kill mid-write can never leave `file_path` truncated or
        partially written — the old file stays intact until the new one is
        fully written (audit finding M2)."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=self.file_path.parent, prefix=f".{self.file_path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.file_path)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    def get_all(self) -> dict[str, Any]:
        with _lock:
            return self._read()

    def get(self, key: str) -> dict[str, Any] | None:
        with _lock:
            return self._read().get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        with _lock:
            data = self._read()
            data[key] = value
            self._write(data)

    def delete(self, key: str) -> bool:
        with _lock:
            data = self._read()
            if key not in data:
                return False
            del data[key]
            self._write(data)
            return True

    def clear(self) -> None:
        with _lock:
            self._write({})


document_store = JSONMetadataStore(settings.METADATA_DIR / "documents.json")
