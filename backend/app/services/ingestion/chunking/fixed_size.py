import tiktoken

from app.config import settings
from app.services.ingestion.chunking.base import BaseChunker, Chunk
from app.services.ingestion.extractors.base import ExtractedDocument


class FixedSizeChunker(BaseChunker):
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
        self._enc = tiktoken.get_encoding("cl100k_base")

    def chunk(self, document: ExtractedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_index = 0

        for page in document.pages:
            tokens = self._enc.encode(page.text)

            start = 0
            while start < len(tokens):
                end = min(start + self.chunk_size, len(tokens))
                chunk_tokens = tokens[start:end]
                chunk_text = self._enc.decode(chunk_tokens)

                if chunk_text.strip():
                    chunks.append(
                        Chunk(
                            text=chunk_text.strip(),
                            chunk_index=chunk_index,
                            page_number=page.page_number,
                            section_heading=page.section_heading,
                        )
                    )
                    chunk_index += 1

                # Move forward by (chunk_size - overlap)
                step = self.chunk_size - self.chunk_overlap
                if step <= 0:
                    step = self.chunk_size
                start += step

        return chunks
