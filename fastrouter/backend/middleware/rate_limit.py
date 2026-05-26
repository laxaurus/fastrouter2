import time

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from backend.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple sliding-window rate limiter backed by Redis."""

    def __init__(self, app, redis_client: redis.Redis, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        # Use API key or IP as identifier
        auth = request.headers.get("Authorization", "")
        identifier = auth.replace("Bearer ", "")[:32] if auth else request.client.host
        key = f"ratelimit:{identifier}"

        current = await self.redis.get(key)
        count = int(current) if current else 0

        if count >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window_seconds)
        await pipe.execute()

        return await call_next(request)
