import pytest

from app.services.ingestion.chunking.fixed_size import FixedSizeChunker
from app.services.ingestion.extractors.base import ExtractedDocument, PageContent


def _make_document(text: str, pages: int = 1) -> ExtractedDocument:
    page_texts = [text] if pages == 1 else [text[i::pages] for i in range(pages)]
    return ExtractedDocument(
        pages=[PageContent(text=t, page_number=i + 1) for i, t in enumerate(page_texts)],
        total_pages=pages,
    )


class TestFixedSizeChunker:
    def test_basic_chunking(self):
        long_text = " ".join(["word"] * 1000)
        doc = _make_document(long_text)
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk(doc)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.text.strip()
            assert chunk.page_number == 1

    def test_chunk_indices_sequential(self):
        long_text = " ".join(["word"] * 500)
        doc = _make_document(long_text)
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=5)
        chunks = chunker.chunk(doc)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_small_text_single_chunk(self):
        doc = _make_document("This is a short text.")
        chunker = FixedSizeChunker(chunk_size=512, chunk_overlap=50)
        chunks = chunker.chunk(doc)
        assert len(chunks) == 1
        assert "short text" in chunks[0].text

    def test_empty_document(self):
        doc = ExtractedDocument(pages=[], total_pages=0)
        chunker = FixedSizeChunker()
        chunks = chunker.chunk(doc)
        assert len(chunks) == 0

    def test_overlap_present(self):
        # Generate text long enough that overlap matters
        words = [f"word{i}" for i in range(200)]
        text = " ".join(words)
        doc = _make_document(text)
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10)
        chunks = chunker.chunk(doc)
        if len(chunks) >= 2:
            # Check that consecutive chunks share some text (overlap)
            chunk0_words = set(chunks[0].text.split())
            chunk1_words = set(chunks[1].text.split())
            overlap = chunk0_words & chunk1_words
            assert len(overlap) > 0
