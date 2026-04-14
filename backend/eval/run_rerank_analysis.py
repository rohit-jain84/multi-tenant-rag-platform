#!/usr/bin/env python3
"""
Run before/after reranking comparison.

Usage:
    python eval/run_rerank_analysis.py --tenant-id <uuid>
"""

import argparse
import asyncio
import uuid
from datetime import datetime, timezone

from app.db.session import async_session_factory
from app.services.evaluation.ab_comparison import run_rerank_comparison


async def main():
    parser = argparse.ArgumentParser(description="Run reranking impact analysis")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    args = parser.parse_args()

    tenant_id = uuid.UUID(args.tenant_id)
    run_id = f"rerank_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    async with async_session_factory() as db:
        comparison = await run_rerank_comparison(db, tenant_id, run_id)
        await db.commit()

    print(f"\n{'='*60}")
    print(f"Reranking Impact Analysis - {run_id}")
    print(f"{'='*60}")

    header = f"{'Metric':<25} {'With Rerank':>12} {'No Rerank':>12} {'Delta':>10}"
    print(header)
    print("-" * 60)

    for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        w = comparison["with_reranking"].get(metric)
        wo = comparison["without_reranking"].get(metric)
        w_str = f"{w:.4f}" if w is not None else "N/A"
        wo_str = f"{wo:.4f}" if wo is not None else "N/A"
        delta = ""
        if w is not None and wo is not None:
            diff = w - wo
            delta = f"{diff:+.4f}"
        print(f"  {metric:<23} {w_str:>12} {wo_str:>12} {delta:>10}")

    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
