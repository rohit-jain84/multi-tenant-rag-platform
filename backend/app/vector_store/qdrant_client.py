import uuid

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    return _client


def collection_name_for_tenant(tenant_id: uuid.UUID) -> str:
    return f"tenant_{str(tenant_id).replace('-', '_')}"


def ensure_collection(tenant_id: uuid.UUID) -> None:
    client = get_qdrant_client()
    name = collection_name_for_tenant(tenant_id)
    try:
        client.get_collection(name)
    except (UnexpectedResponse, Exception):
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )
        # Create payload indices for metadata filtering
        for field in ["document_id", "category", "upload_date", "chunking_strategy"]:
            try:
                client.create_payload_index(
                    collection_name=name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass
        logger.info("qdrant_collection_created", collection=name, tenant_id=str(tenant_id))


def upsert_chunks(
    tenant_id: uuid.UUID,
    chunk_ids: list[str],
    embeddings: list[list[float]],
    payloads: list[dict],
) -> None:
    client = get_qdrant_client()
    name = collection_name_for_tenant(tenant_id)
    points = [
        models.PointStruct(id=cid, vector=emb, payload=payload)
        for cid, emb, payload in zip(chunk_ids, embeddings, payloads)
    ]
    # Batch upsert in groups of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(collection_name=name, points=points[i : i + batch_size])


def search_vectors(
    tenant_id: uuid.UUID,
    query_vector: list[float],
    top_k: int = 20,
    filter_conditions: models.Filter | None = None,
) -> list[models.ScoredPoint]:
    client = get_qdrant_client()
    name = collection_name_for_tenant(tenant_id)
    return client.query_points(
        collection_name=name,
        query=query_vector,
        query_filter=filter_conditions,
        limit=top_k,
        with_payload=True,
    ).points


def delete_by_document(tenant_id: uuid.UUID, document_id: uuid.UUID) -> None:
    client = get_qdrant_client()
    name = collection_name_for_tenant(tenant_id)
    client.delete(
        collection_name=name,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=str(document_id)),
                    )
                ]
            )
        ),
    )


def delete_collection(tenant_id: uuid.UUID) -> None:
    client = get_qdrant_client()
    name = collection_name_for_tenant(tenant_id)
    try:
        client.delete_collection(name)
    except Exception:
        pass


def check_health() -> bool:
    try:
        client = get_qdrant_client()
        client.get_collections()
        return True
    except Exception:
        return False
