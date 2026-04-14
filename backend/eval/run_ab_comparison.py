#!/usr/bin/env python3
"""
Run A/B comparison: hybrid vs. dense-only retrieval.

Usage:
    python eval/run_ab_comparison.py --tenant-id <uuid>
"""

import argparse
import asyncio
import uuid
from datetime import datetime, timezone

from app.db.session import async_session_factory
from app.services.evaluation.ab_comparison import run_ab_comparison


async def main():
    parser = argparse.ArgumentParser(description="Run A/B comparison")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    args = parser.parse_args()

    tenant_id = uuid.UUID(args.tenant_id)
    run_id = f"ab_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    async with async_session_factory() as db:
        comparison = await run_ab_comparison(db, tenant_id, run_id)
        await db.commit()

    print(f"\n{'='*60}")
    print(f"A/B Comparison: Hybrid vs. Dense-Only - {run_id}")
    print(f"{'='*60}")

    header = f"{'Metric':<25} {'Hybrid':>12} {'Dense Only':>12} {'Delta':>10}"
    print(header)
    print("-" * 60)

    for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        h = comparison["hybrid"].get(metric)
        d = comparison["dense_only"].get(metric)
        h_str = f"{h:.4f}" if h is not None else "N/A"
        d_str = f"{d:.4f}" if d is not None else "N/A"
        delta = ""
        if h is not None and d is not None:
            diff = h - d
            delta = f"{diff:+.4f}"
        print(f"  {metric:<23} {h_str:>12} {d_str:>12} {delta:>10}")

    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
