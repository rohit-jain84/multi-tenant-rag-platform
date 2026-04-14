"""
Integration test for the full ingestion pipeline.
Requires running Docker Compose services.
"""

import uuid

import pytest

from app.services.ingestion.pipeline import run_ingestion
from app.vector_store.qdrant_client import delete_collection, ensure_collection, search_vectors
from app.vector_store.embedding import embed_query


@pytest.mark.integration
class TestIngestionPipeline:
    def test_ingest_html_fixed_chunking(self, sample_html_content):
        tenant_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        ensure_collection(tenant_id)

        try:
            result = run_ingestion(
                tenant_id=tenant_id,
                document_id=doc_id,
                filename="test.html",
                file_content=sample_html_content,
                category="test",
                chunking_strategy="fixed",
            )

            assert result.chunk_count > 0
            assert result.content_hash

            # Verify chunks are searchable
            query_vec = embed_query("first paragraph")
            results = search_vectors(tenant_id, query_vec, top_k=5)
            assert len(results) > 0

            # Verify metadata
            payload = results[0].payload
            assert payload["document_id"] == str(doc_id)
            assert payload["chunking_strategy"] == "fixed"
        finally:
            delete_collection(tenant_id)

    def test_ingest_markdown_semantic_chunking(self, sample_markdown_content):
        tenant_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        ensure_collection(tenant_id)

        try:
            result = run_ingestion(
                tenant_id=tenant_id,
                document_id=doc_id,
                filename="test.md",
                file_content=sample_markdown_content,
                category="docs",
                chunking_strategy="semantic",
            )

            assert result.chunk_count > 0

            query_vec = embed_query("first topic")
            results = search_vectors(tenant_id, query_vec, top_k=5)
            assert len(results) > 0
        finally:
            delete_collection(tenant_id)

    def test_ingest_docx(self, sample_docx_content):
        tenant_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        ensure_collection(tenant_id)

        try:
            result = run_ingestion(
                tenant_id=tenant_id,
                document_id=doc_id,
                filename="test.docx",
                file_content=sample_docx_content,
                chunking_strategy="fixed",
            )

            assert result.chunk_count > 0
        finally:
            delete_collection(tenant_id)
