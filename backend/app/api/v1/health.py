import time

from fastapi import APIRouter
from sqlalchemy import text

from app.cache.redis_client import check_health as redis_health
from app.db.session import async_session_factory
from app.vector_store.qdrant_client import check_health as qdrant_health

router = APIRouter()


@router.get("/health")
async def health_check():
    status = {"status": "healthy", "services": {}}

    # PostgreSQL
    try:
        t0 = time.perf_counter()
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        latency = int((time.perf_counter() - t0) * 1000)
        status["services"]["postgresql"] = {"status": "up", "latency_ms": latency}
    except Exception:
        status["services"]["postgresql"] = {"status": "down"}
        status["status"] = "degraded"

    # Redis
    try:
        t0 = time.perf_counter()
        redis_ok = await redis_health()
        latency = int((time.perf_counter() - t0) * 1000)
        if redis_ok:
            status["services"]["redis"] = {"status": "up", "latency_ms": latency}
        else:
            status["services"]["redis"] = {"status": "down"}
            status["status"] = "degraded"
    except Exception:
        status["services"]["redis"] = {"status": "down"}
        status["status"] = "degraded"

    # Qdrant
    try:
        t0 = time.perf_counter()
        qdrant_ok = qdrant_health()
        latency = int((time.perf_counter() - t0) * 1000)
        if qdrant_ok:
            status["services"]["vector_db"] = {"status": "up", "latency_ms": latency}
        else:
            status["services"]["vector_db"] = {"status": "down"}
            status["status"] = "degraded"
    except Exception:
        status["services"]["vector_db"] = {"status": "down"}
        status["status"] = "degraded"

    return status
