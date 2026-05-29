from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, select, func

from backend.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def run_migrations():
    """Run idempotent schema migrations for column additions."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='role'
                ) THEN
                    ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';
                END IF;
            END $$;
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='provider_models' AND column_name='input_cost_per_token'
                ) THEN
                    ALTER TABLE provider_models ADD COLUMN input_cost_per_token DOUBLE PRECISION;
                    ALTER TABLE provider_models ADD COLUMN output_cost_per_token DOUBLE PRECISION;
                END IF;
            END $$;
        """))


SEED_MODELS = [
    {"model_name": "deepseek-chat", "provider": "deepseek", "api_base": "https://api.deepseek.com/v1",
     "input_cost_per_token": 0.00000014, "output_cost_per_token": 0.00000028},
    {"model_name": "deepseek-reasoner", "provider": "deepseek", "api_base": "https://api.deepseek.com/v1",
     "input_cost_per_token": 0.00000055, "output_cost_per_token": 0.00000219},
    {"model_name": "qwen-plus", "provider": "qwen", "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
     "input_cost_per_token": 0.00000080, "output_cost_per_token": 0.00000200},
    {"model_name": "qwen-max", "provider": "qwen", "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
     "input_cost_per_token": 0.00000240, "output_cost_per_token": 0.00000960},
    {"model_name": "qwen-turbo", "provider": "qwen", "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
     "input_cost_per_token": 0.00000030, "output_cost_per_token": 0.00000120},
    {"model_name": "kimi-latest", "provider": "kimi", "api_base": "https://api.moonshot.cn/v1",
     "input_cost_per_token": 0.00000020, "output_cost_per_token": 0.00000060},
    {"model_name": "glm-4", "provider": "glm", "api_base": "https://open.bigmodel.cn/api/paas/v4",
     "input_cost_per_token": 0.00000010, "output_cost_per_token": 0.00000010},
    {"model_name": "glm-4-flash", "provider": "glm", "api_base": "https://open.bigmodel.cn/api/paas/v4",
     "input_cost_per_token": 0.000000014, "output_cost_per_token": 0.000000014},
]


async def seed_defaults(db: AsyncSession):
    """Seed provider_models table if empty."""
    from backend.models.provider_model import ProviderModel

    result = await db.execute(select(func.count(ProviderModel.id)))
    if result.scalar() == 0:
        for m in SEED_MODELS:
            db.add(ProviderModel(**m))
        await db.commit()


async def ensure_admin_users(db: AsyncSession):
    """Promote users to admin based on ADMIN_EMAILS env var."""
    from backend.models.user import User

    if settings.admin_emails:
        emails = [e.strip() for e in settings.admin_emails.split(",") if e.strip()]
        for email in emails:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user and user.role != "admin":
                user.role = "admin"
        await db.commit()
