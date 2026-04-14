"""Tests for parent-child chunking strategy."""

from app.services.ingestion.chunking.parent_child import ParentChildChunker
from app.services.ingestion.extractors.base import ExtractedDocument, PageContent


def _make_doc(text: str, page_number: int = 1) -> ExtractedDocument:
    return ExtractedDocument(
        pages=[PageContent(text=text, page_number=page_number)],
        total_pages=1,
    )


class TestParentChildChunker:
    def test_produces_child_chunks(self):
        long_text = "This is a sentence about machine learning. " * 100
        doc = _make_doc(long_text)
        chunker = ParentChildChunker(parent_chunk_size=200, child_chunk_size=50, child_overlap=10)
        chunks = chunker.chunk(doc)
        assert len(chunks) > 1

    def test_child_chunks_have_parent_text(self):
        long_text = "Word " * 500
        doc = _make_doc(long_text)
        chunker = ParentChildChunker(parent_chunk_size=200, child_chunk_size=50, child_overlap=10)
        chunks = chunker.chunk(doc)
        for chunk in chunks:
            assert chunk.parent_chunk_text is not None
            assert len(chunk.parent_chunk_text) > 0

    def test_parent_text_is_larger_than_child(self):
        long_text = "Word " * 500
        doc = _make_doc(long_text)
        chunker = ParentChildChunker(parent_chunk_size=200, child_chunk_size=50, child_overlap=10)
        chunks = chunker.chunk(doc)
        for chunk in chunks:
            assert len(chunk.parent_chunk_text) >= len(chunk.text)

    def test_chunk_indices_sequential(self):
        long_text = "Word " * 500
        doc = _make_doc(long_text)
        chunker = ParentChildChunker(parent_chunk_size=200, child_chunk_size=50, child_overlap=10)
        chunks = chunker.chunk(doc)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_empty_document(self):
        doc = ExtractedDocument(pages=[], total_pages=0)
        chunker = ParentChildChunker()
        chunks = chunker.chunk(doc)
        assert chunks == []

    def test_short_text_single_parent_and_child(self):
        doc = _make_doc("Short text.")
        chunker = ParentChildChunker(parent_chunk_size=2048, child_chunk_size=256)
        chunks = chunker.chunk(doc)
        assert len(chunks) >= 1
        # With very short text, child == parent
        assert chunks[0].parent_chunk_text is not None

    def test_page_number_preserved(self):
        doc = _make_doc("Word " * 300, page_number=7)
        chunker = ParentChildChunker(parent_chunk_size=100, child_chunk_size=30, child_overlap=5)
        chunks = chunker.chunk(doc)
        assert all(c.page_number == 7 for c in chunks)
