from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://fastrouter:fastrouter@localhost:5432/fastrouter"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Encryption
    encryption_key: str = "change-me-32-bytes-key-here!!"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""

    # LiteLLM
    litellm_url: str = "http://localhost:4000"
    litellm_master_key: str = "sk-master-key-fastrouter"

    # Free tier
    free_requests_limit: int = 1000

    # LiteLLM config
    litellm_config_path: str = "../fastrouter-oss/litellm/config.yaml"

    # Admin
    admin_emails: str = ""

    # App
    app_env: str = "development"
    debug: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
