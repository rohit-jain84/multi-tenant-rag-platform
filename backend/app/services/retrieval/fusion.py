from app.config import settings
from app.services.retrieval.dense_retriever import RetrievedChunk
from app.utils.logging import get_logger

logger = get_logger(__name__)


def reciprocal_rank_fusion(
    dense_results: list[RetrievedChunk],
    sparse_results: list[RetrievedChunk],
    k: int | None = None,
) -> list[RetrievedChunk]:
    """
    Combine dense and sparse retrieval results using Reciprocal Rank Fusion.
    RRF_score(d) = sum(1 / (k + rank_i(d))) for each ranking list i.
    """
    rrf_k = k or settings.RRF_K
    scores: dict[str, float] = {}
    chunk_map: dict[str, RetrievedChunk] = {}

    # Score from dense results
    for rank, chunk in enumerate(dense_results, start=1):
        cid = chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunk_map[cid] = chunk

    # Score from sparse results
    for rank, chunk in enumerate(sparse_results, start=1):
        cid = chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        if cid not in chunk_map:
            chunk_map[cid] = chunk

    # Sort by fused score
    ranked_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    fused = []
    for cid in ranked_ids:
        chunk = chunk_map[cid]
        chunk.score = scores[cid]  # Replace with RRF score
        fused.append(chunk)

    logger.info(
        "rrf_fusion_complete",
        dense_count=len(dense_results),
        sparse_count=len(sparse_results),
        fused_count=len(fused),
    )
    return fused
