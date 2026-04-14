from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.services.ingestion.extractors.base import ExtractedDocument


@dataclass
class Chunk:
    text: str
    chunk_index: int
    page_number: int | None = None
    section_heading: str | None = None
    parent_chunk_text: str | None = None  # For parent-child strategy
    metadata: dict = field(default_factory=dict)


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, document: ExtractedDocument) -> list[Chunk]:
        """Split an extracted document into chunks."""
        ...
