from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.config import get_settings
from backend.middleware.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from backend.models.user import User
from backend.models.api_key import ApiKey

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    settings = get_settings()
    user_count = await db.execute(select(func.count(User.id)))
    is_first_user = user_count.scalar() == 0
    auto_admin = is_first_user and not settings.admin_emails

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        subscription_status="inactive",
        role="admin" if auto_admin else "user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": str(user.id), "email": user.email, "subscription_status": user.subscription_status, "role": user.role},
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "subscription_status": user.subscription_status,
            "free_requests_used": user.free_requests_used,
            "free_requests_limit": user.free_requests_limit,
            "role": user.role,
        },
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user={"id": str(user.id), "email": user.email, "subscription_status": user.subscription_status, "role": user.role},
    )


@router.get("/me", response_model=None)
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "subscription_status": user.subscription_status,
        "free_requests_used": user.free_requests_used,
        "free_requests_limit": user.free_requests_limit,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
