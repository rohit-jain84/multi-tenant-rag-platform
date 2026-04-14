import json
from collections.abc import AsyncGenerator, Awaitable, Callable

from app.schemas.query import Citation
from app.services.generation.llm_service import generate_answer_stream
from app.services.retrieval.dense_retriever import RetrievedChunk


async def stream_response(
    question: str,
    chunks: list[RetrievedChunk],
    citations: list[Citation],
    metadata: dict,
    on_complete: Callable[[dict], Awaitable[None]] | None = None,
) -> AsyncGenerator[dict, None]:
    """Yields event dicts for SSE streaming. EventSourceResponse handles formatting.

    Args:
        on_complete: Optional async callback invoked with a ``usage`` dict
            (prompt_tokens, completion_tokens, total_tokens) after the LLM
            stream finishes.  Used to log token counts after they are known.
    """
    full_answer = ""
    usage: dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    if not chunks:
        # Low confidence - no sufficient context
        full_answer = "I don't have enough information in the provided documents to answer this question."
        yield {"data": json.dumps({"type": "token", "content": full_answer})}
    else:
        # Stream tokens
        async for item in generate_answer_stream(question, chunks):
            if isinstance(item, dict) and "usage" in item:
                # Final item from the LLM stream contains token usage
                usage = item["usage"]
            else:
                full_answer += item
                yield {"data": json.dumps({"type": "token", "content": item})}

    # Invoke the logging callback with real token counts
    if on_complete:
        await on_complete(usage)

    # Send citations
    citations_data = [c.model_dump(mode="json") for c in citations]
    yield {"data": json.dumps({"type": "citations", "content": citations_data})}

    # Send metadata (include token usage so the client can display it)
    metadata["answer_length"] = len(full_answer)
    metadata["tokens"] = usage
    yield {"data": json.dumps({"type": "metadata", "content": metadata})}

    # Done
    yield {"data": json.dumps({"type": "done", "content": None})}
