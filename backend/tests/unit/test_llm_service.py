"""Tests for LLM service context formatting."""

from app.services.generation.llm_service import _format_context
from app.services.retrieval.dense_retriever import RetrievedChunk


def _make_chunk(**kwargs) -> RetrievedChunk:
    defaults = dict(
        chunk_id="c1",
        text="Some text",
        score=0.9,
        document_id="d1",
        document_name="report.pdf",
    )
    defaults.update(kwargs)
    return RetrievedChunk(**defaults)


class TestFormatContext:
    def test_basic_formatting(self):
        chunks = [_make_chunk(text="Hello world")]
        result = _format_context(chunks)
        assert "[Source 1]" in result
        assert "Hello world" in result
        assert "report.pdf" in result

    def test_multiple_chunks_numbered(self):
        chunks = [
            _make_chunk(chunk_id="c1", text="First"),
            _make_chunk(chunk_id="c2", text="Second"),
        ]
        result = _format_context(chunks)
        assert "[Source 1]" in result
        assert "[Source 2]" in result

    def test_includes_page_number(self):
        chunks = [_make_chunk(page_number=5)]
        result = _format_context(chunks)
        assert "p.5" in result

    def test_includes_section_heading(self):
        chunks = [_make_chunk(section_heading="Introduction")]
        result = _format_context(chunks)
        assert "section: Introduction" in result

    def test_uses_parent_text_when_available(self):
        chunks = [_make_chunk(text="child text", parent_text="parent context text")]
        result = _format_context(chunks)
        assert "parent context text" in result
        assert "child text" not in result

    def test_no_parent_text_uses_chunk_text(self):
        chunks = [_make_chunk(text="chunk text", parent_text=None)]
        result = _format_context(chunks)
        assert "chunk text" in result

    def test_separator_between_sources(self):
        chunks = [_make_chunk(chunk_id="c1"), _make_chunk(chunk_id="c2")]
        result = _format_context(chunks)
        assert "---" in result
