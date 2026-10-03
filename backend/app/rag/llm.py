"""
LLM client factory: returns a LangChain chat model for whichever provider
is configured (Groq by default, OpenAI as a drop-in swap).

Switching providers is a single .env change (LLM_PROVIDER=groq|openai) —
no code changes needed anywhere else in the app, since both LangChain chat
model classes implement the same .invoke()/.stream() interface.
"""
from functools import lru_cache

from app.config import settings
from app.core.exceptions import InvalidConfigurationError


@lru_cache
def _get_groq_model(streaming: bool):
    from langchain_groq import ChatGroq

    if not settings.GROQ_API_KEY:
        raise InvalidConfigurationError(
            "GROQ_API_KEY is not set. Add it to backend/.env — "
            "get a free key at https://console.groq.com/keys"
        )
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        streaming=streaming,
    )


@lru_cache
def _get_openai_model(streaming: bool):
    from langchain_openai import ChatOpenAI

    if not settings.OPENAI_API_KEY:
        raise InvalidConfigurationError(
            "OPENAI_API_KEY is not set. Add it to backend/.env, or switch "
            "LLM_PROVIDER back to 'groq'."
        )
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        streaming=streaming,
    )


def get_chat_model(streaming: bool = False):
    """Return a LangChain chat model instance for settings.LLM_PROVIDER."""
    if settings.LLM_PROVIDER == "groq":
        return _get_groq_model(streaming)
    if settings.LLM_PROVIDER == "openai":
        return _get_openai_model(streaming)
    raise InvalidConfigurationError(
        f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'. Must be 'groq' or 'openai'."
    )
