import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eval_result import EvalResult
from app.services.evaluation.ragas_runner import run_ragas_evaluation
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def run_ab_comparison(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    run_id: str,
) -> dict:
    """
    Run A/B comparison: hybrid vs. dense-only retrieval.
    Returns both result sets for comparison.
    """
    # Run hybrid
    hybrid_result = await run_ragas_evaluation(
        db=db,
        tenant_id=tenant_id,
        run_id=f"{run_id}_hybrid",
        strategy="hybrid",
        reranking_enabled=True,
    )

    # Run dense-only
    dense_result = await run_ragas_evaluation(
        db=db,
        tenant_id=tenant_id,
        run_id=f"{run_id}_dense_only",
        strategy="dense_only",
        reranking_enabled=True,
    )

    comparison = {
        "hybrid": {
            "faithfulness": hybrid_result.faithfulness,
            "answer_relevancy": hybrid_result.answer_relevancy,
            "context_precision": hybrid_result.context_precision,
            "context_recall": hybrid_result.context_recall,
        },
        "dense_only": {
            "faithfulness": dense_result.faithfulness,
            "answer_relevancy": dense_result.answer_relevancy,
            "context_precision": dense_result.context_precision,
            "context_recall": dense_result.context_recall,
        },
    }

    logger.info("ab_comparison_complete", run_id=run_id, comparison=comparison)
    return comparison


async def run_rerank_comparison(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    run_id: str,
) -> dict:
    """
    Run before/after reranking comparison.
    Returns both result sets for comparison.
    """
    # With reranking
    with_rerank = await run_ragas_evaluation(
        db=db,
        tenant_id=tenant_id,
        run_id=f"{run_id}_with_rerank",
        strategy="hybrid",
        reranking_enabled=True,
    )

    # Without reranking
    without_rerank = await run_ragas_evaluation(
        db=db,
        tenant_id=tenant_id,
        run_id=f"{run_id}_without_rerank",
        strategy="hybrid",
        reranking_enabled=False,
    )

    comparison = {
        "with_reranking": {
            "faithfulness": with_rerank.faithfulness,
            "answer_relevancy": with_rerank.answer_relevancy,
            "context_precision": with_rerank.context_precision,
            "context_recall": with_rerank.context_recall,
        },
        "without_reranking": {
            "faithfulness": without_rerank.faithfulness,
            "answer_relevancy": without_rerank.answer_relevancy,
            "context_precision": without_rerank.context_precision,
            "context_recall": without_rerank.context_recall,
        },
    }

    logger.info("rerank_comparison_complete", run_id=run_id, comparison=comparison)
    return comparison


async def get_eval_results(
    db: AsyncSession, limit: int = 20
) -> list[EvalResult]:
    result = await db.execute(
        select(EvalResult).order_by(EvalResult.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
