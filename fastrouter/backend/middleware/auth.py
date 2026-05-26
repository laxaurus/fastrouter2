import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.config import get_settings
from backend.models.user import User
from backend.models.api_key import ApiKey

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password.encode()[:72])


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain.encode()[:72], hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "access"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "refresh"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Authenticate via JWT (dashboard) or API key (proxy). Returns User or raises 401."""
    credentials: Optional[HTTPAuthorizationCredentials] = await security(request)

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = credentials.credentials

    # Try API key first (sk-...)
    if token.startswith("sk-"):
        return await _auth_api_key(token, db)

    # Try JWT token (for dashboard)
    return await _auth_jwt(token, db)


async def _auth_api_key(api_key: str, db: AsyncSession) -> User:
    from passlib.hash import bcrypt

    key_hash = bcrypt.hash(api_key)

    result = await db.execute(
        select(ApiKey).where(ApiKey.is_active == True)
    )
    for key in result.scalars().all():
        if bcrypt.verify(api_key, key.key_hash):
            await db.execute(
                update(ApiKey).where(ApiKey.id == key.id).values(last_used_at=datetime.now(timezone.utc))
            )
            await db.commit()

            user_result = await db.execute(select(User).where(User.id == key.user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            return user

    raise HTTPException(status_code=401, detail="Invalid API key")


async def _auth_jwt(token: str, db: AsyncSession) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def check_subscription_or_free_tier(user: User) -> bool:
    """Returns True if user can make API calls."""
    if user.subscription_status == "active":
        return True
    if user.free_requests_used < user.free_requests_limit:
        return True
    return False
