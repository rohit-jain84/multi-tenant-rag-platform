import json
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eval_result import EvalResult
from app.services.generation.llm_service import generate_answer
from app.services.retrieval.pipeline import run_retrieval
from app.utils.logging import get_logger

logger = get_logger(__name__)

EVAL_SET_PATH = Path(__file__).parent.parent.parent.parent / "eval" / "eval_set.json"


def load_eval_set() -> list[dict]:
    if not EVAL_SET_PATH.exists():
        raise FileNotFoundError(f"Eval set not found at {EVAL_SET_PATH}")
    with open(EVAL_SET_PATH) as f:
        return json.load(f)


async def run_ragas_evaluation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    run_id: str,
    strategy: str = "hybrid",
    reranking_enabled: bool = True,
) -> EvalResult:
    """
    Run RAGAS evaluation against the eval set.
    Collects questions, answers, contexts, and ground truths,
    then computes RAGAS metrics.
    """
    eval_set = load_eval_set()

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for item in eval_set:
        question = item["question"]
        ground_truth = item["ground_truth"]

        # Run retrieval
        search_type = "hybrid" if strategy == "hybrid" else "dense_only"
        retrieval_result = await run_retrieval(
            tenant_id=tenant_id,
            query=question,
            search_type=search_type,
            reranking_enabled=reranking_enabled,
        )

        # Generate answer
        llm_result = await generate_answer(question, retrieval_result.chunks)

        # Collect data
        questions.append(question)
        answers.append(llm_result["content"])
        contexts.append([c.text for c in retrieval_result.chunks])
        ground_truths.append(ground_truth)

    # Compute RAGAS metrics
    scores = await _compute_ragas_scores(questions, answers, contexts, ground_truths)

    # Store result
    eval_result = EvalResult(
        run_id=run_id,
        strategy=strategy,
        reranking_enabled=reranking_enabled,
        faithfulness=scores.get("faithfulness"),
        answer_relevancy=scores.get("answer_relevancy"),
        context_precision=scores.get("context_precision"),
        context_recall=scores.get("context_recall"),
        per_question_results=scores.get("per_question"),
    )
    db.add(eval_result)
    await db.flush()

    logger.info(
        "ragas_evaluation_complete",
        run_id=run_id,
        strategy=strategy,
        scores={k: v for k, v in scores.items() if k != "per_question"},
    )
    return eval_result


async def _compute_ragas_scores(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> dict:
    """Compute RAGAS metrics using the ragas library."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })

        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        )

        return {
            "faithfulness": result.get("faithfulness"),
            "answer_relevancy": result.get("answer_relevancy"),
            "context_precision": result.get("context_precision"),
            "context_recall": result.get("context_recall"),
        }
    except ImportError:
        logger.warning("ragas_not_available_returning_placeholder_scores")
        return {
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "context_recall": None,
        }
    except Exception as e:
        logger.error("ragas_evaluation_error", error=str(e))
        return {
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "context_recall": None,
            "error": str(e),
        }
