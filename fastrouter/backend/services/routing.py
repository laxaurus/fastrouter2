import time
import json
import hashlib
import logging
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.routes.provider_keys import get_provider_key

settings = get_settings()
logger = logging.getLogger(__name__)

_model_map: dict[str, str] = {}
_model_providers: list[str] = []


async def load_model_map(db: AsyncSession) -> None:
    """Load model→provider mappings from DB into an in-memory cache."""
    global _model_map, _model_providers
    from backend.models.provider_model import ProviderModel

    result = await db.execute(
        select(ProviderModel).where(ProviderModel.is_active == True)
    )
    models = result.scalars().all()
    _model_map = {m.model_name.lower(): m.provider for m in models}
    _model_providers = sorted(set(m.provider for m in models))


def get_model_map() -> dict[str, str]:
    """Return a snapshot of the current model→provider cache."""
    return dict(_model_map)


def get_model_providers() -> list[str]:
    """Return the list of known providers from the cache."""
    return list(_model_providers)


class LiteLLMRouter:
    """Forwards requests to LiteLLM proxy using customer virtual keys."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        return self._client

    @staticmethod
    def resolve_provider(model: str) -> str:
        model_lower = model.lower()
        # Exact match first
        if model_lower in _model_map:
            return _model_map[model_lower]
        # Fuzzy match on known model names
        for model_name, provider in _model_map.items():
            if model_name in model_lower or model_lower in model_name:
                return provider
        # Fallback: match on provider name
        for provider in _model_providers:
            if provider in model_lower:
                return provider
        return _model_providers[0] if _model_providers else "deepseek"

    async def route(
        self,
        model: str,
        messages: list[dict],
        user_id: str,
        db: AsyncSession,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        **kwargs,
    ) -> dict:
        provider = self.resolve_provider(model)
        keys = await get_provider_key(user_id, provider, db)

        if keys is None:
            raise ValueError(
                f"No API key found for provider '{provider}'. Add one in the dashboard."
            )
        decrypted_key, lite_key = keys

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            "api_key": decrypted_key,
            **{k: v for k, v in kwargs.items() if v is not None},
        }

        headers = {
            "Authorization": f"Bearer {lite_key or settings.litellm_master_key}",
            "Content-Type": "application/json",
        }

        if lite_key is None:
            logger.warning(
                "No virtual key for user=%s provider=%s — falling back to master key. "
                "Customer will NOT be billed by their provider.",
                user_id, provider,
            )

        start = time.time()
        response = await self.client.post(
            f"{settings.litellm_url}/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        latency_ms = int((time.time() - start) * 1000)

        if response.status_code != 200:
            raise RuntimeError(
                f"Provider error ({response.status_code}): {response.text[:500]}"
            )

        data = response.json()

        litellm_cost = response.headers.get("x-litellm-response-cost")
        cost = float(litellm_cost) if litellm_cost else 0.0

        usage = data.get("usage", {})
        return {
            "provider": provider,
            "model": data.get("model", model),
            "content": data["choices"][0]["message"]["content"],
            "choices": data["choices"],
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "latency_ms": latency_ms,
            "cost_usd": cost,
            "cached": False,
            "stream": False,
        }

    async def route_stream(
        self,
        model: str,
        messages: list[dict],
        user_id: str,
        db: AsyncSession,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ):
        provider = self.resolve_provider(model)
        keys = await get_provider_key(user_id, provider, db)

        if keys is None:
            raise ValueError(f"No API key found for provider '{provider}'.")
        decrypted_key, lite_key = keys

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "api_key": decrypted_key,
            **{k: v for k, v in kwargs.items() if v is not None},
        }

        headers = {
            "Authorization": f"Bearer {lite_key or settings.litellm_master_key}",
            "Content-Type": "application/json",
        }

        async with self.client.stream(
            "POST",
            f"{settings.litellm_url}/v1/chat/completions",
            json=payload,
            headers=headers,
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                raise RuntimeError(
                    f"Provider error ({response.status_code}): {body[:500]}"
                )

            async for chunk in response.aiter_bytes():
                yield chunk

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


router = LiteLLMRouter()


def generate_cache_key(messages: list[dict], model: str) -> str:
    content = json.dumps({"messages": messages, "model": model}, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
