import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_tenant_id
from app.schemas.document import DocumentListResponse, DocumentResponse, DocumentUploadResponse
from app.services.document_service import (
    create_document,
    delete_document,
    get_document,
    list_documents,
)
from app.services.ingestion.extractors import SUPPORTED_FORMATS
from app.utils.errors import NotFoundError, UnsupportedFormatError

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    category: str | None = Form(None),
    chunking_strategy: str | None = Form(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB

    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(ext)

    content = await file.read()

    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum upload size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
        )

    doc = await create_document(
        db=db,
        tenant_id=tenant_id,
        filename=filename,
        file_format=ext.lstrip("."),
        file_content=content,
        category=category,
        chunking_strategy=chunking_strategy,
    )

    return DocumentUploadResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
async def list_tenant_documents(
    page: int = 1,
    page_size: int = 20,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_documents(db, tenant_id, page, page_size)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_detail(
    document_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    doc = await get_document(db, tenant_id, document_id)
    if doc is None:
        raise NotFoundError("Document", str(document_id))
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}", status_code=204)
async def remove_document(
    document_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_document(db, tenant_id, document_id)
    if not deleted:
        raise NotFoundError("Document", str(document_id))
