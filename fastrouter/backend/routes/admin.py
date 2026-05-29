"""Admin routes for model management, key visibility, user role management, and service control."""

import asyncio
import os
from datetime import datetime, timezone

import httpx
import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.middleware.auth import get_current_user, require_admin
from backend.models.user import User
from backend.models.provider_key import ProviderKey
from backend.models.provider_model import ProviderModel
from backend.routes.provider_keys import decrypt_api_key
from backend.services.routing import load_model_map
from backend.config import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])

settings = get_settings()


# ── Request/Response schemas ────────────────────────────────────────────

class ModelCreate(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    api_base: str = Field(..., min_length=1)
    description: str | None = None
    input_cost_per_token: float | None = None
    output_cost_per_token: float | None = None
    is_active: bool = True


class ModelUpdate(BaseModel):
    model_name: str | None = None
    provider: str | None = None
    api_base: str | None = None
    description: str | None = None
    input_cost_per_token: float | None = None
    output_cost_per_token: float | None = None
    is_active: bool | None = None


class ModelResponse(BaseModel):
    id: int
    model_name: str
    provider: str
    api_base: str
    description: str | None
    input_cost_per_token: float | None
    output_cost_per_token: float | None
    is_active: bool
    created_at: str
    updated_at: str


class AdminProviderKeyResponse(BaseModel):
    id: str
    user_id: str
    user_email: str
    provider: str
    key_prefix: str
    is_active: bool
    synced: bool
    created_at: str


class AdminProviderKeyDetail(BaseModel):
    id: str
    user_id: str
    user_email: str
    provider: str
    key_prefix: str
    api_key_decrypted: str
    is_active: bool
    synced: bool
    created_at: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    subscription_status: str
    free_requests_used: int
    free_requests_limit: int
    created_at: str


class RoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(admin|user)$")


class ModelImportRow(BaseModel):
    model_name: str
    provider: str
    api_base: str
    description: str | None = None
    input_cost_per_token: float | None = None
    output_cost_per_token: float | None = None
    is_active: bool = True


class ModelImportRequest(BaseModel):
    models: list[ModelImportRow]
    conflict_strategy: str = Field(default="skip", pattern="^(skip|overwrite)$")


# ── Helpers ─────────────────────────────────────────────────────────────

async def _sync_virtual_keys_for_provider(provider: str, db: AsyncSession) -> None:
    """Re-sync all LiteLLM virtual keys for a provider after model changes."""
    from backend.services.lite_key_manager import get_key_manager
    from backend.services.routing import get_provider_models

    result = await db.execute(
        select(ProviderKey).where(
            ProviderKey.provider == provider,
            ProviderKey.lite_key.isnot(None),
        )
    )
    provider_keys = result.scalars().all()
    if not provider_keys:
        return

    models_for_provider = get_provider_models(provider)
    key_mgr = get_key_manager()
    for pk in provider_keys:
        await key_mgr.update_key_models(pk.lite_key, models_for_provider)


def _model_to_response(m: ProviderModel) -> ModelResponse:
    return ModelResponse(
        id=m.id,
        model_name=m.model_name,
        provider=m.provider,
        api_base=m.api_base,
        description=m.description,
        input_cost_per_token=m.input_cost_per_token,
        output_cost_per_token=m.output_cost_per_token,
        is_active=m.is_active,
        created_at=m.created_at.isoformat() if m.created_at else "",
        updated_at=m.updated_at.isoformat() if m.updated_at else "",
    )


async def _provider_names(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(ProviderModel.provider).where(ProviderModel.is_active == True).distinct()
    )
    return sorted(row[0] for row in result)


def _generate_litellm_config(models: list[ProviderModel]) -> str:
    """Generate LiteLLM config.yaml from provider_models table.

    Models are loaded from config.yaml at startup. Since STORE_MODEL_IN_DB=True,
    LiteLLM also persists them to its internal DB, making them available via
    read APIs (/model/info, /v1/models) without a restart.
    """
    providers = sorted(set(m.provider for m in models))
    fallback_pairs = []
    if len(providers) >= 2:
        for i, src in enumerate(providers):
            dst = providers[(i + 1) % len(providers)]
            src_models = [m.model_name for m in models if m.provider == src]
            dst_models = [m.model_name for m in models if m.provider == dst]
            for sm in src_models:
                fallback_pairs.append({sm: dst_models[:1]})

    config = {
        "model_list": [
            {
                "model_name": m.model_name,
                "litellm_params": {
                    "model": f"openai/{m.model_name}",
                    "api_base": m.api_base,
                    "api_key": f"os.environ/{m.provider.upper()}_API_KEY",
                    **({"input_cost_per_token": m.input_cost_per_token} if m.input_cost_per_token is not None else {}),
                    **({"output_cost_per_token": m.output_cost_per_token} if m.output_cost_per_token is not None else {}),
                },
            }
            for m in models
        ],
        "general_settings": {
            "master_key": "os.environ/LITELLM_MASTER_KEY",
            "store_model_in_db": True,
        },
        "litellm_settings": {
            "drop_params": True,
            "set_verbose": True,
        },
        "router_settings": {
            "routing_strategy": "usage-based-routing",
            "enable_pre_call_checks": True,
            "allowed_fails": 3,
            "num_retries": 2,
            "fallbacks": fallback_pairs,
        },
    }

    header = "# Auto-generated by FastRouter Admin\n"
    return header + yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ── Model CRUD ──────────────────────────────────────────────────────────

@router.get("/models", response_model=list[ModelResponse])
async def admin_list_models(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProviderModel).order_by(ProviderModel.provider, ProviderModel.model_name))
    return [_model_to_response(m) for m in result.scalars().all()]


@router.post("/models", response_model=ModelResponse)
async def admin_create_model(
    req: ModelCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(ProviderModel).where(ProviderModel.model_name == req.model_name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Model '{req.model_name}' already exists")

    model = ProviderModel(**req.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    await load_model_map(db)
    await _sync_virtual_keys_for_provider(req.provider, db)
    return _model_to_response(model)


@router.put("/models/{model_id}", response_model=ModelResponse)
async def admin_update_model(
    model_id: int,
    req: ModelUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProviderModel).where(ProviderModel.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    old_provider = model.provider
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)

    await db.commit()
    await db.refresh(model)
    await load_model_map(db)
    await _sync_virtual_keys_for_provider(model.provider, db)
    if req.provider and req.provider != old_provider:
        await _sync_virtual_keys_for_provider(old_provider, db)
    return _model_to_response(model)


@router.delete("/models/{model_id}", response_model=None)
async def admin_delete_model(
    model_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProviderModel).where(ProviderModel.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    # Check for provider keys using this model's provider
    key_count_result = await db.execute(
        select(func.count(ProviderKey.id)).where(ProviderKey.provider == model.provider)
    )
    key_count = key_count_result.scalar()
    warning = None
    if key_count > 0:
        warning = (
            f"Provider '{model.provider}' has {key_count} existing key(s). "
            "Those users will no longer be able to route requests after the LiteLLM config is synced."
        )

    await db.delete(model)
    await db.commit()
    await load_model_map(db)
    await _sync_virtual_keys_for_provider(model.provider, db)
    return {"success": True, "warning": warning}


@router.post("/models/sync", response_model=None)
async def admin_sync_models(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate LiteLLM config.yaml from the provider_models table.

    Models are loaded from config at LiteLLM startup. With STORE_MODEL_IN_DB
    enabled, LiteLLM persists them to its internal DB automatically on restart.
    """
    result = await db.execute(
        select(ProviderModel).where(ProviderModel.is_active == True).order_by(ProviderModel.provider)
    )
    models = result.scalars().all()

    if not models:
        raise HTTPException(status_code=400, detail="No active models to sync")

    yaml_content = _generate_litellm_config(models)
    config_path = os.path.abspath(settings.litellm_config_path)

    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            f.write(yaml_content)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")

    return {
        "success": True,
        "path": config_path,
        "models_synced": len(models),
        "providers": sorted(set(m.provider for m in models)),
        "config_preview": yaml_content[:2000],
    }


@router.post("/models/import", response_model=None)
async def admin_import_models(
    req: ModelImportRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import models from JSON. Returns diff when conflict_strategy is 'skip'."""
    result = await db.execute(select(ProviderModel))
    existing = {m.model_name: m for m in result.scalars().all()}

    created = []
    updated = []
    skipped = []
    affected_providers = set()

    for row in req.models:
        if row.model_name in existing:
            if req.conflict_strategy == "skip":
                skipped.append(row.model_name)
                continue
            # Overwrite
            existing[row.model_name].provider = row.provider
            existing[row.model_name].api_base = row.api_base
            existing[row.model_name].description = row.description
            existing[row.model_name].is_active = row.is_active
            updated.append(row.model_name)
        else:
            model = ProviderModel(**row.model_dump())
            db.add(model)
            created.append(row.model_name)
        affected_providers.add(row.provider)

    await db.commit()
    await load_model_map(db)

    for provider in affected_providers:
        await _sync_virtual_keys_for_provider(provider, db)

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": len(req.models),
    }


# ── Provider Key Visibility ─────────────────────────────────────────────

@router.get("/provider-keys", response_model=list[AdminProviderKeyResponse])
async def admin_list_provider_keys(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProviderKey, User.email)
        .join(User, ProviderKey.user_id == User.id)
        .order_by(ProviderKey.created_at.desc())
    )
    rows = result.all()
    return [
        AdminProviderKeyResponse(
            id=str(pk.id),
            user_id=str(pk.user_id),
            user_email=email,
            provider=pk.provider,
            key_prefix=pk.key_prefix,
            is_active=pk.is_active,
            synced=pk.lite_key is not None,
            created_at=pk.created_at.isoformat() if pk.created_at else "",
        )
        for pk, email in rows
    ]


@router.get("/provider-keys/{key_id}", response_model=AdminProviderKeyDetail)
async def admin_get_provider_key(
    key_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProviderKey, User.email)
        .join(User, ProviderKey.user_id == User.id)
        .where(ProviderKey.id == key_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Provider key not found")

    pk, email = row
    return AdminProviderKeyDetail(
        id=str(pk.id),
        user_id=str(pk.user_id),
        user_email=email,
        provider=pk.provider,
        key_prefix=pk.key_prefix,
        api_key_decrypted=decrypt_api_key(pk.api_key_encrypted),
        is_active=pk.is_active,
        synced=pk.lite_key is not None,
        created_at=pk.created_at.isoformat() if pk.created_at else "",
    )


# ── User Role Management ────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
async def admin_list_users(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserResponse(
            id=str(u.id),
            email=u.email,
            role=u.role,
            subscription_status=u.subscription_status,
            free_requests_used=u.free_requests_used,
            free_requests_limit=u.free_requests_limit,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )
        for u in users
    ]


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def admin_update_user_role(
    user_id: str,
    req: RoleUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if str(admin.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    target.role = req.role
    await db.commit()
    await db.refresh(target)

    return UserResponse(
        id=str(target.id),
        email=target.email,
        role=target.role,
        subscription_status=target.subscription_status,
        free_requests_used=target.free_requests_used,
        free_requests_limit=target.free_requests_limit,
        created_at=target.created_at.isoformat() if target.created_at else "",
    )


# ── Service Control ─────────────────────────────────────────────────────

DOCKER_SOCK = "/var/run/docker.sock"


def _docker_client() -> httpx.AsyncClient:
    transport = httpx.AsyncHTTPTransport(uds=DOCKER_SOCK)
    return httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(30.0), base_url="http://localhost")


@router.get("/services/status", response_model=None)
async def admin_services_status(
    user: User = Depends(require_admin),
):
    """Check status of all services and Docker containers."""
    services = {}

    # Check Docker containers via socket
    try:
        async with _docker_client() as dc:
            resp = await dc.get("/containers/json", params={"all": "true"})
            if resp.status_code == 200:
                containers = {}
                for c in resp.json():
                    names = c.get("Names", [])
                    name = names[0].lstrip("/") if names else c.get("Id", "")[:12]
                    containers[name] = c.get("State", "unknown")
                services["containers"] = containers
            else:
                services["containers"] = {"error": f"Docker API returned {resp.status_code}"}
    except FileNotFoundError:
        services["containers"] = {"error": "Docker socket not available"}
    except Exception as e:
        services["containers"] = {"error": str(e)}

    # Check LiteLLM
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(f"{settings.litellm_url}/health")
            services["litellm"] = {"reachable": True, "status_code": resp.status_code}
    except Exception as e:
        services["litellm"] = {"reachable": False, "error": str(e)}

    return {"services": services, "timestamp": datetime.now(timezone.utc).isoformat()}


async def _restart_container(container_name: str) -> dict:
    """Restart a Docker container via the socket API."""
    try:
        async with _docker_client() as dc:
            resp = await dc.post(f"/containers/{container_name}/restart")
            if resp.status_code == 204:
                return {"success": True, "container": container_name, "action": "restart"}
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
            detail = resp.text[:300] if resp.text else f"HTTP {resp.status_code}"
            raise HTTPException(status_code=500, detail=f"Docker restart failed: {detail}")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Docker socket not available — is the socket mounted?")
    except httpx.TimeoutException:
        raise HTTPException(status_code=500, detail="Docker restart timed out after 30s")


@router.post("/services/litellm/restart", response_model=None)
async def admin_restart_litellm(
    user: User = Depends(require_admin),
):
    """Restart the LiteLLM Docker container and wait for it to be ready."""
    result = await _restart_container("fastrouter-litellm-1")

    # Poll health endpoint until ready (up to 30s)
    for i in range(15):
        await asyncio.sleep(2)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                resp = await client.get(f"{settings.litellm_url}/health")
                if resp.status_code == 200:
                    return {
                        **result,
                        "ready": True,
                        "wait_seconds": (i + 1) * 2,
                    }
        except Exception:
            pass

    return {**result, "ready": False, "warning": "LiteLLM restarted but not reachable after 30s — it may still be starting up."}


@router.post("/services/backend/restart", response_model=None)
async def admin_restart_backend(
    user: User = Depends(require_admin),
):
    """Restart the FastRouter backend container."""
    return await _restart_container("fastrouter-backend-1")


# ── Stats ───────────────────────────────────────────────────────────────

@router.get("/stats", response_model=None)
async def admin_stats(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user_count = await db.execute(select(func.count(User.id)))
    model_count = await db.execute(select(func.count(ProviderModel.id)))
    provider_key_count = await db.execute(select(func.count(ProviderKey.id)))
    active_provider_count = await db.execute(
        select(func.count(func.distinct(ProviderModel.provider))).where(ProviderModel.is_active == True)
    )

    return {
        "users": user_count.scalar(),
        "models": model_count.scalar(),
        "active_providers": active_provider_count.scalar(),
        "provider_keys": provider_key_count.scalar(),
    }
