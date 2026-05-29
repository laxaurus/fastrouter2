"""
FastRouter Test Infrastructure

Real-dependency testing: Real PostgreSQL, real Redis, real external services.
Set environment variables for Stripe/LiteLLM before running tests.

Requires:
  - DATABASE_URL (default: postgresql+asyncpg://fastrouter:fastrouter@localhost:5432/fastrouter_test)
  - REDIS_URL (default: redis://localhost:6379)
  - LITELLM_URL (default: http://localhost:4000)
  - STRIPE_SECRET_KEY (optional, for billing tests)

Usage:
  pytest tests/ -v
  bash tests/run_tests.sh
"""

import os
import sys
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import redis.asyncio as redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override env for tests
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://fastrouter:fastrouter@localhost:5432/fastrouter_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("LITELLM_URL", "http://localhost:4000")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key")
os.environ.setdefault("ENCRYPTION_KEY", "test-32-byte-encryption-key!!")
os.environ.setdefault("LITELLM_MASTER_KEY", "sk-test-master-key")
os.environ.setdefault("STRIPE_SECRET_KEY", "")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "")
os.environ.setdefault("STRIPE_PRICE_ID", "")

from backend.config import get_settings
from backend.database import Base, async_session, engine
from backend.main import app
from backend.middleware.auth import hash_password, create_access_token
from backend.models.user import User
from backend.models.api_key import ApiKey
from backend.models.provider_key import ProviderKey

settings = get_settings()


# ── Session-scoped fixtures ────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def _init_db():
    """Create all tables once per session, drop at end. Uses raw asyncpg
    to avoid SQLAlchemy greenlet + pytest-asyncio event loop conflicts."""
    import asyncpg
    dsn = settings.database_url.replace("+asyncpg", "")

    conn = await asyncpg.connect(dsn)
    await conn.execute("DROP TABLE IF EXISTS usage_logs CASCADE")
    await conn.execute("DROP TABLE IF EXISTS api_keys CASCADE")
    await conn.execute("DROP TABLE IF EXISTS provider_keys CASCADE")
    await conn.execute("DROP TABLE IF EXISTS provider_configs CASCADE")
    await conn.execute("DROP TABLE IF EXISTS provider_models CASCADE")
    await conn.execute("DROP TABLE IF EXISTS users CASCADE")

    await conn.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            subscription_status VARCHAR(20) DEFAULT 'inactive' NOT NULL,
            stripe_customer_id VARCHAR(255), stripe_subscription_id VARCHAR(255),
            free_requests_used INTEGER DEFAULT 0 NOT NULL,
            free_requests_limit INTEGER DEFAULT 1000 NOT NULL,
            role VARCHAR(20) DEFAULT 'user' NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """)
    await conn.execute("""
        CREATE TABLE api_keys (
            id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id),
            key_hash VARCHAR(255) UNIQUE NOT NULL, key_prefix VARCHAR(8) NOT NULL,
            name VARCHAR(100) DEFAULT 'API Key' NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            last_used_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """)
    await conn.execute("""
        CREATE TABLE provider_keys (
            id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id),
            provider VARCHAR(50) NOT NULL, api_key_encrypted VARCHAR NOT NULL,
            key_prefix VARCHAR(8) NOT NULL, lite_key VARCHAR(64),
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """)
    await conn.execute("""
        CREATE TABLE usage_logs (
            id SERIAL PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id),
            api_key_id UUID REFERENCES api_keys(id),
            provider VARCHAR(50) NOT NULL, model VARCHAR(100) NOT NULL,
            prompt_tokens INTEGER DEFAULT 0 NOT NULL,
            completion_tokens INTEGER DEFAULT 0 NOT NULL,
            cost_usd FLOAT DEFAULT 0 NOT NULL,
            latency_ms INTEGER, cached BOOLEAN DEFAULT FALSE NOT NULL,
            agent_type VARCHAR(20) DEFAULT 'unknown' NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS provider_configs (
            id SERIAL PRIMARY KEY, provider VARCHAR(50) NOT NULL,
            model_pattern VARCHAR(100), priority INTEGER DEFAULT 0,
            weight INTEGER DEFAULT 100, is_active BOOLEAN DEFAULT TRUE,
            circuit_breaker_status VARCHAR(20) DEFAULT 'closed',
            failure_count INTEGER DEFAULT 0,
            last_failure_time TIMESTAMP WITH TIME ZONE, settings JSONB DEFAULT '{}'
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS provider_models (
            id SERIAL PRIMARY KEY,
            model_name VARCHAR(100) UNIQUE NOT NULL,
            provider VARCHAR(50) NOT NULL,
            api_base VARCHAR(255) NOT NULL,
            description VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """)
    await conn.close()
    yield
    conn = await asyncpg.connect(dsn)
    await conn.execute("DROP TABLE IF EXISTS usage_logs CASCADE")
    await conn.execute("DROP TABLE IF EXISTS api_keys CASCADE")
    await conn.execute("DROP TABLE IF EXISTS provider_keys CASCADE")
    await conn.execute("DROP TABLE IF EXISTS provider_configs CASCADE")
    await conn.execute("DROP TABLE IF EXISTS provider_models CASCADE")
    await conn.execute("DROP TABLE IF EXISTS users CASCADE")
    await conn.close()


@pytest_asyncio.fixture(scope="session")
async def redis_client():
    """Session-scoped real Redis connection."""
    r = await redis.from_url(settings.redis_url, decode_responses=True)
    yield r
    await r.aclose()


# ── App state setup ────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def _app_redis(redis_client):
    """Set app.state.redis so health check and routes can find Redis."""
    app.state.redis = redis_client
    yield


# ── Function-scoped fixtures ───────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def clean_db(_init_db, _app_redis):
    """Truncate all tables before each test using raw asyncpg."""
    import asyncpg
    dsn = settings.database_url.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute("TRUNCATE TABLE usage_logs CASCADE")
        await conn.execute("TRUNCATE TABLE api_keys CASCADE")
        await conn.execute("TRUNCATE TABLE provider_keys CASCADE")
        await conn.execute("TRUNCATE TABLE provider_models CASCADE")
        await conn.execute("TRUNCATE TABLE users CASCADE")
    finally:
        await conn.close()
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_redis(redis_client):
    """Clean Redis before each test."""
    await redis_client.flushall()
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator:
    """Per-test database session using SQLAlchemy."""
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session) -> User:
    """Create a test user with no subscription."""
    user = User(
        email="test@fastrouter.dev",
        password_hash=hash_password("testpassword123"),
        subscription_status="inactive",
        free_requests_used=0,
        free_requests_limit=settings.free_requests_limit,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_subscribed(db_session) -> User:
    """Create a test user with active subscription."""
    user = User(
        email="paid@fastrouter.dev",
        password_hash=hash_password("testpassword123"),
        subscription_status="active",
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123",
        free_requests_used=9999,
        free_requests_limit=settings.free_requests_limit,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def jwt_token(test_user) -> str:
    """JWT access token for the test user."""
    return create_access_token(str(test_user.id))


@pytest_asyncio.fixture
async def api_key(test_user, db_session) -> tuple[str, ApiKey]:
    """Create a platform API key for the test user."""
    from passlib.context import CryptContext
    import secrets

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    raw_key = f"sk-{secrets.token_urlsafe(36)}"
    key = ApiKey(
        user_id=test_user.id,
        key_hash=pwd.hash(raw_key),
        key_prefix=raw_key[:8],
        name="Test Key",
        is_active=True,
    )
    db_session.add(key)
    await db_session.commit()
    await db_session.refresh(key)
    return raw_key, key


@pytest_asyncio.fixture
async def provider_key(test_user, db_session) -> ProviderKey:
    """Create a test DeepSeek provider key."""
    from backend.routes.provider_keys import encrypt_api_key

    key = ProviderKey(
        user_id=test_user.id,
        provider="deepseek",
        api_key_encrypted=encrypt_api_key("sk-test-deepseek-key-12345"),
        key_prefix="sk-test-",
        is_active=True,
    )
    db_session.add(key)
    await db_session.commit()
    await db_session.refresh(key)
    return key


@pytest_asyncio.fixture
async def admin_user(db_session) -> User:
    """Create an admin user."""
    user = User(
        email="admin@fastrouter.dev",
        password_hash=hash_password("adminpassword123"),
        subscription_status="active",
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(admin_user) -> str:
    """JWT access token for the admin user."""
    return create_access_token(str(admin_user.id))


@pytest_asyncio.fixture
async def admin_client(client, admin_token) -> AsyncClient:
    """HTTP client pre-configured with admin JWT auth header."""
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client


@pytest_asyncio.fixture
async def seed_models(db_session):
    """Seed provider_models with test data."""
    from backend.models.provider_model import ProviderModel

    models = [
        ProviderModel(model_name="deepseek-chat", provider="deepseek", api_base="https://api.deepseek.com/v1"),
        ProviderModel(model_name="deepseek-reasoner", provider="deepseek", api_base="https://api.deepseek.com/v1"),
        ProviderModel(model_name="qwen-plus", provider="qwen", api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"),
    ]
    for m in models:
        db_session.add(m)
    await db_session.commit()

    # Populate the routing cache
    from backend.services.routing import load_model_map
    await load_model_map(db_session)
    return models


# ── HTTP Client fixtures ───────────────────────────────────────────────

@pytest_asyncio.fixture
async def client() -> AsyncGenerator:
    """Async HTTP client against the FastAPI app via ASGI transport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client, jwt_token) -> AsyncClient:
    """Client pre-configured with JWT auth header."""
    client.headers["Authorization"] = f"Bearer {jwt_token}"
    return client


@pytest_asyncio.fixture
async def api_key_client(client, api_key) -> AsyncClient:
    """Client pre-configured with API key auth header."""
    raw_key, _ = api_key
    client.headers["Authorization"] = f"Bearer {raw_key}"
    return client


# ── Helpers ─────────────────────────────────────────────────────────────

async def assert_status(response, expected: int, msg: str = ""):
    """Assert HTTP status code with helpful failure message."""
    body = ""
    try:
        body = response.json()
    except Exception:
        body = response.text[:500]
    assert response.status_code == expected, (
        f"{msg}\nExpected {expected}, got {response.status_code}\nBody: {body}"
    )
