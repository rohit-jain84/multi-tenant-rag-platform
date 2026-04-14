import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MetadataFilter(BaseModel):
    document_ids: list[uuid.UUID] | None = None
    date_range: dict[str, datetime] | None = None  # {"start": ..., "end": ...}
    categories: list[str] | None = None


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None
    top_n: int | None = None
    filters: MetadataFilter | None = None
    chunking_strategy: str | None = None
    search_type: str = Field(default="hybrid", pattern="^(hybrid|dense_only)$")


class Citation(BaseModel):
    source_number: int
    document_name: str
    document_id: uuid.UUID
    page_number: int | None
    section_heading: str | None
    chunk_text: str  # Truncated preview
    relevance_score: float


class LatencyBreakdown(BaseModel):
    embedding_ms: int = 0
    retrieval_ms: int = 0
    reranking_ms: int = 0
    generation_ms: int = 0
    total_ms: int = 0


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    query_metadata: dict  # latency, tokens, strategy info


class StreamEvent(BaseModel):
    type: str  # "token", "citations", "metadata", "error", "done"
    content: str | dict | list | None = None
