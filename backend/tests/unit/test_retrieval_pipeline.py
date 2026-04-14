"""Tests for retrieval pipeline orchestration logic."""

import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.retrieval.dense_retriever import RetrievedChunk
from app.services.retrieval.pipeline import run_retrieval


def _make_chunk(chunk_id: str = "c1", score: float = 0.9, text: str = "chunk") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        score=score,
        document_id="d1",
        document_name="doc.pdf",
    )


@pytest.mark.asyncio
class TestRunRetrieval:
    @patch("app.services.retrieval.pipeline.rerank_with_fallback")
    @patch("app.services.retrieval.pipeline.reciprocal_rank_fusion")
    @patch("app.services.retrieval.pipeline.sparse_retrieve", new_callable=AsyncMock)
    @patch("app.services.retrieval.pipeline.dense_retrieve")
    async def test_hybrid_runs_both_retrievers(
        self, mock_dense, mock_sparse, mock_fusion, mock_rerank
    ):
        tid = uuid.uuid4()
        dense_chunks = [_make_chunk("d1", 0.9)]
        sparse_chunks = [_make_chunk("s1", 0.8)]
        fused_chunks = [_make_chunk("f1", 0.85)]

        mock_dense.return_value = dense_chunks
        mock_sparse.return_value = sparse_chunks
        mock_fusion.return_value = fused_chunks
        mock_rerank.return_value = fused_chunks

        result = await run_retrieval(tid, "test query", search_type="hybrid")

        mock_dense.assert_called_once()
        mock_sparse.assert_awaited_once()
        mock_fusion.assert_called_once_with(dense_chunks, sparse_chunks)

    @patch("app.services.retrieval.pipeline.rerank_with_fallback")
    @patch("app.services.retrieval.pipeline.dense_retrieve")
    async def test_dense_only_skips_sparse(self, mock_dense, mock_rerank):
        tid = uuid.uuid4()
        chunks = [_make_chunk("d1", 0.9)]
        mock_dense.return_value = chunks
        mock_rerank.return_value = chunks

        result = await run_retrieval(tid, "test query", search_type="dense_only")

        mock_dense.assert_called_once()
        assert result.timing["sparse_ms"] == 0
        assert result.timing["fusion_ms"] == 0

    @patch("app.services.retrieval.pipeline.dense_retrieve")
    async def test_no_reranking_when_disabled(self, mock_dense):
        tid = uuid.uuid4()
        chunks = [_make_chunk("d1", 0.9), _make_chunk("d2", 0.7)]
        mock_dense.return_value = chunks

        result = await run_retrieval(
            tid, "test query", search_type="dense_only", reranking_enabled=False
        )

        assert result.timing["reranking_ms"] == 0
        assert len(result.chunks) <= 5  # DEFAULT_TOP_N

    @patch("app.services.retrieval.pipeline.dense_retrieve")
    async def test_empty_results(self, mock_dense):
        tid = uuid.uuid4()
        mock_dense.return_value = []

        result = await run_retrieval(
            tid, "test query", search_type="dense_only", reranking_enabled=False
        )

        assert result.chunks == []
        assert "retrieval_ms" in result.timing

    @patch("app.services.retrieval.pipeline.rerank_with_fallback")
    @patch("app.services.retrieval.pipeline.reciprocal_rank_fusion")
    @patch("app.services.retrieval.pipeline.sparse_retrieve", new_callable=AsyncMock)
    @patch("app.services.retrieval.pipeline.dense_retrieve")
    async def test_timing_keys_present(
        self, mock_dense, mock_sparse, mock_fusion, mock_rerank
    ):
        tid = uuid.uuid4()
        chunks = [_make_chunk()]
        mock_dense.return_value = chunks
        mock_sparse.return_value = chunks
        mock_fusion.return_value = chunks
        mock_rerank.return_value = chunks

        result = await run_retrieval(tid, "query", search_type="hybrid")

        assert "embedding_and_dense_ms" in result.timing
        assert "sparse_ms" in result.timing
        assert "fusion_ms" in result.timing
        assert "reranking_ms" in result.timing
        assert "retrieval_ms" in result.timing
