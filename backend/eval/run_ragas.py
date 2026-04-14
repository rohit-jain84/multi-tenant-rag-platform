#!/usr/bin/env python3
"""
Run RAGAS evaluation against the eval set.

Usage:
    python eval/run_ragas.py --tenant-id <uuid> [--strategy hybrid|dense_only] [--no-rerank]

Requires a running backend with documents already ingested for the specified tenant.
"""

import argparse
import asyncio
import uuid
from datetime import datetime, timezone

from app.db.session import async_session_factory
from app.services.evaluation.ragas_runner import run_ragas_evaluation


async def main():
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    parser.add_argument("--strategy", default="hybrid", choices=["hybrid", "dense_only"])
    parser.add_argument("--no-rerank", action="store_true")
    args = parser.parse_args()

    tenant_id = uuid.UUID(args.tenant_id)
    run_id = f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    async with async_session_factory() as db:
        result = await run_ragas_evaluation(
            db=db,
            tenant_id=tenant_id,
            run_id=run_id,
            strategy=args.strategy,
            reranking_enabled=not args.no_rerank,
        )
        await db.commit()

    print(f"\n{'='*50}")
    print(f"RAGAS Evaluation Results - {run_id}")
    print(f"Strategy: {args.strategy} | Reranking: {not args.no_rerank}")
    print(f"{'='*50}")
    print(f"  Faithfulness:      {result.faithfulness}")
    print(f"  Answer Relevancy:  {result.answer_relevancy}")
    print(f"  Context Precision: {result.context_precision}")
    print(f"  Context Recall:    {result.context_recall}")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
