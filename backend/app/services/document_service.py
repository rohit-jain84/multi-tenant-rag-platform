import asyncio
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.ingestion.pipeline import IngestionResult, run_ingestion
from app.services.retrieval.sparse_retriever import build_bm25_index
from app.utils.hashing import hash_content
from app.utils.logging import get_logger
from app.vector_store.qdrant_client import delete_by_document

logger = get_logger(__name__)


async def create_document(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    filename: str,
    file_format: str,
    file_content: bytes,
    category: str | None = None,
    chunking_strategy: str | None = None,
) -> Document:
    content_hash = hash_content(file_content)

    # Check for duplicates
    existing = await db.execute(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.content_hash == content_hash,
        )
    )
    if existing.scalar_one_or_none():
        from app.utils.errors import ConflictError
        raise ConflictError(f"Document with identical content already exists for this tenant")

    doc = Document(
        tenant_id=tenant_id,
        filename=filename,
        format=file_format,
        category=category,
        status=DocumentStatus.PROCESSING,
        content_hash=content_hash,
        chunking_strategy=chunking_strategy,
    )
    db.add(doc)
    await db.flush()

    # Run ingestion - in thread to avoid blocking the event loop
    try:
        result: IngestionResult = await asyncio.to_thread(
            run_ingestion,
            tenant_id=tenant_id,
            document_id=doc.id,
            filename=filename,
            file_content=file_content,
            category=category,
            chunking_strategy=chunking_strategy,
        )
        doc.status = DocumentStatus.COMPLETED
        doc.page_count = result.page_count
        doc.chunk_count = result.chunk_count
        await db.flush()

        # Rebuild BM25 index
        await build_bm25_index(tenant_id)

    except Exception as e:
        doc.status = DocumentStatus.FAILED
        doc.error_message = str(e)
        await db.flush()
        logger.error("ingestion_failed", document_id=str(doc.id), error=str(e))
        raise

    return doc


async def get_document(
    db: AsyncSession, tenant_id: uuid.UUID, document_id: uuid.UUID
) -> Document | None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.tenant_id == tenant_id
        )
    )
    return result.scalar_one_or_none()


async def list_documents(
    db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> DocumentListResponse:
    # Count
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
    )
    total = count_result.scalar() or 0

    # Fetch page
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Document)
        .where(Document.tenant_id == tenant_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    docs = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


async def delete_document(
    db: AsyncSession, tenant_id: uuid.UUID, document_id: uuid.UUID
) -> bool:
    doc = await get_document(db, tenant_id, document_id)
    if doc is None:
        return False

    # Delete chunks from Qdrant - run in thread to avoid blocking event loop
    await asyncio.to_thread(delete_by_document, tenant_id, document_id)

    # Delete from DB
    await db.delete(doc)
    await db.flush()

    # Rebuild BM25 index
    await build_bm25_index(tenant_id)

    logger.info("document_deleted", document_id=str(document_id), tenant_id=str(tenant_id))
    return True
