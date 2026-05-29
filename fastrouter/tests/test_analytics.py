"""Tests for /analytics endpoints — usage, providers, health."""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_status


class TestAnalyticsOverview:
    ENDPOINT = "/analytics/overview"

    async def test_returns_structure(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert "total_requests" in data
        assert "total_tokens" in data
        assert "cached_requests" in data
        assert "estimated_savings" in data
        assert "free_requests_used" in data
        assert "free_requests_limit" in data

    async def test_new_user_has_zero_usage(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert data["total_requests"] == 0
        assert data["total_tokens"] == 0
        assert data["cached_requests"] == 0

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 401)


class TestAnalyticsUsage:
    ENDPOINT = "/analytics/usage"

    async def test_returns_data_array(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert "days" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    async def test_custom_days_parameter(self, auth_client: AsyncClient):
        res = await auth_client.get(f"{self.ENDPOINT}?days=7")
        await assert_status(res, 200)
        assert res.json()["days"] == 7

    async def test_days_below_minimum_defaults(self, auth_client: AsyncClient):
        res = await auth_client.get(f"{self.ENDPOINT}?days=0")
        assert res.status_code == 422  # validation rejects < 1

    async def test_days_above_maximum_rejected(self, auth_client: AsyncClient):
        res = await auth_client.get(f"{self.ENDPOINT}?days=400")
        assert res.status_code == 422  # validation rejects > 365

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 401)

    async def test_api_key_auth_works(self, api_key_client: AsyncClient):
        res = await api_key_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        assert "data" in res.json()


class TestAnalyticsProviders:
    ENDPOINT = "/analytics/providers"

    async def test_returns_data_array(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 401)


class TestAnalyticsHealth:
    ENDPOINT = "/analytics/health"

    async def test_returns_providers_health(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert "providers" in data
        providers = data["providers"]
        assert len(providers) >= 1
        for p in providers:
            assert "provider" in p
            assert "state" in p
            assert "failure_count" in p

    async def test_initial_state_is_closed(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        for p in res.json()["providers"]:
            assert p["state"] == "closed"

    async def test_no_auth_required(self, client: AsyncClient):
        """Health endpoint is public — no auth dependency."""
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 200)
