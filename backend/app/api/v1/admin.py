import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.eval_result import EvalResult
from app.schemas.eval import EvalResultResponse, EvalResultsListResponse, EvalRunRequest
from app.schemas.tenant import TenantCreate, TenantCreateResponse, TenantResponse, TenantUsageResponse
from app.services.evaluation.ab_comparison import get_eval_results
from app.services.evaluation.ragas_runner import run_ragas_evaluation
from app.services.tenant_service import create_tenant, get_tenant_usage_summary, list_tenants
from app.utils.errors import NotFoundError

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Tenant Management ---

@router.post("/tenants", response_model=TenantCreateResponse, status_code=201)
async def provision_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_tenant(db, body)


@router.get("/tenants", response_model=list[TenantResponse])
async def get_tenants(db: AsyncSession = Depends(get_db)):
    return await list_tenants(db)


@router.get("/tenants/{tenant_id}/usage", response_model=TenantUsageResponse)
async def get_usage(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_tenant_usage_summary(db, tenant_id)
    except ValueError:
        raise NotFoundError("Tenant", str(tenant_id))


# --- Evaluation ---

@router.post("/eval/run", response_model=EvalResultResponse)
async def trigger_evaluation(
    body: EvalRunRequest,
    tenant_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    if tenant_id is None:
        raise NotFoundError("Tenant", "must specify tenant_id query parameter")

    run_id = f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    result = await run_ragas_evaluation(
        db=db,
        tenant_id=tenant_id,
        run_id=run_id,
        strategy=body.strategy,
        reranking_enabled=body.reranking_enabled,
    )

    return EvalResultResponse.model_validate(result)


@router.get("/eval/results", response_model=EvalResultsListResponse)
async def get_evaluation_results(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    results = await get_eval_results(db, limit)
    return EvalResultsListResponse(
        results=[EvalResultResponse.model_validate(r) for r in results],
        total=len(results),
    )


# --- Config ---

@router.get("/config/chunking-strategies")
async def get_chunking_strategies():
    return {
        "strategies": [
            {
                "name": "fixed",
                "description": "Fixed-size token chunking with configurable overlap",
            },
            {
                "name": "semantic",
                "description": "Embedding similarity-based semantic chunking",
            },
            {
                "name": "parent_child",
                "description": "Hierarchical parent-child chunking for precise retrieval with broad context",
            },
        ]
    }
