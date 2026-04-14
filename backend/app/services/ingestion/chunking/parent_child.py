import tiktoken

from app.config import settings
from app.services.ingestion.chunking.base import BaseChunker, Chunk
from app.services.ingestion.extractors.base import ExtractedDocument


class ParentChildChunker(BaseChunker):
    """
    Creates hierarchical chunks:
    - Parent chunks (~2048 tokens) provide broad context for LLM generation.
    - Child chunks (~256 tokens) are stored in the vector DB for precise retrieval.
    At query time, children are retrieved, but their parent text is passed to the LLM.
    """

    def __init__(
        self,
        parent_chunk_size: int = 2048,
        child_chunk_size: int = 256,
        child_overlap: int = 50,
    ):
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap
        self._enc = tiktoken.get_encoding("cl100k_base")

    def _split_to_token_chunks(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        tokens = self._enc.encode(text)
        chunks = []
        start = 0
        step = max(chunk_size - overlap, 1)
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_text = self._enc.decode(tokens[start:end]).strip()
            if chunk_text:
                chunks.append(chunk_text)
            start += step
        return chunks

    def chunk(self, document: ExtractedDocument) -> list[Chunk]:
        full_text = document.full_text
        all_chunks: list[Chunk] = []
        chunk_index = 0

        # Build a page lookup: char offset -> page info
        page_map: list[tuple[int, int | None, str | None]] = []  # (start_offset, page_num, heading)
        offset = 0
        for page in document.pages:
            page_map.append((offset, page.page_number, page.section_heading))
            offset += len(page.text) + 2  # +2 for "\n\n" separator

        def _find_page(text_offset: int) -> tuple[int | None, str | None]:
            page_num = None
            heading = None
            for start, pn, hd in reversed(page_map):
                if text_offset >= start:
                    page_num = pn
                    heading = hd
                    break
            return page_num, heading

        # Create parent chunks
        parent_texts = self._split_to_token_chunks(full_text, self.parent_chunk_size, overlap=0)

        text_offset = 0
        for parent_text in parent_texts:
            # Create child chunks from each parent
            child_texts = self._split_to_token_chunks(
                parent_text, self.child_chunk_size, self.child_overlap
            )

            parent_start_offset = full_text.find(parent_text, text_offset)
            if parent_start_offset == -1:
                parent_start_offset = text_offset

            for child_text in child_texts:
                child_offset = full_text.find(child_text, parent_start_offset)
                if child_offset == -1:
                    child_offset = parent_start_offset
                page_num, heading = _find_page(child_offset)

                all_chunks.append(
                    Chunk(
                        text=child_text,
                        chunk_index=chunk_index,
                        page_number=page_num,
                        section_heading=heading,
                        parent_chunk_text=parent_text,
                    )
                )
                chunk_index += 1

            text_offset = parent_start_offset + len(parent_text)

        return all_chunks
