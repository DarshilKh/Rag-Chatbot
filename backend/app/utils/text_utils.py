"""Small, stateless text-processing helpers shared across the RAG pipeline."""
import re


def clean_whitespace(text: str) -> str:
    """Collapse repeated blank lines/spaces produced by PDF/DOCX extraction artifacts."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_snippet(text: str, max_length: int = 220) -> str:
    """Produce a short, citation-friendly excerpt from a chunk of text."""
    cleaned = clean_whitespace(text).replace("\n", " ")
    if len(cleaned) <= max_length:
        return cleaned
    truncated = cleaned[:max_length].rsplit(" ", 1)[0]
    return f"{truncated}…"


def word_count(text: str) -> int:
    return len(text.split())
