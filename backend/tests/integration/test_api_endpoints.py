"""
Integration test for API endpoints.
Requires running Docker Compose services.

Run with: pytest tests/integration/test_api_endpoints.py -v
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.integration
class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "services" in data


@pytest.mark.integration
class TestAuthMiddleware:
    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/documents")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_key_rejected(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/documents",
                headers={"Authorization": "Bearer invalid_key_here"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_wrong_key_rejected(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/admin/tenants",
                headers={"Authorization": "Bearer wrong-admin-key"},
            )
            assert response.status_code == 401


@pytest.mark.integration
class TestAdminEndpoints:
    @pytest.mark.asyncio
    async def test_create_tenant(self):
        from app.config import settings

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/admin/tenants",
                json={"name": "Test Corp", "rate_limit_qpm": 100},
                headers={"Authorization": f"Bearer {settings.ADMIN_API_KEY}"},
            )
            assert response.status_code == 201
            data = response.json()
            assert "tenant" in data
            assert "api_key" in data
            assert data["tenant"]["name"] == "Test Corp"
            assert data["api_key"].startswith("rag_")

    @pytest.mark.asyncio
    async def test_get_chunking_strategies(self):
        from app.config import settings

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/admin/config/chunking-strategies",
                headers={"Authorization": f"Bearer {settings.ADMIN_API_KEY}"},
            )
            assert response.status_code == 200
            data = response.json()
            strategies = [s["name"] for s in data["strategies"]]
            assert "fixed" in strategies
            assert "semantic" in strategies
            assert "parent_child" in strategies
