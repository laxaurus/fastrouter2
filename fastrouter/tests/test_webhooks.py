"""Tests for /webhooks/stripe endpoint."""

import json

import pytest
from httpx import AsyncClient

from tests.conftest import assert_status


class TestStripeWebhook:
    ENDPOINT = "/webhooks/stripe"

    async def test_missing_signature_returns_400(self, client: AsyncClient):
        """Webhook without stripe-signature header should return error."""
        res = await client.post(self.ENDPOINT, content=b"{}")
        # Missing signature → Stripe signature verification fails → 400
        await assert_status(res, 400)

    async def test_invalid_payload_returns_400(self, client: AsyncClient):
        res = await client.post(
            self.ENDPOINT,
            content=b"not-valid-json",
            headers={"stripe-signature": "fake_sig"},
        )
        await assert_status(res, 400)

    async def test_valid_signature_with_test_data(self, client: AsyncClient):
        """Webhook with proper test signature format. Expects 400 (signature verification
        with real Stripe key will fail for constructed payloads), or 200 if key not configured."""
        # A valid webhook event shape — signature is fake but the format is correct
        payload = json.dumps({
            "id": "evt_test123",
            "object": "event",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test123",
                    "object": "checkout.session",
                    "metadata": {"user_id": "00000000-0000-0000-0000-000000000000"},
                    "subscription": "sub_test123",
                }
            },
        })

        res = await client.post(
            self.ENDPOINT,
            content=payload,
            headers={
                "stripe-signature": "t=1234567890,v1=fakesig",
                "content-type": "application/json",
            },
        )
        # Should be 400 (invalid signature) — never 500
        assert res.status_code in (200, 400), (
            f"Expected 200 or 400, got {res.status_code}: {res.text[:300]}"
        )

    async def test_no_auth_required(self, client: AsyncClient):
        """Webhook endpoint should be public — Stripe calls it directly."""
        res = await client.post(self.ENDPOINT, content=b"{}")
        assert res.status_code != 401, f"Webhook should not require auth: {res.status_code}"
