import re

import tiktoken

from app.config import settings
from app.services.ingestion.chunking.base import BaseChunker, Chunk
from app.services.ingestion.extractors.base import ExtractedDocument
from app.vector_store.embedding import cosine_similarity, embed_texts


class SemanticChunker(BaseChunker):
    def __init__(
        self,
        similarity_threshold: float | None = None,
        max_chunk_tokens: int | None = None,
    ):
        self.similarity_threshold = similarity_threshold or settings.SEMANTIC_SIMILARITY_THRESHOLD
        self.max_chunk_tokens = max_chunk_tokens or settings.DEFAULT_CHUNK_SIZE
        self._enc = tiktoken.get_encoding("cl100k_base")

    def _split_sentences(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _token_count(self, text: str) -> int:
        return len(self._enc.encode(text))

    def chunk(self, document: ExtractedDocument) -> list[Chunk]:
        all_chunks: list[Chunk] = []
        chunk_index = 0

        for page in document.pages:
            sentences = self._split_sentences(page.text)
            if not sentences:
                continue

            if len(sentences) == 1:
                all_chunks.append(
                    Chunk(
                        text=sentences[0],
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        section_heading=page.section_heading,
                    )
                )
                chunk_index += 1
                continue

            # Embed all sentences for this page
            embeddings = embed_texts(sentences)

            # Compute similarity between consecutive sentences
            similarities = []
            for i in range(len(embeddings) - 1):
                sim = cosine_similarity(embeddings[i], embeddings[i + 1])
                similarities.append(sim)

            # Group sentences into chunks by splitting at low-similarity boundaries
            groups: list[list[str]] = []
            current_group: list[str] = [sentences[0]]

            for i, sim in enumerate(similarities):
                if sim < self.similarity_threshold or self._token_count(
                    " ".join(current_group + [sentences[i + 1]])
                ) > self.max_chunk_tokens:
                    groups.append(current_group)
                    current_group = [sentences[i + 1]]
                else:
                    current_group.append(sentences[i + 1])

            if current_group:
                groups.append(current_group)

            # Create chunks from groups
            for group in groups:
                text = " ".join(group).strip()
                if text:
                    all_chunks.append(
                        Chunk(
                            text=text,
                            chunk_index=chunk_index,
                            page_number=page.page_number,
                            section_heading=page.section_heading,
                        )
                    )
                    chunk_index += 1

        return all_chunks
