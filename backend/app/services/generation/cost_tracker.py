import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.query_log import QueryLog
from app.utils.logging import get_logger

logger = get_logger(__name__)


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    prompt_cost = (prompt_tokens / 1000) * settings.LLM_PRICE_PROMPT_PER_1K
    completion_cost = (completion_tokens / 1000) * settings.LLM_PRICE_COMPLETION_PER_1K
    return round(prompt_cost + completion_cost, 6)


async def log_query(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    query_text: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: int,
    latency_breakdown: dict | None = None,
    retrieval_strategy: str | None = None,
) -> QueryLog:
    cost = estimate_cost(prompt_tokens, completion_tokens)

    log = QueryLog(
        tenant_id=tenant_id,
        query_text=query_text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=cost,
        latency_ms=latency_ms,
        latency_breakdown=latency_breakdown,
        retrieval_strategy=retrieval_strategy,
    )
    db.add(log)
    await db.flush()

    logger.info(
        "query_logged",
        tenant_id=str(tenant_id),
        tokens=total_tokens,
        cost=cost,
        latency_ms=latency_ms,
    )
    return log


async def get_tenant_usage(
    db: AsyncSession, tenant_id: uuid.UUID
) -> dict:
    result = await db.execute(
        select(
            func.count(QueryLog.id).label("total_queries"),
            func.coalesce(func.sum(QueryLog.prompt_tokens), 0).label("total_prompt_tokens"),
            func.coalesce(func.sum(QueryLog.completion_tokens), 0).label("total_completion_tokens"),
            func.coalesce(func.sum(QueryLog.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(QueryLog.estimated_cost), 0.0).label("total_cost"),
        ).where(QueryLog.tenant_id == tenant_id)
    )
    row = result.one()
    return {
        "total_queries": row.total_queries,
        "total_prompt_tokens": row.total_prompt_tokens,
        "total_completion_tokens": row.total_completion_tokens,
        "total_tokens": row.total_tokens,
        "total_estimated_cost": float(row.total_cost),
    }
