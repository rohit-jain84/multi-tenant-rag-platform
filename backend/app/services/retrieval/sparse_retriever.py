import asyncio
import json
import re
import uuid

from rank_bm25 import BM25Okapi

from app.cache.redis_client import get_bm25_corpus, store_bm25_corpus
from app.services.retrieval.dense_retriever import RetrievedChunk
from app.utils.logging import get_logger
from app.vector_store.qdrant_client import get_qdrant_client, collection_name_for_tenant

logger = get_logger(__name__)

# Common English stop words for BM25 filtering
_STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "not", "no", "nor",
    "so", "if", "then", "than", "that", "this", "these", "those", "it",
    "its", "i", "me", "my", "we", "our", "you", "your", "he", "him",
    "his", "she", "her", "they", "them", "their", "what", "which", "who",
    "whom", "when", "where", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "only", "own", "same",
    "as", "also", "just", "about", "into", "over", "after", "before",
    "between", "through", "during", "above", "below", "up", "down", "out",
    "off", "again", "further", "once", "here", "there", "very", "too",
}

_WORD_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Tokenize text with lowercasing, punctuation removal, and stop word filtering."""
    tokens = _WORD_PATTERN.findall(text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _scroll_all_chunks(tenant_id: uuid.UUID) -> list[dict] | None:
    """Sync helper: scroll all chunks from Qdrant for BM25 indexing."""
    client = get_qdrant_client()
    collection = collection_name_for_tenant(tenant_id)

    try:
        info = client.get_collection(collection)
        total_points = info.points_count
    except Exception:
        logger.warning("bm25_index_no_collection", tenant_id=str(tenant_id))
        return None

    if total_points == 0:
        return []

    corpus_data = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=500,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            corpus_data.append({
                "chunk_id": str(point.id),
                "text": payload.get("text", ""),
                "document_id": payload.get("document_id", ""),
                "document_name": payload.get("document_name", ""),
                "page_number": payload.get("page_number"),
                "section_heading": payload.get("section_heading"),
                "category": payload.get("category"),
                "chunk_index": payload.get("chunk_index", 0),
                "chunking_strategy": payload.get("chunking_strategy", ""),
                "parent_text": payload.get("parent_text"),
            })
        if offset is None:
            break

    return corpus_data


async def build_bm25_index(tenant_id: uuid.UUID) -> None:
    """Rebuild BM25 index for a tenant from all chunks in Qdrant."""
    corpus_data = await asyncio.to_thread(_scroll_all_chunks, tenant_id)
    if corpus_data is None:
        return

    if not corpus_data:
        return

    # Serialize and store in Redis
    serialized = json.dumps(corpus_data)
    await store_bm25_corpus(str(tenant_id), serialized)
    logger.info("bm25_index_built", tenant_id=str(tenant_id), documents=len(corpus_data))


async def sparse_retrieve(
    tenant_id: uuid.UUID,
    query: str,
    top_k: int = 20,
) -> list[RetrievedChunk]:
    """BM25-based sparse retrieval."""
    corpus_json = await get_bm25_corpus(str(tenant_id))
    if not corpus_json:
        logger.warning("bm25_no_index", tenant_id=str(tenant_id))
        return []

    corpus_data = json.loads(corpus_json)
    if not corpus_data:
        return []

    tokenized_corpus = [_tokenize(doc["text"]) for doc in corpus_data]
    bm25 = BM25Okapi(tokenized_corpus)

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    # Get top-K indices
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    chunks = []
    for idx in ranked_indices:
        if scores[idx] <= 0:
            continue
        doc = corpus_data[idx]
        chunks.append(
            RetrievedChunk(
                chunk_id=doc["chunk_id"],
                text=doc["text"],
                score=float(scores[idx]),
                document_id=doc["document_id"],
                document_name=doc["document_name"],
                page_number=doc.get("page_number"),
                section_heading=doc.get("section_heading"),
                category=doc.get("category"),
                chunk_index=doc.get("chunk_index", 0),
                chunking_strategy=doc.get("chunking_strategy", ""),
                parent_text=doc.get("parent_text"),
            )
        )

    logger.info("sparse_retrieval_complete", tenant_id=str(tenant_id), results=len(chunks))
    return chunks
