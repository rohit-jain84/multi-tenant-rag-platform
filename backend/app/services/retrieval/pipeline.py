import asyncio
import time
import uuid
from dataclasses import dataclass

from app.config import settings
from app.schemas.query import MetadataFilter
from app.services.retrieval.dense_retriever import RetrievedChunk, dense_retrieve
from app.services.retrieval.fusion import reciprocal_rank_fusion
from app.services.retrieval.reranker import rerank_with_fallback
from app.services.retrieval.sparse_retriever import sparse_retrieve
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    timing: dict  # embedding_ms, retrieval_ms, reranking_ms


async def run_retrieval(
    tenant_id: uuid.UUID,
    query: str,
    top_k: int | None = None,
    top_n: int | None = None,
    filters: MetadataFilter | None = None,
    search_type: str = "hybrid",
    reranking_enabled: bool = True,
) -> RetrievalResult:
    top_k = top_k or settings.DEFAULT_TOP_K
    top_n = top_n or settings.DEFAULT_TOP_N
    timing = {}

    # Dense retrieval (embedding + search) - run in thread to avoid blocking event loop
    t0 = time.perf_counter()
    dense_results = await asyncio.to_thread(dense_retrieve, tenant_id, query, top_k, filters)
    timing["embedding_and_dense_ms"] = int((time.perf_counter() - t0) * 1000)

    if search_type == "hybrid":
        # Sparse retrieval
        t1 = time.perf_counter()
        sparse_results = await sparse_retrieve(tenant_id, query, top_k)
        timing["sparse_ms"] = int((time.perf_counter() - t1) * 1000)

        # Fusion
        t2 = time.perf_counter()
        fused = reciprocal_rank_fusion(dense_results, sparse_results)
        timing["fusion_ms"] = int((time.perf_counter() - t2) * 1000)
        candidates = fused[:top_k]
    else:
        candidates = dense_results
        timing["sparse_ms"] = 0
        timing["fusion_ms"] = 0

    timing["retrieval_ms"] = timing["embedding_and_dense_ms"] + timing.get("sparse_ms", 0) + timing.get("fusion_ms", 0)

    # Reranking - run in thread to avoid blocking event loop
    if reranking_enabled and candidates:
        t3 = time.perf_counter()
        reranked = await asyncio.to_thread(rerank_with_fallback, query, candidates, top_n)
        timing["reranking_ms"] = int((time.perf_counter() - t3) * 1000)
    else:
        reranked = candidates[:top_n]
        timing["reranking_ms"] = 0

    logger.info(
        "retrieval_pipeline_complete",
        tenant_id=str(tenant_id),
        search_type=search_type,
        candidates=len(candidates),
        final_results=len(reranked),
        timing=timing,
    )

    return RetrievalResult(chunks=reranked, timing=timing)
