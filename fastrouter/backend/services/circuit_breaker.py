from datetime import datetime, timezone
from enum import Enum

import redis.asyncio as redis


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Redis-backed circuit breaker for provider failover."""

    def __init__(
        self,
        redis_client: redis.Redis,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ):
        self.redis = redis_client
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    async def before_call(self, provider: str) -> None:
        state = await self._get_state(provider)

        if state == CircuitState.OPEN:
            last_failure = await self._get_last_failure(provider)
            if last_failure:
                elapsed = (datetime.now(timezone.utc) - last_failure).total_seconds()
                if elapsed > self.recovery_timeout:
                    await self._set_state(provider, CircuitState.HALF_OPEN)
                    return
            raise CircuitOpenError(f"Circuit open for {provider}. Requests blocked.")

    async def on_success(self, provider: str):
        state = await self._get_state(provider)
        await self._record_success(provider)
        if state == CircuitState.HALF_OPEN:
            success_count = await self._get_success_count(provider)
            if success_count >= 3:
                await self._reset(provider)

    async def on_failure(self, provider: str):
        await self._record_failure(provider)
        failure_count = await self._get_failure_count(provider)
        if failure_count >= self.failure_threshold:
            await self._set_state(provider, CircuitState.OPEN)

    async def get_state(self, provider: str) -> CircuitState:
        return await self._get_state(provider)

    async def get_health(self) -> list[dict]:
        providers = ["deepseek", "qwen"]
        result = []
        for p in providers:
            state = await self._get_state(p)
            failures = await self._get_failure_count(p)
            result.append({
                "provider": p,
                "state": state.value,
                "failure_count": failures,
            })
        return result

    async def _get_state(self, provider: str) -> CircuitState:
        val = await self.redis.get(f"cb:{provider}:state")
        return CircuitState(val.decode()) if val else CircuitState.CLOSED

    async def _set_state(self, provider: str, state: CircuitState):
        await self.redis.set(f"cb:{provider}:state", state.value)

    async def _record_failure(self, provider: str):
        pipe = self.redis.pipeline()
        pipe.incr(f"cb:{provider}:failures")
        pipe.set(f"cb:{provider}:last_failure", datetime.now(timezone.utc).isoformat())
        await pipe.execute()

    async def _record_success(self, provider: str):
        await self.redis.incr(f"cb:{provider}:successes")

    async def _get_failure_count(self, provider: str) -> int:
        val = await self.redis.get(f"cb:{provider}:failures")
        return int(val) if val else 0

    async def _get_success_count(self, provider: str) -> int:
        val = await self.redis.get(f"cb:{provider}:successes")
        return int(val) if val else 0

    async def _get_last_failure(self, provider: str) -> datetime | None:
        val = await self.redis.get(f"cb:{provider}:last_failure")
        if val:
            return datetime.fromisoformat(val.decode())
        return None

    async def _reset(self, provider: str):
        await self.redis.delete(f"cb:{provider}:state")
        await self.redis.delete(f"cb:{provider}:failures")
        await self.redis.delete(f"cb:{provider}:successes")


class CircuitOpenError(Exception):
    pass
