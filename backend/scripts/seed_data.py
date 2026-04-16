"""
Seed script for Multi-Tenant RAG Platform.

Creates realistic demo data: tenants, API keys, documents, query logs,
and evaluation results. Run from the backend directory:

    python -m scripts.seed_data
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.base import Base
from app.models.tenant import Tenant
from app.models.api_key import ApiKey
from app.models.document import Document, DocumentStatus
from app.models.query_log import QueryLog
from app.models.eval_result import EvalResult
from app.utils.hashing import generate_api_key, hash_api_key

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
random.seed(42)

# ---------------------------------------------------------------------------
# Tenant definitions
# ---------------------------------------------------------------------------
TENANTS = [
    {"name": "acme-corp", "rate_limit_qpm": 60},
    {"name": "legal-firm", "rate_limit_qpm": 120},
    {"name": "tech-startup", "rate_limit_qpm": 30},
]

# ---------------------------------------------------------------------------
# Document definitions per tenant
# ---------------------------------------------------------------------------
DOCUMENTS: dict[str, list[dict]] = {
    "acme-corp": [
        {"filename": "quarterly-report-q4-2025.pdf", "category": "finance", "page_count": 34, "chunk_count": 142},
        {"filename": "employee-handbook-v3.pdf", "category": "hr", "page_count": 45, "chunk_count": 198},
        {"filename": "vendor-contract-acme-supplies.pdf", "category": "legal", "page_count": 12, "chunk_count": 48},
        {"filename": "board-meeting-minutes-jan-2026.pdf", "category": "governance", "page_count": 8, "chunk_count": 32},
        {"filename": "expense-policy-2026.pdf", "category": "finance", "page_count": 6, "chunk_count": 24},
    ],
    "legal-firm": [
        {"filename": "client-nda-template.pdf", "category": "contracts", "page_count": 4, "chunk_count": 16},
        {"filename": "litigation-brief-smith-v-jones.docx", "category": "litigation", "page_count": 28, "chunk_count": 120},
        {"filename": "compliance-audit-2025.pdf", "category": "compliance", "page_count": 18, "chunk_count": 76},
        {"filename": "partnership-agreement-draft.pdf", "category": "contracts", "page_count": 15, "chunk_count": 62},
        {"filename": "ip-patent-filing-us2025.pdf", "category": "ip", "page_count": 22, "chunk_count": 94},
    ],
    "tech-startup": [
        {"filename": "series-a-pitch-deck.pdf", "category": "fundraising", "page_count": 18, "chunk_count": 54},
        {"filename": "technical-architecture-doc.md", "category": "engineering", "page_count": 12, "chunk_count": 68},
        {"filename": "api-documentation-v2.pdf", "category": "engineering", "page_count": 30, "chunk_count": 156},
        {"filename": "product-roadmap-2026.pdf", "category": "product", "page_count": 10, "chunk_count": 40},
        {"filename": "security-audit-report.pdf", "category": "security", "page_count": 24, "chunk_count": 102},
    ],
}

# ---------------------------------------------------------------------------
# Realistic queries per tenant domain
# ---------------------------------------------------------------------------
QUERIES: dict[str, list[str]] = {
    "acme-corp": [
        "What was Q4 2025 total revenue?",
        "What is the PTO policy for full-time employees?",
        "How much did we spend on vendor contracts last quarter?",
        "What were the key decisions from the January board meeting?",
        "What is the maximum reimbursable expense without manager approval?",
        "What was the gross margin percentage in Q4?",
        "How many new hires were onboarded in Q4 2025?",
        "What is the company policy on remote work?",
        "Summarize the vendor contract terms with Acme Supplies.",
        "What are the quarterly revenue targets for 2026?",
        "What benefits are included in the standard employee package?",
        "What was the year-over-year revenue growth?",
        "What is the dress code policy?",
        "Describe the company parental leave policy.",
        "What was EBITDA for Q4 2025?",
        "How are performance reviews conducted?",
        "What are the travel reimbursement limits?",
        "Who were the top-performing sales regions in Q4?",
        "What is the procedure for reporting workplace incidents?",
        "What was the operating expense breakdown for Q4?",
        "Describe the health insurance options available.",
        "What is the company policy on stock option vesting?",
        "How is the annual bonus calculated?",
        "What was the customer churn rate in Q4?",
        "What were the board's strategic priorities for 2026?",
        "What is the policy on moonlighting or side projects?",
        "Summarize the expense report approval workflow.",
        "What was the R&D budget allocation for Q4?",
        "What training programs are available for employees?",
        "How does the 401k matching work?",
        "What was net income for the fiscal year 2025?",
        "What is the policy on workplace harassment?",
        "Summarize the IT equipment reimbursement policy.",
        "What was the accounts receivable aging in Q4?",
        "How many board meetings were held in 2025?",
        "What is the bereavement leave policy?",
        "Describe the annual performance review timeline.",
        "What marketing expenses were incurred in Q4?",
        "What is the policy for using company credit cards?",
        "What was the debt-to-equity ratio at year end?",
        "What is the process for requesting a leave of absence?",
        "How are vendor contracts evaluated for renewal?",
        "What was the inventory turnover ratio in Q4?",
        "Describe the employee referral bonus program.",
        "What cybersecurity policies are in the handbook?",
        "What was the free cash flow in Q4 2025?",
        "How does the company handle whistleblower reports?",
        "What was the capital expenditure for 2025?",
        "What is the policy on conference attendance?",
        "What were the key financial risks identified in Q4?",
    ],
    "legal-firm": [
        "What are the NDA termination clauses?",
        "Summarize the litigation brief for Smith v. Jones.",
        "What compliance gaps were found in the 2025 audit?",
        "What are the key terms of the partnership agreement?",
        "What claims are covered in the patent filing US2025?",
        "What is the confidentiality scope in the NDA template?",
        "What are the damages sought in Smith v. Jones?",
        "List the corrective actions from the compliance audit.",
        "What is the profit-sharing formula in the partnership agreement?",
        "Describe the patent claims in the IP filing.",
        "What is the non-compete clause duration in the NDA?",
        "What evidence was presented in the litigation brief?",
        "What regulatory frameworks were assessed in the compliance audit?",
        "What dispute resolution mechanism is in the partnership agreement?",
        "What prior art was cited in the patent filing?",
        "What are the exceptions to confidentiality in the NDA?",
        "What is the legal basis for the Smith v. Jones claims?",
        "Were there any material weaknesses found in the audit?",
        "What are the capital contribution requirements in the partnership?",
        "What is the scope of the patent protection sought?",
        "How is the NDA enforced across jurisdictions?",
        "What expert witnesses are referenced in the brief?",
        "What data protection findings were in the compliance audit?",
        "How are new partners admitted under the agreement?",
        "What is the filing date and priority date of the patent?",
        "What indemnification clauses are in the NDA?",
        "What settlement offers were discussed in the brief?",
        "What anti-money laundering findings were in the audit?",
        "What governance structure does the partnership define?",
        "What international protections does the patent cover?",
        "What is the governing law for the NDA template?",
        "What procedural history is outlined in the litigation brief?",
        "What employee training gaps were found in the audit?",
        "How is dissolution handled in the partnership agreement?",
        "What continuation patents are referenced?",
        "What are the penalties for NDA breach?",
        "What counterclaims exist in Smith v. Jones?",
        "What cybersecurity findings are in the compliance audit?",
        "What non-compete provisions are in the partnership agreement?",
        "What drawings are included in the patent filing?",
        "What assignment provisions are in the NDA?",
        "What timeline is proposed in the litigation brief?",
        "What were the audit recommendations for vendor management?",
        "What exit provisions does the partnership agreement contain?",
        "What technical specifications are in the patent claims?",
        "How long is the NDA effective after termination?",
        "What damages methodology is used in the brief?",
        "What conflict of interest policies were audited?",
        "What reporting obligations exist in the partnership?",
        "What is the patent abstract summary?",
    ],
    "tech-startup": [
        "What is the API rate limit for authenticated users?",
        "Describe the microservices architecture.",
        "What authentication method does the API use?",
        "What is the product roadmap for Q1 2026?",
        "Summarize the key findings from the security audit.",
        "What was the Series A valuation?",
        "How is data encrypted at rest and in transit?",
        "What are the API versioning conventions?",
        "What features are planned for the Q2 2026 release?",
        "What vulnerabilities were found in the security audit?",
        "What is the total addressable market in the pitch deck?",
        "Describe the database sharding strategy.",
        "What error codes does the API return?",
        "What is the product vision statement?",
        "What penetration testing was performed?",
        "What is the revenue model described in the pitch deck?",
        "How does the message queue architecture work?",
        "What are the API pagination parameters?",
        "What competitive advantages are listed in the roadmap?",
        "What compliance certifications are mentioned in the audit?",
        "What is the burn rate shown in the pitch deck?",
        "How is horizontal scaling handled?",
        "What webhook endpoints are documented?",
        "What key milestones are on the product roadmap?",
        "What OWASP findings were in the security report?",
        "What investor terms are in the Series A deck?",
        "Describe the CI/CD pipeline architecture.",
        "What are the API request/response formats?",
        "How is customer feedback incorporated into the roadmap?",
        "What access control issues were found in the audit?",
        "What is the go-to-market strategy in the pitch deck?",
        "How does service discovery work in the architecture?",
        "What rate limiting strategy does the API implement?",
        "What technical debt items are on the roadmap?",
        "What logging and monitoring findings were in the audit?",
        "What is the competitive landscape in the pitch deck?",
        "Describe the caching architecture and cache invalidation.",
        "What SDK libraries are available for the API?",
        "What infrastructure changes are planned for 2026?",
        "What incident response procedures were audited?",
        "What financial projections are in the Series A deck?",
        "How does the event-driven architecture work?",
        "What are the API authentication scopes?",
        "What user research informed the product roadmap?",
        "What dependency vulnerabilities were flagged?",
        "What team structure is described in the pitch deck?",
        "How is database failover handled?",
        "What are the API deprecation policies?",
        "What mobile features are on the product roadmap?",
        "What cloud security configurations were reviewed?",
    ],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _file_format(filename: str) -> str:
    """Extract format from filename extension."""
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext  # pdf, docx, md


def _random_content_hash() -> str:
    """Generate a random SHA-256-like hex string."""
    return uuid.uuid4().hex + uuid.uuid4().hex  # 64 hex chars


def _random_chunking_strategy() -> str:
    return random.choice(["semantic", "semantic", "semantic", "fixed"])  # 75% semantic


def _make_latency_breakdown(total_ms: int) -> dict:
    """Generate a realistic latency breakdown that sums to total_ms."""
    embedding_ms = random.randint(50, 150)
    retrieval_ms = random.randint(100, 400)
    reranking_ms = random.randint(50, 200)
    generation_ms = total_ms - embedding_ms - retrieval_ms - reranking_ms
    # Ensure generation_ms is reasonable; clamp if needed
    if generation_ms < 100:
        generation_ms = random.randint(300, 500)
    return {
        "embedding_ms": embedding_ms,
        "retrieval_ms": retrieval_ms,
        "reranking_ms": reranking_ms,
        "generation_ms": generation_ms,
        "total_ms": total_ms,
    }


def _make_per_question_results() -> list[dict]:
    """Generate 5 sample per-question evaluation results."""
    sample_questions = [
        "What is the main topic of the document?",
        "Summarize the key findings.",
        "What recommendations were made?",
        "What data supports the conclusion?",
        "Are there any limitations mentioned?",
    ]
    results = []
    for q in sample_questions:
        results.append({
            "question": q,
            "faithfulness": round(random.uniform(0.65, 0.98), 3),
            "answer_relevancy": round(random.uniform(0.60, 0.95), 3),
            "context_precision": round(random.uniform(0.55, 0.92), 3),
            "context_recall": round(random.uniform(0.60, 0.95), 3),
        })
    return results


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

async def seed() -> None:
    print("=" * 60)
    print("  Multi-Tenant RAG Platform — Database Seeder")
    print("=" * 60)
    print()

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Create tables
    print("[1/6] Creating tables (if not exist)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("       Tables ready.")

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    tenant_map: dict[str, Tenant] = {}       # name -> Tenant
    api_key_map: dict[str, str] = {}          # tenant name -> raw API key

    async with async_session() as session:
        async with session.begin():

            # ----------------------------------------------------------
            # Tenants
            # ----------------------------------------------------------
            print("[2/6] Creating tenants...")
            for t_def in TENANTS:
                tenant = Tenant(
                    id=uuid.uuid4(),
                    name=t_def["name"],
                    is_active=True,
                    rate_limit_qpm=t_def["rate_limit_qpm"],
                )
                session.add(tenant)
                tenant_map[t_def["name"]] = tenant
                print(f"       + {t_def['name']} (rate_limit_qpm={t_def['rate_limit_qpm']})")

            # ----------------------------------------------------------
            # API Keys
            # ----------------------------------------------------------
            print("[3/6] Generating API keys...")
            for tenant_name, tenant in tenant_map.items():
                raw_key = generate_api_key()
                hashed = hash_api_key(raw_key)
                api_key = ApiKey(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    key_hash=hashed,
                    key_prefix=raw_key[:8],
                    is_active=True,
                )
                session.add(api_key)
                api_key_map[tenant_name] = raw_key
                print(f"       + Key for {tenant_name}: {raw_key[:8]}...")

            # ----------------------------------------------------------
            # Documents
            # ----------------------------------------------------------
            print("[4/6] Creating documents...")
            doc_count = 0
            for tenant_name, docs in DOCUMENTS.items():
                tenant = tenant_map[tenant_name]
                for doc_def in docs:
                    doc = Document(
                        id=uuid.uuid4(),
                        tenant_id=tenant.id,
                        filename=doc_def["filename"],
                        format=_file_format(doc_def["filename"]),
                        category=doc_def.get("category"),
                        status=DocumentStatus.COMPLETED,
                        content_hash=_random_content_hash(),
                        page_count=doc_def["page_count"],
                        chunk_count=doc_def["chunk_count"],
                        chunking_strategy=_random_chunking_strategy(),
                    )
                    session.add(doc)
                    doc_count += 1
            print(f"       + {doc_count} documents created across {len(DOCUMENTS)} tenants.")

            # ----------------------------------------------------------
            # Query Logs
            # ----------------------------------------------------------
            print("[5/6] Creating query logs...")
            now = datetime.now(timezone.utc)
            query_count = 0
            for tenant_name, queries in QUERIES.items():
                tenant = tenant_map[tenant_name]
                selected_queries = queries[:50]  # exactly 50 per tenant
                for i, query_text in enumerate(selected_queries):
                    # Spread over last 30 days
                    days_ago = random.randint(0, 29)
                    hours_ago = random.randint(0, 23)
                    minutes_ago = random.randint(0, 59)
                    created_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

                    prompt_tokens = random.randint(200, 800)
                    completion_tokens = random.randint(100, 500)
                    total_tokens = prompt_tokens + completion_tokens
                    estimated_cost = (prompt_tokens / 1000) * 0.00015 + (completion_tokens / 1000) * 0.0006

                    latency_ms = random.randint(500, 3000)
                    retrieval_strategy = "hybrid" if random.random() < 0.7 else "dense_only"

                    ql = QueryLog(
                        id=uuid.uuid4(),
                        tenant_id=tenant.id,
                        query_text=query_text,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        estimated_cost=round(estimated_cost, 6),
                        latency_ms=latency_ms,
                        latency_breakdown=_make_latency_breakdown(latency_ms),
                        retrieval_strategy=retrieval_strategy,
                        created_at=created_at,
                    )
                    session.add(ql)
                    query_count += 1
            print(f"       + {query_count} query logs created across {len(QUERIES)} tenants.")

            # ----------------------------------------------------------
            # Eval Results
            # ----------------------------------------------------------
            print("[6/6] Creating evaluation results...")
            eval_configs = [
                # run_id, strategy, reranking, score_offsets (higher = better)
                ("eval-run-001", "hybrid", True, 0.05),
                ("eval-run-001", "dense_only", False, 0.0),
                ("eval-run-002", "hybrid", True, 0.04),
                ("eval-run-002", "dense_only", False, 0.0),
            ]
            for run_id, strategy, reranking, offset in eval_configs:
                er = EvalResult(
                    id=uuid.uuid4(),
                    run_id=run_id,
                    strategy=strategy,
                    reranking_enabled=reranking,
                    faithfulness=round(random.uniform(0.75, 0.90) + offset, 4),
                    answer_relevancy=round(random.uniform(0.70, 0.87) + offset, 4),
                    context_precision=round(random.uniform(0.65, 0.83) + offset, 4),
                    context_recall=round(random.uniform(0.72, 0.86) + offset, 4),
                    per_question_results=_make_per_question_results(),
                )
                session.add(er)
                print(f"       + {run_id} / {strategy} (reranking={reranking})")

    await engine.dispose()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  SEED COMPLETE — Summary")
    print("=" * 60)
    print()
    print(f"  Tenants created:      {len(TENANTS)}")
    print(f"  API keys created:     {len(api_key_map)}")
    print(f"  Documents created:    {doc_count}")
    print(f"  Query logs created:   {query_count}")
    print(f"  Eval results created: {len(eval_configs)}")
    print()
    print("-" * 60)
    print("  API Keys (save these — they cannot be retrieved later)")
    print("-" * 60)
    for tenant_name, raw_key in api_key_map.items():
        print(f"  {tenant_name:20s}  {raw_key}")
    print()
    print("=" * 60)
    print("  Done! You can now test the platform with these credentials.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
