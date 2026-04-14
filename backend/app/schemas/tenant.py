import uuid
from datetime import datetime

from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str
    rate_limit_qpm: int = 60


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    rate_limit_qpm: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantCreateResponse(BaseModel):
    tenant: TenantResponse
    api_key: str  # Plaintext key, shown only once


class TenantUsageResponse(BaseModel):
    tenant_id: uuid.UUID
    tenant_name: str
    total_queries: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_estimated_cost: float
    document_count: int
