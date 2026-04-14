import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    format: str
    category: str | None
    status: str
    upload_date: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    filename: str
    format: str
    category: str | None
    status: str
    error_message: str | None
    content_hash: str | None
    page_count: int | None
    chunk_count: int | None
    chunking_strategy: str | None
    upload_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int
