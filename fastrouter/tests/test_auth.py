"""Tests for /auth endpoints — register, login, refresh, me."""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_status


class TestRegister:
    ENDPOINT = "/auth/register"

    async def test_register_creates_user_returns_tokens(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={
            "email": "newuser@test.com",
            "password": "securepassword123",
        })
        await assert_status(res, 200)
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "newuser@test.com"
        assert data["user"]["subscription_status"] == "inactive"

    async def test_register_duplicate_email_returns_409(self, client: AsyncClient):
        payload = {"email": "dup@test.com", "password": "securepassword123"}
        await client.post(self.ENDPOINT, json=payload)
        res = await client.post(self.ENDPOINT, json=payload)
        await assert_status(res, 409)

    async def test_register_invalid_email_rejected(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={
            "email": "not-an-email",
            "password": "securepassword123",
        })
        assert res.status_code == 422

    async def test_register_short_password_rejected(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={
            "email": "test@test.com",
            "password": "short",
        })
        assert res.status_code == 422

    async def test_register_missing_fields_returns_422(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={})
        assert res.status_code == 422

    async def test_register_empty_body_returns_422(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT)
        assert res.status_code == 422


class TestLogin:
    ENDPOINT = "/auth/login"

    async def test_login_valid_credentials_returns_tokens(self, client: AsyncClient, test_user):
        res = await client.post(self.ENDPOINT, json={
            "email": "test@fastrouter.dev",
            "password": "testpassword123",
        })
        await assert_status(res, 200)
        data = res.json()
        assert "access_token" in data
        assert data["user"]["subscription_status"] == "inactive"

    async def test_login_wrong_password_returns_401(self, client: AsyncClient, test_user):
        res = await client.post(self.ENDPOINT, json={
            "email": "test@fastrouter.dev",
            "password": "wrongpassword!!",
        })
        await assert_status(res, 401)

    async def test_login_nonexistent_email_returns_401(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={
            "email": "nobody@test.com",
            "password": "whatever123",
        })
        await assert_status(res, 401)

    async def test_login_returns_free_tier_stats(self, client: AsyncClient, test_user):
        res = await client.post(self.ENDPOINT, json={
            "email": "test@fastrouter.dev",
            "password": "testpassword123",
        })
        await assert_status(res, 200)
        data = res.json()
        assert data["user"]["free_requests_used"] == 0
        assert data["user"]["free_requests_limit"] == test_user.free_requests_limit


class TestRefresh:
    ENDPOINT = "/auth/refresh"

    async def test_refresh_valid_token_returns_new_tokens(self, client: AsyncClient, test_user):
        from backend.middleware.auth import create_refresh_token
        refresh = create_refresh_token(str(test_user.id))
        res = await client.post(self.ENDPOINT, json={"refresh_token": refresh})
        await assert_status(res, 200)
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_access_token_rejected(self, client: AsyncClient, test_user):
        from backend.middleware.auth import create_access_token
        access = create_access_token(str(test_user.id))
        res = await client.post(self.ENDPOINT, json={"refresh_token": access})
        await assert_status(res, 401)

    async def test_refresh_bad_token_returns_401(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={"refresh_token": "not.a.token"})
        await assert_status(res, 401)

    async def test_refresh_deleted_user_returns_401(self, client: AsyncClient, db_session, test_user):
        from backend.middleware.auth import create_refresh_token
        refresh = create_refresh_token(str(test_user.id))
        await db_session.delete(test_user)
        await db_session.commit()
        res = await client.post(self.ENDPOINT, json={"refresh_token": refresh})
        await assert_status(res, 401)


class TestMe:
    ENDPOINT = "/auth/me"

    async def test_me_with_jwt_returns_user(self, auth_client: AsyncClient, test_user):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert data["email"] == test_user.email
        assert "id" in data

    async def test_me_with_api_key_returns_user(self, api_key_client: AsyncClient, test_user):
        res = await api_key_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        assert res.json()["email"] == test_user.email

    async def test_me_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 401)
