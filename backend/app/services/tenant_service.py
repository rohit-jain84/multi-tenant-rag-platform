import asyncio
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.document import Document
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantCreateResponse, TenantResponse, TenantUsageResponse
from app.services.generation.cost_tracker import get_tenant_usage
from app.utils.hashing import generate_api_key, hash_api_key
from app.utils.logging import get_logger
from app.vector_store.qdrant_client import ensure_collection

logger = get_logger(__name__)


async def create_tenant(db: AsyncSession, data: TenantCreate) -> TenantCreateResponse:
    tenant = Tenant(name=data.name, rate_limit_qpm=data.rate_limit_qpm)
    db.add(tenant)
    await db.flush()

    # Generate API key
    raw_key = generate_api_key()
    api_key = ApiKey(
        tenant_id=tenant.id,
        key_hash=hash_api_key(raw_key),
        key_prefix=raw_key[:8],
    )
    db.add(api_key)
    await db.flush()

    # Provision Qdrant collection - run in thread to avoid blocking event loop
    await asyncio.to_thread(ensure_collection, tenant.id)

    logger.info("tenant_created", tenant_id=str(tenant.id), name=data.name)

    return TenantCreateResponse(
        tenant=TenantResponse.model_validate(tenant),
        api_key=raw_key,
    )


async def list_tenants(db: AsyncSession) -> list[TenantResponse]:
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()
    return [TenantResponse.model_validate(t) for t in tenants]


async def get_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


async def get_tenant_usage_summary(
    db: AsyncSession, tenant_id: uuid.UUID
) -> TenantUsageResponse:
    tenant = await get_tenant(db, tenant_id)
    if tenant is None:
        raise ValueError(f"Tenant {tenant_id} not found")

    usage = await get_tenant_usage(db, tenant_id)

    doc_count_result = await db.execute(
        select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
    )
    doc_count = doc_count_result.scalar() or 0

    return TenantUsageResponse(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        total_queries=usage["total_queries"],
        total_prompt_tokens=usage["total_prompt_tokens"],
        total_completion_tokens=usage["total_completion_tokens"],
        total_tokens=usage["total_tokens"],
        total_estimated_cost=usage["total_estimated_cost"],
        document_count=doc_count,
    )
