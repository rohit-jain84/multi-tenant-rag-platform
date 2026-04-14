import os
import uuid

from app.config import settings
from app.services.ingestion.chunking import get_chunker
from app.services.ingestion.extractors import get_extractor
from app.utils.hashing import hash_content
from app.utils.logging import get_logger
from app.vector_store.embedding import embed_texts
from app.vector_store.qdrant_client import ensure_collection, upsert_chunks

logger = get_logger(__name__)


class IngestionResult:
    def __init__(self):
        self.chunk_count: int = 0
        self.page_count: int | None = None
        self.content_hash: str = ""


def run_ingestion(
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    filename: str,
    file_content: bytes,
    category: str | None = None,
    chunking_strategy: str | None = None,
) -> IngestionResult:
    strategy = chunking_strategy or settings.DEFAULT_CHUNKING_STRATEGY
    result = IngestionResult()

    logger.info(
        "ingestion_started",
        tenant_id=str(tenant_id),
        document_id=str(document_id),
        filename=filename,
        strategy=strategy,
    )

    # 1. Extract text
    ext = os.path.splitext(filename)[1].lower()
    extractor = get_extractor(ext)
    extracted = extractor.extract(file_content, filename)
    result.page_count = extracted.total_pages
    result.content_hash = hash_content(file_content)

    logger.info(
        "extraction_complete",
        document_id=str(document_id),
        pages=extracted.total_pages,
    )

    if not extracted.pages:
        logger.warning("no_content_extracted", document_id=str(document_id))
        result.chunk_count = 0
        return result

    # 2. Chunk
    chunker = get_chunker(strategy)
    chunks = chunker.chunk(extracted)

    if not chunks:
        logger.warning("no_chunks_produced", document_id=str(document_id))
        result.chunk_count = 0
        return result

    logger.info("chunking_complete", document_id=str(document_id), chunk_count=len(chunks))

    # 3. Embed
    chunk_texts = [c.text for c in chunks]
    embeddings = embed_texts(chunk_texts)

    # 4. Prepare payloads and IDs
    chunk_ids: list[str] = []
    payloads: list[dict] = []
    for i, chunk in enumerate(chunks):
        cid = str(uuid.uuid4())
        chunk_ids.append(cid)
        payloads.append({
            "tenant_id": str(tenant_id),
            "document_id": str(document_id),
            "document_name": filename,
            "page_number": chunk.page_number,
            "section_heading": chunk.section_heading,
            "upload_date": None,  # Set by caller
            "category": category,
            "chunk_index": chunk.chunk_index,
            "chunking_strategy": strategy,
            "text": chunk.text,
            "parent_text": chunk.parent_chunk_text,
        })

    # 5. Store in Qdrant
    ensure_collection(tenant_id)
    upsert_chunks(tenant_id, chunk_ids, embeddings, payloads)

    result.chunk_count = len(chunks)
    logger.info(
        "ingestion_complete",
        document_id=str(document_id),
        chunks_stored=len(chunks),
    )
    return result
