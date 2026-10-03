"""
Centralized application configuration.

All environment-driven settings live here. Every other module should import
`settings` from this file instead of reading `os.environ` directly — this
keeps configuration a single source of truth and makes testing/overriding
trivial.
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = backend/
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings, populated from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    APP_NAME: str = "Document Chat RAG API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DEBUG: bool = True

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        """Allow CORS_ORIGINS to be set in .env as a plain comma-separated
        string (e.g. `CORS_ORIGINS=https://app.com,https://admin.app.com`)
        instead of requiring JSON-list syntax — much easier to set correctly
        in deployment dashboards like Render/Railway/Vercel."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # ------------------------------------------------------------------
    # LLM Provider (Groq by default, OpenAI as a drop-in alternative)
    # ------------------------------------------------------------------
    LLM_PROVIDER: Literal["groq", "openai"] = "groq"

    GROQ_API_KEY: str = ""
    # llama-3.3-70b-versatile was deprecated by Groq on 2026-06-17; this is
    # their recommended current replacement. Override via .env if it changes.
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 1024
    LLM_STREAMING: bool = True

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # ------------------------------------------------------------------
    # RAG / Chunking / Retrieval (all configurable, per spec)
    # ------------------------------------------------------------------
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.2  # cosine similarity, 0..1 (higher = stricter)

    # ------------------------------------------------------------------
    # Uploads
    # ------------------------------------------------------------------
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".md"]

    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    VECTORSTORE_DIR: Path = BASE_DIR / "data" / "vectorstore"
    METADATA_DIR: Path = BASE_DIR / "data" / "metadata"

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------
    MAX_CHAT_HISTORY_TURNS: int = 10

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create all runtime data directories if they don't exist yet."""
        for directory in (self.UPLOAD_DIR, self.VECTORSTORE_DIR, self.METADATA_DIR):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — settings are read once per process."""
    settings = Settings()
    settings.ensure_directories()
    return settings


settings = get_settings()
