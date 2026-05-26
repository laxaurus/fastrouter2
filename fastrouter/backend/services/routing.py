import time
import json
import hashlib
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import get_settings
from backend.models.provider_key import ProviderKey
from backend.routes.provider_keys import decrypt_api_key

settings = get_settings()


class LiteLLMRouter:
    """Forwards requests to LiteLLM proxy, injecting the customer's provider API key."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))

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
        provider = self._resolve_provider(model)
        api_key = await self._get_provider_key(user_id, provider, db)

        if api_key is None:
            raise ValueError(f"No API key found for provider '{provider}'. Add one in the dashboard.")

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **{k: v for k, v in kwargs.items() if v is not None},
        }

        headers = {
            "Authorization": f"Bearer {settings.litellm_master_key}",
            "Content-Type": "application/json",
        }

        start = time.time()
        response = await self.client.post(
            f"{settings.litellm_url}/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        latency_ms = int((time.time() - start) * 1000)

        if response.status_code != 200:
            raise RuntimeError(f"Provider error ({response.status_code}): {response.text[:500]}")

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
        provider = self._resolve_provider(model)
        api_key = await self._get_provider_key(user_id, provider, db)

        if api_key is None:
            raise ValueError(f"No API key found for provider '{provider}'.")

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **{k: v for k, v in kwargs.items() if v is not None},
        }

        headers = {
            "Authorization": f"Bearer {settings.litellm_master_key}",
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
                raise RuntimeError(f"Provider error ({response.status_code}): {body[:500]}")

            async for chunk in response.aiter_bytes():
                yield chunk

    def _resolve_provider(self, model: str) -> str:
        model_lower = model.lower()
        if "deepseek" in model_lower:
            return "deepseek"
        if "qwen" in model_lower:
            return "qwen"
        # Default - try DeepSeek first (cheapest)
        return "deepseek"

    async def _get_provider_key(self, user_id: str, provider: str, db: AsyncSession) -> Optional[str]:
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

    async def close(self):
        await self.client.aclose()


router = LiteLLMRouter()


def generate_cache_key(messages: list[dict], model: str) -> str:
    content = json.dumps({"messages": messages, "model": model}, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
