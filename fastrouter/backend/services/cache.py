import json
from typing import Optional

import redis.asyncio as redis

from backend.config import get_settings

settings = get_settings()


class PromptCache:
    """Per-user prompt cache backed by Redis. Reduces repeat provider calls on BYOK keys."""

    CACHE_TTL = 3600  # 1 hour

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get(self, user_id: str, cache_key: str) -> Optional[dict]:
        data = await self.redis.get(f"cache:{user_id}:{cache_key}")
        if data:
            return json.loads(data)
        return None

    async def set(self, user_id: str, cache_key: str, response: dict, ttl: int = CACHE_TTL):
        cache_data = {
            "content": response.get("content"),
            "choices": response.get("choices"),
            "usage": response.get("usage"),
            "provider": response.get("provider"),
            "model": response.get("model"),
        }
        await self.redis.setex(
            f"cache:{user_id}:{cache_key}",
            ttl,
            json.dumps(cache_data, default=str),
        )

    async def invalidate_user(self, user_id: str):
        keys = await self.redis.keys(f"cache:{user_id}:*")
        if keys:
            await self.redis.delete(*keys)
