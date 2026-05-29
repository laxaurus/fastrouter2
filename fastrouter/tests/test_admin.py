"""Tests for admin routes: model CRUD, key visibility, user management, service control, stats."""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_status


# ── Auth / Access Control ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_routes_require_admin(test_user, jwt_token, client: AsyncClient, seed_models):
    """Non-admin user gets 403 on all admin routes."""
    client.headers["Authorization"] = f"Bearer {jwt_token}"
    admin_paths = [
        ("GET", "/admin/models"),
        ("POST", "/admin/models"),
        ("GET", "/admin/provider-keys"),
        ("GET", "/admin/users"),
        ("GET", "/admin/stats"),
        ("GET", "/admin/services/status"),
    ]
    for method, path in admin_paths:
        if method == "GET":
            resp = await client.get(path)
        else:
            resp = await client.post(path, json={})
        assert resp.status_code == 403, f"{method} {path} should require admin, got {resp.status_code}"


@pytest.mark.asyncio
async def test_admin_routes_unauthenticated(client: AsyncClient):
    """No auth header → 401 on admin routes."""
    resp = await client.get("/admin/models")
    assert resp.status_code == 401


# ── Model CRUD ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_models(admin_client: AsyncClient, seed_models):
    resp = await admin_client.get("/admin/models")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["model_name"] == "deepseek-chat"


@pytest.mark.asyncio
async def test_create_model(admin_client: AsyncClient, seed_models):
    resp = await admin_client.post("/admin/models", json={
        "model_name": "glm-4",
        "provider": "glm",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_name"] == "glm-4"
    assert data["provider"] == "glm"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_duplicate_model(admin_client: AsyncClient, seed_models):
    resp = await admin_client.post("/admin/models", json={
        "model_name": "deepseek-chat",
        "provider": "deepseek",
        "api_base": "https://api.deepseek.com/v1",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_model(admin_client: AsyncClient, seed_models):
    models = (await admin_client.get("/admin/models")).json()
    model_id = models[0]["id"]

    resp = await admin_client.put(f"/admin/models/{model_id}", json={
        "description": "Updated description",
        "is_active": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Updated description"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_nonexistent_model(admin_client: AsyncClient, seed_models):
    resp = await admin_client.put("/admin/models/99999", json={"description": "nope"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_model(admin_client: AsyncClient, seed_models):
    models = (await admin_client.get("/admin/models")).json()
    initial_count = len(models)
    model_id = models[-1]["id"]

    resp = await admin_client.delete(f"/admin/models/{model_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    remaining = (await admin_client.get("/admin/models")).json()
    assert len(remaining) == initial_count - 1


@pytest.mark.asyncio
async def test_sync_models(admin_client: AsyncClient, seed_models):
    resp = await admin_client.post("/admin/models/sync")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["models_synced"] == 3
    assert "config_preview" in data


# ── Provider Key Visibility ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_provider_keys_admin(admin_client: AsyncClient, provider_key):
    resp = await admin_client.get("/admin/provider-keys")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert "user_email" in data[0]
    # Key is masked — no api_key_decrypted in list
    assert "api_key_decrypted" not in data[0]


@pytest.mark.asyncio
async def test_get_provider_key_detail(admin_client: AsyncClient, provider_key):
    resp = await admin_client.get(f"/admin/provider-keys/{provider_key.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["api_key_decrypted"] == "sk-test-deepseek-key-12345"
    assert data["user_email"] == "test@fastrouter.dev"


@pytest.mark.asyncio
async def test_get_nonexistent_provider_key(admin_client: AsyncClient):
    resp = await admin_client.get("/admin/provider-keys/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ── User Role Management ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_users(admin_client: AsyncClient, test_user, admin_user):
    resp = await admin_client.get("/admin/users")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    emails = [u["email"] for u in data]
    assert "test@fastrouter.dev" in emails
    assert "admin@fastrouter.dev" in emails


@pytest.mark.asyncio
async def test_update_user_role(admin_client: AsyncClient, test_user):
    resp = await admin_client.patch(f"/admin/users/{test_user.id}/role", json={"role": "admin"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_cannot_change_own_role(admin_client: AsyncClient, admin_user):
    resp = await admin_client.patch(f"/admin/users/{admin_user.id}/role", json={"role": "user"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_nonexistent_user_role(admin_client: AsyncClient):
    resp = await admin_client.patch("/admin/users/00000000-0000-0000-0000-000000000000/role", json={"role": "admin"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_role_value(admin_client: AsyncClient, test_user):
    resp = await admin_client.patch(f"/admin/users/{test_user.id}/role", json={"role": "superuser"})
    assert resp.status_code == 422


# ── Stats ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_stats(admin_client: AsyncClient, test_user, admin_user, seed_models, provider_key):
    resp = await admin_client.get("/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["users"] >= 2
    assert data["models"] >= 3
    assert data["active_providers"] >= 2
    assert data["provider_keys"] >= 1


# ── Service Status ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_services_status(admin_client: AsyncClient):
    resp = await admin_client.get("/admin/services/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert "timestamp" in data
