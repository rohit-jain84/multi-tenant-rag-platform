import uuid
from dataclasses import dataclass, field

from qdrant_client import models as qmodels

from app.schemas.query import MetadataFilter
from app.vector_store.embedding import embed_query
from app.vector_store.qdrant_client import search_vectors
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    document_id: str
    document_name: str
    page_number: int | None = None
    section_heading: str | None = None
    category: str | None = None
    chunk_index: int = 0
    chunking_strategy: str = ""
    parent_text: str | None = None
    metadata: dict = field(default_factory=dict)


def build_qdrant_filter(filters: MetadataFilter | None) -> qmodels.Filter | None:
    if filters is None:
        return None

    conditions = []

    if filters.document_ids:
        conditions.append(
            qmodels.FieldCondition(
                key="document_id",
                match=qmodels.MatchAny(any=[str(did) for did in filters.document_ids]),
            )
        )

    if filters.categories:
        conditions.append(
            qmodels.FieldCondition(
                key="category",
                match=qmodels.MatchAny(any=filters.categories),
            )
        )

    if filters.date_range:
        range_kwargs = {}
        if "start" in filters.date_range:
            range_kwargs["gte"] = filters.date_range["start"].isoformat()
        if "end" in filters.date_range:
            range_kwargs["lte"] = filters.date_range["end"].isoformat()
        if range_kwargs:
            conditions.append(
                qmodels.FieldCondition(
                    key="upload_date",
                    range=qmodels.Range(**range_kwargs),
                )
            )

    if not conditions:
        return None

    return qmodels.Filter(must=conditions)


def dense_retrieve(
    tenant_id: uuid.UUID,
    query: str,
    top_k: int = 20,
    filters: MetadataFilter | None = None,
) -> list[RetrievedChunk]:
    query_embedding = embed_query(query)
    qdrant_filter = build_qdrant_filter(filters)

    results = search_vectors(
        tenant_id=tenant_id,
        query_vector=query_embedding,
        top_k=top_k,
        filter_conditions=qdrant_filter,
    )

    chunks = []
    for point in results:
        payload = point.payload or {}
        chunks.append(
            RetrievedChunk(
                chunk_id=str(point.id),
                text=payload.get("text", ""),
                score=point.score,
                document_id=payload.get("document_id", ""),
                document_name=payload.get("document_name", ""),
                page_number=payload.get("page_number"),
                section_heading=payload.get("section_heading"),
                category=payload.get("category"),
                chunk_index=payload.get("chunk_index", 0),
                chunking_strategy=payload.get("chunking_strategy", ""),
                parent_text=payload.get("parent_text"),
            )
        )

    logger.info("dense_retrieval_complete", tenant_id=str(tenant_id), results=len(chunks))
    return chunks
