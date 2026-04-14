from app.services.ingestion.chunking.base import BaseChunker, Chunk
from app.services.ingestion.chunking.fixed_size import FixedSizeChunker
from app.services.ingestion.chunking.semantic import SemanticChunker
from app.services.ingestion.chunking.parent_child import ParentChildChunker

CHUNKER_MAP: dict[str, type[BaseChunker]] = {
    "fixed": FixedSizeChunker,
    "semantic": SemanticChunker,
    "parent_child": ParentChildChunker,
}


def get_chunker(strategy: str, **kwargs) -> BaseChunker:
    chunker_cls = CHUNKER_MAP.get(strategy)
    if chunker_cls is None:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
    return chunker_cls(**kwargs)


__all__ = ["BaseChunker", "Chunk", "get_chunker", "CHUNKER_MAP"]
