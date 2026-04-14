"""Tests for rate limit middleware logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.middleware.rate_limit import RateLimitMiddleware


def _make_request(path: str, tenant_id=None, tenant=None) -> MagicMock:
    request = MagicMock(spec=Request)
    request.url.path = path
    request.state = MagicMock()
    request.state.tenant_id = tenant_id
    request.state.tenant = tenant
    return request


def _make_tenant(rate_limit_qpm: int = 60) -> MagicMock:
    tenant = MagicMock()
    tenant.rate_limit_qpm = rate_limit_qpm
    return tenant


class TestRateLimitMiddleware:
    @pytest.fixture
    def middleware(self):
        app = MagicMock()
        return RateLimitMiddleware(app)

    @pytest.mark.asyncio
    async def test_skips_non_query_paths(self, middleware):
        request = _make_request("/api/v1/documents")
        call_next = AsyncMock(return_value=JSONResponse(content={"ok": True}))

        response = await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_skips_when_no_tenant(self, middleware):
        request = _make_request("/api/v1/query", tenant_id=None, tenant=None)
        call_next = AsyncMock(return_value=JSONResponse(content={"ok": True}))

        response = await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    @patch("app.api.middleware.rate_limit.check_rate_limit")
    async def test_allows_when_under_limit(self, mock_check, middleware):
        tenant = _make_tenant(rate_limit_qpm=60)
        request = _make_request("/api/v1/query", tenant_id="t1", tenant=tenant)
        call_next = AsyncMock(return_value=JSONResponse(content={"ok": True}))
        mock_check.return_value = (True, 0)

        response = await middleware.dispatch(request, call_next)

        call_next.assert_awaited_once_with(request)
        mock_check.assert_awaited_once_with("t1", 60)

    @pytest.mark.asyncio
    @patch("app.api.middleware.rate_limit.check_rate_limit")
    async def test_blocks_when_over_limit(self, mock_check, middleware):
        tenant = _make_tenant(rate_limit_qpm=10)
        request = _make_request("/api/v1/query", tenant_id="t1", tenant=tenant)
        call_next = AsyncMock()
        mock_check.return_value = (False, 45)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429
        call_next.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.api.middleware.rate_limit.check_rate_limit")
    async def test_429_includes_retry_after_header(self, mock_check, middleware):
        tenant = _make_tenant(rate_limit_qpm=10)
        request = _make_request("/api/v1/query", tenant_id="t1", tenant=tenant)
        call_next = AsyncMock()
        mock_check.return_value = (False, 30)

        response = await middleware.dispatch(request, call_next)

        assert response.headers["Retry-After"] == "30"

    @pytest.mark.asyncio
    @patch("app.api.middleware.rate_limit.check_rate_limit")
    async def test_applies_to_stream_endpoint(self, mock_check, middleware):
        tenant = _make_tenant(rate_limit_qpm=5)
        request = _make_request("/api/v1/query/stream", tenant_id="t1", tenant=tenant)
        call_next = AsyncMock()
        mock_check.return_value = (False, 20)

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429
