import os
import time
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from cryptography.fernet import Fernet
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.middleware.auth import get_current_user
from backend.models.user import User
from backend.models.provider_key import ProviderKey
from backend.models.provider_model import ProviderModel
from backend.config import get_settings
from backend.services.lite_key_manager import get_key_manager

settings = get_settings()
router = APIRouter(prefix="/providers/keys", tags=["provider-keys"])
logger = logging.getLogger(__name__)


def _get_cipher() -> Fernet:
    import base64, hashlib
    key = settings.encryption_key.encode()
    digest = hashlib.sha256(key).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_api_key(plain: str) -> str:
    cipher = _get_cipher()
    return cipher.encrypt(plain.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    cipher = _get_cipher()
    return cipher.decrypt(encrypted.encode()).decode()


class AddProviderKeyRequest(BaseModel):
    provider: str
    api_key: str


class ProviderKeyResponse(BaseModel):
    id: str
    provider: str
    key_prefix: str
    is_active: bool
    synced: bool
    created_at: str


@router.get("", response_model=list[ProviderKeyResponse])
async def list_provider_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProviderKey).where(ProviderKey.user_id == user.id).order_by(ProviderKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        ProviderKeyResponse(
            id=str(k.id),
            provider=k.provider,
            key_prefix=k.key_prefix,
            is_active=k.is_active,
            synced=k.lite_key is not None,
            created_at=k.created_at.isoformat() if k.created_at else "",
        )
        for k in keys
    ]


@router.post("", response_model=None)
async def add_provider_key(
    req: AddProviderKeyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.routing import get_model_providers, get_model_map

    supported = get_model_providers()
    if req.provider not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider '{req.provider}'. Supported: {', '.join(supported)}",
        )

    encrypted = encrypt_api_key(req.api_key)
    key_prefix = req.api_key[:8]

    provider_key = ProviderKey(
        user_id=user.id,
        provider=req.provider,
        api_key_encrypted=encrypted,
        key_prefix=key_prefix,
    )
    db.add(provider_key)
    await db.commit()
    await db.refresh(provider_key)

    # Collect models for this provider from the cache
    model_map = get_model_map()
    provider_models = [m for m, p in model_map.items() if p == req.provider]

    # Sync to LiteLLM virtual key
    key_mgr = get_key_manager()
    lite_key = await key_mgr.create_key(
        user_id=str(user.id),
        provider_key_id=str(provider_key.id),
        provider=req.provider,
        api_key=req.api_key,
        models=provider_models,
    )
    if lite_key:
        provider_key.lite_key = lite_key
        await db.commit()
    else:
        logger.warning(
            "Failed to create LiteLLM virtual key for provider_key=%s provider=%s",
            provider_key.id, req.provider,
        )

    return {
        "id": str(provider_key.id),
        "provider": provider_key.provider,
        "key_prefix": provider_key.key_prefix,
        "synced": lite_key is not None,
        "message": "Provider key added successfully."
        if lite_key
        else "Provider key saved but routing sync failed — will retry shortly.",
    }


@router.delete("/{key_id}", response_model=None)
async def delete_provider_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch first to get lite_key for cleanup
    result = await db.execute(
        select(ProviderKey).where(ProviderKey.id == key_id, ProviderKey.user_id == user.id)
    )
    pk = result.scalar_one_or_none()
    if pk is None:
        raise HTTPException(status_code=404, detail="Provider key not found")

    lite_key = pk.lite_key

    await db.delete(pk)
    await db.commit()

    # Clean up LiteLLM virtual key (fire and forget)
    if lite_key:
        key_mgr = get_key_manager()
        ok = await key_mgr.delete_key(lite_key)
        if not ok:
            logger.warning("Failed to delete LiteLLM virtual key for pk=%s", key_id)

    return {"success": True}


@router.post("/{key_id}/test", response_model=None)
async def test_provider_connection(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    model: str | None = None,
):
    """Test connectivity to a provider using the stored API key.

    Makes a minimal API call to the provider and returns latency + success/failure.
    Accepts an optional model query parameter; defaults to the first active model
    for the provider.
    """
    result = await db.execute(
        select(ProviderKey).where(ProviderKey.id == key_id, ProviderKey.user_id == user.id)
    )
    pk = result.scalar_one_or_none()
    if pk is None:
        raise HTTPException(status_code=404, detail="Provider key not found")

    api_key = decrypt_api_key(pk.api_key_encrypted)

    # Get all active models for this provider (need api_base + model name)
    model_result = await db.execute(
        select(ProviderModel.model_name, ProviderModel.api_base).where(
            ProviderModel.provider == pk.provider,
            ProviderModel.is_active == True,
        )
    )
    provider_models = model_result.all()
    if not provider_models:
        raise HTTPException(status_code=400, detail=f"No models configured for provider '{pk.provider}'")

    # Use specified model or first available
    model_names = [m.model_name for m in provider_models]
    if model and model in model_names:
        test_model = model
    else:
        test_model = model_names[0]

    api_base = provider_models[0].api_base

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 1,
    }

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            resp = await client.post(
                f"{api_base}/chat/completions",
                json=payload,
                headers=headers,
            )
        latency_ms = int((time.time() - start) * 1000)

        if resp.status_code in (200, 401, 403):
            # 200 = valid key, 401/403 = key rejected (but connectivity works)
            ok = resp.status_code == 200
            return {
                "success": True,
                "reachable": True,
                "authenticated": ok,
                "latency_ms": latency_ms,
                "model_used": test_model,
                "available_models": model_names,
                "detail": "Provider responded successfully" if ok else f"Provider reached but key rejected ({resp.status_code})",
            }
        else:
            return {
                "success": False,
                "reachable": False,
                "authenticated": False,
                "latency_ms": latency_ms,
                "model_used": test_model,
                "available_models": model_names,
                "detail": f"Provider returned {resp.status_code}: {resp.text[:300]}",
            }
    except httpx.ConnectError:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "success": False,
            "reachable": False,
            "authenticated": False,
            "latency_ms": latency_ms,
            "model_used": test_model,
            "available_models": model_names,
            "detail": f"Could not connect to {api_base}",
        }
    except httpx.TimeoutException:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "success": False,
            "reachable": False,
            "authenticated": False,
            "latency_ms": latency_ms,
            "model_used": test_model,
            "available_models": model_names,
            "detail": f"Connection to {api_base} timed out after 15s",
        }


async def get_provider_key(
    user_id: str, provider: str, db: AsyncSession
) -> tuple[str, str | None] | None:
    """Get decrypted provider key and LiteLLM virtual key for routing.

    Returns (decrypted_api_key, lite_key) or None if no active key found.
    lite_key is None if the key hasn't been synced to LiteLLM yet.
    """
    result = await db.execute(
        select(ProviderKey).where(
            ProviderKey.user_id == user_id,
            ProviderKey.provider == provider,
            ProviderKey.is_active == True,
        )
    )
    key = result.scalar_one_or_none()
    if key is None:
        return None
    return decrypt_api_key(key.api_key_encrypted), key.lite_key
