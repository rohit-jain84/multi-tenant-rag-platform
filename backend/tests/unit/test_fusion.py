from app.services.retrieval.dense_retriever import RetrievedChunk
from app.services.retrieval.fusion import reciprocal_rank_fusion


def _make_chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=f"Text for {chunk_id}",
        score=score,
        document_id="doc1",
        document_name="test.pdf",
    )


class TestRRFFusion:
    def test_basic_fusion(self):
        dense = [_make_chunk("a", 0.9), _make_chunk("b", 0.8), _make_chunk("c", 0.7)]
        sparse = [_make_chunk("b", 5.0), _make_chunk("d", 4.0), _make_chunk("a", 3.0)]

        fused = reciprocal_rank_fusion(dense, sparse, k=60)

        # "a" and "b" should be ranked highest (appear in both lists)
        ids = [c.chunk_id for c in fused]
        assert "a" in ids[:3]
        assert "b" in ids[:3]
        # All unique chunks present
        assert set(ids) == {"a", "b", "c", "d"}

    def test_empty_lists(self):
        fused = reciprocal_rank_fusion([], [])
        assert fused == []

    def test_one_empty_list(self):
        dense = [_make_chunk("a", 0.9)]
        fused = reciprocal_rank_fusion(dense, [])
        assert len(fused) == 1
        assert fused[0].chunk_id == "a"

    def test_scores_are_rrf(self):
        dense = [_make_chunk("a", 0.9)]
        sparse = [_make_chunk("a", 5.0)]
        fused = reciprocal_rank_fusion(dense, sparse, k=60)
        # RRF score for "a" = 1/(60+1) + 1/(60+1) = 2/61
        expected = 2.0 / 61.0
        assert abs(fused[0].score - expected) < 0.001
