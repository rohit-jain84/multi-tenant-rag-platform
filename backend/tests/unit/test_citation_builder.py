import uuid

from app.services.generation.citation_builder import (
    build_citations,
    extract_cited_sources,
    filter_cited_citations,
)
from app.services.retrieval.dense_retriever import RetrievedChunk


def _make_chunk(idx: int) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=str(uuid.uuid4()),
        text=f"This is the content of chunk {idx} with some details.",
        score=0.9 - idx * 0.1,
        document_id=str(uuid.uuid4()),
        document_name=f"document_{idx}.pdf",
        page_number=idx + 1,
        section_heading=f"Section {idx}",
    )


class TestBuildCitations:
    def test_builds_correct_count(self):
        chunks = [_make_chunk(i) for i in range(3)]
        citations = build_citations(chunks)
        assert len(citations) == 3

    def test_source_numbers_sequential(self):
        chunks = [_make_chunk(i) for i in range(3)]
        citations = build_citations(chunks)
        for i, c in enumerate(citations, 1):
            assert c.source_number == i

    def test_truncates_long_text(self):
        chunk = _make_chunk(0)
        chunk.text = "x" * 500
        citations = build_citations([chunk])
        assert len(citations[0].chunk_text) < 500
        assert citations[0].chunk_text.endswith("...")


class TestExtractCitedSources:
    def test_extracts_sources(self):
        answer = "According to [Source 1], the answer is yes. [Source 3] also confirms this."
        sources = extract_cited_sources(answer)
        assert sources == [1, 3]

    def test_no_sources(self):
        answer = "This is a plain answer without citations."
        sources = extract_cited_sources(answer)
        assert sources == []

    def test_duplicate_sources(self):
        answer = "[Source 1] says X. [Source 1] also says Y."
        sources = extract_cited_sources(answer)
        assert sources == [1]


class TestFilterCitedCitations:
    def test_filters_to_cited_only(self):
        chunks = [_make_chunk(i) for i in range(5)]
        citations = build_citations(chunks)
        answer = "Based on [Source 1] and [Source 3], the answer is clear."
        filtered = filter_cited_citations(citations, answer)
        assert len(filtered) == 2
        assert filtered[0].source_number == 1
        assert filtered[1].source_number == 3

    def test_returns_all_if_no_citations_found(self):
        chunks = [_make_chunk(i) for i in range(3)]
        citations = build_citations(chunks)
        answer = "Plain answer without source references."
        filtered = filter_cited_citations(citations, answer)
        assert len(filtered) == 3
