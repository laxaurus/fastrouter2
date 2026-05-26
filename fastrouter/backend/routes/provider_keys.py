import os

from fastapi import APIRouter, Depends, HTTPException
from cryptography.fernet import Fernet
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.middleware.auth import get_current_user
from backend.models.user import User
from backend.models.provider_key import ProviderKey
from backend.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/providers/keys", tags=["provider-keys"])

SUPPORTED_PROVIDERS = ["deepseek", "qwen"]


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
    if req.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider '{req.provider}'. Supported: {', '.join(SUPPORTED_PROVIDERS)}",
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

    return {
        "id": str(provider_key.id),
        "provider": provider_key.provider,
        "key_prefix": provider_key.key_prefix,
        "message": "Provider key added successfully.",
    }


@router.delete("/{key_id}", response_model=None)
async def delete_provider_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(ProviderKey).where(ProviderKey.id == key_id, ProviderKey.user_id == user.id)
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Provider key not found")

    return {"success": True}


async def get_provider_key(user_id: str, provider: str, db: AsyncSession) -> str | None:
    """Get decrypted provider key for routing. Used by proxy endpoint."""
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
    return decrypt_api_key(key.api_key_encrypted)
