import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.middleware.auth import get_current_user
from backend.models.user import User
from backend.models.api_key import ApiKey

router = APIRouter(prefix="/keys", tags=["api-keys"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CreateKeyRequest(BaseModel):
    name: str = "Default"


class KeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    is_active: bool
    last_used_at: str | None
    created_at: str


@router.get("", response_model=list[KeyResponse])
async def list_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        KeyResponse(
            id=str(k.id),
            key_prefix=k.key_prefix,
            name=k.name,
            is_active=k.is_active,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            created_at=k.created_at.isoformat() if k.created_at else "",
        )
        for k in keys
    ]


@router.post("", response_model=None)
async def create_key(
    req: CreateKeyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_key = f"sk-{secrets.token_urlsafe(36)}"
    key_prefix = raw_key[:8]
    key_hash = pwd_context.hash(raw_key)

    api_key = ApiKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=req.name,
    )
    db.add(api_key)
    await db.commit()

    return {
        "id": str(api_key.id),
        "key": raw_key,
        "key_prefix": key_prefix,
        "name": api_key.name,
        "message": "Store this key securely - it will not be shown again.",
    }


@router.get("/{key_id}", response_model=None)
async def get_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=404, detail="Key not found")

    from backend.models.provider_key import ProviderKey
    pk_result = await db.execute(
        select(ProviderKey).where(ProviderKey.user_id == user.id)
    )
    provider_keys = pk_result.scalars().all()

    return {
        "id": str(key.id),
        "name": key.name,
        "key_prefix": key.key_prefix,
        "is_active": key.is_active,
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        "created_at": key.created_at.isoformat() if key.created_at else "",
        "provider_keys": [
            {
                "id": str(pk.id),
                "provider": pk.provider,
                "key_prefix": pk.key_prefix,
                "synced": pk.lite_key is not None,
                "is_active": pk.is_active,
                "created_at": pk.created_at.isoformat() if pk.created_at else "",
            }
            for pk in provider_keys
        ],
    }


@router.delete("/{key_id}", response_model=None)
async def delete_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Key not found")

    return {"success": True}
