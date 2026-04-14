from app.services.ingestion.extractors.base import BaseExtractor, ExtractedDocument
from app.services.ingestion.extractors.pdf_extractor import PdfExtractor
from app.services.ingestion.extractors.docx_extractor import DocxExtractor
from app.services.ingestion.extractors.html_extractor import HtmlExtractor
from app.services.ingestion.extractors.markdown_extractor import MarkdownExtractor

EXTRACTOR_MAP: dict[str, type[BaseExtractor]] = {
    ".pdf": PdfExtractor,
    ".docx": DocxExtractor,
    ".html": HtmlExtractor,
    ".htm": HtmlExtractor,
    ".md": MarkdownExtractor,
    ".markdown": MarkdownExtractor,
}

SUPPORTED_FORMATS = set(EXTRACTOR_MAP.keys())


def get_extractor(file_extension: str) -> BaseExtractor:
    ext = file_extension.lower()
    extractor_cls = EXTRACTOR_MAP.get(ext)
    if extractor_cls is None:
        raise ValueError(f"Unsupported format: {ext}")
    return extractor_cls()


__all__ = [
    "BaseExtractor",
    "ExtractedDocument",
    "get_extractor",
    "SUPPORTED_FORMATS",
]
