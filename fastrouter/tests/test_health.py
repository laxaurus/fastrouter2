"""Tests for /health endpoint."""

from httpx import AsyncClient

from tests.conftest import assert_status


class TestHealth:
    ENDPOINT = "/health"

    async def test_returns_healthy(self, client):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert data["status"] == "healthy"
        assert "redis" in data
        assert "version" in data

    async def test_redis_reported(self, client):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 200)
        assert res.json()["redis"] is True

    async def test_no_auth_required(self, client):
        """Health endpoint should be public — no auth required."""
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 200)
