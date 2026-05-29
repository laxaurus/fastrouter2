"""Tests for /providers/keys endpoints — BYOK provider key management."""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_status


class TestListProviderKeys:
    ENDPOINT = "/providers/keys"

    async def test_list_empty_returns_array(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        assert isinstance(res.json(), list)

    async def test_list_shows_stored_keys(self, auth_client: AsyncClient, provider_key):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        keys = res.json()
        assert len(keys) >= 1
        assert "provider" in keys[0]
        assert "key_prefix" in keys[0]
        # Encrypted key must never be exposed
        assert "api_key_encrypted" not in keys[0]
        assert "api_key" not in keys[0]

    async def test_list_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 401)


class TestAddProviderKey:
    ENDPOINT = "/providers/keys"

    async def test_add_deepseek_key(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={
            "provider": "deepseek",
            "api_key": "sk-deepseek-test-key-1234567890abcdef",
        })
        await assert_status(res, 200)
        assert res.json()["provider"] == "deepseek"
        assert "message" in res.json()

    async def test_add_qwen_key(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={
            "provider": "qwen",
            "api_key": "sk-qwen-test-key-1234567890abcdef",
        })
        await assert_status(res, 200)
        assert res.json()["provider"] == "qwen"

    async def test_add_unsupported_provider_returns_400(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={
            "provider": "openai",
            "api_key": "sk-test-key",
        })
        await assert_status(res, 400)

    async def test_add_unknown_provider_returns_400(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={
            "provider": "azure",
            "api_key": "sk-test-key",
        })
        await assert_status(res, 400)

    async def test_add_empty_provider_returns_400(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={
            "provider": "",
            "api_key": "sk-test-key",
        })
        await assert_status(res, 400)

    async def test_key_is_encrypted(self, auth_client: AsyncClient, db_session, test_user):
        """Verify the stored key is actually encrypted, not plaintext."""
        await auth_client.post(self.ENDPOINT, json={
            "provider": "deepseek",
            "api_key": "sk-plaintext-secret-key-12345",
        })

        from backend.models.provider_key import ProviderKey
        from sqlalchemy import select
        result = await db_session.execute(
            select(ProviderKey).where(ProviderKey.user_id == test_user.id)
        )
        stored = result.scalar_one()
        assert "sk-plaintext" not in stored.api_key_encrypted, (
            f"Key stored in plaintext! Value: {stored.api_key_encrypted[:50]}"
        )

    async def test_add_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={
            "provider": "deepseek",
            "api_key": "sk-test",
        })
        await assert_status(res, 401)


class TestDeleteProviderKey:
    async def test_delete_existing_key(self, auth_client: AsyncClient, provider_key):
        res = await auth_client.delete(f"/providers/keys/{provider_key.id}")
        await assert_status(res, 200)
        assert res.json()["success"] is True

    async def test_delete_nonexistent_returns_404(self, auth_client: AsyncClient):
        res = await auth_client.delete("/providers/keys/00000000-0000-0000-0000-000000000000")
        await assert_status(res, 404)

    async def test_delete_then_list_empty(self, auth_client: AsyncClient, provider_key):
        await auth_client.delete(f"/providers/keys/{provider_key.id}")
        list_res = await auth_client.get("/providers/keys")
        await assert_status(list_res, 200)
        ids = [k["id"] for k in list_res.json()]
        assert str(provider_key.id) not in ids

    async def test_delete_unauthenticated_returns_401(self, client: AsyncClient, provider_key):
        res = await client.delete(f"/providers/keys/{provider_key.id}")
        await assert_status(res, 401)
