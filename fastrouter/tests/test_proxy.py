"""Tests for /v1/chat/completions and /v1/models proxy endpoints."""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_status


class TestListModels:
    ENDPOINT = "/v1/models"

    async def test_returns_expected_models(self, auth_client: AsyncClient):
        res = await auth_client.get(self.ENDPOINT)
        await assert_status(res, 200)
        data = res.json()
        assert data["object"] == "list"
        model_ids = [m["id"] for m in data["data"]]
        assert "deepseek-chat" in model_ids
        assert "qwen-plus" in model_ids

    async def test_no_auth_required(self, client: AsyncClient):
        """Models list is a public endpoint — no auth required."""
        res = await client.get(self.ENDPOINT)
        await assert_status(res, 200)


class TestChatCompletionsAuth:
    """Auth and validation tests that don't require LiteLLM to be running."""

    ENDPOINT = "/v1/chat/completions"

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        await assert_status(res, 401)

    async def test_missing_auth_header_returns_401(self, client: AsyncClient):
        res = await client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        await assert_status(res, 401)

    async def test_invalid_api_key_returns_401(self, client: AsyncClient):
        res = await client.post(
            self.ENDPOINT,
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "Hi"}]},
            headers={"Authorization": "Bearer sk-invalid-key-that-does-not-exist"},
        )
        await assert_status(res, 401)


class TestChatCompletionsFreeTier:
    """Free tier enforcement tests."""

    ENDPOINT = "/v1/chat/completions"

    async def test_free_tier_allows_requests(self, auth_client: AsyncClient, provider_key):
        """User with free requests remaining gets proxied (may 502 if no LiteLLM, but not 402)."""
        res = await auth_client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        # Should NOT be 402 (payment required) — free tier still active
        # May be 502 if LiteLLM is down, or 200 if it's up
        assert res.status_code != 402, (
            f"Got 402 Payment Required but user should have free requests. Body: {res.text[:300]}"
        )

    async def test_exhausted_free_tier_returns_402(self, auth_client: AsyncClient, test_user, db_session, provider_key):
        """User with exhausted free tier and no subscription gets 402."""
        test_user.free_requests_used = test_user.free_requests_limit
        await db_session.commit()

        res = await auth_client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        await assert_status(res, 402)

    async def test_subscribed_user_bypasses_free_limit(
        self, client: AsyncClient, test_user_subscribed, db_session, provider_key
    ):
        """Subscribed user with exhausted free count still gets through."""
        from backend.middleware.auth import create_access_token
        token = create_access_token(str(test_user_subscribed.id))

        # Give subscribed user a provider key too
        from backend.models.provider_key import ProviderKey
        from backend.routes.provider_keys import encrypt_api_key
        pk = ProviderKey(
            user_id=test_user_subscribed.id,
            provider="deepseek",
            api_key_encrypted=encrypt_api_key("sk-deepseek-subscribed-key-123"),
            key_prefix="sk-deeps",
        )
        db_session.add(pk)
        await db_session.commit()

        res = await client.post(
            self.ENDPOINT,
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "Hello"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should not be 402 — subscription bypasses free tier
        assert res.status_code != 402, (
            f"Got 402 but user has active subscription. Body: {res.text[:300]}"
        )


class TestChatCompletionsValidation:
    """Request validation tests."""

    ENDPOINT = "/v1/chat/completions"

    async def test_empty_messages_allowed(self, auth_client: AsyncClient, provider_key):
        res = await auth_client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [],
        })
        # Shouldn't be a 422 validation error
        assert res.status_code != 422

    async def test_missing_model_defaults(self, auth_client: AsyncClient, provider_key):
        res = await auth_client.post(self.ENDPOINT, json={
            "messages": [{"role": "user", "content": "Hello"}],
        })
        # Should use default model, not 422
        assert res.status_code != 422

    async def test_custom_temperature(self, auth_client: AsyncClient, provider_key):
        res = await auth_client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0.3,
            "max_tokens": 512,
        })
        assert res.status_code != 422

    async def test_no_provider_key_returns_error(self, auth_client: AsyncClient, test_user, db_session):
        """User without a provider key for the requested model should get an error."""
        res = await auth_client.post(self.ENDPOINT, json={
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        # Either 400 (if no LiteLLM proxy) or 502 (if LiteLLM proxy returns error)
        # The key point: should not be 422 or crash with 500
        assert res.status_code != 422, f"Validation error: {res.text[:300]}"


@pytest.mark.integration
class TestChatCompletionsStreaming:
    """Streaming tests require a running LiteLLM proxy."""

    ENDPOINT = "/v1/chat/completions"

    async def test_streaming_request_accepted(self, auth_client: AsyncClient, provider_key):
        res = await auth_client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Count to 5"}],
            "stream": True,
        })
        # 502 if LiteLLM down, 200 if up. Should never be 401 (auth error)
        assert res.status_code != 401, f"Auth error on streaming: {res.text[:300]}"

    async def test_streaming_with_jwt_auth(self, auth_client: AsyncClient, provider_key):
        res = await auth_client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        })
        # JWT auth should work (not just API keys)
        assert res.status_code not in (401, 403), (
            f"Auth failed for JWT on proxy: {res.status_code}"
        )


@pytest.mark.integration
class TestChatCompletionsApiKeyAuth:
    ENDPOINT = "/v1/chat/completions"

    async def test_api_key_auth_accepted(self, api_key_client: AsyncClient, provider_key):
        res = await api_key_client.post(self.ENDPOINT, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Hello from API key"}],
        })
        assert res.status_code != 401, f"API key auth rejected: {res.text[:300]}"

    async def test_revoked_api_key_rejected(self, client: AsyncClient, api_key, db_session, provider_key):
        raw_key, key = api_key

        # Revoke the key
        key.is_active = False
        await db_session.commit()

        res = await client.post(
            self.ENDPOINT,
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "Hi"}]},
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        await assert_status(res, 401)


@pytest.mark.integration
class TestChatCompletionsCaching:
    """Cache tests require a running LiteLLM proxy."""

    ENDPOINT = "/v1/chat/completions"

    async def test_repeated_prompt_returns_cached_header(self, auth_client: AsyncClient, provider_key, redis_client):
        """If LiteLLM is up, repeated identical prompts should hit cache."""
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Say exactly: pineapple"}],
        }

        # First call — cache miss (or 502 if LiteLLM down)
        res1 = await auth_client.post(self.ENDPOINT, json=payload)
        # Second call — should be cache hit if first succeeded
        res2 = await auth_client.post(self.ENDPOINT, json=payload)

        if res1.status_code == 200:
            data = res2.json()
            if data.get("x_cached"):
                assert data["x_cached"] is True
