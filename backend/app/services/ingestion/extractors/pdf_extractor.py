import io

import fitz  # PyMuPDF

from app.services.ingestion.extractors.base import BaseExtractor, ExtractedDocument, PageContent
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PdfExtractor(BaseExtractor):
    def extract(self, file_content: bytes, filename: str) -> ExtractedDocument:
        pages = []
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                if text.strip():
                    pages.append(
                        PageContent(
                            text=text.strip(),
                            page_number=page_num + 1,
                        )
                    )
            total_pages = len(doc)
            doc.close()
        except Exception as e:
            logger.warning("pymupdf_failed_trying_pdfplumber", error=str(e), filename=filename)
            pages, total_pages = self._fallback_pdfplumber(file_content, filename)

        return ExtractedDocument(pages=pages, total_pages=total_pages, title=filename)

    def _fallback_pdfplumber(
        self, file_content: bytes, filename: str
    ) -> tuple[list[PageContent], int]:
        import pdfplumber

        pages = []
        pdf = pdfplumber.open(io.BytesIO(file_content))
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(PageContent(text=text.strip(), page_number=i + 1))
        total = len(pdf.pages)
        pdf.close()
        return pages, total
