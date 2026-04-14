from collections.abc import AsyncGenerator

import httpx

from app.config import settings
from app.services.retrieval.dense_retriever import RetrievedChunk
from app.utils.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful document Q&A assistant. Answer the user's question ONLY using the provided source context below. Follow these rules strictly:

1. Only use information present in the provided sources. Do NOT use external knowledge.
2. Cite your sources using [Source N] notation inline in your answer, where N corresponds to the source number.
3. If the provided context does not contain enough information to answer the question, say: "I don't have enough information in the provided documents to answer this question."
4. Be concise and accurate. Provide specific details from the sources when available.
5. If multiple sources support a claim, cite all relevant sources."""


def _format_context(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        # Use parent text if available (parent-child strategy)
        text = chunk.parent_text or chunk.text
        loc = f"{chunk.document_name}"
        if chunk.page_number:
            loc += f", p.{chunk.page_number}"
        if chunk.section_heading:
            loc += f", section: {chunk.section_heading}"
        parts.append(f"[Source {i}] ({loc}):\n{text}")
    return "\n\n---\n\n".join(parts)


async def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
) -> dict:
    """Non-streaming LLM call. Returns {"content": str, "usage": dict}."""
    context = _format_context(chunks)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.LLM_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1024,
            },
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    return {
        "content": content,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    }


async def generate_answer_stream(
    question: str,
    chunks: list[RetrievedChunk],
) -> AsyncGenerator[str | dict, None]:
    """Streaming LLM call. Yields content tokens (str) as they arrive.

    The final yielded item is a dict with key ``"usage"`` containing token
    counts captured from the API's ``stream_options.include_usage`` response,
    or estimated via *tiktoken* when the API doesn't provide them.
    """
    context = _format_context(chunks)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    prompt_text = SYSTEM_PROMPT + context + question  # for tiktoken fallback

    usage_from_api: dict | None = None

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.LLM_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1024,
                "stream": True,
                "stream_options": {"include_usage": True},
            },
        ) as response:
            response.raise_for_status()
            full_content = ""
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    import json

                    data = json.loads(data_str)

                    # Capture usage from the final chunk (OpenAI sends it
                    # when stream_options.include_usage is true)
                    if data.get("usage"):
                        usage_from_api = data["usage"]

                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_content += content
                        yield content
                except (KeyError, IndexError, json.JSONDecodeError):
                    continue

    # Build usage dict — prefer API-reported values, fall back to tiktoken
    if usage_from_api:
        usage = {
            "prompt_tokens": usage_from_api.get("prompt_tokens", 0),
            "completion_tokens": usage_from_api.get("completion_tokens", 0),
            "total_tokens": usage_from_api.get("total_tokens", 0),
        }
    else:
        usage = _estimate_tokens(prompt_text, full_content)
        logger.debug("stream_usage_estimated", usage=usage)

    yield {"usage": usage}


def _estimate_tokens(prompt_text: str, completion_text: str) -> dict:
    """Estimate token counts using tiktoken when the API doesn't report them."""
    try:
        import tiktoken

        enc = tiktoken.encoding_for_model(settings.LLM_MODEL)
        prompt_tokens = len(enc.encode(prompt_text))
        completion_tokens = len(enc.encode(completion_text))
    except Exception:
        # Rough fallback: ~4 chars per token
        prompt_tokens = len(prompt_text) // 4
        completion_tokens = len(completion_text) // 4
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
