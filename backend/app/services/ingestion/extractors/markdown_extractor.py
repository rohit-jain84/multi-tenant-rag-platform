import re

from app.services.ingestion.extractors.base import BaseExtractor, ExtractedDocument, PageContent

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class MarkdownExtractor(BaseExtractor):
    def extract(self, file_content: bytes, filename: str) -> ExtractedDocument:
        text = file_content.decode("utf-8", errors="replace")

        # Split by headings
        sections: list[tuple[str | None, str]] = []
        last_end = 0
        last_heading = None

        for match in HEADING_PATTERN.finditer(text):
            # Text before this heading belongs to the previous section
            section_text = text[last_end : match.start()].strip()
            if section_text:
                sections.append((last_heading, section_text))
            last_heading = match.group(2).strip()
            last_end = match.end()

        # Remaining text
        remaining = text[last_end:].strip()
        if remaining:
            sections.append((last_heading, remaining))

        # If no headings, treat whole content as one section
        if not sections:
            clean = self._strip_markdown(text)
            if clean.strip():
                return ExtractedDocument(
                    pages=[PageContent(text=clean.strip(), page_number=1)],
                    total_pages=1,
                    title=filename,
                )
            return ExtractedDocument(pages=[], total_pages=0, title=filename)

        pages = []
        for i, (heading, content) in enumerate(sections, 1):
            clean = self._strip_markdown(content)
            if clean.strip():
                pages.append(
                    PageContent(text=clean.strip(), page_number=i, section_heading=heading)
                )

        return ExtractedDocument(pages=pages, total_pages=len(pages), title=filename)

    @staticmethod
    def _strip_markdown(text: str) -> str:
        # Remove inline code, bold, italic markers but keep text
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)  # images
        text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)  # links
        text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)  # list markers
        text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)  # numbered lists
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)  # blockquotes
        return text
