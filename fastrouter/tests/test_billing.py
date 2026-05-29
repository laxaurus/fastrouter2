"""Tests for /billing endpoints — status, checkout, portal.

Checkout/portal tests require STRIPE_SECRET_KEY to be set.
"""

import os

import pytest
from httpx import AsyncClient

from tests.conftest import assert_status

stripe_configured = bool(os.environ.get("STRIPE_SECRET_KEY"))


class TestBillingStatus:
    ENDPOINT = "/billing/status"

    async def test_returns_free_tier_info(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert data["subscription_status"] == "inactive"
        assert data["free_requests_used"] == 0
        assert data["free_requests_limit"] > 0
        assert "free_requests_remaining" in data
        assert data["free_requests_remaining"] == data["free_requests_limit"] - data["free_requests_used"]

    async def test_subscribed_user_status(self, client: AsyncClient, test_user_subscribed):
        from backend.middleware.auth import create_access_token
        token = create_access_token(str(test_user_subscribed.id))

        res = await client.get(
            self.ENDPOINT,
            headers={"Authorization": f"Bearer {token}"},
        )
        await assert_status(res, 200)
        data = res.json()
        assert data["subscription_status"] == "active"
        assert data["free_requests_remaining"] == 0  # used=9999, limit=1000

    async def test_free_requests_remaining_matches_math(self, auth_client: AsyncClient, test_user):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        remaining = test_user.free_requests_limit - test_user.free_requests_used
        assert data["free_requests_remaining"] == remaining

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 401)


class TestBillingCheckout:
    ENDPOINT = "/billing/checkout"

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={
            "success_url": "http://localhost/success",
            "cancel_url": "http://localhost/cancel",
        })
        await assert_status(res, 401)

    async def test_missing_urls_returns_422(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={})
        assert res.status_code == 422

    @pytest.mark.skipif(not stripe_configured, reason="STRIPE_SECRET_KEY not set")
    async def test_creates_checkout_session(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={
            "success_url": "http://localhost/success",
            "cancel_url": "http://localhost/cancel",
        })
        await assert_status(res, 200)
        data = res.json()
        assert "checkout_url" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com/")


class TestBillingPortal:
    ENDPOINT = "/billing/portal"

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.post(f"{self.ENDPOINT}?return_url=http://localhost/back")
        await assert_status(res, 401)

    async def test_no_stripe_customer_returns_400(self, auth_client: AsyncClient, test_user):
        """User without stripe_customer_id should get 400."""
        res = await auth_client.post(f"{self.ENDPOINT}?return_url=http://localhost/back")
        await assert_status(res, 400)

    @pytest.mark.skipif(not stripe_configured, reason="STRIPE_SECRET_KEY not set")
    async def test_subscribed_user_gets_portal(self, client: AsyncClient, test_user_subscribed):
        from backend.middleware.auth import create_access_token
        token = create_access_token(str(test_user_subscribed.id))

        res = await client.post(
            f"{self.ENDPOINT}?return_url=http://localhost/back",
            headers={"Authorization": f"Bearer {token}"},
        )
        await assert_status(res, 200)
        assert "portal_url" in res.json()

