"""
Text chunking: splits extracted document text into overlapping chunks
suitable for embedding, using LangChain's RecursiveCharacterTextSplitter.

Recursive splitting tries paragraph breaks first, then sentences, then
words, then characters — it only falls back to a harder split point when
a chunk doesn't fit within `chunk_size` any other way, which keeps chunks
semantically coherent far more often than a naive fixed-width split.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.document import DocumentChunk


def split_into_chunks(
    text: str,
    document_id: str,
    filename: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    """
    Split raw document text into overlapping DocumentChunk objects.

    Returns:
        Ordered list of DocumentChunk objects (chunk_index starts at 0).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    raw_chunks = splitter.split_text(text)

    return [
        DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            text=chunk_text,
            filename=filename,
        )
        for index, chunk_text in enumerate(raw_chunks)
        if chunk_text.strip()
    ]
