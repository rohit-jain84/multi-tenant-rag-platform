from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.cache.redis_client import check_rate_limit
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only rate limit query endpoints
        if not request.url.path.startswith("/api/v1/query"):
            return await call_next(request)

        tenant_id = getattr(request.state, "tenant_id", None)
        tenant = getattr(request.state, "tenant", None)

        if tenant_id is None or tenant is None:
            return await call_next(request)

        rate_limit = tenant.rate_limit_qpm
        allowed, retry_after = await check_rate_limit(str(tenant_id), rate_limit)

        if not allowed:
            logger.warning("rate_limited", tenant_id=str(tenant_id), retry_after=retry_after)
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limited", "message": f"Rate limit exceeded. Retry after {retry_after}s"}},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
