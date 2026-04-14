from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PageContent:
    text: str
    page_number: int | None = None
    section_heading: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractedDocument:
    pages: list[PageContent]
    total_pages: int | None = None
    title: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_content: bytes, filename: str) -> ExtractedDocument:
        """Extract text and metadata from a document file."""
        ...
