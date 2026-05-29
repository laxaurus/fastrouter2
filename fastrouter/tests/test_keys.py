"""Tests for /keys endpoints — CRUD platform API keys."""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_status


class TestListKeys:
    ENDPOINT = "/keys"

    async def test_list_empty_returns_array(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        assert isinstance(res.json(), list)

    async def test_list_with_keys_returns_all(self, auth_client: AsyncClient, api_key):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        keys = res.json()
        assert len(keys) >= 1
        assert "key_prefix" in keys[0]
        assert "name" in keys[0]
        assert "is_active" in keys[0]
        # Full key must never be returned
        assert "key" not in keys[0]

    async def test_list_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 401)

    async def test_list_jwt_auth_works(self, auth_client: AsyncClient, api_key):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        assert len(res.json()) >= 1

    async def test_list_api_key_auth_works(self, api_key_client: AsyncClient, api_key):
        res = await api_key_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        assert len(res.json()) >= 1


class TestCreateKey:
    ENDPOINT = "/keys"

    async def test_create_returns_full_key_once(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={"name": "My Key"})
        await assert_status(res, 200)
        data = res.json()
        assert data["key"].startswith("sk-")
        assert len(data["key"]) > 20
        assert data["key_prefix"]
        assert "message" in data  # warning about saving

    async def test_create_default_name(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={})
        await assert_status(res, 200)
        assert res.json()["key"].startswith("sk-")

    async def test_create_key_shows_in_list(self, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={"name": "Visible"})
        await assert_status(res, 200)
        created_prefix = res.json()["key_prefix"]

        list_res = await auth_client.get(self.ENDPOINT)
        await assert_status(list_res, 200)
        prefixes = [k["key_prefix"] for k in list_res.json()]
        assert created_prefix in prefixes

    async def test_create_creates_usable_key(self, client: AsyncClient, auth_client: AsyncClient):
        res = await auth_client.post(self.ENDPOINT, json={"name": "Usable"})
        await assert_status(res, 200)
        raw_key = res.json()["key"]

        # Use the new key to authenticate
        me_res = await client.get("/auth/me", headers={"Authorization": f"Bearer {raw_key}"})
        await assert_status(me_res, 200)

    async def test_create_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={"name": "X"})
        await assert_status(res, 401)


class TestDeleteKey:
    async def test_delete_existing_key(self, auth_client: AsyncClient, api_key):
        _, key = api_key
        res = await auth_client.delete(f"/keys/{key.id}")
        await assert_status(res, 200)
        assert res.json()["success"] is True

        # Verify it's gone from list
        list_res = await auth_client.get("/keys")
        await assert_status(list_res, 200)
        ids = [k["id"] for k in list_res.json()]
        assert str(key.id) not in ids

    async def test_delete_nonexistent_returns_404(self, auth_client: AsyncClient):
        res = await auth_client.delete("/keys/00000000-0000-0000-0000-000000000000")
        await assert_status(res, 404)

    async def test_delete_other_users_key_returns_404(self, auth_client: AsyncClient, db_session):
        """A user cannot delete another user's key — it simply appears as not-found."""
        from backend.models.user import User
        from backend.models.api_key import ApiKey
        from backend.middleware.auth import hash_password
        from passlib.context import CryptContext
        import secrets

        other = User(email="other@test.com", password_hash=hash_password("password123"))
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        raw = f"sk-{secrets.token_urlsafe(36)}"
        other_key = ApiKey(user_id=other.id, key_hash=pwd.hash(raw), key_prefix=raw[:8], name="Other")
        db_session.add(other_key)
        await db_session.commit()
        await db_session.refresh(other_key)

        res = await auth_client.delete(f"/keys/{other_key.id}")
        await assert_status(res, 404)

    async def test_delete_unauthenticated_returns_401(self, client: AsyncClient, api_key):
        _, key = api_key
        res = await client.delete(f"/keys/{key.id}")
        await assert_status(res, 401)
