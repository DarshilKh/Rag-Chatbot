"""
Application-wide logging configuration using loguru.

Import `logger` from this module anywhere instead of the stdlib `logging`
module — it's pre-configured with a consistent format and sensible levels
for both development and production.
"""
import io
import sys

from loguru import logger

from app.config import settings


def configure_logging() -> None:
    """Configure loguru sinks. Call once at application startup."""
    logger.remove()  # drop the default handler so we control format/level

    level = "DEBUG" if settings.DEBUG else "INFO"

    # Debug-level logs can include raw document content (see rag/retriever.py
    # and rag/pipeline.py), which may contain non-ASCII characters (currency
    # symbols, accented text, etc.). Classic Windows console hosts often
    # don't default sys.stdout to UTF-8, which would otherwise raise
    # UnicodeEncodeError on every such log line. Wrapping stdout explicitly
    # with UTF-8 + errors="replace" makes this safe on every platform
    # without silently dropping/crashing on the log call itself.
    stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", newline="")

    logger.add(
        stdout,
        level=level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
    )

    if settings.ENVIRONMENT == "production":
        # Also persist logs to a rotating file in production.
        logger.add(
            "logs/app.log",
            level="INFO",
            rotation="10 MB",
            retention="14 days",
            compression="zip",
            encoding="utf-8",
        )


__all__ = ["logger", "configure_logging"]