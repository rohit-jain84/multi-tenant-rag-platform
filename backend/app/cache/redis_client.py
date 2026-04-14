import hashlib
import json
import time

import redis.asyncio as aioredis

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


# --- Rate Limiting ---

async def check_rate_limit(tenant_id: str, rate_limit_qpm: int) -> tuple[bool, int]:
    """Returns (allowed, retry_after_seconds). Uses sliding window counter."""
    r = await get_redis()
    now = int(time.time())
    minute_bucket = now // 60
    key = f"rate:{tenant_id}:{minute_bucket}"

    current = await r.get(key)
    current_count = int(current) if current else 0

    if current_count >= rate_limit_qpm:
        retry_after = 60 - (now % 60)
        return False, retry_after

    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, 120)  # Expire after 2 minutes
    await pipe.execute()
    return True, 0


# --- Query Cache ---

def _cache_key(tenant_id: str, query: str, filters: dict | None) -> str:
    payload = json.dumps({"q": query, "f": filters}, sort_keys=True, default=str)
    h = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"cache:{tenant_id}:{h}"


async def get_cached_response(tenant_id: str, query: str, filters: dict | None) -> dict | None:
    r = await get_redis()
    key = _cache_key(tenant_id, query, filters)
    data = await r.get(key)
    if data:
        logger.info("cache_hit", key=key)
        return json.loads(data)
    logger.debug("cache_miss", key=key)
    return None


async def set_cached_response(
    tenant_id: str, query: str, filters: dict | None, response: dict
) -> None:
    r = await get_redis()
    key = _cache_key(tenant_id, query, filters)
    await r.setex(key, settings.QUERY_CACHE_TTL_SECONDS, json.dumps(response, default=str))


# --- BM25 Index Storage ---

async def store_bm25_corpus(tenant_id: str, corpus_data: str) -> None:
    r = await get_redis()
    await r.set(f"bm25:{tenant_id}", corpus_data)


async def get_bm25_corpus(tenant_id: str) -> str | None:
    r = await get_redis()
    return await r.get(f"bm25:{tenant_id}")


async def delete_bm25_corpus(tenant_id: str) -> None:
    r = await get_redis()
    await r.delete(f"bm25:{tenant_id}")


# --- Health ---

async def check_health() -> bool:
    try:
        r = await get_redis()
        return await r.ping()
    except Exception:
        return False
