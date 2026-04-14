from abc import ABC, abstractmethod

from app.config import settings
from app.services.retrieval.dense_retriever import RetrievedChunk
from app.utils.logging import get_logger

logger = get_logger(__name__)


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, chunks: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]:
        ...


class CohereReranker(BaseReranker):
    def __init__(self):
        import cohere

        self._client = cohere.Client(settings.COHERE_API_KEY)

    def rerank(self, query: str, chunks: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]:
        if not chunks:
            return []

        documents = [c.text for c in chunks]
        try:
            response = self._client.rerank(
                query=query,
                documents=documents,
                top_n=min(top_n, len(chunks)),
                model="rerank-english-v3.0",
            )
            reranked = []
            for result in response.results:
                chunk = chunks[result.index]
                chunk.score = result.relevance_score
                reranked.append(chunk)
            logger.info("cohere_rerank_complete", results=len(reranked))
            return reranked
        except Exception as e:
            logger.error("cohere_rerank_failed", error=str(e))
            # Return original chunks sorted by existing score instead of crashing
            return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_n]


class CrossEncoderReranker(BaseReranker):
    def __init__(self):
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(settings.CROSS_ENCODER_MODEL)

    def rerank(self, query: str, chunks: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]:
        if not chunks:
            return []

        pairs = [[query, c.text] for c in chunks]
        scores = self._model.predict(pairs)

        for i, score in enumerate(scores):
            chunks[i].score = float(score)

        ranked = sorted(chunks, key=lambda c: c.score, reverse=True)
        result = ranked[:top_n]
        logger.info("cross_encoder_rerank_complete", results=len(result))
        return result


def get_reranker() -> BaseReranker:
    if settings.RERANKER_TYPE == "cohere" and settings.COHERE_API_KEY:
        return CohereReranker()
    return CrossEncoderReranker()


def rerank_with_fallback(
    query: str, chunks: list[RetrievedChunk], top_n: int
) -> list[RetrievedChunk]:
    """Try Cohere reranker first, fall back to local cross-encoder."""
    if settings.RERANKER_TYPE == "cohere" and settings.COHERE_API_KEY:
        try:
            return CohereReranker().rerank(query, chunks, top_n)
        except Exception:
            logger.warning("cohere_unavailable_falling_back_to_cross_encoder")

    return CrossEncoderReranker().rerank(query, chunks, top_n)
