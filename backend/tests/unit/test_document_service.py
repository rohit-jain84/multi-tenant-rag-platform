"""Tests for document service business logic."""

import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.document_service import create_document, get_document, delete_document


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


class TestCreateDocument:
    @pytest.mark.asyncio
    @patch("app.services.document_service.build_bm25_index", new_callable=AsyncMock)
    @patch("app.services.document_service.run_ingestion")
    async def test_successful_ingestion(self, mock_ingest, mock_bm25, mock_db, tenant_id):
        # No duplicate found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        ingest_result = MagicMock()
        ingest_result.page_count = 3
        ingest_result.chunk_count = 15
        mock_ingest.return_value = ingest_result

        doc = await create_document(
            db=mock_db,
            tenant_id=tenant_id,
            filename="test.html",
            file_format="html",
            file_content=b"<html>test</html>",
        )

        mock_ingest.assert_called_once()
        mock_bm25.assert_awaited_once_with(tenant_id)
        assert doc.status.value == "completed"

    @pytest.mark.asyncio
    async def test_duplicate_raises_conflict(self, mock_db, tenant_id):
        # Duplicate found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # existing doc
        mock_db.execute = AsyncMock(return_value=mock_result)

        from app.utils.errors import ConflictError

        with pytest.raises(ConflictError):
            await create_document(
                db=mock_db,
                tenant_id=tenant_id,
                filename="test.html",
                file_format="html",
                file_content=b"<html>duplicate</html>",
            )

    @pytest.mark.asyncio
    @patch("app.services.document_service.run_ingestion")
    async def test_failed_ingestion_sets_status(self, mock_ingest, mock_db, tenant_id):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_ingest.side_effect = RuntimeError("Extraction failed")

        with pytest.raises(RuntimeError):
            await create_document(
                db=mock_db,
                tenant_id=tenant_id,
                filename="bad.pdf",
                file_format="pdf",
                file_content=b"not a pdf",
            )


class TestDeleteDocument:
    @pytest.mark.asyncio
    @patch("app.services.document_service.build_bm25_index", new_callable=AsyncMock)
    @patch("app.services.document_service.delete_by_document")
    @patch("app.services.document_service.get_document")
    async def test_delete_existing_document(self, mock_get, mock_qdrant_del, mock_bm25, mock_db, tenant_id):
        doc_id = uuid.uuid4()
        mock_doc = MagicMock()
        mock_get.return_value = mock_doc

        result = await delete_document(mock_db, tenant_id, doc_id)

        assert result is True
        mock_qdrant_del.assert_called_once_with(tenant_id, doc_id)
        mock_db.delete.assert_awaited_once_with(mock_doc)
        mock_bm25.assert_awaited_once_with(tenant_id)

    @pytest.mark.asyncio
    @patch("app.services.document_service.get_document")
    async def test_delete_nonexistent_returns_false(self, mock_get, mock_db, tenant_id):
        mock_get.return_value = None
        result = await delete_document(mock_db, tenant_id, uuid.uuid4())
        assert result is False
