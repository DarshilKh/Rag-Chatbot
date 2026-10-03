"""Unit tests for the RAG internals directly — loader, chunker, vectorstore,
and retriever — independent of the HTTP layer."""
from pathlib import Path

import pytest

from app.core.exceptions import DocumentParsingError, EmptyDocumentError
from app.models.document import DocumentChunk
from app.rag.chunker import split_into_chunks
from app.rag.loader import load_document_text
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.vectorstore import get_vector_store_manager


class TestLoader:
    def test_loads_markdown(self, sample_md_path):
        text = load_document_text(sample_md_path, ".md")
        assert "PostgreSQL" in text

    def test_loads_docx_including_paragraphs(self, sample_docx_path):
        text = load_document_text(sample_docx_path, ".docx")
        assert "Project Phoenix" in text

    def test_loads_txt(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("Plain text content here.")
        text = load_document_text(path, ".txt")
        assert text == "Plain text content here."

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(DocumentParsingError):
            load_document_text(tmp_path / "nope.txt", ".txt")

    def test_raises_on_empty_extracted_text(self, tmp_path):
        path = tmp_path / "empty.txt"
        path.write_text("   \n\n   ")
        with pytest.raises(EmptyDocumentError):
            load_document_text(path, ".txt")


class TestChunker:
    def test_splits_long_text_into_multiple_chunks(self):
        text = "Sentence one. " * 100
        chunks = split_into_chunks(text, "doc1", "file.txt", chunk_size=100, chunk_overlap=20)

        assert len(chunks) > 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert [c.chunk_index for c in chunks] == list(range(len(chunks)))

    def test_short_text_produces_single_chunk(self):
        chunks = split_into_chunks("Short text.", "doc1", "file.txt", chunk_size=1000, chunk_overlap=100)
        assert len(chunks) == 1
        assert chunks[0].text == "Short text."

    def test_chunk_vector_id_is_stable_and_unique(self):
        chunks = split_into_chunks("A. " * 200, "doc1", "file.txt", chunk_size=50, chunk_overlap=5)
        vector_ids = [c.vector_id for c in chunks]
        assert len(vector_ids) == len(set(vector_ids))  # all unique
        assert vector_ids[0] == "doc1::0"


class TestVectorStore:
    def test_add_and_search_returns_relevant_chunk_first(self):
        vsm = get_vector_store_manager()
        vsm.add_chunks(
            [
                DocumentChunk(document_id="d1", chunk_index=0, text="PostgreSQL billing database transactions", filename="a.md"),
                DocumentChunk(document_id="d1", chunk_index=1, text="company picnic scheduled August", filename="a.md"),
            ]
        )

        results = vsm.similarity_search("billing database", top_k=2)

        assert len(results) == 2
        assert results[0][0].page_content.startswith("PostgreSQL")
        assert 0.0 <= results[0][1] <= 1.0
        assert results[0][1] > results[1][1]

    def test_persists_across_manager_instances(self):
        vsm = get_vector_store_manager()
        vsm.add_chunks([DocumentChunk(document_id="d1", chunk_index=0, text="persisted content", filename="a.md")])

        get_vector_store_manager.cache_clear()
        reloaded = get_vector_store_manager()

        assert not reloaded.is_empty
        results = reloaded.similarity_search("persisted", top_k=1)
        assert len(results) == 1

    def test_filters_by_document_id(self):
        vsm = get_vector_store_manager()
        vsm.add_chunks([DocumentChunk(document_id="d1", chunk_index=0, text="alpha content here", filename="a.md")])
        vsm.add_chunks([DocumentChunk(document_id="d2", chunk_index=0, text="beta content here", filename="b.md")])

        results = vsm.similarity_search("content", top_k=5, document_ids=["d1"])

        assert len(results) == 1
        assert results[0][0].metadata["document_id"] == "d1"

    def test_document_id_filter_finds_target_beyond_default_fetch_k(self):
        """Regression test for audit finding C2: langchain-community's FAISS
        filter fetches the top `fetch_k` (default 20) nearest neighbors
        *globally first*, then filters — so a targeted document's chunk that
        doesn't happen to rank in the unfiltered top-20 was previously
        invisible to a document_ids-scoped search, even when it's clearly
        the most relevant chunk *within* that document. This indexes 25
        decoy chunks that all closely match the query (guaranteeing they
        fill the default top-20) plus one target chunk, from a different
        document, that shares only one word with the query — low enough to
        rank outside the top 20 globally, but it must still be found once
        filtered to its own document.
        """
        vsm = get_vector_store_manager()

        for i in range(25):
            vsm.add_chunks(
                [
                    DocumentChunk(
                        document_id=f"decoy-{i}",
                        chunk_index=0,
                        text="quarterly revenue growth quarterly revenue metrics quarterly",
                        filename=f"decoy-{i}.md",
                    )
                ]
            )

        vsm.add_chunks(
            [
                DocumentChunk(
                    document_id="target",
                    chunk_index=0,
                    text="revenue was flat this year unlike prior periods",
                    filename="target.md",
                )
            ]
        )

        results = vsm.similarity_search("quarterly revenue", top_k=5, document_ids=["target"])

        assert len(results) == 1, (
            "Expected the target document's chunk to be found even though 25 "
            "more-similar decoy chunks from other documents exist — if this "
            "fails, fetch_k isn't being widened for filtered searches (C2)."
        )
        assert results[0][0].metadata["document_id"] == "target"

    def test_delete_document_removes_only_its_own_chunks(self):
        vsm = get_vector_store_manager()
        vsm.add_chunks([DocumentChunk(document_id="d1", chunk_index=0, text="alpha content here", filename="a.md")])
        vsm.add_chunks([DocumentChunk(document_id="d2", chunk_index=0, text="beta content here", filename="b.md")])

        vsm.delete_document("d1")

        results = vsm.similarity_search("content", top_k=5)
        assert {doc.metadata["document_id"] for doc, _ in results} == {"d2"}

    def test_empty_store_returns_no_results(self):
        vsm = get_vector_store_manager()
        assert vsm.is_empty
        assert vsm.similarity_search("anything", top_k=5) == []


class TestRetriever:
    def test_threshold_filters_out_low_relevance_matches(self):
        vsm = get_vector_store_manager()
        vsm.add_chunks(
            [
                DocumentChunk(document_id="d1", chunk_index=0, text="PostgreSQL billing database transactions", filename="a.md"),
                DocumentChunk(document_id="d1", chunk_index=1, text="company picnic scheduled August", filename="a.md"),
            ]
        )

        strict = retrieve_relevant_chunks("billing database", top_k=5, similarity_threshold=0.15)
        permissive = retrieve_relevant_chunks("billing database", top_k=5, similarity_threshold=0.0)

        assert len(strict) == 1
        assert len(permissive) == 2

    def test_citation_has_expected_fields(self):
        vsm = get_vector_store_manager()
        vsm.add_chunks([DocumentChunk(document_id="d1", chunk_index=3, text="a fact worth citing", filename="doc.pdf")])

        citations = retrieve_relevant_chunks("fact worth citing", top_k=1, similarity_threshold=0.0)

        assert len(citations) == 1
        citation = citations[0]
        assert citation.document_id == "d1"
        assert citation.filename == "doc.pdf"
        assert citation.chunk_index == 3
        assert citation.snippet
