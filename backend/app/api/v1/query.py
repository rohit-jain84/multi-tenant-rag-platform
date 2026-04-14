import time
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_tenant_id
from app.schemas.query import QueryRequest, QueryResponse
from app.services.generation.citation_builder import build_citations
from app.services.generation.cost_tracker import log_query
from app.services.generation.llm_service import generate_answer
from app.services.generation.streaming import stream_response
from app.services.retrieval.pipeline import run_retrieval
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    body: QueryRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    t_start = time.perf_counter()

    # Check low-confidence threshold
    reranking_enabled = True

    # Retrieval
    retrieval_result = await run_retrieval(
        tenant_id=tenant_id,
        query=body.question,
        top_k=body.top_k,
        top_n=body.top_n,
        filters=body.filters,
        search_type=body.search_type,
        reranking_enabled=reranking_enabled,
    )

    chunks = retrieval_result.chunks
    timing = retrieval_result.timing

    # Check if context is sufficient
    if not chunks or (chunks and chunks[0].score < settings.RERANK_SCORE_THRESHOLD):
        answer = "I don't have enough information in the provided documents to answer this question."
        citations = []
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    else:
        # Generation
        t_gen = time.perf_counter()
        llm_result = await generate_answer(body.question, chunks)
        timing["generation_ms"] = int((time.perf_counter() - t_gen) * 1000)

        answer = llm_result["content"]
        usage = llm_result["usage"]
        citations = build_citations(chunks)

    timing["total_ms"] = int((time.perf_counter() - t_start) * 1000)

    # Log query
    await log_query(
        db=db,
        tenant_id=tenant_id,
        query_text=body.question,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        latency_ms=timing["total_ms"],
        latency_breakdown=timing,
        retrieval_strategy=body.search_type,
    )

    return QueryResponse(
        answer=answer,
        citations=citations,
        query_metadata={
            "latency": timing,
            "tokens": usage,
            "retrieval_strategy": body.search_type,
            "reranking_enabled": reranking_enabled,
            "chunks_retrieved": len(chunks),
        },
    )


@router.post("/stream")
async def query_documents_stream(
    body: QueryRequest,
    request: Request,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    t_start = time.perf_counter()

    # Retrieval
    retrieval_result = await run_retrieval(
        tenant_id=tenant_id,
        query=body.question,
        top_k=body.top_k,
        top_n=body.top_n,
        filters=body.filters,
        search_type=body.search_type,
    )

    chunks = retrieval_result.chunks

    # Check if context is sufficient (same threshold as non-streaming)
    if not chunks or (chunks and chunks[0].score < settings.RERANK_SCORE_THRESHOLD):
        chunks = []

    citations = build_citations(chunks)
    metadata = {
        "latency": retrieval_result.timing,
        "retrieval_strategy": body.search_type,
        "chunks_retrieved": len(chunks),
    }

    # Callback invoked by the stream generator once token usage is known
    async def _log_usage(usage: dict) -> None:
        latency_ms = int((time.perf_counter() - t_start) * 1000)
        await log_query(
            db=db,
            tenant_id=tenant_id,
            query_text=body.question,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=latency_ms,
            latency_breakdown=retrieval_result.timing,
            retrieval_strategy=body.search_type,
        )

    return EventSourceResponse(
        stream_response(body.question, chunks, citations, metadata, on_complete=_log_usage)
    )
