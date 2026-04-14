import re

from bs4 import BeautifulSoup

from app.services.ingestion.extractors.base import BaseExtractor, ExtractedDocument, PageContent

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class HtmlExtractor(BaseExtractor):
    def extract(self, file_content: bytes, filename: str) -> ExtractedDocument:
        soup = BeautifulSoup(file_content, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else filename

        pages: list[PageContent] = []
        current_heading: str | None = None
        current_parts: list[str] = []
        section_index = 0

        body = soup.body if soup.body else soup

        for element in body.children:
            if hasattr(element, "name") and element.name in HEADING_TAGS:
                # Save previous section
                if current_parts:
                    section_index += 1
                    pages.append(
                        PageContent(
                            text="\n".join(current_parts).strip(),
                            page_number=section_index,
                            section_heading=current_heading,
                        )
                    )
                    current_parts = []
                current_heading = element.get_text(strip=True)
            else:
                text = element.get_text(strip=True) if hasattr(element, "get_text") else str(element).strip()
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    current_parts.append(text)

        # Last section
        if current_parts:
            section_index += 1
            pages.append(
                PageContent(
                    text="\n".join(current_parts).strip(),
                    page_number=section_index,
                    section_heading=current_heading,
                )
            )

        # Fallback: if no sections extracted, use full text
        if not pages:
            full_text = soup.get_text(separator="\n", strip=True)
            if full_text:
                pages.append(PageContent(text=full_text, page_number=1))

        return ExtractedDocument(pages=pages, total_pages=len(pages), title=title)
