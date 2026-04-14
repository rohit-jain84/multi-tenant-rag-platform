import uuid

from fastapi import Request
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.db.session import async_session_factory
from app.models.api_key import ApiKey
from app.models.tenant import Tenant
from app.utils.hashing import verify_api_key
from app.utils.logging import correlation_id_var, get_logger

logger = get_logger(__name__)

# Paths that don't require tenant auth
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
ADMIN_PREFIX = "/api/v1/admin"


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Set correlation ID for request
        correlation_id_var.set(str(uuid.uuid4()))

        path = request.url.path

        # Public paths bypass auth
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Admin paths use admin API key
        if path.startswith(ADMIN_PREFIX):
            return await self._handle_admin_auth(request, call_next)

        # Tenant API paths require tenant API key
        if path.startswith("/api/"):
            return await self._handle_tenant_auth(request, call_next)

        return await call_next(request)

    async def _handle_admin_auth(self, request: Request, call_next):
        from app.config import settings

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "unauthorized", "message": "Missing or invalid Authorization header"}},
            )

        token = auth_header[7:]
        if token != settings.ADMIN_API_KEY:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "unauthorized", "message": "Invalid admin API key"}},
            )

        return await call_next(request)

    async def _handle_tenant_auth(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "unauthorized", "message": "Missing or invalid Authorization header"}},
            )

        token = auth_header[7:]

        async with async_session_factory() as session:
            # Look up active API keys matching the prefix
            prefix = token[:8]
            result = await session.execute(
                select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True))
            )
            api_keys = result.scalars().all()

            tenant_id = None
            for api_key in api_keys:
                if verify_api_key(token, api_key.key_hash):
                    tenant_id = api_key.tenant_id
                    break

            if tenant_id is None:
                return JSONResponse(
                    status_code=401,
                    content={"error": {"code": "unauthorized", "message": "Invalid API key"}},
                )

            # Verify tenant is active
            tenant_result = await session.execute(
                select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active.is_(True))
            )
            tenant = tenant_result.scalar_one_or_none()
            if tenant is None:
                return JSONResponse(
                    status_code=401,
                    content={"error": {"code": "unauthorized", "message": "Tenant is inactive"}},
                )

            request.state.tenant_id = tenant_id
            request.state.tenant = tenant

        logger.info("authenticated", tenant_id=str(tenant_id), path=request.url.path)
        return await call_next(request)
