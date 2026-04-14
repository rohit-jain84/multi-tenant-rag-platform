import pytest

from app.services.ingestion.extractors import get_extractor, SUPPORTED_FORMATS
from app.services.ingestion.extractors.html_extractor import HtmlExtractor
from app.services.ingestion.extractors.markdown_extractor import MarkdownExtractor


class TestSupportedFormats:
    def test_all_formats_registered(self):
        assert ".pdf" in SUPPORTED_FORMATS
        assert ".docx" in SUPPORTED_FORMATS
        assert ".html" in SUPPORTED_FORMATS
        assert ".htm" in SUPPORTED_FORMATS
        assert ".md" in SUPPORTED_FORMATS

    def test_get_extractor_valid(self):
        for ext in [".pdf", ".docx", ".html", ".md"]:
            extractor = get_extractor(ext)
            assert extractor is not None

    def test_get_extractor_invalid(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            get_extractor(".xyz")


class TestHtmlExtractor:
    def test_basic_extraction(self, sample_html_content):
        extractor = HtmlExtractor()
        result = extractor.extract(sample_html_content, "test.html")
        assert result.pages
        assert result.total_pages > 0
        # Should extract text from sections
        full_text = result.full_text
        assert "first paragraph" in full_text
        assert "second section" in full_text.lower()

    def test_heading_sections(self, sample_html_content):
        extractor = HtmlExtractor()
        result = extractor.extract(sample_html_content, "test.html")
        # Should have section headings
        headings = [p.section_heading for p in result.pages if p.section_heading]
        assert len(headings) >= 1


class TestMarkdownExtractor:
    def test_basic_extraction(self, sample_markdown_content):
        extractor = MarkdownExtractor()
        result = extractor.extract(sample_markdown_content, "test.md")
        assert result.pages
        assert result.total_pages > 0
        full_text = result.full_text
        assert "introduction" in full_text
        assert "first topic" in full_text

    def test_heading_sections(self, sample_markdown_content):
        extractor = MarkdownExtractor()
        result = extractor.extract(sample_markdown_content, "test.md")
        headings = [p.section_heading for p in result.pages if p.section_heading]
        assert "Section One" in headings or "Test Document" in headings

    def test_empty_content(self):
        extractor = MarkdownExtractor()
        result = extractor.extract(b"", "empty.md")
        assert len(result.pages) == 0
