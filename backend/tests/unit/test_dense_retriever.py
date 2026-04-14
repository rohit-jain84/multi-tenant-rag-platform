"""Tests for build_qdrant_filter in dense_retriever."""

import uuid

from qdrant_client import models as qmodels

from app.schemas.query import MetadataFilter
from app.services.retrieval.dense_retriever import build_qdrant_filter


class TestBuildQdrantFilter:
    def test_none_filter_returns_none(self):
        assert build_qdrant_filter(None) is None

    def test_empty_filter_returns_none(self):
        f = MetadataFilter()
        assert build_qdrant_filter(f) is None

    def test_document_ids_filter(self):
        doc_id = uuid.uuid4()
        f = MetadataFilter(document_ids=[doc_id])
        result = build_qdrant_filter(f)
        assert result is not None
        assert isinstance(result, qmodels.Filter)
        assert len(result.must) == 1

    def test_categories_filter(self):
        f = MetadataFilter(categories=["legal", "finance"])
        result = build_qdrant_filter(f)
        assert result is not None
        assert len(result.must) == 1

    def test_combined_filters(self):
        f = MetadataFilter(
            document_ids=[uuid.uuid4()],
            categories=["legal"],
        )
        result = build_qdrant_filter(f)
        assert result is not None
        assert len(result.must) == 2

    def test_only_empty_lists_returns_none(self):
        f = MetadataFilter(document_ids=[], categories=[])
        assert build_qdrant_filter(f) is None
