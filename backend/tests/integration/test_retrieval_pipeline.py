"""
Integration test for the retrieval pipeline.
Requires running Docker Compose services.
"""

import uuid

import pytest

from app.services.ingestion.pipeline import run_ingestion
from app.services.retrieval.pipeline import run_retrieval
from app.services.retrieval.sparse_retriever import build_bm25_index
from app.vector_store.qdrant_client import delete_collection, ensure_collection


@pytest.mark.integration
class TestRetrievalPipeline:
    @pytest.fixture
    def populated_tenant(self, sample_html_content, sample_markdown_content):
        tenant_id = uuid.uuid4()
        ensure_collection(tenant_id)

        # Ingest HTML doc
        run_ingestion(
            tenant_id=tenant_id,
            document_id=uuid.uuid4(),
            filename="report.html",
            file_content=sample_html_content,
            category="reports",
            chunking_strategy="fixed",
        )

        # Ingest Markdown doc
        run_ingestion(
            tenant_id=tenant_id,
            document_id=uuid.uuid4(),
            filename="guide.md",
            file_content=sample_markdown_content,
            category="guides",
            chunking_strategy="fixed",
        )

        yield tenant_id
        delete_collection(tenant_id)

    @pytest.mark.asyncio
    async def test_dense_only_retrieval(self, populated_tenant):
        result = await run_retrieval(
            tenant_id=populated_tenant,
            query="What information is in the first paragraph?",
            search_type="dense_only",
            reranking_enabled=False,
        )

        assert len(result.chunks) > 0
        assert result.timing["retrieval_ms"] >= 0

    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self, populated_tenant):
        # Build BM25 index first
        await build_bm25_index(populated_tenant)

        result = await run_retrieval(
            tenant_id=populated_tenant,
            query="first topic details",
            search_type="hybrid",
            reranking_enabled=False,
        )

        assert len(result.chunks) > 0
        assert "sparse_ms" in result.timing
