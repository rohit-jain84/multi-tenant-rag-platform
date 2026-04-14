from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware.auth import AuthMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.cache.redis_client import close_redis, get_redis
from app.db.session import engine
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # Startup: ensure connections are ready
    await get_redis()
    yield
    # Shutdown
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="Multi-Tenant RAG Platform",
    description="Production-grade multi-tenant document Q&A system with hybrid retrieval, reranking, and citations",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware (order matters: auth runs first, then rate limit)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Routes
app.include_router(health_router)
app.include_router(api_v1_router)
